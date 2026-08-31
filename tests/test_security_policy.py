import datetime as dt
import unittest

from pathlib import Path

from container_factory.security.policy import (
    load_policy,
    ExceptionRule,
    Finding,
    Policy,
    evaluate,
    parse_findings,
    print_report,
)


class SecurityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = Policy(
            fail_severity=frozenset({"critical", "high"}),
            ignore_severity=frozenset({"medium", "low", "negligible", "unknown"}),
            high_cvss_threshold=7.0,
            no_fix_action="review",
            image_exceptions={},
        )
        self.today = dt.date(2026, 8, 12)

    def finding(self, **kwargs):
        values = dict(
            vulnerability_id="CVE-TEST-1", severity="high", cvss=8.0,
            fix_state="fixed", fix_available=True, package="example", installed="1.0",
        )
        values.update(kwargs)
        return Finding(**values)

    def policy_with_exception(self, expires=dt.date(2026, 9, 30)):
        return Policy(
            **{
                **self.policy.__dict__,
                "image_exceptions": {
                    "python": {
                        "CVE-TEST-1": ExceptionRule(
                            "CVE-TEST-1", "Temporary exception.", expires
                        )
                    }
                },
            }
        )


    def test_repository_policy_contains_python_exception(self):
        policy = load_policy(Path(".config/security-policy.yaml"))
        rule = policy.image_exceptions["python"]["CVE-2026-15308"]
        self.assertEqual(rule.expires, dt.date(2026, 9, 30))
        self.assertIn("html.parser.HTMLParser", rule.reason)

    def test_fixed_high_fails(self):
        result = evaluate([self.finding()], self.policy, today=self.today)
        self.assertEqual(len(result["failures"]), 1)

    def test_unfixed_critical_is_review_only(self):
        result = evaluate([self.finding(severity="critical", cvss=9.8, fix_available=False, fix_state="wont-fix")], self.policy, today=self.today)
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["reviews"]), 1)

    def test_exception_suppresses_finding(self):
        result = evaluate([self.finding()], self.policy_with_exception(), image="python", today=self.today)
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["exceptions"]), 1)

    def test_exception_is_scoped_to_image(self):
        result = evaluate([self.finding()], self.policy_with_exception(), image="hello", today=self.today)
        self.assertEqual(len(result["failures"]), 1)
        self.assertFalse(result["exceptions"])

    def test_expired_exception_fails(self):
        result = evaluate([self.finding()], self.policy_with_exception(dt.date(2026, 8, 1)), image="python", today=self.today)
        self.assertEqual(len(result["failures"]), 1)
        self.assertEqual(len(result["expired"]), 1)

    def test_high_below_cvss_threshold_is_ignored(self):
        result = evaluate([self.finding(cvss=6.9)], self.policy, today=self.today)
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["ignored"]), 1)

    def test_high_at_cvss_threshold_fails(self):
        result = evaluate([self.finding(cvss=7.0)], self.policy, today=self.today)
        self.assertEqual(len(result["failures"]), 1)

    def test_no_fix_can_fail_closed(self):
        policy = Policy(**{**self.policy.__dict__, "no_fix_action": "fail"})
        result = evaluate([self.finding(fix_available=False, fix_state="wont-fix")], policy, today=self.today)
        self.assertEqual(len(result["failures"]), 1)

    def test_expiring_today_exception_is_still_active(self):
        result = evaluate([self.finding()], self.policy_with_exception(self.today), image="python", today=self.today)
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["exceptions"]), 1)

    def test_medium_is_ignored(self):
        result = evaluate([self.finding(severity="medium", cvss=5.0)], self.policy, today=self.today)
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["ignored"]), 1)


class ParseFindingsTests(unittest.TestCase):
    def _match(self, **kwargs) -> dict:
        base = {
            "vulnerability": {
                "id": "CVE-TEST-1",
                "severity": "High",
                "cvss": [{"metrics": {"baseScore": 8.1}}],
                "fix": {"state": "fixed", "versions": ["1.2.3"]},
            },
            "artifact": {"name": "libfoo", "version": "1.0.0"},
        }
        base["vulnerability"].update(kwargs.get("vulnerability", {}))
        if "artifact" in kwargs:
            base["artifact"].update(kwargs["artifact"])
        return base

    def test_parses_basic_finding(self):
        report = {"matches": [self._match()]}
        findings = parse_findings(report)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f.vulnerability_id, "CVE-TEST-1")
        self.assertEqual(f.severity, "high")
        self.assertAlmostEqual(f.cvss, 8.1)
        self.assertTrue(f.fix_available)
        self.assertEqual(f.fix_state, "fixed")
        self.assertEqual(f.package, "libfoo")
        self.assertEqual(f.installed, "1.0.0")

    def test_empty_matches_returns_empty_list(self):
        self.assertEqual(parse_findings({"matches": []}), [])

    def test_missing_matches_key_returns_empty_list(self):
        self.assertEqual(parse_findings({}), [])

    def test_missing_cvss_defaults_to_zero(self):
        match = self._match()
        match["vulnerability"]["cvss"] = []
        findings = parse_findings({"matches": [match]})
        self.assertEqual(findings[0].cvss, 0.0)

    def test_fix_available_from_versions_list(self):
        match = self._match()
        match["vulnerability"]["fix"] = {"state": "unknown", "versions": ["2.0.0"]}
        findings = parse_findings({"matches": [match]})
        self.assertTrue(findings[0].fix_available)

    def test_no_fix_available_when_no_versions_and_not_fixed_state(self):
        match = self._match()
        match["vulnerability"]["fix"] = {"state": "wont-fix", "versions": []}
        findings = parse_findings({"matches": [match]})
        self.assertFalse(findings[0].fix_available)

    def test_severity_is_lowercased(self):
        match = self._match(vulnerability={"severity": "CRITICAL"})
        findings = parse_findings({"matches": [match]})
        self.assertEqual(findings[0].severity, "critical")


class PrintReportTests(unittest.TestCase):
    def _finding(self, **kwargs):
        base = dict(
            vulnerability_id="CVE-TEST-1", severity="high", cvss=8.0,
            fix_state="fixed", fix_available=True, package="lib", installed="1.0",
        )
        base.update(kwargs)
        return Finding(**base)

    def _capture(self, result, total=1):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_report(result, total=total)
        return buf.getvalue()

    def _empty_result(self):
        return {"failures": [], "reviews": [], "ignored": [], "exceptions": [], "expired": []}

    def test_passing_gate_prints_passed(self):
        output = self._capture(self._empty_result(), total=0)
        self.assertIn("PASSED", output)

    def test_failing_gate_prints_failed_and_cve(self):
        result = {**self._empty_result(), "failures": [self._finding()]}
        output = self._capture(result)
        self.assertIn("FAILED", output)
        self.assertIn("CVE-TEST-1", output)

    def test_review_finding_is_printed(self):
        f = self._finding(fix_available=False, fix_state="wont-fix")
        result = {**self._empty_result(), "reviews": [f]}
        output = self._capture(result)
        self.assertIn("REVIEW", output)
        self.assertIn("CVE-TEST-1", output)

    def test_expired_exception_is_printed(self):
        import datetime as dt
        f = self._finding()
        rule = ExceptionRule("CVE-TEST-1", "reason", dt.date(2020, 1, 1))
        result = {**self._empty_result(), "expired": [(f, rule)], "failures": [f]}
        output = self._capture(result)
        self.assertIn("EXPIRED", output)


class PolicyVersionTests(unittest.TestCase):
    def _write_policy(self, content: str) -> "Path":
        import tempfile
        from pathlib import Path
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        return Path(f.name)

    def test_version_1_is_accepted(self):
        p = self._write_policy("version: 1\nsecurity:\n  fail_severity: []\n  ignore_severity: []\n")
        load_policy(p)

    def test_unsupported_version_raises(self):
        p = self._write_policy("version: 2\nsecurity:\n  fail_severity: []\n  ignore_severity: []\n")
        with self.assertRaisesRegex(ValueError, "unsupported policy schema version"):
            load_policy(p)

    def test_missing_version_is_accepted(self):
        p = self._write_policy("security:\n  fail_severity: []\n  ignore_severity: []\n")
        load_policy(p)


if __name__ == "__main__":
    unittest.main()

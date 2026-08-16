import datetime as dt
import unittest

from pathlib import Path

from container_factory.security.policy import (
    load_policy,
    ExceptionRule,
    Finding,
    Policy,
    evaluate,
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
            vulnerability_id="CVE-TEST-1",
            severity="high",
            cvss=8.0,
            fix_state="fixed",
            fix_available=True,
            package="example",
            installed="1.0",
        )
        values.update(kwargs)
        return Finding(**values)

    def policy_with_exception(self, expires=dt.date(2026, 12, 30)):
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
        self.assertEqual(rule.expires, dt.date(2026, 12, 30))
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


if __name__ == "__main__":
    unittest.main()

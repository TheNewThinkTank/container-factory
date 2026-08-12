import datetime as dt
import unittest

from container_factory.security.policy import (
    Finding,
    ExceptionRule,
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
            exceptions={},
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

    def test_fixed_high_fails(self):
        result = evaluate([self.finding()], self.policy, today=self.today)
        self.assertEqual(len(result["failures"]), 1)
        self.assertFalse(result["reviews"])

    def test_unfixed_critical_is_review_only(self):
        result = evaluate(
            [self.finding(severity="critical", cvss=9.8, fix_available=False, fix_state="wont-fix")],
            self.policy,
            today=self.today,
        )
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["reviews"]), 1)

    def test_exception_suppresses_finding(self):
        policy = Policy(
            **{
                **self.policy.__dict__,
                "exceptions": {
                    "CVE-TEST-1": ExceptionRule(
                        "CVE-TEST-1",
                        "No fix available; accepted temporarily.",
                        dt.date(2026, 9, 30),
                    )
                },
            }
        )
        result = evaluate([self.finding()], policy, today=self.today)
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["exceptions"]), 1)

    def test_expired_exception_fails(self):
        policy = Policy(
            **{
                **self.policy.__dict__,
                "exceptions": {
                    "CVE-TEST-1": ExceptionRule(
                        "CVE-TEST-1",
                        "Temporary exception.",
                        dt.date(2026, 8, 1),
                    )
                },
            }
        )
        result = evaluate([self.finding()], policy, today=self.today)
        self.assertEqual(len(result["failures"]), 1)
        self.assertEqual(len(result["expired"]), 1)

    def test_medium_is_ignored(self):
        result = evaluate(
            [self.finding(severity="medium", cvss=5.0)],
            self.policy,
            today=self.today,
        )
        self.assertFalse(result["failures"])
        self.assertEqual(len(result["ignored"]), 1)


if __name__ == "__main__":
    unittest.main()

"""Evaluate a Grype JSON report against the container-factory security policy."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Finding:
    vulnerability_id: str
    severity: str
    cvss: float
    fix_state: str
    fix_available: bool
    package: str
    installed: str


@dataclass(frozen=True)
class ExceptionRule:
    vulnerability_id: str
    reason: str
    expires: dt.date


@dataclass(frozen=True)
class Policy:
    fail_severity: frozenset[str]
    ignore_severity: frozenset[str]
    high_cvss_threshold: float
    no_fix_action: str
    exceptions: dict[str, ExceptionRule]


def load_policy(path: Path) -> Policy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    security = raw.get("security")
    if not isinstance(security, dict):
        raise ValueError("policy must contain a 'security' mapping")

    fail_severity = frozenset(
        str(value).lower() for value in security.get("fail_severity", [])
    )
    ignore_severity = frozenset(
        str(value).lower() for value in security.get("ignore_severity", [])
    )

    threshold = float(security.get("high_cvss_threshold", 7.0))
    if not 0 <= threshold <= 10:
        raise ValueError("high_cvss_threshold must be between 0 and 10")

    no_fix_action = str(security.get("no_fix_action", "review")).lower()
    if no_fix_action not in {"review", "fail"}:
        raise ValueError("no_fix_action must be 'review' or 'fail'")

    exceptions: dict[str, ExceptionRule] = {}
    for item in security.get("exceptions", []):
        if not isinstance(item, dict):
            raise ValueError("each exception must be a mapping")
        vuln_id = str(item.get("id", "")).strip()
        reason = str(item.get("reason", "")).strip()
        expires_text = str(item.get("expires", "")).strip()
        if not vuln_id or not reason or not expires_text:
            raise ValueError("exceptions require id, reason and expires")
        expires = dt.date.fromisoformat(expires_text)
        if vuln_id in exceptions:
            raise ValueError(f"duplicate exception: {vuln_id}")
        exceptions[vuln_id] = ExceptionRule(vuln_id, reason, expires)

    return Policy(
        fail_severity=fail_severity,
        ignore_severity=ignore_severity,
        high_cvss_threshold=threshold,
        no_fix_action=no_fix_action,
        exceptions=exceptions,
    )


def _cvss(match: dict[str, Any]) -> float:
    scores: list[float] = []
    for item in match.get("vulnerability", {}).get("cvss", []) or []:
        metrics = item.get("metrics", {}) or {}
        score = metrics.get("baseScore")
        if score is not None:
            try:
                scores.append(float(score))
            except (TypeError, ValueError):
                pass
    return max(scores, default=0.0)


def _fix(match: dict[str, Any]) -> tuple[str, bool]:
    fix = match.get("vulnerability", {}).get("fix", {}) or {}
    state = str(fix.get("state", "")).lower() or "unknown"
    versions = fix.get("versions", []) or []
    # Grype commonly reports a fixed version through versions + state=fixed.
    available = bool(versions) or state == "fixed"
    return state, available


def parse_findings(report: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for match in report.get("matches", []) or []:
        vulnerability = match.get("vulnerability", {}) or {}
        artifact = match.get("artifact", {}) or {}
        state, available = _fix(match)
        findings.append(
            Finding(
                vulnerability_id=str(vulnerability.get("id", "UNKNOWN")),
                severity=str(vulnerability.get("severity", "unknown")).lower(),
                cvss=_cvss(match),
                fix_state=state,
                fix_available=available,
                package=str(artifact.get("name", "unknown")),
                installed=str(artifact.get("version", "unknown")),
            )
        )
    return findings


def evaluate(
    findings: list[Finding],
    policy: Policy,
    *,
    today: dt.date | None = None,
) -> dict[str, Any]:
    today = today or dt.date.today()
    failures: list[Finding] = []
    reviews: list[Finding] = []
    ignored: list[Finding] = []
    exceptions: list[tuple[Finding, ExceptionRule]] = []
    expired: list[tuple[Finding, ExceptionRule]] = []

    for finding in findings:
        if finding.severity in policy.ignore_severity:
            ignored.append(finding)
            continue

        rule = policy.exceptions.get(finding.vulnerability_id)
        if rule:
            if rule.expires >= today:
                exceptions.append((finding, rule))
                continue
            expired.append((finding, rule))
            failures.append(finding)
            continue

        if finding.severity not in policy.fail_severity:
            ignored.append(finding)
            continue

        if (
            finding.severity == "high"
            and finding.cvss < policy.high_cvss_threshold
        ):
            ignored.append(finding)
            continue

        if not finding.fix_available:
            if policy.no_fix_action == "fail":
                failures.append(finding)
            else:
                reviews.append(finding)
            continue

        failures.append(finding)

    return {
        "failures": failures,
        "reviews": reviews,
        "ignored": ignored,
        "exceptions": exceptions,
        "expired": expired,
    }


def print_report(result: dict[str, Any], total: int) -> None:
    print()
    print("Container Security Report")
    print("=========================")
    print(f"Total findings:       {total}")
    print(f"Policy failures:      {len(result['failures'])}")
    print(f"Review findings:      {len(result['reviews'])}")
    print(f"Active exceptions:    {len(result['exceptions'])}")
    print(f"Expired exceptions:   {len(result['expired'])}")
    print(f"Ignored findings:     {len(result['ignored'])}")

    if result["reviews"]:
        print("\nREVIEW — high/critical findings without an available fix:")
        for finding in result["reviews"]:
            print(
                f"  - {finding.vulnerability_id}: "
                f"{finding.severity}, CVSS {finding.cvss:.1f}, "
                f"{finding.package} {finding.installed}, "
                f"fix={finding.fix_state}"
            )

    if result["exceptions"]:
        print("\nEXCEPTIONS:")
        for finding, rule in result["exceptions"]:
            print(
                f"  - {finding.vulnerability_id}: "
                f"expires {rule.expires.isoformat()} — {rule.reason}"
            )

    if result["expired"]:
        print("\nEXPIRED EXCEPTIONS:")
        for finding, rule in result["expired"]:
            print(
                f"  - {finding.vulnerability_id}: "
                f"expired {rule.expires.isoformat()}"
            )

    if result["failures"]:
        print("\nSecurity policy FAILED:")
        for finding in result["failures"]:
            fix = "fix available" if finding.fix_available else "no fix available"
            print(
                f"  - {finding.vulnerability_id}: "
                f"severity={finding.severity}, "
                f"cvss={finding.cvss:.1f}, "
                f"{fix}"
            )
    else:
        print("\nSecurity policy PASSED.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("policy", type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    policy = load_policy(args.policy)
    findings = parse_findings(report)
    result = evaluate(findings, policy)
    print_report(result, len(findings))

    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

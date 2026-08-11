#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:?IMAGE is required}"
TAG="${TAG:-local}"
POLICY="${POLICY:-.config/security-policy.yaml}"
MAX_CVSS="${MAX_CVSS:-}"

command -v grype >/dev/null 2>&1 || {
  echo "grype is required: https://github.com/anchore/grype" >&2
  exit 1
}

if [[ -z "${MAX_CVSS}" ]]; then
  MAX_CVSS="$(
    python3 - "${POLICY}" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r"^max_cvss:\s*([0-9]+(?:\.[0-9]+)?)\s*$", text, re.M)
if not match:
    raise SystemExit("Policy must contain max_cvss")
print(match.group(1))
PY
  )"
fi

echo "Scanning container-factory/${IMAGE}:${TAG}"
echo "Failing on CVSS >= ${MAX_CVSS}"

grype "container-factory/${IMAGE}:${TAG}" -o table

# Capture grype JSON output to a temp file
GRYPE_JSON=$(mktemp)
if ! grype "container-factory/${IMAGE}:${TAG}" -o json > "$GRYPE_JSON" 2>&1; then
  echo "Error: grype scan failed" >&2
  cat "$GRYPE_JSON" >&2
  rm -f "$GRYPE_JSON"
  exit 1
fi

if [[ ! -s "$GRYPE_JSON" ]]; then
  echo "Error: grype produced no output" >&2
  cat "$GRYPE_JSON" >&2
  rm -f "$GRYPE_JSON"
  exit 1
fi

# Parse with Python, passing the file path as an argument
python3 - "${GRYPE_JSON}" "${MAX_CVSS}" <<'PY'
import json
import sys

grype_json_file = sys.argv[1]
max_cvss = float(sys.argv[2])

with open(grype_json_file) as f:
    report = json.load(f)

violations = []
for match in report.get("matches", []):
    vuln = match.get("vulnerability", {})
    severity = str(vuln.get("severity", "")).lower()
    scores = vuln.get("cvss", [])
    score = max(
        (entry.get("metrics", {}).get("baseScore") for entry in scores
         if entry.get("metrics", {}).get("baseScore") is not None),
        default=None,
    )

    if severity in ("critical", "unknown") or (score is not None and float(score) >= max_cvss):
        violations.append(
            f"{vuln.get('id', 'unknown')}: severity={severity}, cvss={score}"
        )

if violations:
    print("\nSecurity policy FAILED:")
    for violation in violations:
        print(f"  - {violation}")
    raise SystemExit(1)

print("\nSecurity policy PASSED.")
PY

# Clean up temp file
rm -f "$GRYPE_JSON"

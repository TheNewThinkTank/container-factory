#!/usr/bin/env bash
set -euo pipefail

REPORT="${1:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY="${POLICY_FILE:-${ROOT}/.config/security-policy.yaml}"
SECURITY_PYTHON="${SECURITY_PYTHON:-python3}"

if [[ -z "${REPORT}" ]]; then
    echo "Usage: $0 <grype-json-report>" >&2
    exit 2
fi

[[ -f "${REPORT}" ]] || { echo "ERROR: Report not found: ${REPORT}" >&2; exit 2; }
[[ -f "${POLICY}" ]] || { echo "ERROR: Security policy not found: ${POLICY}" >&2; exit 2; }

PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"     "${SECURITY_PYTHON}" -m container_factory.security.policy     "${REPORT}" "${POLICY}"

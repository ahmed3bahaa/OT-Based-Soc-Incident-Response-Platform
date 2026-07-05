#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURE_DIR="$PROJECT_ROOT/wazuh/tests/fixtures"
LOGTEST="/var/ossec/bin/wazuh-logtest"

run_test() {
    local name="$1"
    local fixture="$2"
    local expected_rule="$3"
    local expected_level="$4"
    local output

    # wazuh-logtest writes important output to stderr,
    # so capture both stdout and stderr.
    output="$(sudo "$LOGTEST" < "$fixture" 2>&1)"

    if ! grep -Fq "id: '$expected_rule'" <<<"$output"; then
        echo "FAIL: $name did not match rule $expected_rule"
        echo "$output"
        return 1
    fi

    if ! grep -Fq "level: '$expected_level'" <<<"$output"; then
        echo "FAIL: $name did not produce level $expected_level"
        echo "$output"
        return 1
    fi

    echo "PASS: $name -> rule $expected_rule, level $expected_level"
}

run_test \
    "successful OPC UA write" \
    "$FIXTURE_DIR/success.json" \
    "110100" \
    "0"

run_test \
    "failed OPC UA write" \
    "$FIXTURE_DIR/failure.json" \
    "110101" \
    "7"

run_test \
    "verification mismatch" \
    "$FIXTURE_DIR/verification_mismatch.json" \
    "110102" \
    "10"

echo "All OPC UA Wazuh rule tests passed."

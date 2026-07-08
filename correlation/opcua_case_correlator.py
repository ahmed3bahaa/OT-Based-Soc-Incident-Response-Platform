#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WATCH_RULES = {
    "110103", "110104", "110105",
    "110200", "110201", "110202", "110203", "110204", "110205",
}


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_json_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("rb") as f:
        for raw in f:
            raw = raw.replace(b"\x00", b"").strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def rule_id(alert: dict[str, Any]) -> str:
    return str(alert.get("rule", {}).get("id", ""))


def get_nested(obj: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
    return cur if cur is not None else default


def evidence(alert: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": alert.get("timestamp"),
        "rule_id": rule_id(alert),
        "description": alert.get("rule", {}).get("description"),
        "agent": alert.get("agent", {}).get("name"),
        "location": alert.get("location"),
    }


def classify(rule_ids: set[str]) -> str:
    if {"110202", "110203", "110205"} & rule_ids:
        return "suspicious_ot_operation"
    if {"110201", "110204"} & rule_ids:
        return "important_ot_operation"
    return "validation_not_malicious"


def correlate(alerts: list[dict[str, Any]], window_seconds: int) -> list[dict[str, Any]]:
    timed: list[tuple[datetime, dict[str, Any]]] = []

    for alert in alerts:
        rid = rule_id(alert)
        if rid not in WATCH_RULES:
            continue
        ts = parse_ts(str(alert.get("timestamp", "")))
        if ts:
            timed.append((ts, alert))

    process_rules = {"110103", "110200", "110201", "110202", "110203", "110204"}
    process_events = [(ts, a) for ts, a in timed if rule_id(a) in process_rules]
    flow_events = [(ts, a) for ts, a in timed if rule_id(a) == "110104"]
    diag_events = [(ts, a) for ts, a in timed if rule_id(a) == "110105"]

    cases: list[dict[str, Any]] = []

    for pts, p in process_events:
        nearest_flow: tuple[datetime, dict[str, Any]] | None = None
        nearest_delta: float | None = None

        for fts, f in flow_events:
            delta = abs((pts - fts).total_seconds())
            if delta <= window_seconds and (nearest_delta is None or delta < nearest_delta):
                nearest_flow = (fts, f)
                nearest_delta = delta

        if nearest_flow is None:
            continue

        evs = [p, nearest_flow[1]]

        for dts, d in diag_events:
            if abs((pts - dts).total_seconds()) <= window_seconds:
                evs.append(d)
                break

        ids = {rule_id(e) for e in evs}
        p_data = p.get("data", {})
        f_data = nearest_flow[1].get("data", {})

        cases.append(
            {
                "case_type": "confirmed_opcua_operation",
                "classification": classify(ids),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "correlation_window_seconds": window_seconds,
                "tag": get_nested(p_data, "ot.tag", "unknown"),
                "node_id": get_nested(p_data, "ot.node_id", "unknown"),
                "old_value": get_nested(p_data, "ot.old_value", None),
                "new_value": get_nested(p_data, "ot.new_value", None),
                "source_ip": get_nested(f_data, "src_ip", None),
                "destination_ip": get_nested(f_data, "dest_ip", None),
                "destination_port": get_nested(f_data, "dest_port", None),
                "rule_ids": sorted(ids),
                "evidence": [evidence(e) for e in evs],
            }
        )

    # Simple dedupe
    seen = set()
    unique = []
    for c in cases:
        key = (c["tag"], tuple(c["rule_ids"]), c["destination_ip"], c["destination_port"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alerts", type=Path, default=Path("/var/ossec/logs/alerts/alerts.json"))
    parser.add_argument("--window-seconds", type=int, default=900)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows = load_json_lines(args.alerts)
    cases = correlate(rows, args.window_seconds)
    text = json.dumps(cases, indent=2, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    return 0 if cases else 2


if __name__ == "__main__":
    raise SystemExit(main())

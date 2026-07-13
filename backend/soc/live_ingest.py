from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from .catalog import seed_catalogs
from .importers import ImportResult, import_cases_payload, parse_timestamp
from .models import LiveAlert

WATCH_RULES = {
    "110103",
    "110104",
    "110105",
    "110200",
    "110201",
    "110202",
    "110203",
    "110204",
    "110205",
}

PROCESS_RULES = {
    "110103",
    "110200",
    "110201",
    "110202",
    "110203",
    "110204",
    "110205",
}

FLOW_RULE = "110104"
DIAGNOSTIC_RULE = "110105"

RULE_DESCRIPTIONS = {
    "110103": "OT OPC UA datachange observed by passive monitor - validation scenario",
    "110104": "OT OPC UA network flow observed by Suricata - validation scenario",
    "110105": "OT OPC UA write observed in KEPServerEX diagnostics - validation scenario",
    "110200": "OT simulator selected tag datachange observed - MVP rule",
    "110201": "OT simulator critical command tag changed",
    "110202": "OT simulator motor or pump command changed",
    "110203": "OT simulator valve command changed",
    "110204": "OT simulator water level tag changed",
    "110205": "OT repeated failed OPC UA write attempts observed",
}


@dataclass(frozen=True)
class LiveIngestResult:
    alerts_received: int = 0
    alerts_created: int = 0
    alerts_skipped: int = 0
    cases_created: int = 0
    cases_skipped: int = 0
    evidence_created: int = 0
    evidence_skipped: int = 0


def get_nested(obj: dict[str, Any], dotted: str, default: Any = None) -> Any:
    if dotted in obj:
        return obj[dotted]

    cur: Any = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return default
        if part in cur:
            cur = cur[part]
            continue
        return default
    return cur if cur is not None else default


def first_value(obj: dict[str, Any], paths: list[str], default: Any = None) -> Any:
    for path in paths:
        value = get_nested(obj, path)
        if value not in (None, ""):
            return value
    return default


def normalize_alert_object(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    if isinstance(item.get("_source"), dict):
        return item["_source"]
    return item


def extract_alert_objects(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [alert for item in payload if (alert := normalize_alert_object(item))]

    if not isinstance(payload, dict):
        return []

    hits = get_nested(payload, "hits.hits")
    if isinstance(hits, list):
        return [alert for item in hits if (alert := normalize_alert_object(item))]

    for path in (
        "alerts",
        "events",
        "items",
        "results",
        "data.alerts",
        "data.events",
        "data.items",
        "data.affected_items",
    ):
        value = get_nested(payload, path)
        if isinstance(value, list):
            return [alert for item in value if (alert := normalize_alert_object(item))]

    return [payload]


def infer_rule_id(alert: dict[str, Any]) -> str:
    explicit = first_value(
        alert,
        [
            "_live_rule_id",
            "rule.id",
            "rule_id",
            "wazuh.rule.id",
            "data.rule.id",
            "data.rule_id",
        ],
    )
    if explicit:
        return str(explicit)

    action = str(first_value(alert, ["event.action", "data.event.action"], "")).lower()
    event_type = str(first_value(alert, ["event_type", "data.event_type"], "")).lower()
    proto = str(first_value(alert, ["proto", "data.proto", "network.transport"], "")).lower()
    destination_port = str(
        first_value(alert, ["dest_port", "data.dest_port", "destination.port"], "")
    )
    tag = str(first_value(alert, ["data.ot.tag", "ot.tag"], "")).upper()

    if event_type == "flow" and proto == "tcp" and destination_port == "49320":
        return FLOW_RULE
    if action == "kepserver_opcua_write":
        return DIAGNOSTIC_RULE
    if action == "opcua_datachange":
        if tag in {"MOTOR1", "MOTOR2", "MOTOR3"}:
            return "110202"
        if tag == "VALF":
            return "110203"
        if tag == "SU_SEVIYESI":
            return "110204"
        return "110103"

    return ""


def alert_timestamp(alert: dict[str, Any]):
    return parse_timestamp(first_value(alert, ["_live_timestamp", "timestamp", "@timestamp"]))


def alert_agent(alert: dict[str, Any]) -> str:
    return str(
        first_value(
            alert,
            [
                "agent.name",
                "agent_name",
                "host.name",
                "host.hostname",
                "observer.name",
                "data.agent.name",
            ],
            "",
        )
        or ""
    )


def alert_location(alert: dict[str, Any]) -> str:
    return str(
        first_value(
            alert,
            ["location", "log.file.path", "file.path", "data.location"],
            "",
        )
        or ""
    )


def alert_fingerprint(alert: dict[str, Any], source: str) -> str:
    alert_id = first_value(alert, ["id", "_id", "alert.id", "data.id"])
    if alert_id:
        key_data: Any = {"source": source, "id": str(alert_id)}
    else:
        key_data = {
            "source": source,
            "timestamp": first_value(alert, ["timestamp", "@timestamp"]),
            "rule_id": infer_rule_id(alert),
            "agent": alert_agent(alert),
            "location": alert_location(alert),
            "raw": alert,
        }

    encoded = json.dumps(key_data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def store_alerts(alerts: list[dict[str, Any]], source: str) -> tuple[int, int, list[LiveAlert]]:
    created = 0
    skipped = 0
    rows: list[LiveAlert] = []

    for alert in alerts:
        rule_id = infer_rule_id(alert)
        fingerprint = alert_fingerprint(alert, source)

        try:
            with transaction.atomic():
                row = LiveAlert.objects.create(
                    source=source,
                    fingerprint=fingerprint,
                    timestamp=alert_timestamp(alert),
                    rule_id=rule_id,
                    agent=alert_agent(alert),
                    location=alert_location(alert),
                    raw=alert,
                )
            created += 1
            rows.append(row)
        except IntegrityError:
            skipped += 1
            existing = LiveAlert.objects.filter(fingerprint=fingerprint).first()
            if existing is not None:
                rows.append(existing)

    return created, skipped, rows


def hydrated_alert(row: LiveAlert) -> dict[str, Any]:
    alert = dict(row.raw or {})
    alert["_live_rule_id"] = row.rule_id
    if row.timestamp:
        alert["_live_timestamp"] = row.timestamp.isoformat()
    return alert


def evidence(alert: dict[str, Any]) -> dict[str, Any]:
    rid = infer_rule_id(alert)

    return {
        "timestamp": first_value(alert, ["_live_timestamp", "timestamp", "@timestamp"]),
        "rule_id": rid,
        "description": first_value(alert, ["rule.description", "description"], RULE_DESCRIPTIONS.get(rid, "Wazuh alert")),
        "agent": alert_agent(alert) or "unknown-agent",
        "location": alert_location(alert) or "live_ingest",
        "raw": alert,
    }


def classify(rule_ids: set[str]) -> str:
    if {"110202", "110203", "110205"} & rule_ids:
        return "suspicious_ot_operation"
    if {"110201", "110204"} & rule_ids:
        return "important_ot_operation"
    return "validation_not_malicious"


def correlate_alerts(alerts: list[dict[str, Any]], window_seconds: int) -> list[dict[str, Any]]:
    timed: list[tuple[Any, dict[str, Any]]] = []

    for alert in alerts:
        rid = infer_rule_id(alert)
        if rid not in WATCH_RULES:
            continue
        ts = alert_timestamp(alert)
        if ts:
            timed.append((ts, alert))

    process_events = [(ts, alert) for ts, alert in timed if infer_rule_id(alert) in PROCESS_RULES]
    flow_events = [(ts, alert) for ts, alert in timed if infer_rule_id(alert) == FLOW_RULE]
    diag_events = [(ts, alert) for ts, alert in timed if infer_rule_id(alert) == DIAGNOSTIC_RULE]

    cases: list[dict[str, Any]] = []

    for process_ts, process_alert in process_events:
        nearest_flow: tuple[Any, dict[str, Any]] | None = None
        nearest_delta: float | None = None

        for flow_ts, flow_alert in flow_events:
            delta = abs((process_ts - flow_ts).total_seconds())
            if delta <= window_seconds and (nearest_delta is None or delta < nearest_delta):
                nearest_flow = (flow_ts, flow_alert)
                nearest_delta = delta

        if nearest_flow is None:
            continue

        evidence_alerts = [process_alert, nearest_flow[1]]

        for diag_ts, diag_alert in diag_events:
            if abs((process_ts - diag_ts).total_seconds()) <= window_seconds:
                evidence_alerts.append(diag_alert)
                break

        rule_ids = {infer_rule_id(item) for item in evidence_alerts}
        flow_alert = nearest_flow[1]

        cases.append(
            {
                "case_type": "confirmed_opcua_operation",
                "classification": classify(rule_ids),
                "created_at": process_ts.isoformat(),
                "correlation_window_seconds": window_seconds,
                "tag": first_value(process_alert, ["data.ot.tag", "ot.tag"], "unknown"),
                "node_id": first_value(process_alert, ["data.ot.node_id", "ot.node_id"], "unknown"),
                "old_value": first_value(process_alert, ["data.ot.old_value", "ot.old_value"]),
                "new_value": first_value(process_alert, ["data.ot.new_value", "ot.new_value"]),
                "source_ip": first_value(
                    flow_alert,
                    ["data.src_ip", "src_ip", "source.ip", "data.source.ip"],
                ),
                "destination_ip": first_value(
                    flow_alert,
                    ["data.dest_ip", "dest_ip", "destination.ip", "data.destination.ip"],
                ),
                "destination_port": first_value(
                    flow_alert,
                    ["data.dest_port", "dest_port", "destination.port", "data.destination.port"],
                ),
                "rule_ids": sorted(rule_ids),
                "evidence": [evidence(item) for item in evidence_alerts],
            }
        )

    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []

    for case in cases:
        key = (
            case["created_at"],
            case["tag"],
            tuple(case["rule_ids"]),
            case["destination_ip"],
            str(case["destination_port"]),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)

    return unique


def recent_alert_queryset(anchor_rows: list[LiveAlert], window_seconds: int):
    latest_timestamp = max(
        (row.timestamp for row in anchor_rows if row.timestamp is not None),
        default=None,
    )
    lookback = max(window_seconds * 2, 1800)

    if latest_timestamp is None:
        return LiveAlert.objects.filter(received_at__gte=timezone.now() - timedelta(seconds=lookback))

    return LiveAlert.objects.filter(
        timestamp__gte=latest_timestamp - timedelta(seconds=lookback),
        timestamp__lte=latest_timestamp + timedelta(seconds=window_seconds),
    )


def ingest_live_alerts(
    payload: Any,
    *,
    source: str,
    window_seconds: int = 900,
) -> LiveIngestResult:
    seed_catalogs()
    alerts = extract_alert_objects(payload)
    created, skipped, rows = store_alerts(alerts, source=source)

    if rows:
        recent_rows = list(recent_alert_queryset(rows, window_seconds))
    else:
        recent_rows = []

    cases = correlate_alerts([hydrated_alert(row) for row in recent_rows], window_seconds)
    import_result = import_cases_payload(cases) if cases else ImportResult()

    if rows:
        LiveAlert.objects.filter(id__in=[row.id for row in recent_rows]).update(
            correlated_at=timezone.now()
        )

    return LiveIngestResult(
        alerts_received=len(alerts),
        alerts_created=created,
        alerts_skipped=skipped,
        cases_created=import_result.cases_created,
        cases_skipped=import_result.cases_skipped,
        evidence_created=import_result.evidence_created,
        evidence_skipped=import_result.evidence_skipped,
    )

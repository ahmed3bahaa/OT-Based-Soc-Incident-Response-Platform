from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Case, EvidenceEvent


@dataclass(frozen=True)
class ImportResult:
    cases_created: int = 0
    cases_skipped: int = 0
    evidence_created: int = 0
    evidence_skipped: int = 0


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None

    text = str(value)
    parsed = parse_datetime(text)

    if parsed is None:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.utc)

    return parsed


def normalize_port(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def evidence_type_for_rule(rule_id: str) -> str:
    if rule_id == "110104":
        return "suricata_network_flow"
    if rule_id == "110105":
        return "kepserverex_diagnostics"
    if rule_id.startswith("1102") or rule_id == "110103":
        return "opcua_process_monitor"
    return "wazuh_alert"


def case_dedupe_key(case_data: dict[str, Any]) -> str:
    evidence = case_data.get("evidence", [])
    key_data = {
        "case_type": case_data.get("case_type"),
        "classification": case_data.get("classification"),
        "created_at": case_data.get("created_at"),
        "tag": case_data.get("tag"),
        "node_id": case_data.get("node_id"),
        "old_value": case_data.get("old_value"),
        "new_value": case_data.get("new_value"),
        "source_ip": case_data.get("source_ip"),
        "destination_ip": case_data.get("destination_ip"),
        "destination_port": str(case_data.get("destination_port", "")),
        "rule_ids": sorted(str(rule_id) for rule_id in case_data.get("rule_ids", [])),
        "evidence": [
            {
                "timestamp": item.get("timestamp"),
                "rule_id": str(item.get("rule_id", "")),
                "location": item.get("location"),
            }
            for item in evidence
            if isinstance(item, dict)
        ],
    }
    encoded = json.dumps(key_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def import_case_payload(case_data: dict[str, Any]) -> tuple[Case, bool, int, int]:
    key = case_dedupe_key(case_data)
    case = Case.objects.filter(dedupe_key=key).first()

    if case is not None:
        return case, False, 0, len(case_data.get("evidence", []))

    with transaction.atomic():
        case = Case.objects.create(
            dedupe_key=key,
            case_type=case_data.get("case_type", ""),
            classification=case_data.get("classification", ""),
            tag=case_data.get("tag", ""),
            node_id=case_data.get("node_id", ""),
            old_value=case_data.get("old_value"),
            new_value=case_data.get("new_value"),
            source_ip=case_data.get("source_ip") or None,
            destination_ip=case_data.get("destination_ip") or None,
            destination_port=normalize_port(case_data.get("destination_port")),
            correlation_window_seconds=case_data.get("correlation_window_seconds"),
            created_at_from_case=parse_timestamp(case_data.get("created_at")),
            rule_ids=[str(rule_id) for rule_id in case_data.get("rule_ids", [])],
            raw=case_data,
        )

        evidence_created = 0
        for evidence_data in case_data.get("evidence", []):
            if not isinstance(evidence_data, dict):
                continue

            rule_id = str(evidence_data.get("rule_id", ""))
            EvidenceEvent.objects.create(
                case=case,
                timestamp=parse_timestamp(evidence_data.get("timestamp")),
                rule_id=rule_id,
                description=evidence_data.get("description", ""),
                agent=evidence_data.get("agent", ""),
                location=evidence_data.get("location", ""),
                evidence_type=evidence_type_for_rule(rule_id),
                raw=evidence_data,
            )
            evidence_created += 1

    return case, True, evidence_created, 0


def import_cases_payload(payload: Any) -> ImportResult:
    cases = payload if isinstance(payload, list) else [payload]
    result = ImportResult()

    for item in cases:
        if not isinstance(item, dict):
            continue

        _, created, evidence_created, evidence_skipped = import_case_payload(item)
        result = ImportResult(
            cases_created=result.cases_created + int(created),
            cases_skipped=result.cases_skipped + int(not created),
            evidence_created=result.evidence_created + evidence_created,
            evidence_skipped=result.evidence_skipped + evidence_skipped,
        )

    return result

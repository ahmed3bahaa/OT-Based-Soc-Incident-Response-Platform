from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_ipv46_address
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


class CaseImportValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


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
    port = int(value)
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


def evidence_type_for_rule(rule_id: str) -> str:
    if rule_id == "110104":
        return "suricata_network_flow"
    if rule_id == "110105":
        return "kepserverex_diagnostics"
    if rule_id == "110205":
        return "opcua_write_failure_repeated"
    if rule_id.startswith("1102") or rule_id == "110103":
        return "opcua_process_monitor"
    return "wazuh_alert"


def validate_text_field(
    data: dict[str, Any],
    field: str,
    errors: list[str],
    prefix: str,
) -> None:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}.{field} is required and must be a non-empty string")


def validate_ip_field(
    data: dict[str, Any],
    field: str,
    errors: list[str],
    prefix: str,
) -> None:
    value = data.get(field)
    if value in (None, ""):
        return
    try:
        validate_ipv46_address(str(value))
    except DjangoValidationError:
        errors.append(f"{prefix}.{field} must be a valid IPv4 or IPv6 address")


def validate_case_payload(case_data: Any, index: int = 0) -> dict[str, Any]:
    prefix = f"cases[{index}]"
    errors: list[str] = []

    if not isinstance(case_data, dict):
        raise CaseImportValidationError([f"{prefix} must be an object"])

    for field in ("case_type", "classification", "tag", "node_id"):
        validate_text_field(case_data, field, errors, prefix)

    valid_classifications = {choice[0] for choice in Case.Classification.choices}
    classification = case_data.get("classification")
    if classification and classification not in valid_classifications:
        errors.append(
            f"{prefix}.classification must be one of: "
            + ", ".join(sorted(valid_classifications))
        )

    if parse_timestamp(case_data.get("created_at")) is None:
        errors.append(f"{prefix}.created_at is required and must be a timestamp")

    try:
        window = int(case_data.get("correlation_window_seconds"))
        if window < 0:
            errors.append(f"{prefix}.correlation_window_seconds must be zero or greater")
    except (TypeError, ValueError):
        errors.append(f"{prefix}.correlation_window_seconds must be an integer")

    for field in ("source_ip", "destination_ip"):
        if case_data.get(field) in (None, ""):
            errors.append(f"{prefix}.{field} is required")
        validate_ip_field(case_data, field, errors, prefix)

    if case_data.get("destination_port") in (None, ""):
        errors.append(f"{prefix}.destination_port is required")
    else:
        try:
            normalize_port(case_data.get("destination_port"))
        except (TypeError, ValueError):
            errors.append(f"{prefix}.destination_port must be a valid TCP/UDP port")

    rule_ids = case_data.get("rule_ids")
    if not isinstance(rule_ids, list) or not rule_ids:
        errors.append(f"{prefix}.rule_ids is required and must be a non-empty list")
        rule_id_set: set[str] = set()
    else:
        rule_id_set = {str(rule_id) for rule_id in rule_ids}

    evidence = case_data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{prefix}.evidence is required and must be a non-empty list")
    else:
        for evidence_index, evidence_data in enumerate(evidence):
            evidence_prefix = f"{prefix}.evidence[{evidence_index}]"
            if not isinstance(evidence_data, dict):
                errors.append(f"{evidence_prefix} must be an object")
                continue

            for field in ("timestamp", "rule_id", "description", "agent", "location"):
                validate_text_field(evidence_data, field, errors, evidence_prefix)

            if parse_timestamp(evidence_data.get("timestamp")) is None:
                errors.append(f"{evidence_prefix}.timestamp must be a timestamp")

            evidence_rule_id = str(evidence_data.get("rule_id", ""))
            if rule_id_set and evidence_rule_id not in rule_id_set:
                errors.append(
                    f"{evidence_prefix}.rule_id must also appear in {prefix}.rule_ids"
                )

    if errors:
        raise CaseImportValidationError(errors)

    return case_data


def normalize_cases_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        cases = [payload]
    elif isinstance(payload, list):
        cases = payload
    else:
        raise CaseImportValidationError(["payload must be a case object or a list of cases"])

    if not cases:
        raise CaseImportValidationError(["payload must contain at least one case"])

    errors: list[str] = []
    normalized: list[dict[str, Any]] = []

    for index, item in enumerate(cases):
        try:
            normalized.append(validate_case_payload(item, index=index))
        except CaseImportValidationError as error:
            errors.extend(error.errors)

    if errors:
        raise CaseImportValidationError(errors)

    return normalized


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
    validate_case_payload(case_data)
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
    cases = normalize_cases_payload(payload)
    result = ImportResult()

    for item in cases:
        _, created, evidence_created, evidence_skipped = import_case_payload(item)
        result = ImportResult(
            cases_created=result.cases_created + int(created),
            cases_skipped=result.cases_skipped + int(not created),
            evidence_created=result.evidence_created + evidence_created,
            evidence_skipped=result.evidence_skipped + evidence_skipped,
        )

    return result

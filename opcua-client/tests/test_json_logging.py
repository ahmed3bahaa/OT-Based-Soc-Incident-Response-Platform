import json
from pathlib import Path

from src import opcua_scenario_client as scenario_client


def test_append_json_event_creates_parent_and_jsonl_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    log_file = tmp_path / "nested" / "events.jsonl"

    monkeypatch.setattr(
        scenario_client,
        "LOG_FILE",
        log_file,
    )

    event = {
        "@timestamp": "2026-07-05T14:00:00Z",
        "event": {
            "action": "opcua_write",
            "outcome": "success",
        },
        "ot": {
            "tag": "SU_SEVIYESI",
            "new_value": 14.0,
            "verified": True,
        },
    }

    scenario_client.append_json_event(event)

    assert log_file.exists()

    lines = log_file.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1
    assert json.loads(lines[0]) == event


def test_append_json_event_appends_one_object_per_line(
    tmp_path: Path,
    monkeypatch,
) -> None:
    log_file = tmp_path / "events.jsonl"

    monkeypatch.setattr(
        scenario_client,
        "LOG_FILE",
        log_file,
    )

    first_event = {
        "scenario_id": "scenario-001",
        "message": "Seviye değişti",
    }
    second_event = {
        "scenario_id": "scenario-002",
        "message": "Motor çalıştı",
    }

    scenario_client.append_json_event(first_event)
    scenario_client.append_json_event(second_event)

    raw_content = log_file.read_text(encoding="utf-8")
    lines = raw_content.splitlines()

    assert raw_content.endswith("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == first_event
    assert json.loads(lines[1]) == second_event
    assert "\\u" not in raw_content

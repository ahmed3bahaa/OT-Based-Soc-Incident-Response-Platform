from __future__ import annotations

import json
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_wazuh_rule_files_are_parseable_and_include_mvp_rules() -> None:
    required_rule_ids = {
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
    discovered: set[str] = set()

    for path in [
        ROOT / "wazuh" / "rules" / "ot_opcua_rules.xml",
        ROOT / "wazuh" / "rules" / "zz_ot_simulator_mvp_rules.xml",
    ]:
        root = ET.parse(path).getroot()
        assert root.tag == "group"
        discovered.update(rule.attrib["id"] for rule in root.findall(".//rule") if "id" in rule.attrib)

    assert required_rule_ids <= discovered


def test_vector_live_ingest_config_points_to_django_endpoint() -> None:
    config = tomllib.loads((ROOT / "vector" / "django-live-ingest.toml").read_text())

    assert "wazuh_alerts_json" in config["sources"]
    assert "ot_rule_filter" in config["transforms"]
    assert config["sinks"]["django_live_ingest"]["uri"].endswith(
        "/api/ingest/vector-alerts/"
    )
    assert config["sinks"]["django_live_ingest"]["method"] == "post"


def test_docker_compose_wires_frontend_to_backend_service() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())

    assert {"db", "backend", "frontend", "wazuh-poller"} <= set(compose["services"])
    assert compose["services"]["db"]["image"] == "postgres:18-alpine"
    assert compose["services"]["db"]["volumes"] == ["postgres18-data:/var/lib/postgresql"]
    assert "${POSTGRES_HOST_PORT:-5434}:5432" in compose["services"]["db"]["ports"]
    assert compose["services"]["backend"]["environment"]["POSTGRES_HOST"] == "db"
    assert compose["services"]["backend"]["environment"]["POSTGRES_PASSWORD"].startswith("${")
    assert (
        compose["services"]["backend"]["environment"]["WAZUH_API_PASSWORD"]
        == "${WAZUH_API_PASSWORD:-}"
    )
    assert compose["services"]["wazuh-poller"]["profiles"] == ["wazuh-poller"]
    assert compose["services"]["wazuh-poller"]["command"] == "python manage.py poll_wazuh_alerts"
    assert (
        compose["services"]["frontend"]["environment"]["OT_SOC_API_BASE_URL"]
        == "${OT_SOC_API_BASE_URL:-http://backend:8000/api}"
    )
    assert "3000:3000" in compose["services"]["frontend"]["ports"]
    assert "8000:8000" in compose["services"]["backend"]["ports"]


def test_correlation_fixtures_match_minimal_case_contract() -> None:
    required_case_fields = {
        "case_type",
        "classification",
        "created_at",
        "correlation_window_seconds",
        "tag",
        "node_id",
        "source_ip",
        "destination_ip",
        "destination_port",
        "rule_ids",
        "evidence",
    }
    required_evidence_fields = {"timestamp", "rule_id", "description", "agent", "location"}

    for path in (ROOT / "tests" / "fixtures" / "correlation").glob("*.json"):
        cases = json.loads(path.read_text())
        assert isinstance(cases, list)
        assert cases

        for case in cases:
            assert required_case_fields <= set(case)
            assert case["case_type"] == "confirmed_opcua_operation"
            assert isinstance(case["rule_ids"], list) and case["rule_ids"]
            assert isinstance(case["evidence"], list) and case["evidence"]
            for evidence in case["evidence"]:
                assert required_evidence_fields <= set(evidence)
                assert evidence["rule_id"] in case["rule_ids"]

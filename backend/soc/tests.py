from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from rest_framework.test import APITestCase

from soc.management.commands.poll_wazuh_alerts import default_search_body

from .models import Asset, Case, EvidenceEvent, LiveAlert, Rule, Tag


def fixture_path(name: str = "opcua_cases_valf.json") -> Path:
    return settings.BASE_DIR.parent / "tests" / "fixtures" / "correlation" / name


def live_valve_alerts() -> list[dict]:
    return [
        {
            "timestamp": "2026-07-08T17:20:00.000000Z",
            "rule": {
                "id": "110203",
                "description": "OT simulator valve command changed",
            },
            "agent": {"name": "Ubuntu"},
            "location": "/home/ahmed_bahaa/ot-project/opcua-client/logs/opcua_monitor.jsonl",
            "data": {
                "ot": {
                    "tag": "VALF",
                    "node_id": "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.VALF",
                    "old_value": False,
                    "new_value": True,
                }
            },
        },
        {
            "timestamp": "2026-07-08T17:20:00.250000Z",
            "rule": {
                "id": "110104",
                "description": "OT OPC UA network flow observed by Suricata - validation scenario",
            },
            "agent": {"name": "My-Win-Machine"},
            "location": "C:\\OT-Project\\suricata-output\\flow-proof-current\\eve.json",
            "data": {
                "src_ip": "192.168.56.10",
                "dest_ip": "192.168.56.1",
                "dest_port": "49320",
            },
        },
    ]


class SeedCatalogsCommandTests(TestCase):
    def test_seed_catalogs_command_is_idempotent(self) -> None:
        out = StringIO()

        call_command("seed_catalogs", stdout=out)

        assert Rule.objects.count() == 9
        assert Tag.objects.count() == 8
        assert Asset.objects.count() == 2

        call_command("seed_catalogs", stdout=out)

        assert Rule.objects.count() == 9
        assert Tag.objects.count() == 8
        assert Asset.objects.count() == 2
        assert "rules updated=9" in out.getvalue()


class PollWazuhAlertsCommandTests(TestCase):
    def test_default_search_body_filters_recent_watch_rules(self) -> None:
        body = default_search_body(size=25, lookback_seconds=1800)

        assert body["size"] == 25
        assert body["sort"] == [{"@timestamp": {"order": "desc"}}]

        filters = body["query"]["bool"]["filter"]
        assert {"terms": {"rule.id": sorted({
            "110103",
            "110104",
            "110105",
            "110200",
            "110201",
            "110202",
            "110203",
            "110204",
            "110205",
        })}} in filters
        assert {
            "range": {
                "@timestamp": {
                    "gte": "now-1800s",
                    "lte": "now",
                }
            }
        } in filters


class ImportOpcuaCasesCommandTests(TestCase):
    def test_import_command_imports_fixture_and_skips_duplicates(self) -> None:
        out = StringIO()

        call_command("import_opcua_cases", file=str(fixture_path()), stdout=out)

        assert Case.objects.count() == 1
        assert EvidenceEvent.objects.count() == 2
        assert Rule.objects.count() == 9
        assert Tag.objects.count() == 8
        assert Asset.objects.count() == 2

        case = Case.objects.get()
        assert case.classification == "suspicious_ot_operation"
        assert case.tag == "VALF"
        assert case.destination_port == 49320
        assert case.rule_ids == ["110104", "110203"]

        call_command("import_opcua_cases", file=str(fixture_path()), stdout=out)

        assert Case.objects.count() == 1
        assert EvidenceEvent.objects.count() == 2
        assert "cases skipped=1" in out.getvalue()

    def test_import_command_rejects_invalid_payload(self) -> None:
        bad_file = settings.BASE_DIR / "invalid-opcua-case-test.json"
        bad_file.write_text('{"case_type": ""}', encoding="utf-8")

        try:
            try:
                call_command("import_opcua_cases", file=str(bad_file))
            except CommandError as error:
                assert "Invalid case payload" in str(error)
            else:
                raise AssertionError("Expected CommandError for invalid case payload")

            assert Case.objects.count() == 0
            assert EvidenceEvent.objects.count() == 0
        finally:
            bad_file.unlink(missing_ok=True)

    def test_import_command_imports_mixed_fixture(self) -> None:
        call_command("import_opcua_cases", file=str(fixture_path("opcua_cases_mixed.json")))

        assert Case.objects.count() == 4
        assert EvidenceEvent.objects.count() == 9
        assert Case.objects.filter(classification="important_ot_operation").count() == 1
        assert Case.objects.filter(classification="suspicious_ot_operation").count() == 3
        assert EvidenceEvent.objects.get(rule_id="110105").evidence_type == "kepserverex_diagnostics"
        assert EvidenceEvent.objects.get(rule_id="110205").evidence_type == "opcua_write_failure_repeated"


class CaseApiTests(APITestCase):
    def setUp(self) -> None:
        call_command("import_opcua_cases", file=str(fixture_path()))

    def test_case_list_returns_imported_case(self) -> None:
        response = self.client.get("/api/cases/")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["classification"] == "suspicious_ot_operation"
        assert response.data["results"][0]["tag"] == "VALF"
        assert response.data["results"][0]["evidence_count"] == 2

    def test_case_detail_returns_nested_evidence(self) -> None:
        case = Case.objects.get()
        response = self.client.get(f"/api/cases/{case.id}/")

        assert response.status_code == 200
        assert response.data["tag"] == "VALF"
        assert len(response.data["evidence"]) == 2

        rule_ids = {item["rule_id"] for item in response.data["evidence"]}
        assert rule_ids == {"110104", "110203"}

    def test_catalog_endpoints_return_seeded_data(self) -> None:
        assert self.client.get("/api/rules/").status_code == 200
        assert self.client.get("/api/tags/").status_code == 200
        assert self.client.get("/api/assets/").status_code == 200
        assert self.client.get("/api/health/").data == {
            "status": "ok",
            "service": "ot-soc-backend",
        }

    def test_openapi_schema_and_swagger_docs_are_available(self) -> None:
        schema_response = self.client.get("/api/schema/")
        docs_response = self.client.get("/api/docs/")

        assert schema_response.status_code == 200
        assert docs_response.status_code == 200
        assert schema_response.data["info"]["title"] == "OT SOC Incident Response MVP API"
        assert "/api/cases/" in schema_response.data["paths"]
        assert "/api/summary/" in schema_response.data["paths"]

    def test_import_api_rejects_invalid_payload(self) -> None:
        Case.objects.all().delete()
        EvidenceEvent.objects.all().delete()

        response = self.client.post("/api/cases/import/", {"case_type": ""}, format="json")

        assert response.status_code == 400
        assert "errors" in response.data
        assert Case.objects.count() == 0


class LiveIngestionApiTests(APITestCase):
    def test_wazuh_live_ingest_creates_case_without_manual_import(self) -> None:
        response = self.client.post(
            "/api/ingest/wazuh-alerts/?window_seconds=60",
            live_valve_alerts(),
            format="json",
        )

        assert response.status_code == 201
        assert response.data["alerts_received"] == 2
        assert response.data["alerts_created"] == 2
        assert response.data["cases_created"] == 1
        assert response.data["evidence_created"] == 2
        assert LiveAlert.objects.count() == 2
        assert Case.objects.count() == 1

        case = Case.objects.get()
        assert case.tag == "VALF"
        assert case.classification == "suspicious_ot_operation"
        assert case.rule_ids == ["110104", "110203"]

    def test_live_ingest_skips_duplicate_alerts_and_cases(self) -> None:
        self.client.post(
            "/api/ingest/wazuh-alerts/?window_seconds=60",
            live_valve_alerts(),
            format="json",
        )
        response = self.client.post(
            "/api/ingest/wazuh-alerts/?window_seconds=60",
            live_valve_alerts(),
            format="json",
        )

        assert response.status_code == 200
        assert response.data["alerts_skipped"] == 2
        assert response.data["cases_skipped"] == 1
        assert LiveAlert.objects.count() == 2
        assert Case.objects.count() == 1

    def test_vector_endpoint_uses_same_live_correlation_path(self) -> None:
        response = self.client.post(
            "/api/ingest/vector-alerts/?window_seconds=60",
            {"events": live_valve_alerts()},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["cases_created"] == 1
        assert Case.objects.get().tag == "VALF"

    def test_live_alert_list_endpoint_returns_ingested_alerts(self) -> None:
        self.client.post(
            "/api/ingest/wazuh-alerts/?window_seconds=60",
            live_valve_alerts(),
            format="json",
        )

        response = self.client.get("/api/live-alerts/?rule_id=110203")

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["rule_id"] == "110203"


class WatchWazuhAlertsCommandTests(TestCase):
    def test_watch_command_ingests_existing_file_once(self) -> None:
        alert_file = settings.BASE_DIR / "watch-wazuh-alerts-test.json"
        alert_file.write_text(
            "\n".join(json.dumps(alert) for alert in live_valve_alerts()) + "\n",
            encoding="utf-8",
        )

        try:
            call_command(
                "watch_wazuh_alerts",
                file=str(alert_file),
                from_start=True,
                once=True,
                window_seconds=60,
            )
        finally:
            alert_file.unlink(missing_ok=True)

        assert LiveAlert.objects.count() == 2
        assert Case.objects.count() == 1


class CaseFilteringAndSummaryApiTests(APITestCase):
    def setUp(self) -> None:
        call_command("import_opcua_cases", file=str(fixture_path("opcua_cases_mixed.json")))

    def test_case_filters_search_and_ordering_are_frontend_ready(self) -> None:
        suspicious = self.client.get("/api/cases/?classification=suspicious_ot_operation")
        water_level = self.client.get("/api/cases/?tag=SU_SEVIYESI")
        kepserver = self.client.get("/api/cases/?rule_id=110105")
        motor_search = self.client.get("/api/cases/?search=motor")

        assert suspicious.status_code == 200
        assert suspicious.data["count"] == 3
        assert water_level.data["count"] == 2
        assert kepserver.data["count"] == 1
        assert kepserver.data["results"][0]["tag"] == "VALF"
        assert motor_search.data["count"] == 1
        assert motor_search.data["results"][0]["tag"] == "MOTOR1"

    def test_evidence_and_catalog_filters_are_available(self) -> None:
        flow_evidence = self.client.get("/api/evidence/?rule_id=110104")
        writable_tags = self.client.get("/api/tags/?is_writable=true")
        suspicious_rules = self.client.get(
            "/api/rules/?classification_hint=suspicious_ot_operation"
        )
        windows_assets = self.client.get("/api/assets/?platform=Windows")

        assert flow_evidence.status_code == 200
        assert flow_evidence.data["count"] == 4
        assert writable_tags.data["count"] == 5
        assert suspicious_rules.data["count"] == 3
        assert windows_assets.data["count"] == 1

    def test_summary_endpoint_returns_dashboard_counts(self) -> None:
        response = self.client.get("/api/summary/")

        assert response.status_code == 200
        assert response.data["total_cases"] == 4
        assert response.data["total_evidence"] == 9
        assert response.data["total_rules"] == 9
        assert response.data["total_tags"] == 8
        assert response.data["total_assets"] == 2

        classification_counts = {
            row["value"]: row["count"] for row in response.data["cases_by_classification"]
        }
        assert classification_counts == {
            "suspicious_ot_operation": 3,
            "important_ot_operation": 1,
        }

        assert response.data["latest_cases"][0]["tag"] == "SU_SEVIYESI"

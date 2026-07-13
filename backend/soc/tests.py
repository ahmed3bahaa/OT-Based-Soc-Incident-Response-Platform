from __future__ import annotations

from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Asset, Case, EvidenceEvent, Rule, Tag


def fixture_path() -> Path:
    return settings.BASE_DIR.parent / "tests" / "fixtures" / "correlation" / "opcua_cases_valf.json"


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


class CaseApiTests(APITestCase):
    def setUp(self) -> None:
        call_command("import_opcua_cases", file=str(fixture_path()))

    def test_case_list_returns_imported_case(self) -> None:
        response = self.client.get("/api/cases/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["classification"] == "suspicious_ot_operation"
        assert response.data[0]["tag"] == "VALF"
        assert response.data[0]["evidence_count"] == 2

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

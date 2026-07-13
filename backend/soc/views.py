from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .catalog import seed_catalogs
from .importers import CaseImportValidationError, import_cases_payload
from .live_ingest import ingest_live_alerts
from .models import Asset, Case, EvidenceEvent, LiveAlert, Rule, Tag
from .serializers import (
    AssetSerializer,
    CaseImportSerializer,
    CaseDetailSerializer,
    CaseListSerializer,
    DashboardSummarySerializer,
    EvidenceEventSerializer,
    HealthSerializer,
    ImportCasesErrorSerializer,
    ImportCasesResultSerializer,
    LiveAlertIngestResultSerializer,
    LiveAlertSerializer,
    RuleSerializer,
    TagSerializer,
)


@extend_schema(responses=HealthSerializer)
@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "ot-soc-backend"})


def count_by(queryset, field: str) -> list[dict[str, int | str]]:
    rows = (
        queryset.values(field)
        .annotate(count=Count("id"))
        .order_by("-count", field)
    )
    return [{"value": row[field] or "unknown", "count": row["count"]} for row in rows]


@extend_schema(responses=DashboardSummarySerializer)
@api_view(["GET"])
def summary(request):
    latest_cases = Case.objects.annotate(
        evidence_count=Count("evidence_events")
    ).order_by("-created_at_from_case", "-ingested_at", "-id")[:5]

    return Response(
        {
            "total_cases": Case.objects.count(),
            "total_evidence": EvidenceEvent.objects.count(),
            "total_rules": Rule.objects.count(),
            "total_tags": Tag.objects.count(),
            "total_assets": Asset.objects.count(),
            "cases_by_classification": count_by(Case.objects.all(), "classification"),
            "cases_by_tag": count_by(Case.objects.all(), "tag"),
            "evidence_by_rule_id": count_by(EvidenceEvent.objects.all(), "rule_id"),
            "latest_cases": CaseListSerializer(latest_cases, many=True).data,
        }
    )


class CaseListView(generics.ListAPIView):
    serializer_class = CaseListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["case_type", "classification", "tag", "node_id", "source_ip", "destination_ip"]
    ordering_fields = [
        "created_at_from_case",
        "ingested_at",
        "classification",
        "tag",
        "destination_port",
    ]
    ordering = ["-created_at_from_case", "-ingested_at", "-id"]

    def get_queryset(self):
        queryset = Case.objects.annotate(evidence_count=Count("evidence_events"))

        if classification := self.request.query_params.get("classification"):
            queryset = queryset.filter(classification=classification)
        if tag := self.request.query_params.get("tag"):
            queryset = queryset.filter(tag__iexact=tag)
        if source_ip := self.request.query_params.get("source_ip"):
            queryset = queryset.filter(source_ip=source_ip)
        if destination_ip := self.request.query_params.get("destination_ip"):
            queryset = queryset.filter(destination_ip=destination_ip)
        if rule_id := self.request.query_params.get("rule_id"):
            queryset = queryset.filter(evidence_events__rule_id=rule_id).distinct()

        return queryset


class CaseDetailView(generics.RetrieveAPIView):
    queryset = Case.objects.prefetch_related("evidence_events")
    serializer_class = CaseDetailSerializer


class EvidenceEventListView(generics.ListAPIView):
    queryset = EvidenceEvent.objects.select_related("case")
    serializer_class = EvidenceEventSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["rule_id", "description", "agent", "location", "evidence_type"]
    ordering_fields = ["timestamp", "rule_id", "agent", "evidence_type"]
    ordering = ["timestamp", "id"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if case_id := self.request.query_params.get("case"):
            queryset = queryset.filter(case_id=case_id)
        if rule_id := self.request.query_params.get("rule_id"):
            queryset = queryset.filter(rule_id=rule_id)
        if evidence_type := self.request.query_params.get("evidence_type"):
            queryset = queryset.filter(evidence_type=evidence_type)
        if agent := self.request.query_params.get("agent"):
            queryset = queryset.filter(agent__iexact=agent)

        return queryset


class LiveAlertListView(generics.ListAPIView):
    queryset = LiveAlert.objects.all()
    serializer_class = LiveAlertSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["rule_id", "agent", "location", "source"]
    ordering_fields = ["timestamp", "received_at", "rule_id", "source", "agent"]
    ordering = ["-timestamp", "-received_at", "-id"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if source := self.request.query_params.get("source"):
            queryset = queryset.filter(source=source)
        if rule_id := self.request.query_params.get("rule_id"):
            queryset = queryset.filter(rule_id=rule_id)
        if agent := self.request.query_params.get("agent"):
            queryset = queryset.filter(agent__iexact=agent)

        return queryset


class RuleListView(generics.ListAPIView):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["rule_id", "name", "description", "source", "category"]
    ordering_fields = ["rule_id", "level", "source", "category", "classification_hint"]
    ordering = ["rule_id"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if source := self.request.query_params.get("source"):
            queryset = queryset.filter(source=source)
        if category := self.request.query_params.get("category"):
            queryset = queryset.filter(category=category)
        if classification_hint := self.request.query_params.get("classification_hint"):
            queryset = queryset.filter(classification_hint=classification_hint)

        return queryset


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "node_id", "tag_type", "criticality", "station_or_area", "description"]
    ordering_fields = ["name", "tag_type", "criticality", "station_or_area", "is_writable"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if tag_type := self.request.query_params.get("tag_type"):
            queryset = queryset.filter(tag_type=tag_type)
        if criticality := self.request.query_params.get("criticality"):
            queryset = queryset.filter(criticality=criticality)
        if station_or_area := self.request.query_params.get("station_or_area"):
            queryset = queryset.filter(station_or_area=station_or_area)
        if is_writable := self.request.query_params.get("is_writable"):
            queryset = queryset.filter(is_writable=is_writable.lower() in {"1", "true", "yes"})

        return queryset


class AssetListView(generics.ListAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "ip_address", "role", "platform", "description"]
    ordering_fields = ["name", "ip_address", "role", "platform"]
    ordering = ["ip_address", "name"]

    def get_queryset(self):
        queryset = super().get_queryset()

        if role := self.request.query_params.get("role"):
            queryset = queryset.filter(role=role)
        if platform := self.request.query_params.get("platform"):
            queryset = queryset.filter(platform__iexact=platform)

        return queryset


@extend_schema(
    request=CaseImportSerializer(many=True),
    responses={
        200: ImportCasesResultSerializer,
        201: ImportCasesResultSerializer,
        400: OpenApiResponse(ImportCasesErrorSerializer, description="Invalid case payload"),
    },
)
@api_view(["POST"])
def import_cases(request):
    seed_catalogs()
    try:
        result = import_cases_payload(request.data)
    except CaseImportValidationError as error:
        return Response({"errors": error.errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "cases_created": result.cases_created,
            "cases_skipped": result.cases_skipped,
            "evidence_created": result.evidence_created,
            "evidence_skipped": result.evidence_skipped,
        },
        status=status.HTTP_201_CREATED if result.cases_created else status.HTTP_200_OK,
    )


def live_ingest_response(request, source: str):
    try:
        window_seconds = int(request.query_params.get("window_seconds", 900))
    except ValueError:
        return Response({"errors": ["window_seconds must be an integer"]}, status=status.HTTP_400_BAD_REQUEST)

    if window_seconds < 1:
        return Response({"errors": ["window_seconds must be greater than zero"]}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = ingest_live_alerts(
            request.data,
            source=source,
            window_seconds=window_seconds,
        )
    except CaseImportValidationError as error:
        return Response({"errors": error.errors}, status=status.HTTP_400_BAD_REQUEST)

    payload = {
        "alerts_received": result.alerts_received,
        "alerts_created": result.alerts_created,
        "alerts_skipped": result.alerts_skipped,
        "cases_created": result.cases_created,
        "cases_skipped": result.cases_skipped,
        "evidence_created": result.evidence_created,
        "evidence_skipped": result.evidence_skipped,
    }

    return Response(
        payload,
        status=status.HTTP_201_CREATED if result.alerts_created or result.cases_created else status.HTTP_200_OK,
    )


@extend_schema(
    request=OpenApiTypes.OBJECT,
    responses={
        200: LiveAlertIngestResultSerializer,
        201: LiveAlertIngestResultSerializer,
        400: OpenApiResponse(ImportCasesErrorSerializer, description="Invalid live alert payload"),
    },
)
@api_view(["POST"])
def ingest_wazuh_alerts(request):
    return live_ingest_response(request, source="wazuh")


@extend_schema(
    request=OpenApiTypes.OBJECT,
    responses={
        200: LiveAlertIngestResultSerializer,
        201: LiveAlertIngestResultSerializer,
        400: OpenApiResponse(ImportCasesErrorSerializer, description="Invalid Vector alert payload"),
    },
)
@api_view(["POST"])
def ingest_vector_alerts(request):
    return live_ingest_response(request, source="vector")

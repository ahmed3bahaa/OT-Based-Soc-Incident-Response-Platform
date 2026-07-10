from django.db.models import Count
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .catalog import seed_catalogs
from .importers import import_cases_payload
from .models import Asset, Case, EvidenceEvent, Rule, Tag
from .serializers import (
    AssetSerializer,
    CaseDetailSerializer,
    CaseListSerializer,
    EvidenceEventSerializer,
    RuleSerializer,
    TagSerializer,
)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "ot-soc-backend"})


class CaseListView(generics.ListAPIView):
    serializer_class = CaseListSerializer

    def get_queryset(self):
        return Case.objects.annotate(evidence_count=Count("evidence_events"))


class CaseDetailView(generics.RetrieveAPIView):
    queryset = Case.objects.prefetch_related("evidence_events")
    serializer_class = CaseDetailSerializer


class EvidenceEventListView(generics.ListAPIView):
    queryset = EvidenceEvent.objects.select_related("case")
    serializer_class = EvidenceEventSerializer


class RuleListView(generics.ListAPIView):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class AssetListView(generics.ListAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


@api_view(["POST"])
def import_cases(request):
    seed_catalogs()
    result = import_cases_payload(request.data)

    return Response(
        {
            "cases_created": result.cases_created,
            "cases_skipped": result.cases_skipped,
            "evidence_created": result.evidence_created,
            "evidence_skipped": result.evidence_skipped,
        },
        status=status.HTTP_201_CREATED if result.cases_created else status.HTTP_200_OK,
    )

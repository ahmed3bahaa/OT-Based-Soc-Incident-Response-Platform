from rest_framework import serializers

from .models import Asset, Case, EvidenceEvent, LiveAlert, Rule, Tag


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()


class ImportCasesResultSerializer(serializers.Serializer):
    cases_created = serializers.IntegerField()
    cases_skipped = serializers.IntegerField()
    evidence_created = serializers.IntegerField()
    evidence_skipped = serializers.IntegerField()


class LiveAlertIngestResultSerializer(serializers.Serializer):
    alerts_received = serializers.IntegerField()
    alerts_created = serializers.IntegerField()
    alerts_skipped = serializers.IntegerField()
    cases_created = serializers.IntegerField()
    cases_skipped = serializers.IntegerField()
    evidence_created = serializers.IntegerField()
    evidence_skipped = serializers.IntegerField()


class ImportCasesErrorSerializer(serializers.Serializer):
    errors = serializers.ListField(child=serializers.CharField())


class EvidenceImportSerializer(serializers.Serializer):
    timestamp = serializers.CharField()
    rule_id = serializers.CharField()
    description = serializers.CharField()
    agent = serializers.CharField()
    location = serializers.CharField()


class CaseImportSerializer(serializers.Serializer):
    case_type = serializers.CharField()
    classification = serializers.ChoiceField(choices=Case.Classification.choices)
    created_at = serializers.CharField()
    correlation_window_seconds = serializers.IntegerField(min_value=0)
    tag = serializers.CharField()
    node_id = serializers.CharField()
    old_value = serializers.JSONField(required=False, allow_null=True)
    new_value = serializers.JSONField(required=False, allow_null=True)
    source_ip = serializers.IPAddressField()
    destination_ip = serializers.IPAddressField()
    destination_port = serializers.IntegerField(min_value=1, max_value=65535)
    rule_ids = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    evidence = EvidenceImportSerializer(many=True)


class CountByValueSerializer(serializers.Serializer):
    value = serializers.CharField()
    count = serializers.IntegerField()


class DashboardSummarySerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    total_evidence = serializers.IntegerField()
    total_rules = serializers.IntegerField()
    total_tags = serializers.IntegerField()
    total_assets = serializers.IntegerField()
    cases_by_classification = CountByValueSerializer(many=True)
    cases_by_tag = CountByValueSerializer(many=True)
    evidence_by_rule_id = CountByValueSerializer(many=True)
    latest_cases = serializers.ListField(child=serializers.DictField())


class EvidenceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceEvent
        fields = [
            "id",
            "case",
            "timestamp",
            "rule_id",
            "description",
            "agent",
            "location",
            "evidence_type",
            "raw",
        ]
        read_only_fields = fields


class LiveAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveAlert
        fields = [
            "id",
            "source",
            "timestamp",
            "rule_id",
            "agent",
            "location",
            "received_at",
            "correlated_at",
            "raw",
        ]
        read_only_fields = fields


class NestedEvidenceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceEvent
        fields = [
            "id",
            "timestamp",
            "rule_id",
            "description",
            "agent",
            "location",
            "evidence_type",
            "raw",
        ]
        read_only_fields = fields


class CaseListSerializer(serializers.ModelSerializer):
    evidence_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "case_type",
            "classification",
            "tag",
            "node_id",
            "old_value",
            "new_value",
            "source_ip",
            "destination_ip",
            "destination_port",
            "correlation_window_seconds",
            "created_at_from_case",
            "ingested_at",
            "rule_ids",
            "evidence_count",
        ]
        read_only_fields = fields


class CaseDetailSerializer(serializers.ModelSerializer):
    evidence = NestedEvidenceEventSerializer(
        source="evidence_events",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Case
        fields = [
            "id",
            "case_type",
            "classification",
            "tag",
            "node_id",
            "old_value",
            "new_value",
            "source_ip",
            "destination_ip",
            "destination_port",
            "correlation_window_seconds",
            "created_at_from_case",
            "ingested_at",
            "rule_ids",
            "evidence",
            "raw",
        ]
        read_only_fields = fields


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = [
            "id",
            "rule_id",
            "name",
            "description",
            "level",
            "source",
            "category",
            "classification_hint",
        ]
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "node_id",
            "tag_type",
            "criticality",
            "station_or_area",
            "is_writable",
            "description",
        ]
        read_only_fields = fields


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "ip_address",
            "role",
            "platform",
            "description",
        ]
        read_only_fields = fields

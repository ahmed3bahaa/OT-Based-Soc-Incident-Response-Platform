from rest_framework import serializers

from .models import Asset, Case, EvidenceEvent, Rule, Tag


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

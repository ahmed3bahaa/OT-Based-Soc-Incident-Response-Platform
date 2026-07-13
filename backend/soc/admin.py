from django.contrib import admin

from .models import Asset, Case, EvidenceEvent, LiveAlert, Rule, Tag


class EvidenceEventInline(admin.TabularInline):
    model = EvidenceEvent
    extra = 0
    fields = ("timestamp", "rule_id", "evidence_type", "agent", "location")


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "case_type",
        "classification",
        "tag",
        "source_ip",
        "destination_ip",
        "destination_port",
        "created_at_from_case",
    )
    list_filter = ("classification", "case_type", "tag")
    search_fields = ("tag", "node_id", "source_ip", "destination_ip")
    inlines = [EvidenceEventInline]


@admin.register(EvidenceEvent)
class EvidenceEventAdmin(admin.ModelAdmin):
    list_display = ("id", "case", "timestamp", "rule_id", "evidence_type", "agent")
    list_filter = ("rule_id", "evidence_type", "agent")
    search_fields = ("rule_id", "description", "agent", "location")


@admin.register(LiveAlert)
class LiveAlertAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "timestamp", "rule_id", "agent", "received_at", "correlated_at")
    list_filter = ("source", "rule_id", "agent")
    search_fields = ("fingerprint", "rule_id", "agent", "location")
    readonly_fields = ("fingerprint", "received_at")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("rule_id", "name", "level", "source", "category")
    list_filter = ("source", "category", "classification_hint")
    search_fields = ("rule_id", "name", "description")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "tag_type", "criticality", "station_or_area", "is_writable")
    list_filter = ("tag_type", "criticality", "station_or_area", "is_writable")
    search_fields = ("name", "node_id", "description")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "role", "platform")
    list_filter = ("role", "platform")
    search_fields = ("name", "ip_address", "description")

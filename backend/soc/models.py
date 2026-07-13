from django.db import models


class Case(models.Model):
    class Classification(models.TextChoices):
        VALIDATION = "validation_not_malicious", "Validation, not malicious"
        IMPORTANT = "important_ot_operation", "Important OT operation"
        SUSPICIOUS = "suspicious_ot_operation", "Suspicious OT operation"

    case_type = models.CharField(max_length=100)
    classification = models.CharField(
        max_length=64,
        choices=Classification.choices,
    )
    tag = models.CharField(max_length=100)
    node_id = models.CharField(max_length=255)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    destination_ip = models.GenericIPAddressField(null=True, blank=True)
    destination_port = models.PositiveIntegerField(null=True, blank=True)
    correlation_window_seconds = models.PositiveIntegerField(null=True, blank=True)
    created_at_from_case = models.DateTimeField(null=True, blank=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    rule_ids = models.JSONField(default=list, blank=True)
    raw = models.JSONField(default=dict, blank=True)
    dedupe_key = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ("-created_at_from_case", "-ingested_at", "-id")

    def __str__(self) -> str:
        return f"{self.case_type} {self.tag} ({self.classification})"


class EvidenceEvent(models.Model):
    case = models.ForeignKey(
        Case,
        related_name="evidence_events",
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(null=True, blank=True)
    rule_id = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    agent = models.CharField(max_length=100, blank=True)
    location = models.TextField(blank=True)
    evidence_type = models.CharField(max_length=100, blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("timestamp", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("case", "timestamp", "rule_id", "location"),
                name="unique_evidence_event_per_case",
            )
        ]

    def __str__(self) -> str:
        return f"{self.rule_id} evidence for case {self.case_id}"


class Rule(models.Model):
    rule_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    level = models.PositiveSmallIntegerField(default=0)
    source = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    classification_hint = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ("rule_id",)

    def __str__(self) -> str:
        return f"{self.rule_id} - {self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    node_id = models.CharField(max_length=255, unique=True)
    tag_type = models.CharField(max_length=100)
    criticality = models.CharField(max_length=50)
    station_or_area = models.CharField(max_length=100, blank=True)
    is_writable = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Asset(models.Model):
    name = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(unique=True)
    role = models.CharField(max_length=100)
    platform = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("ip_address", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

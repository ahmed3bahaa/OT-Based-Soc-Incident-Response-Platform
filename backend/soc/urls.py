from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("summary/", views.summary, name="summary"),
    path("cases/", views.CaseListView.as_view(), name="case-list"),
    path("cases/import/", views.import_cases, name="case-import"),
    path("cases/<int:pk>/", views.CaseDetailView.as_view(), name="case-detail"),
    path("evidence/", views.EvidenceEventListView.as_view(), name="evidence-list"),
    path("live-alerts/", views.LiveAlertListView.as_view(), name="live-alert-list"),
    path("ingest/wazuh-alerts/", views.ingest_wazuh_alerts, name="ingest-wazuh-alerts"),
    path("ingest/vector-alerts/", views.ingest_vector_alerts, name="ingest-vector-alerts"),
    path("rules/", views.RuleListView.as_view(), name="rule-list"),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    path("assets/", views.AssetListView.as_view(), name="asset-list"),
]

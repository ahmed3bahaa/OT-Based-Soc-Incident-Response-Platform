from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("cases/", views.CaseListView.as_view(), name="case-list"),
    path("cases/import/", views.import_cases, name="case-import"),
    path("cases/<int:pk>/", views.CaseDetailView.as_view(), name="case-detail"),
    path("evidence/", views.EvidenceEventListView.as_view(), name="evidence-list"),
    path("rules/", views.RuleListView.as_view(), name="rule-list"),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    path("assets/", views.AssetListView.as_view(), name="asset-list"),
]

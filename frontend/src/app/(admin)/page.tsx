import type { Metadata } from "next";

import { OtSocDashboard } from "@/components/ot-soc/OtSocDashboard";
import { OtSocShell } from "@/components/ot-soc/OtSocShell";
import type { Asset, DashboardSummary, OtCase, PaginatedResponse, Rule, Tag } from "@/lib/otSocApi";
import { fetchApi } from "@/lib/otSocApi";

export const metadata: Metadata = {
  title: "OT SOC Console | Incident Response MVP",
  description: "Frontend console for correlated OPC UA incident-response cases.",
};

const emptyPage = <T,>(): PaginatedResponse<T> => ({
  count: 0,
  next: null,
  previous: null,
  results: [],
});

const emptySummary: DashboardSummary = {
  total_cases: 0,
  total_evidence: 0,
  total_rules: 0,
  total_tags: 0,
  total_assets: 0,
  cases_by_classification: [],
  cases_by_tag: [],
  evidence_by_rule_id: [],
  latest_cases: [],
};

export default async function OtSocHome() {
  const [summaryResult, casesResult, rulesResult, tagsResult, assetsResult] = await Promise.all([
    fetchApi<DashboardSummary>("/summary/"),
    fetchApi<PaginatedResponse<OtCase>>("/cases/?ordering=-created_at_from_case"),
    fetchApi<PaginatedResponse<Rule>>("/rules/"),
    fetchApi<PaginatedResponse<Tag>>("/tags/"),
    fetchApi<PaginatedResponse<Asset>>("/assets/"),
  ]);

  const apiError = [
    summaryResult,
    casesResult,
    rulesResult,
    tagsResult,
    assetsResult,
  ].find((result) => !result.ok)?.error;

  return (
    <OtSocShell
      title="OT SOC command console"
      description="A focused analyst view for confirmed OPC UA operations from the simulator MVP. It brings together correlated cases, evidence, Wazuh rule context, OT tags, and lab assets without changing the telemetry pipeline."
      apiError={apiError}
    >
      <OtSocDashboard
        summary={summaryResult.ok ? summaryResult.data : emptySummary}
        cases={casesResult.ok ? casesResult.data : emptyPage<OtCase>()}
        rules={rulesResult.ok ? rulesResult.data : emptyPage<Rule>()}
        tags={tagsResult.ok ? tagsResult.data : emptyPage<Tag>()}
        assets={assetsResult.ok ? assetsResult.data : emptyPage<Asset>()}
      />
    </OtSocShell>
  );
}

import type { Metadata } from "next";

import { OtSocShell } from "@/components/ot-soc/OtSocShell";
import type { PaginatedResponse, Rule } from "@/lib/otSocApi";
import { buildQuery, fetchApi } from "@/lib/otSocApi";

export const metadata: Metadata = {
  title: "Rules | OT SOC Console",
};

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function RulesPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const query = buildQuery({
    search: first(params.search),
    classification_hint: first(params.classification_hint),
    source: first(params.source),
  });
  const result = await fetchApi<PaginatedResponse<Rule>>(`/rules/${query}`);

  return (
    <OtSocShell
      title="Detection rule catalog"
      description="Wazuh rule context used by the simulator MVP correlation and case classification."
      apiError={result.ok ? undefined : result.error}
    >
      <div className="command-panel overflow-hidden">
        <div className="border-b border-white/10 bg-[#111]/90 p-4">
          <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" action="/rules">
            <input
              name="search"
              defaultValue={first(params.search) || ""}
              placeholder="Search rule, source, category"
              className="command-input"
            />
            <select
              name="classification_hint"
              defaultValue={first(params.classification_hint) || ""}
              className="command-input"
            >
              <option value="">All hints</option>
              <option value="suspicious_ot_operation">Suspicious</option>
              <option value="important_ot_operation">Important</option>
              <option value="validation_not_malicious">Validation</option>
            </select>
            <button className="command-button">
              Apply
            </button>
          </form>
        </div>
        <div className="overflow-x-auto">
          <table className="command-table min-w-full">
            <thead>
              <tr>
                <th>Rule</th>
                <th>Description</th>
                <th>Level</th>
                <th>Source</th>
                <th>Hint</th>
              </tr>
            </thead>
            <tbody>
              {result.ok && result.data.results.map((rule) => (
                <tr key={rule.id}>
                  <td className="font-semibold text-[#ff5a2f] [font-family:var(--font-command)]">{rule.rule_id}</td>
                  <td>
                    <p className="font-medium text-white/82">{rule.name}</p>
                    <p className="mt-1 text-xs text-white/38">{rule.description}</p>
                  </td>
                  <td className="[font-family:var(--font-command)]">{rule.level}</td>
                  <td>{rule.source}</td>
                  <td>{rule.classification_hint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </OtSocShell>
  );
}

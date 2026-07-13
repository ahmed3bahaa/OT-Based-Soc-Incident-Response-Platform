import type { Metadata } from "next";
import Link from "next/link";

import { OtSocShell } from "@/components/ot-soc/OtSocShell";
import { classificationBadge, classificationLabel } from "@/components/ot-soc/status";
import { ArrowRightIcon } from "@/icons";
import type { OtCase, PaginatedResponse } from "@/lib/otSocApi";
import { buildQuery, fetchApi, formatDateTime, formatValue } from "@/lib/otSocApi";

export const metadata: Metadata = {
  title: "Cases | OT SOC Console",
};

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function CasesPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const query = buildQuery({
    classification: first(params.classification),
    tag: first(params.tag),
    rule_id: first(params.rule_id),
    search: first(params.search),
    ordering: first(params.ordering) || "-created_at_from_case",
  });
  const result = await fetchApi<PaginatedResponse<OtCase>>(`/cases/${query}`);

  return (
    <OtSocShell
      title="Case triage"
      description="Review confirmed OPC UA operations with process, network, and evidence context."
      apiError={result.ok ? undefined : result.error}
    >
      <div className="command-panel overflow-hidden">
        <div className="border-b border-white/10 bg-[#111]/90 p-4">
          <form className="grid gap-3 md:grid-cols-[1.4fr_1fr_1fr_auto]" action="/cases">
            <input
              name="search"
              defaultValue={first(params.search) || ""}
              placeholder="Search tag, node, IP, classification"
              className="command-input"
            />
            <select
              name="classification"
              defaultValue={first(params.classification) || ""}
              className="command-input"
            >
              <option value="">All classifications</option>
              <option value="suspicious_ot_operation">Suspicious</option>
              <option value="important_ot_operation">Important</option>
              <option value="validation_not_malicious">Validation</option>
            </select>
            <input
              name="rule_id"
              defaultValue={first(params.rule_id) || ""}
              placeholder="Rule ID"
              className="command-input"
            />
            <button className="command-button">
              Apply
            </button>
          </form>
        </div>

        <div>
          {result.ok && result.data.results.length ? (
            result.data.results.map((item) => (
              <Link
                key={item.id}
                href={`/cases/${item.id}`}
                className="grid gap-4 border-b border-white/[0.07] p-4 transition hover:bg-white/[0.035] lg:grid-cols-[1.2fr_0.9fr_0.9fr_auto]"
              >
                <div>
                  <span className={`inline-flex border px-2.5 py-1 text-xs font-medium ${classificationBadge(item.classification)}`}>
                    {classificationLabel(item.classification)}
                  </span>
                  <p className="mt-2 font-semibold text-white">{item.tag}</p>
                  <p className="mt-1 truncate text-xs text-white/38 [font-family:var(--font-command)]">{item.node_id}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-white/34 [font-family:var(--font-command)]">Change</p>
                  <p className="mt-2 text-sm text-white/72">
                    {formatValue(item.old_value)} to {formatValue(item.new_value)}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-white/34 [font-family:var(--font-command)]">Evidence</p>
                  <p className="mt-2 text-sm text-white/72">
                    {(item.evidence_count || 0).toString()} records, {item.rule_ids.join(", ")}
                  </p>
                  <p className="mt-1 text-xs text-white/38 [font-family:var(--font-command)]">
                    {formatDateTime(item.created_at_from_case)}
                  </p>
                </div>
                <div className="flex items-center justify-end">
                  <ArrowRightIcon className="h-4 w-4 text-[#ff5a2f]" />
                </div>
              </Link>
            ))
          ) : (
            <div className="p-6 text-sm text-white/42">No cases match the current filters.</div>
          )}
        </div>
      </div>
    </OtSocShell>
  );
}

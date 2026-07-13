import type { Metadata } from "next";
import Link from "next/link";

import { OtSocShell } from "@/components/ot-soc/OtSocShell";
import { classificationBadge, classificationLabel } from "@/components/ot-soc/status";
import type { OtCase } from "@/lib/otSocApi";
import { fetchApi, formatDateTime, formatValue } from "@/lib/otSocApi";

export const metadata: Metadata = {
  title: "Case Detail | OT SOC Console",
};

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function CaseDetailPage({ params }: PageProps) {
  const { id } = await params;
  const result = await fetchApi<OtCase>(`/cases/${id}/`);

  if (!result.ok) {
    return (
      <OtSocShell title="Case detail" apiError={result.error}>
        <Link href="/cases" className="command-ghost w-fit">
          Back to cases
        </Link>
      </OtSocShell>
    );
  }

  const item = result.data;

  return (
    <OtSocShell
      title={`${item.tag} operation`}
      description="Case detail preserves the correlated evidence exactly as imported from the backend."
    >
      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        <section className="command-panel p-5">
          <span className={`inline-flex border px-2.5 py-1 text-xs font-medium ${classificationBadge(item.classification)}`}>
            {classificationLabel(item.classification)}
          </span>
          <h2 className="mt-4 text-2xl font-normal text-white [font-family:var(--font-command)]">
            {item.case_type}
          </h2>
          <dl className="mt-5 grid gap-4 md:grid-cols-2">
            {[
              ["Node ID", item.node_id],
              ["Old value", formatValue(item.old_value)],
              ["New value", formatValue(item.new_value)],
              ["Created", formatDateTime(item.created_at_from_case)],
              ["Source", item.source_ip || "unknown"],
              ["Destination", `${item.destination_ip || "unknown"}:${item.destination_port || "?"}`],
            ].map(([label, value]) => (
              <div key={label} className="border border-white/10 bg-white/[0.025] p-3">
                <dt className="text-xs font-medium uppercase text-white/34 [font-family:var(--font-command)]">{label}</dt>
                <dd className="mt-2 break-words text-sm font-medium text-white/78">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <aside className="command-panel-muted p-5">
          <p className="text-sm uppercase text-white/58 [font-family:var(--font-command)]">Rule chain</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {item.rule_ids.map((ruleId) => (
              <Link
                href={`/rules?search=${ruleId}`}
                key={ruleId}
                className="border border-[#ff5a2f]/35 bg-[#ff5a2f]/12 px-3 py-1 text-sm font-medium text-[#ff7a52] [font-family:var(--font-command)]"
              >
                {ruleId}
              </Link>
            ))}
          </div>
        </aside>
      </div>

      <section className="command-panel overflow-hidden">
        <div className="border-b border-white/10 bg-[#111]/90 p-4">
          <h2 className="font-normal uppercase text-white [font-family:var(--font-command)]">Evidence timeline</h2>
        </div>
        <div>
          {(item.evidence || []).map((evidence) => (
            <div key={evidence.id} className="grid gap-3 border-b border-white/[0.07] p-4 md:grid-cols-[170px_120px_1fr]">
              <p className="text-sm text-white/40 [font-family:var(--font-command)]">{formatDateTime(evidence.timestamp)}</p>
              <p className="font-medium text-[#ff5a2f] [font-family:var(--font-command)]">{evidence.rule_id}</p>
              <div>
                <p className="text-sm text-white/72">{evidence.description}</p>
                <p className="mt-1 break-all text-xs text-white/34">
                  {evidence.agent} | {evidence.evidence_type} | {evidence.location}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </OtSocShell>
  );
}

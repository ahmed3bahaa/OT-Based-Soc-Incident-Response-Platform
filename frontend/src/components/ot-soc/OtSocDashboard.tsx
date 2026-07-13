import Link from "next/link";
import type { ComponentType, ReactNode, SVGProps } from "react";

import {
  AlertIcon,
  ArrowRightIcon,
  BoxCubeIcon,
  CheckCircleIcon,
  DocsIcon,
  ListIcon,
  TableIcon,
} from "@/icons";
import type { Asset, DashboardSummary, OtCase, PaginatedResponse, Rule, Tag } from "@/lib/otSocApi";
import { formatDateTime, formatValue } from "@/lib/otSocApi";

import { classificationBadge, classificationLabel } from "./status";

type DashboardProps = {
  summary: DashboardSummary;
  cases: PaginatedResponse<OtCase>;
  rules: PaginatedResponse<Rule>;
  tags: PaginatedResponse<Tag>;
  assets: PaginatedResponse<Asset>;
};

type StatCardProps = {
  label: string;
  value: number | string;
  subtext: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
};

function StatCard({ label, value, subtext, icon: Icon }: StatCardProps) {
  return (
    <div className="command-panel-muted p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase text-white/40 [font-family:var(--font-command)]">
            {label}
          </p>
          <p className="mt-3 text-3xl font-normal text-white [font-family:var(--font-command)]">
            {value}
          </p>
        </div>
        <span className="flex h-10 w-10 items-center justify-center border border-[#ff5a2f]/35 bg-[#ff5a2f]/12 text-[#ff5a2f]">
          <Icon className="h-5 w-5" />
        </span>
      </div>
      <p className="mt-4 text-xs leading-5 text-white/48">{subtext}</p>
    </div>
  );
}

function FieldRow({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="grid grid-cols-[150px_1fr] gap-4 border-b border-white/[0.06] px-4 py-3 text-sm md:grid-cols-[210px_1fr]">
      <dt className="text-[#ff7a52] [font-family:var(--font-command)]">{label}</dt>
      <dd className="min-w-0 break-words text-white/76 [font-family:var(--font-command)]">
        {children}
      </dd>
    </div>
  );
}

function InvestigationPanel({
  latestCase,
  rules,
  suspicious,
  important,
}: {
  latestCase?: OtCase;
  rules: PaginatedResponse<Rule>;
  suspicious: number;
  important: number;
}) {
  const confidence = suspicious > 0 ? 87 : important > 0 ? 74 : 61;
  const ruleIds = latestCase?.rule_ids.length
    ? latestCase.rule_ids
    : rules.results.slice(0, 2).map((rule) => rule.rule_id);
  const verdict = suspicious > 0 ? "SUSPICIOUS" : important > 0 ? "IMPORTANT" : "VALIDATED";
  const eventName = latestCase ? `${latestCase.case_type} - Simulator` : "OPC UA Operation - Simulator";
  const decodedPayload = latestCase
    ? `${latestCase.tag} changed ${formatValue(latestCase.old_value)} -> ${formatValue(latestCase.new_value)}`
    : "Waiting for imported correlated case JSON";
  const fusion =
    ruleIds.includes("110203") && ruleIds.includes("110104")
      ? "OPCUA + SURICATA AGREEMENT"
      : "CORRELATED EVIDENCE";

  return (
    <div className="command-panel overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/10 bg-[#171717] px-4 py-4">
        <p className="text-sm uppercase text-white/44 [font-family:var(--font-command)]">
          OTSOC COMMAND // INVESTIGATION
        </p>
        <span className="h-2.5 w-2.5 rounded-full bg-[#ff5a2f]" />
      </div>
      <div className="grid grid-cols-4 border-b border-white/10 text-center text-xs uppercase text-white/38 [font-family:var(--font-command)]">
        <span className="border-b-2 border-[#ff5a2f] px-3 py-4 text-[#ff5a2f]">
          Alert Detail
        </span>
        <span className="px-3 py-4">Timeline</span>
        <span className="px-3 py-4">Detections</span>
        <span className="px-3 py-4">Reports</span>
      </div>

      <dl className="px-4 py-8">
        <FieldRow label="Event">{eventName}</FieldRow>
        <FieldRow label="Analyst Verdict">
          <span className="inline-flex border border-[#ff5a2f]/35 bg-[#ff5a2f]/18 px-3 py-1 text-xs font-bold uppercase text-[#ff7a52]">
            {verdict}
          </span>
        </FieldRow>
        <FieldRow label="Confidence">
          <span>{confidence}%</span>
          <span className="mt-3 block h-1.5 bg-white/8">
            <span
              className="block h-full bg-[#ff5a2f]"
              style={{ width: `${confidence}%` }}
            />
          </span>
        </FieldRow>
        <FieldRow label="Rule Chain">
          {ruleIds.length ? ruleIds.join(" + ") : "No rules mapped"}
        </FieldRow>
        <FieldRow label="Decoded Payload">{decodedPayload}</FieldRow>
        <FieldRow label="Signal Fusion">
          <span className="inline-flex bg-[#23445c]/55 px-3 py-1 text-xs font-bold text-[#9bd7ff]">
            {fusion}
          </span>
        </FieldRow>
        <FieldRow label="Campaign">
          {summaryLine(latestCase, suspicious, important)}
        </FieldRow>
      </dl>

      <div className="grid grid-cols-3 gap-3 border-t border-white/10 p-4">
        <Link
          href={latestCase ? `/cases/${latestCase.id}` : "/cases"}
          className="command-button"
        >
          Open Case
        </Link>
        <Link href="/rules" className="command-ghost">
          Rules
        </Link>
        <Link href="/tags" className="command-ghost">
          Tags
        </Link>
      </div>
    </div>
  );
}

function summaryLine(latestCase: OtCase | undefined, suspicious: number, important: number) {
  if (!latestCase) {
    return "No confirmed OPC UA case imported yet";
  }

  return `${suspicious} suspicious / ${important} important cases in imported backend view`;
}

function CaseRow({ item }: { item: OtCase }) {
  return (
    <Link
      href={`/cases/${item.id}`}
      className="grid gap-4 border-t border-white/[0.07] px-4 py-4 transition hover:bg-white/[0.035] lg:grid-cols-[1.2fr_0.8fr_1fr_auto]"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`border px-2.5 py-1 text-xs font-medium ${classificationBadge(item.classification)}`}>
            {classificationLabel(item.classification)}
          </span>
          <span className="text-xs text-white/42 [font-family:var(--font-command)]">
            {formatDateTime(item.created_at_from_case)}
          </span>
        </div>
        <p className="mt-3 font-semibold text-white">{item.tag}</p>
        <p className="mt-1 truncate text-xs text-white/38 [font-family:var(--font-command)]">
          {item.node_id}
        </p>
      </div>
      <div>
        <p className="text-xs uppercase text-white/34 [font-family:var(--font-command)]">
          Value Change
        </p>
        <p className="mt-2 text-sm text-white/72">
          {formatValue(item.old_value)} <span className="text-white/32">to</span>{" "}
          {formatValue(item.new_value)}
        </p>
      </div>
      <div>
        <p className="text-xs uppercase text-white/34 [font-family:var(--font-command)]">
          Network Path
        </p>
        <p className="mt-2 text-sm text-white/72">
          {item.source_ip || "unknown"} <span className="text-white/32">to</span>{" "}
          {item.destination_ip || "unknown"}:{item.destination_port || "?"}
        </p>
      </div>
      <div className="flex items-center justify-between gap-3 lg:justify-end">
        <span className="border border-white/10 bg-white/[0.03] px-2.5 py-1 text-xs text-white/55">
          {item.evidence_count ?? item.evidence?.length ?? 0} evidence
        </span>
        <ArrowRightIcon className="h-4 w-4 text-[#ff5a2f]" />
      </div>
    </Link>
  );
}

function CountBars({
  title,
  rows,
}: {
  title: string;
  rows: { value: string; count: number }[];
}) {
  const max = Math.max(...rows.map((row) => row.count), 1);

  return (
    <div className="command-panel-muted p-4">
      <div className="mb-5 flex items-center justify-between gap-4">
        <h2 className="text-sm uppercase text-white/58 [font-family:var(--font-command)]">
          {title}
        </h2>
        <span className="h-2 w-2 rounded-full bg-[#ff5a2f]" />
      </div>
      <div className="space-y-4">
        {rows.length ? (
          rows.map((row) => (
            <div key={row.value}>
              <div className="mb-2 flex items-center justify-between gap-3 text-xs">
                <span className="truncate text-white/72">{row.value}</span>
                <span className="text-white/40 [font-family:var(--font-command)]">
                  {row.count}
                </span>
              </div>
              <div className="h-1.5 bg-white/8">
                <div
                  className="h-full bg-[#ff5a2f]"
                  style={{ width: `${Math.max((row.count / max) * 100, 8)}%` }}
                />
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-white/42">No imported data yet.</p>
        )}
      </div>
    </div>
  );
}

function PlatformPreview({
  summary,
  cases,
  rules,
}: {
  summary: DashboardSummary;
  cases: PaginatedResponse<OtCase>;
  rules: PaginatedResponse<Rule>;
}) {
  const topRules = rules.results.slice(0, 5);

  return (
    <section className="grid min-h-[560px] gap-8 overflow-hidden border-y border-white/10 py-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
      <div className="night-grid relative min-h-[360px] px-4 py-8 md:px-8">
        <div className="absolute inset-y-0 right-0 hidden w-px bg-white/10 lg:block" />
        <p className="text-sm uppercase text-[#ff5a2f] [font-family:var(--font-command)]">
          MDR at machine speed
        </p>
        <h2 className="mt-16 max-w-xl text-5xl font-normal leading-none text-white [font-family:var(--font-command)] md:text-7xl">
          OT SOC
          <span className="block text-[#ff5a2f]">Platform</span>
        </h2>
        <p className="mt-12 max-w-xl text-base leading-7 text-white/76 md:text-lg">
          A security operations surface for the simulator MVP: confirmed case JSON,
          Wazuh rules, OPC UA tag context, Suricata evidence, and lab assets in one
          analyst view.
        </p>
        <Link href="/cases" className="command-button mt-12 w-fit">
          See cases
          <ArrowRightIcon className="h-4 w-4" />
        </Link>
      </div>

      <div className="relative min-h-[480px] overflow-hidden px-4 md:px-8">
        <div className="command-panel absolute left-8 right-[-120px] top-10 origin-center -rotate-6 p-6 shadow-2xl md:left-16">
          <div className="grid gap-5 md:grid-cols-[260px_1fr]">
            <div className="border border-white/10 p-5">
              <p className="text-sm text-white/58">Case Severity</p>
              <div
                className="mx-auto mt-6 flex h-36 w-36 items-center justify-center rounded-full"
                style={{
                  background:
                    "conic-gradient(#f3f3f3 0 58%, #9a9a9a 58% 76%, #333 76% 100%)",
                }}
              >
                <div className="flex h-24 w-24 flex-col items-center justify-center rounded-full bg-[#111]">
                  <span className="text-3xl text-white [font-family:var(--font-command)]">
                    {summary.total_cases}
                  </span>
                  <span className="text-sm text-white/48">Total</span>
                </div>
              </div>
            </div>
            <div className="border border-white/10 p-5">
              <p className="text-sm text-white/58">Escalation of Priority</p>
              <div className="mt-5 space-y-4">
                {topRules.length ? (
                  topRules.map((rule) => (
                    <div key={rule.id} className="flex items-center justify-between gap-4">
                      <span className="truncate text-sm text-white/72">{rule.name}</span>
                      <span className="text-xs text-[#ff5a2f] [font-family:var(--font-command)]">
                        {rule.rule_id}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-white/42">No rules imported yet.</p>
                )}
              </div>
            </div>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-white/10 pt-5">
            <div className="flex h-12 min-w-[280px] items-center border border-white/10 bg-black/35 px-4 text-white/38">
              Search alerts...
            </div>
            {["Open", "Critical", "Informational"].map((filter) => (
              <span
                key={filter}
                className="border border-white/10 bg-white/[0.045] px-4 py-3 text-sm text-white/58"
              >
                {filter}
              </span>
            ))}
          </div>
          <div className="mt-5 border border-white/10 bg-white/[0.035]">
            <div className="grid grid-cols-[64px_1fr_140px] border-b border-white/10 px-4 py-3 text-sm text-white/46">
              <span />
              <span>Detection Type</span>
              <span>Rule</span>
            </div>
            {cases.results.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-[64px_1fr_140px] px-4 py-3 text-sm text-white/70"
              >
                <span className="text-[#ff5a2f]">+</span>
                <span className="truncate">{item.case_type}</span>
                <span className="text-white/42 [font-family:var(--font-command)]">
                  {item.rule_ids[0] || "n/a"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export function OtSocDashboard({ summary, cases, rules, tags, assets }: DashboardProps) {
  const suspicious =
    summary.cases_by_classification.find((item) => item.value === "suspicious_ot_operation")?.count || 0;
  const important =
    summary.cases_by_classification.find((item) => item.value === "important_ot_operation")?.count || 0;
  const writableTags = tags.results.filter((tag) => tag.is_writable).length;
  const highestRule = rules.results.reduce((highest, rule) => Math.max(highest, rule.level), 0);
  const latestCase = cases.results[0] || summary.latest_cases[0];

  return (
    <div className="space-y-10">
      <section className="grid gap-10 lg:grid-cols-[0.95fr_1fr] lg:items-center">
        <InvestigationPanel
          latestCase={latestCase}
          rules={rules}
          suspicious={suspicious}
          important={important}
        />

        <div className="px-1 lg:px-8">
          <p className="text-sm uppercase text-white [font-family:var(--font-command)]">
            OTSOC command
          </p>
          <h2 className="mt-12 max-w-3xl text-5xl font-normal leading-none text-white [font-family:var(--font-command)] md:text-7xl">
            Full visibility
            <span className="block">
              into <span className="text-[#ff5a2f]">every</span>
            </span>
            <span className="block text-[#ff5a2f]">OT investigation.</span>
          </h2>
          <p className="mt-12 max-w-2xl text-lg leading-8 text-white/78">
            The portal shows exactly what the MVP pipeline already proved:
            a simulator tag change, local OPC UA monitor evidence, Wazuh rule context,
            Suricata network flow, and the correlated case record analysts can review.
          </p>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Confirmed Cases"
          value={summary.total_cases}
          subtext={`${suspicious} suspicious, ${important} important`}
          icon={AlertIcon}
        />
        <StatCard
          label="Evidence Records"
          value={summary.total_evidence}
          subtext="Process, network, and diagnostics imported"
          icon={DocsIcon}
        />
        <StatCard
          label="Writable OT Tags"
          value={writableTags}
          subtext={`${summary.total_tags} simulator tags cataloged`}
          icon={TableIcon}
        />
        <StatCard
          label="Highest Rule Level"
          value={highestRule}
          subtext={`${summary.total_rules} Wazuh rules mapped`}
          icon={CheckCircleIcon}
        />
      </div>

      <PlatformPreview summary={summary} cases={cases} rules={rules} />

      <section className="command-panel overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-white/10 bg-[#111]/90 p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase text-[#ff5a2f] [font-family:var(--font-command)]">
              Triage queue
            </p>
            <h2 className="mt-1 text-xl font-normal text-white [font-family:var(--font-command)]">
              Confirmed OPC UA operations
            </h2>
          </div>
          <Link
            href="/cases?classification=suspicious_ot_operation"
            className="command-button"
          >
            Review suspicious
            <ArrowRightIcon className="h-4 w-4" />
          </Link>
        </div>
        {cases.results.length ? (
          cases.results.slice(0, 5).map((item) => <CaseRow key={item.id} item={item} />)
        ) : (
          <div className="p-6 text-sm text-white/42">No correlated cases imported yet.</div>
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="grid gap-6 md:grid-cols-2">
          <CountBars title="Cases by classification" rows={summary.cases_by_classification} />
          <CountBars title="Evidence by rule" rows={summary.evidence_by_rule_id} />
        </div>

        <div className="command-panel-muted p-4">
          <div className="mb-5 flex items-center justify-between gap-4">
            <h2 className="text-sm uppercase text-white/58 [font-family:var(--font-command)]">
              OT lab inventory
            </h2>
            <BoxCubeIcon className="h-5 w-5 text-[#ff5a2f]" />
          </div>
          <div className="space-y-3">
            {assets.results.length ? (
              assets.results.map((asset) => (
                <div key={asset.id} className="border border-white/10 bg-white/[0.025] p-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium text-white [font-family:var(--font-command)]">
                      {asset.ip_address}
                    </p>
                    <span className="border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-white/58">
                      {asset.platform}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-white/58">{asset.name}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-white/42">No assets imported yet.</p>
            )}
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Link href="/tags" className="command-ghost">
              <TableIcon className="h-4 w-4" />
              Tags
            </Link>
            <Link href="/rules" className="command-ghost">
              <ListIcon className="h-4 w-4" />
              Rules
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

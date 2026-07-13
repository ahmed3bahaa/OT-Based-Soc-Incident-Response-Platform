import type { Metadata } from "next";

import { OtSocShell } from "@/components/ot-soc/OtSocShell";
import { criticalityBadge } from "@/components/ot-soc/status";
import type { PaginatedResponse, Tag } from "@/lib/otSocApi";
import { buildQuery, fetchApi } from "@/lib/otSocApi";

export const metadata: Metadata = {
  title: "Tags | OT SOC Console",
};

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function TagsPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const query = buildQuery({
    search: first(params.search),
    criticality: first(params.criticality),
    is_writable: first(params.is_writable),
  });
  const result = await fetchApi<PaginatedResponse<Tag>>(`/tags/${query}`);

  return (
    <OtSocShell
      title="OT tag inventory"
      description="Selected simulator tags used for live MVP visibility, correlation, and analyst context."
      apiError={result.ok ? undefined : result.error}
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {result.ok && result.data.results.map((tag) => (
          <div key={tag.id} className="command-panel-muted p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-white">{tag.name}</p>
                <p className="mt-1 text-xs text-white/38 [font-family:var(--font-command)]">{tag.tag_type}</p>
              </div>
              <span className={`border px-2.5 py-1 text-xs font-medium ${criticalityBadge(tag.criticality)}`}>
                {tag.criticality}
              </span>
            </div>
            <p className="mt-4 break-all text-xs text-white/38 [font-family:var(--font-command)]">{tag.node_id}</p>
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-white/48">{tag.station_or_area}</span>
              <span className="font-medium text-[#ff5a2f]">
                {tag.is_writable ? "Writable" : "Observed"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </OtSocShell>
  );
}

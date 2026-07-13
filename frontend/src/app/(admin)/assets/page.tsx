import type { Metadata } from "next";

import { OtSocShell } from "@/components/ot-soc/OtSocShell";
import type { Asset, PaginatedResponse } from "@/lib/otSocApi";
import { fetchApi } from "@/lib/otSocApi";

export const metadata: Metadata = {
  title: "Assets | OT SOC Console",
};

export default async function AssetsPage() {
  const result = await fetchApi<PaginatedResponse<Asset>>("/assets/");

  return (
    <OtSocShell
      title="Lab asset map"
      description="The two-host MVP lab context for OPC UA monitoring, KEPServerEX simulation, Suricata, and Wazuh evidence."
      apiError={result.ok ? undefined : result.error}
    >
      <div className="grid gap-4 lg:grid-cols-2">
        {result.ok && result.data.results.map((asset) => (
          <div key={asset.id} className="command-panel-muted p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-2xl font-normal text-white [font-family:var(--font-command)]">{asset.ip_address}</p>
                <p className="mt-2 font-medium text-white/72">{asset.name}</p>
              </div>
              <span className="border border-[#ff5a2f]/35 bg-[#ff5a2f]/12 px-3 py-1 text-xs font-medium text-[#ff7a52]">
                {asset.platform}
              </span>
            </div>
            <p className="mt-4 text-sm leading-6 text-white/58">{asset.description}</p>
            <p className="mt-4 border border-white/10 bg-white/[0.025] px-3 py-2 text-sm text-white/68">
              {asset.role}
            </p>
          </div>
        ))}
      </div>
    </OtSocShell>
  );
}

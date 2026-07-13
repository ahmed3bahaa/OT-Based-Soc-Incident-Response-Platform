import Link from "next/link";
import type { ReactNode } from "react";

import { AlertIcon, ArrowRightIcon, BoltIcon, DocsIcon } from "@/icons";
import { getPublicApiBaseUrl } from "@/lib/otSocApi";

import { LiveRefresh } from "./LiveRefresh";

type ShellProps = {
  title: string;
  eyebrow?: string;
  description?: string;
  apiError?: string;
  children: ReactNode;
};

export function OtSocShell({
  title,
  eyebrow = "OT SOC command",
  description,
  apiError,
  children,
}: ShellProps) {
  const publicApiBaseUrl = getPublicApiBaseUrl();

  return (
    <div className="space-y-8">
      <LiveRefresh />
      <section className="command-panel night-grid overflow-hidden">
        <div className="border-b border-white/10 bg-[#111]/90 px-5 py-4 lg:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-3">
                <span className="inline-flex items-center gap-2 text-xs uppercase text-[#ff5a2f] [font-family:var(--font-command)]">
                  <BoltIcon className="h-4 w-4" />
                  {eyebrow}
                </span>
                <span className="inline-flex items-center gap-2 text-xs uppercase text-white/45 [font-family:var(--font-command)]">
                  <span className="h-2 w-2 rounded-full bg-[#ff5a2f]" />
                  backend import view
                </span>
              </div>
              <h1 className="text-2xl font-normal leading-tight text-white [font-family:var(--font-command)] md:text-3xl">
                {title}
              </h1>
              {description ? (
                <p className="mt-2 max-w-4xl text-sm leading-6 text-white/58">
                  {description}
                </p>
              ) : null}
            </div>

            <div className="command-panel-muted min-w-0 p-4 lg:w-[360px]">
              <p className="text-xs uppercase text-white/38 [font-family:var(--font-command)]">
                API contract
              </p>
              <p className="mt-2 break-all text-sm text-white [font-family:var(--font-command)]">
                {publicApiBaseUrl}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <Link href="/cases" className="command-button">
                  Cases
                  <ArrowRightIcon className="h-4 w-4" />
                </Link>
                <a
                  href={`${publicApiBaseUrl}/docs/`}
                  target="_blank"
                  className="command-ghost"
                >
                  <DocsIcon className="h-4 w-4" />
                  Swagger
                </a>
              </div>
            </div>
          </div>
        </div>

        {apiError ? (
          <div className="flex items-start gap-3 border-b border-[#ff5a2f]/35 bg-[#ff5a2f]/10 px-5 py-4 text-sm text-[#ffb199] lg:px-6">
            <AlertIcon className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-medium text-white">Backend data is unavailable.</p>
              <p className="mt-1 text-xs text-[#ffb199]">{apiError}</p>
            </div>
          </div>
        ) : null}
      </section>

      {children}
    </div>
  );
}

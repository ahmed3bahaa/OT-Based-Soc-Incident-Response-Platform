"use client";

import { ThemeToggleButton } from "@/components/common/ThemeToggleButton";
import { useSidebar } from "@/context/SidebarContext";
import { getPublicApiBaseUrl } from "@/lib/otSocApi";
import Link from "next/link";
import React from "react";

const AppHeader: React.FC = () => {
  const { isMobileOpen, toggleSidebar, toggleMobileSidebar } = useSidebar();

  const handleToggle = () => {
    if (window.innerWidth >= 1024) {
      toggleSidebar();
    } else {
      toggleMobileSidebar();
    }
  };

  return (
    <header className="sticky top-0 z-99999 flex w-full border-b border-white/10 bg-[#080808]/95 text-white backdrop-blur">
      <div className="flex w-full flex-col gap-3 px-3 py-3 lg:flex-row lg:items-center lg:justify-between lg:px-6">
        <div className="flex items-center gap-3">
          <button
            className="flex h-11 w-11 items-center justify-center border border-white/12 bg-white/[0.025] text-white/58 transition hover:border-[#ff5a2f]/45 hover:text-[#ff5a2f]"
            onClick={handleToggle}
            aria-label="Toggle Sidebar"
          >
            {isMobileOpen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M6 6L18 18M18 6L6 18"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
              </svg>
            ) : (
              <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
                <path
                  d="M1 1H17M1 7H13M1 13H17"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </button>

          <div className="min-w-0">
            <p className="truncate text-sm uppercase text-white [font-family:var(--font-command)]">
              OT-Based SOC Incident Response Platform
            </p>
            <p className="truncate text-xs text-white/38">
              Simulator MVP | backend API: {getPublicApiBaseUrl()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <form action="/cases" className="hidden md:block">
            <input
              name="search"
              type="text"
              placeholder="Search cases"
              className="command-input w-[260px]"
            />
          </form>
          <Link
            href="/cases?classification=suspicious_ot_operation"
            className="hidden min-h-11 items-center border border-[#ff5a2f]/45 bg-[#ff5a2f]/12 px-3 text-sm font-medium uppercase text-[#ff5a2f] [font-family:var(--font-command)] sm:inline-flex"
          >
            Suspicious
          </Link>
          <ThemeToggleButton />
        </div>
      </div>
    </header>
  );
};

export default AppHeader;

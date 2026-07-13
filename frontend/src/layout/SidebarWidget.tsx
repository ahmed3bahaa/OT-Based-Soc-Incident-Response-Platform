import Link from "next/link";
import React from "react";

export default function SidebarWidget() {
  return (
    <div className="mx-auto mb-10 w-full max-w-60 border border-white/10 bg-white/[0.025] px-4 py-4">
      <h3 className="text-sm uppercase text-white [font-family:var(--font-command)]">
        Backend-first MVP
      </h3>
      <p className="mt-3 text-sm leading-5 text-white/48">
        Imports correlated OPC UA case JSON and keeps analyst decisions human reviewed.
      </p>
      <Link href="/cases" className="command-button mt-4 w-full">
        Review cases
      </Link>
    </div>
  );
}

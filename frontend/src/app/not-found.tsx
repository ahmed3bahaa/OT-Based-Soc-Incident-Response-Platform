import Link from "next/link";

export default function NotFound() {
  return (
    <main className="night-grid flex min-h-screen items-center justify-center bg-[#070707] p-6 text-white">
      <section className="command-panel w-full max-w-lg p-8 text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center border border-[#ff5a2f]/45 bg-[#ff5a2f]/12 text-sm font-semibold text-[#ff5a2f] [font-family:var(--font-command)]">
          OT
        </span>
        <h1 className="mt-6 text-2xl font-normal text-white [font-family:var(--font-command)]">
          Page not found
        </h1>
        <p className="mt-3 text-sm leading-6 text-white/58">
          This route is not part of the OT SOC MVP console.
        </p>
        <Link
          href="/"
          className="command-button mt-6"
        >
          Back to command console
        </Link>
      </section>
    </main>
  );
}

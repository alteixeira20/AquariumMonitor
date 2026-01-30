"use client";

import { useMemo, useState } from "react";
import HelpModal from "../components/HelpModal";

type HelpKey = "storage" | "backups" | "owner";

const helpContent: Record<HelpKey, { title: string; content: string }> = {
  storage: {
    title: "Storage engine",
    content:
      "SQLite is the default for single-node setups and runs well on small hardware. MariaDB is ideal if you expect multiple clients or higher write volume. Choose now because storage migrations are heavier once data exists.",
  },
  backups: {
    title: "Backups",
    content:
      "Backups are recommended for SQLite. Interval controls how often snapshots are taken, and retention keeps only the most recent days. The backup directory stays inside the backend data volume unless you change it.",
  },
  owner: {
    title: "Owner account",
    content:
      "Create the owner account that controls device settings. Demo access is optional and read-only, so visitors can view dashboards without editing anything.",
  },
};

export default function HomePage() {
  const [activeHelp, setActiveHelp] = useState<HelpKey | null>(null);
  const helpDetails = useMemo(
    () => (activeHelp ? helpContent[activeHelp] : null),
    [activeHelp]
  );

  return (
    <div className="flex min-h-screen flex-col gap-8 px-6 py-8 md:px-12 md:py-10">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="h-11 w-11 rounded-full bg-gradient-to-br from-ocean-700 to-ocean-500 shadow-glow" />
          <div className="flex flex-col">
            <span className="font-display text-xl">AquariumMonitor</span>
            <span className="text-sm text-white/60">Self-hosted setup</span>
          </div>
        </div>
        <nav className="flex gap-3">
          <button
            type="button"
            className="rounded-full border border-white/20 px-4 py-2 text-sm font-semibold transition hover:border-ocean-500/60"
          >
            Docs
          </button>
          <button
            type="button"
            className="rounded-full border border-white/20 px-4 py-2 text-sm font-semibold transition hover:border-ocean-500/60"
          >
            Support
          </button>
        </nav>
      </header>

      <main className="flex flex-col gap-7">
        <section className="grid items-center gap-6 md:grid-cols-[1.2fr_0.8fr]">
          <div>
            <h1 className="font-display text-4xl">First-run setup</h1>
            <p className="mt-3 text-base leading-relaxed text-white/70">
              Configure storage, backups, and your owner account. You can change
              most settings later, but storage selection should be made now.
            </p>
          </div>
          <div className="glass-panel grid gap-4 border border-ocean-500/20 p-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-ocean-500/10 px-4 py-2 text-sm text-ocean-400">
              <span className="h-2 w-2 rounded-full bg-ocean-500 shadow-glow animate-pulseGlow" />
              Waiting for backend
            </div>
            <div className="grid gap-3">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-white/50">
                  Backend
                </div>
                <div className="text-sm">localhost:8000</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-white/50">
                  Mode
                </div>
                <div className="text-sm">Single owner</div>
              </div>
            </div>
          </div>
        </section>

        <section className="glass-panel section-divider p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl">Storage engine</h2>
            <button
              type="button"
              onClick={() => setActiveHelp("storage")}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-white/20 text-sm transition hover:border-ocean-500/60"
            >
              ?
            </button>
          </div>
          <div className="grid gap-5">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="flex cursor-pointer flex-col gap-2 rounded-xl border border-white/10 bg-black/20 p-4 transition hover:-translate-y-0.5 hover:border-ocean-500/40 hover:shadow-lg">
                <input type="radio" name="storage" defaultChecked className="accent-ocean-500" />
                <span className="text-sm font-semibold">SQLite</span>
                <span className="text-sm text-white/60">
                  Best for single-node self-hosting. Zero-config and reliable.
                </span>
              </label>
              <label className="flex cursor-pointer flex-col gap-2 rounded-xl border border-white/10 bg-black/20 p-4 transition hover:-translate-y-0.5 hover:border-ocean-500/40 hover:shadow-lg">
                <input type="radio" name="storage" className="accent-ocean-500" />
                <span className="text-sm font-semibold">MariaDB</span>
                <span className="text-sm text-white/60">
                  Stronger concurrency for multi-client use and larger systems.
                </span>
              </label>
              <label className="flex cursor-not-allowed flex-col gap-2 rounded-xl border border-white/5 bg-black/10 p-4 opacity-60">
                <input type="radio" name="storage" disabled className="accent-ocean-500" />
                <span className="text-sm font-semibold">Postgres</span>
                <span className="text-sm text-white/50">
                  Planned. Available in a later release.
                </span>
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2 text-sm text-white/70">
                Database host
                <input type="text" defaultValue="localhost" />
              </label>
              <label className="grid gap-2 text-sm text-white/70">
                Database name
                <input type="text" defaultValue="aquarium" />
              </label>
              <label className="grid gap-2 text-sm text-white/70">
                User
                <input type="text" defaultValue="aquarium_app" />
              </label>
              <label className="grid gap-2 text-sm text-white/70">
                Password
                <input type="password" placeholder="••••••••" />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <button
                type="button"
                className="rounded-full border border-ocean-500/40 bg-ocean-500/10 px-5 py-2 text-sm font-semibold transition hover:border-ocean-500/70"
              >
                Verify connection
              </button>
              <span className="text-sm text-white/60">Not connected</span>
            </div>
          </div>
        </section>

        <section className="glass-panel section-divider p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl">Backups</h2>
            <button
              type="button"
              onClick={() => setActiveHelp("backups")}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-white/20 text-sm transition hover:border-ocean-500/60"
            >
              ?
            </button>
          </div>
          <div className="grid gap-5">
            <div className="flex flex-wrap items-center gap-4">
              <label className="relative inline-flex h-7 w-12 cursor-pointer items-center">
                <input type="checkbox" className="peer sr-only" defaultChecked />
                <span className="absolute inset-0 rounded-full bg-white/20 transition peer-checked:bg-ocean-500/40" />
                <span className="absolute left-1 top-1 h-5 w-5 rounded-full bg-ocean-900 transition peer-checked:translate-x-5" />
              </label>
              <div>
                <p className="text-sm font-semibold">Enable automatic backups</p>
                <p className="text-sm text-white/60">
                  Recommended for SQLite deployments.
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <label className="grid gap-2 text-sm text-white/70">
                Interval (hours)
                <input type="number" defaultValue={6} />
              </label>
              <label className="grid gap-2 text-sm text-white/70">
                Retention (days)
                <input type="number" defaultValue={7} />
              </label>
              <label className="grid gap-2 text-sm text-white/70">
                Backup directory
                <input type="text" defaultValue="backups" />
              </label>
            </div>
          </div>
        </section>

        <section className="glass-panel section-divider p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl">Owner account</h2>
            <button
              type="button"
              onClick={() => setActiveHelp("owner")}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-white/20 text-sm transition hover:border-ocean-500/60"
            >
              ?
            </button>
          </div>
          <div className="grid gap-5">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="grid gap-2 text-sm text-white/70">
                Email
                <input type="email" placeholder="owner@example.com" />
              </label>
              <label className="grid gap-2 text-sm text-white/70">
                Password
                <input type="password" placeholder="Create a strong password" />
              </label>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <label className="relative inline-flex h-7 w-12 cursor-pointer items-center">
                <input type="checkbox" className="peer sr-only" defaultChecked />
                <span className="absolute inset-0 rounded-full bg-white/20 transition peer-checked:bg-ocean-500/40" />
                <span className="absolute left-1 top-1 h-5 w-5 rounded-full bg-ocean-900 transition peer-checked:translate-x-5" />
              </label>
              <div>
                <p className="text-sm font-semibold">Enable demo login</p>
                <p className="text-sm text-white/60">
                  Read-only access for dashboard previews.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            className="rounded-full border border-white/20 px-5 py-2 text-sm font-semibold transition hover:border-ocean-500/60"
          >
            Save draft
          </button>
          <button
            type="button"
            className="rounded-full bg-gradient-to-br from-[#1f8a9b] to-ocean-500 px-5 py-2 text-sm font-semibold text-ocean-950 shadow-ocean transition hover:-translate-y-0.5"
          >
            Complete setup
          </button>
        </section>
      </main>

      {helpDetails ? (
        <HelpModal
          title={helpDetails.title}
          content={helpDetails.content}
          isOpen={Boolean(activeHelp)}
          onClose={() => setActiveHelp(null)}
        />
      ) : null}
    </div>
  );
}

"use client";

export default function SetupHeader() {
  return (
    <header className="flex flex-col gap-4 border-b border-white/10 pb-4 md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-4">
        <div className="h-11 w-11 rounded-full bg-gradient-to-br from-ocean-700 to-ocean-500 shadow-glow" />
        <div className="flex flex-col">
          <span className="font-display text-xl">AquariumMonitor</span>
          <span className="text-sm text-white/60">Setup Wizard</span>
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
  );
}

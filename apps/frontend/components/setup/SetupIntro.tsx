"use client";

import { useState } from "react";
import Field from "../ui/Field";
import Select from "../ui/Select";
import StatusBadge from "../ui/StatusBadge";

type BackendMode = "single" | "team";

type Props = {
  backendUrl: string;
  backendMode: BackendMode;
  onBackendUrlChange: (value: string) => void;
  onBackendModeChange: (value: BackendMode) => void;
  onCheckBackend: () => void;
  isChecking: boolean;
  statusLabel: string;
  statusTone?: "info" | "ready" | "error";
};

export default function SetupIntro({
  backendUrl,
  backendMode,
  onBackendUrlChange,
  onBackendModeChange,
  onCheckBackend,
  isChecking,
  statusLabel,
  statusTone = "info",
}: Props) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const badgeTone =
    statusTone === "ready"
      ? "success"
      : statusTone === "error"
        ? "error"
        : "waiting";
  const hasValidUrl = (() => {
    const value = backendUrl.trim();
    if (!value) return false;
    try {
      const parsed = new URL(value);
      return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
      return false;
    }
  })();

  return (
    <section className="grid items-stretch gap-6 md:grid-cols-[1.2fr_0.8fr]">
      <div className="h-full">
        <h1 className="font-display text-4xl">Setup Wizard</h1>
        <p className="mt-3 text-base leading-relaxed text-white/70">
          Configure your admin account, database, and backups. You can change
          most settings later, but database selection should be made now.
        </p>
      </div>

      <div className="glass-panel grid h-full gap-4 border border-ocean-500/20 p-6">
        <div className="grid gap-4">
          <div className="flex flex-nowrap items-center gap-3">
            <div className="text-base font-semibold">Backend</div>
            <StatusBadge label={statusLabel} tone={badgeTone} />
          </div>
          <Field label="Backend URL">
            <input
              type="url"
              value={backendUrl}
              onChange={(event) => onBackendUrlChange(event.target.value)}
              placeholder="http://localhost:8000"
            />
          </Field>

          <button
            type="button"
            onClick={() => setShowAdvanced((value) => !value)}
            className="w-fit rounded-full border border-white/20 px-3 py-1.5 text-xs font-semibold transition hover:border-ocean-500/60"
          >
            {showAdvanced ? "Hide advanced" : "Show advance"}
          </button>

          {showAdvanced ? (
            <div className="grid gap-2 text-sm text-white/70">
              <div>Mode</div>
              <Select<BackendMode>
                value={backendMode}
                onChange={onBackendModeChange}
                options={[
                  {
                    value: "single",
                    label: "Single owner (recommended)",
                    hint: "Optimized for personal hosting",
                  },
                  {
                    value: "team",
                    label: "Team (coming soon)",
                    hint: "Planned for multi-user deployments",
                    disabled: true,
                  },
                ]}
              />
            </div>
          ) : null}

          <button
            type="button"
            onClick={onCheckBackend}
            disabled={isChecking || !hasValidUrl}
            className="rounded-full border border-white/20 px-4 py-2 text-sm font-semibold transition hover:border-ocean-500/60 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isChecking ? "Checking connection..." : "Check connection"}
          </button>
        </div>
      </div>
    </section>
  );
}

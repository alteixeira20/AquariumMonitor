"use client";

import React from "react";

type SetupSectionProps = {
  title: string;
  subtitle?: string;
  onHelp?: () => void;
  hasError?: boolean;
  children: React.ReactNode;
};

export default function SetupSection({
  title,
  subtitle,
  onHelp,
  hasError,
  children,
}: SetupSectionProps) {
  return (
    <section className="glass-panel section-divider p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="grid gap-1">
          <h2 className="text-xl">
            {title}
            {hasError ? <span className="ml-2 text-red-300">*</span> : null}
          </h2>
          {subtitle ? <p className="text-sm text-white/60">{subtitle}</p> : null}
        </div>

        {onHelp ? (
          <button
            type="button"
            onClick={onHelp}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/20 text-sm transition hover:border-ocean-500/60"
            aria-label={`Help: ${title}`}
          >
            ?
          </button>
        ) : null}
      </div>

      <div className="mt-6">{children}</div>
    </section>
  );
}

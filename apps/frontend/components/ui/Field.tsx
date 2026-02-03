"use client";

import type { ReactNode } from "react";

type Props = {
  label: ReactNode;
  hint?: string;
  children: ReactNode;
  className?: string;
  error?: boolean;
};

export default function Field({ label, hint, children, className, error }: Props) {
  const classes = ["grid gap-2 text-sm text-white/70", className]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={classes}>
      <span className={error ? "text-red-200" : undefined}>{label}</span>
      {children}
      <span
        className={[
          "text-xs",
          "min-h-[1rem]",
          error ? "text-red-200" : "text-white/50",
        ].join(" ")}
      >
        {hint ?? ""}
      </span>
    </label>
  );
}

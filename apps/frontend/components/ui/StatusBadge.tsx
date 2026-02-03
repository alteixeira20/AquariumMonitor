"use client";

type StatusTone = "waiting" | "success" | "error" | "info";

type Props = {
  label: string;
  tone: StatusTone;
  className?: string;
};

const toneStyles: Record<StatusTone, { badge: string; dot: string }> = {
  waiting: {
    badge: "bg-amber-400/20 text-amber-100",
    dot: "bg-amber-300",
  },
  success: {
    badge: "bg-emerald-500/20 text-emerald-200",
    dot: "bg-emerald-300",
  },
  error: {
    badge: "bg-red-500/20 text-red-200",
    dot: "bg-red-300",
  },
  info: {
    badge: "bg-white/10 text-white/70",
    dot: "bg-white/60",
  },
};

export default function StatusBadge({ label, tone, className }: Props) {
  const styles = toneStyles[tone];
  return (
    <div
      className={[
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] whitespace-nowrap",
        styles.badge,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span
        className={[
          "h-2 w-2 rounded-full shadow-glow animate-pulseGlow",
          styles.dot,
        ].join(" ")}
      />
      {label}
    </div>
  );
}

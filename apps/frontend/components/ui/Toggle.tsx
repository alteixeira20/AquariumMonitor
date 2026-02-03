"use client";

type Props = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
};

export default function Toggle({ checked, onChange, label, description }: Props) {
  return (
    <div className="flex flex-wrap items-center gap-4">
      <button
        type="button"
        onClick={() => onChange(!checked)}
        aria-pressed={checked}
        className="relative inline-flex h-7 w-12 items-center rounded-full border border-white/10 bg-white/10 transition hover:border-ocean-500/40"
      >
        <span
          className={[
            "absolute left-1 top-1 h-5 w-5 rounded-full bg-ocean-900 transition",
            checked ? "translate-x-5" : "translate-x-0",
          ].join(" ")}
        />
        <span
          className={[
            "absolute inset-0 rounded-full transition",
            checked ? "bg-ocean-500/35" : "bg-white/10",
          ].join(" ")}
        />
      </button>

      <div>
        <p className="text-sm font-semibold">{label}</p>
        {description ? (
          <p className="text-sm text-white/60">{description}</p>
        ) : null}
      </div>
    </div>
  );
}

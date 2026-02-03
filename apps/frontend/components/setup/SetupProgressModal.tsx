"use client";

type StepStatus = "pending" | "active" | "done" | "error";

export type SetupProgressStep = {
  id: string;
  label: string;
  status: StepStatus;
  detail?: string;
};

type Props = {
  isOpen: boolean;
  title: string;
  steps: SetupProgressStep[];
  onClose?: () => void;
};

export default function SetupProgressModal({ isOpen, title, steps, onClose }: Props) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-ocean-950/80"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className="glass-panel w-[min(520px,92vw)] animate-floatIn p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold">{title}</div>
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              className="text-xl text-white/50 transition hover:text-white"
              aria-label="Close"
            >
              ×
            </button>
          ) : null}
        </div>

        <div className="mt-4 grid gap-3">
          {steps.map((step) => (
            <div
              key={step.id}
              className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3"
            >
              <span
                className={[
                  "mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-semibold",
                  step.status === "done" ? "bg-ocean-500/30 text-ocean-300" : "",
                  step.status === "active" ? "bg-ocean-500 text-ocean-950" : "",
                  step.status === "error" ? "bg-red-500/80 text-white" : "",
                  step.status === "pending" ? "bg-white/10 text-white/60" : "",
                ].join(" ")}
              >
                {step.status === "done" ? "✓" : step.status === "error" ? "!" : "•"}
              </span>
              <div className="flex-1">
                <div className="text-sm font-semibold">{step.label}</div>
                {step.detail ? (
                  <div className="text-xs text-white/60">{step.detail}</div>
                ) : null}
              </div>
              {step.status === "active" ? (
                <span className="h-2 w-2 animate-pulseGlow rounded-full bg-ocean-500" />
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

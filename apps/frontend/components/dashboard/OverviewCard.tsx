import { ReactNode } from "react";

type OverviewCardProps = {
  title: string;
  children: ReactNode;
  className?: string;
};

export function OverviewCard({ title, children, className = "" }: OverviewCardProps) {
  return (
    <div className={`rounded-2xl bg-white/6 p-5 ${className}`.trim()}>
      <div className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60">
        {title}
      </div>
      <div className="mt-3">{children}</div>
    </div>
  );
}

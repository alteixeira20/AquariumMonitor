import { ReactNode } from "react";

type PanelProps = {
  title?: string;
  children: ReactNode;
  className?: string;
};

export function Panel({ title, children, className = "" }: PanelProps) {
  return (
    <section className={`glass-panel p-6 ${className}`.trim()}>
      {title ? (
        <div className="inline-flex text-sm font-semibold uppercase tracking-[0.2em] text-ocean-100">
          {title}
        </div>
      ) : null}
      <div className={title ? "mt-4" : ""}>{children}</div>
    </section>
  );
}

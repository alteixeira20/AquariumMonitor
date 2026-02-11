import { ReactNode } from "react";

type StatRow = {
  label: string;
  value: ReactNode;
};

type StatListProps = {
  rows: StatRow[];
  valueClassName?: string;
  valueClassNameFor?: (label: string) => string;
};

export function StatList({
  rows,
  valueClassName = "",
  valueClassNameFor,
}: StatListProps) {
  return (
    <div className="grid gap-3 text-base text-white/70">
      {rows.map((row) => (
        <div key={row.label} className="flex items-center justify-between">
          <span>{row.label}</span>
          <span className={valueClassNameFor?.(row.label) ?? valueClassName}>
            {row.value}
          </span>
        </div>
      ))}
    </div>
  );
}

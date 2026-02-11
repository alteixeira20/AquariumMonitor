import { useState } from "react";
import SensorChart from "./SensorChart";

type SensorPanelProps = {
  title: string;
  rangeLabel: string;
  latestValue: string;
  latestUnit?: string;
  lastUpdate: string;
  insight: string;
  statusLabel: string;
  statusTone: string;
  median: string;
  minMax: string;
  series: number[];
  seriesTimestamps: string[];
  timeRangeOptions: Array<{ key: string; label: string; disabled?: boolean; hint?: string }>;
  activeRange: string;
  onRangeChange: (key: string) => void;
  xTickIndices: number[];
  formatValue: (value: number) => string;
  formatTime: (iso: string) => string;
};

export function SensorPanel({
  title,
  rangeLabel,
  latestValue,
  latestUnit,
  lastUpdate,
  insight,
  statusLabel,
  statusTone,
  median,
  minMax,
  series,
  seriesTimestamps,
  timeRangeOptions,
  activeRange,
  onRangeChange,
  xTickIndices,
  formatValue,
  formatTime,
}: SensorPanelProps) {
  const [isRangeMenuOpen, setIsRangeMenuOpen] = useState(false);
  const activeRangeLabel =
    timeRangeOptions.find((option) => option.key === activeRange)?.label ?? "Range";
  return (
    <div className="glass-panel p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-base uppercase tracking-[0.3em] text-white/40">
            Sensor
          </div>
          <div className="mt-2 text-2xl font-semibold">{title}</div>
          <div className="mt-1 text-sm text-white/60">{rangeLabel}</div>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="text-sm uppercase tracking-[0.2em] text-white/50">
            Latest
          </div>
          <div className="mt-4 text-3xl font-semibold text-white">
            {latestValue}
            {latestUnit ? (
              <span className="text-lg text-white/50"> {latestUnit}</span>
            ) : null}
          </div>
          <div className="mt-2 text-sm text-white/60">Last update: {lastUpdate}</div>
          <div className="mt-2 text-sm text-white/60">{insight}</div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <div className="text-sm uppercase tracking-[0.2em] text-white/50">
            Status & 24h stats
          </div>
          <div className={`mt-4 text-2xl font-semibold ${statusTone}`}>
            {statusLabel}
          </div>
          <div className="mt-3 grid gap-2 text-sm text-white/60">
            <div>
              Median: <span className="text-white/80">{median}</span>
            </div>
            <div>
              Min/Max: <span className="text-white/80">{minMax}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 px-5 py-2 min-h-[620px]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm uppercase tracking-[0.2em] text-white/50">Trend</div>
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsRangeMenuOpen((prev) => !prev)}
              className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/70 transition hover:border-white/30 hover:text-white"
            >
              {activeRangeLabel}
            </button>
            {isRangeMenuOpen ? (
              <div className="absolute right-0 z-10 mt-2 w-44 rounded-2xl border border-white/10 bg-ocean-950/95 p-2 shadow-lg backdrop-blur">
                {timeRangeOptions.map((option) => (
                  <button
                    key={option.key}
                    type="button"
                    onClick={() => {
                      if (option.disabled) return;
                      onRangeChange(option.key);
                      setIsRangeMenuOpen(false);
                    }}
                    title={option.hint}
                    disabled={option.disabled}
                    className={
                      option.disabled
                        ? "w-full cursor-not-allowed rounded-xl px-3 py-2 text-left text-xs uppercase tracking-[0.2em] text-white/30"
                        : option.key === activeRange
                        ? "w-full rounded-xl bg-ocean-500/20 px-3 py-2 text-left text-xs font-semibold uppercase tracking-[0.2em] text-ocean-100"
                        : "w-full rounded-xl px-3 py-2 text-left text-xs uppercase tracking-[0.2em] text-white/70 hover:bg-white/5"
                    }
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
        <div className="mt-2">
          <SensorChart
            points={series.map((value, index) => ({
              value,
              timestamp: seriesTimestamps[index] ?? "",
            }))}
            formatValue={formatValue}
            timeFormat={formatTime}
            xTickIndices={xTickIndices}
            height={500}
            width={900}
          />
        </div>
        <div className="mt-3 text-sm text-white/60">
          Last bucket: {seriesTimestamps.length ? formatTime(seriesTimestamps[seriesTimestamps.length - 1]) : "—"}
        </div>
      </div>
    </div>
  );
}

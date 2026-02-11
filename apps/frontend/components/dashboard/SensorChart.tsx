type SensorPoint = {
  timestamp: string;
  value: number;
};

type SensorChartProps = {
  points: SensorPoint[];
  unit?: string;
  color?: string;
  formatValue?: (value: number) => string;
  timeFormat?: (iso: string) => string;
  xTickIndices?: number[];
  height?: number;
  width?: number;
};

function formatTimeLabel(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export default function SensorChart({
  points,
  unit = "",
  color = "rgba(84, 201, 255, 0.9)",
  formatValue,
  timeFormat,
  xTickIndices,
  height = 190,
  width = 600,
}: SensorChartProps) {
  if (points.length < 2) {
    return (
      <div className="h-28 rounded-2xl border border-dashed border-white/10 bg-white/5" />
    );
  }

  const padding = 36;
  const values = points.map((p) => p.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const startTime = points[0].timestamp;
  const endTime = points[points.length - 1].timestamp;

  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;
  const tickCount = 5;
  const ticks = Array.from({ length: tickCount }, (_, index) => {
    const ratio = index / (tickCount - 1);
    const value = max - ratio * spread;
    const y = padding + ratio * plotHeight;
    return { value, y };
  });

  const path = points
    .map((point, index) => {
      const x = padding + (index / (points.length - 1)) * plotWidth;
      const y =
        padding + plotHeight - ((point.value - min) / spread) * plotHeight;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        style={{ height }}
        role="img"
        aria-label="Sensor trend chart"
      >
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={height - padding}
          stroke="rgba(255,255,255,0.15)"
          strokeWidth="1"
        />
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="rgba(255,255,255,0.15)"
          strokeWidth="1"
        />
        {ticks.map((tick, index) => (
          <g key={index}>
            <line
              x1={padding}
              y1={tick.y}
              x2={width - padding}
              y2={tick.y}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="1"
            />
            <text
              x={padding - 8}
              y={tick.y + 4}
              fill="rgba(255,255,255,0.45)"
              fontSize="10"
              textAnchor="end"
            >
              {(formatValue ? formatValue(tick.value) : tick.value.toFixed(1))}
            </text>
          </g>
        ))}
        <path d={path} fill="none" stroke={color} strokeWidth="2.5" />

        {points.length >= 2
          ? (() => {
              const indices =
                xTickIndices ?? [0, Math.floor((points.length - 1) / 2), points.length - 1];
              let lastX = -Infinity;
              const minSpacing = 52;
              return indices.map((index) => {
                const clamped = Math.min(Math.max(index, 0), points.length - 1);
                const x = padding + (clamped / (points.length - 1)) * plotWidth;
                if (x - lastX < minSpacing && clamped !== points.length - 1) {
                  return null;
                }
                lastX = x;
                return (
                  <text
                    key={index}
                    x={x}
                    y={height - 8}
                    fill="rgba(255,255,255,0.5)"
                    fontSize="10"
                    textAnchor={
                      clamped === 0
                        ? "start"
                        : clamped === points.length - 1
                        ? "end"
                        : "middle"
                    }
                  >
                    {(timeFormat ?? formatTimeLabel)(
                      points[clamped]?.timestamp ?? ""
                    )}
                  </text>
                );
              });
            })()
          : null}
      </svg>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import TopNav from "../../../../components/dashboard/TopNav";
import { OverviewCard } from "../../../../components/dashboard/OverviewCard";
import { Panel } from "../../../../components/dashboard/Panel";
import { StatList } from "../../../../components/dashboard/StatList";
import { SensorPanel } from "../../../../components/dashboard/SensorPanel";
import { clearAuthToken, getAuthToken } from "../../../../lib/auth";
import { getMe } from "../../../../lib/auth_api";
import { fetchJson } from "../../../../lib/api";
import { getClientApiBaseUrl } from "../../../../lib/config";

type Aquarium = {
  id: string;
  name: string;
  water_type: string;
  liters: number;
  temperature_min: number;
  temperature_max: number;
  ph_min: number;
  ph_max: number;
  tds_min: number;
  tds_max: number;
};

type LatestReading = {
  temperature_c: number | null;
  ph_value: number | null;
  tds_ppm: number | null;
  received_at: string | null;
};

type Device = {
  id: string;
  name: string;
  location: string | null;
};

type DeviceStatus = {
  device_id: string;
  last_seen: string | null;
  status: "online" | "offline" | "unknown";
};

type SeriesPoint = {
  bucket_start: string;
  temperature_median: number;
  ph_median: number;
  tds_median: number;
  count: number;
};

type DeviceStats = {
  temperature_median: number;
  ph_median: number;
  tds_median: number;
};

type SensorKey = "temperature" | "ph" | "tds";

type TimeRangeKey = "30m" | "1h" | "12h" | "24h" | "48h" | "7d" | "30d" | "all";

function formatAgo(iso: string | null | undefined, nowMs?: number) {
  if (!iso) return "No recent data";
  const diffMs = (nowMs ?? Date.now()) - new Date(iso).getTime();
  if (diffMs < 0) return "Just now";
  const diffSeconds = Math.floor(diffMs / 1000);
  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  return `${diffHours}h ago`;
}

function formatTime(iso: string | null | undefined) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function statusFromRange(
  value: number | null | undefined,
  min: number | undefined,
  max: number | undefined
) {
  if (value === null || value === undefined || min === undefined || max === undefined) {
    return { label: "Awaiting data", tone: "text-white/50" };
  }
  if (value < min) return { label: "Below range", tone: "text-sun-300" };
  if (value > max) return { label: "Above range", tone: "text-sun-300" };
  return { label: "Healthy", tone: "text-emerald-300" };
}

function rangeTone(
  value: number | null | undefined,
  min: number | undefined,
  max: number | undefined
) {
  if (value === null || value === undefined || min === undefined || max === undefined) {
    return "text-emerald-300";
  }
  if (value < min || value > max) return "text-rose-300";
  const range = max - min || 1;
  const distance = Math.min(value - min, max - value);
  const closeness = 1 - distance / range;
  if (closeness >= 0.9) return "text-orange-300";
  if (closeness >= 0.75) return "text-sun-300";
  return "text-emerald-300";
}

function rangeFromSeries(values: number[]) {
  if (!values.length) return { min: null, max: null };
  return { min: Math.min(...values), max: Math.max(...values) };
}

function median(values: number[]) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

type TimeRangeOption = {
  key: TimeRangeKey;
  label: string;
  hours: number;
  bucketSeconds: number;
  tickMinutes: number;
};

const TIME_RANGE_OPTIONS: TimeRangeOption[] = [
  { key: "30m", label: "30 Min", hours: 0.5, bucketSeconds: 30, tickMinutes: 10 },
  { key: "1h", label: "1 Hour", hours: 1, bucketSeconds: 60, tickMinutes: 15 },
  { key: "12h", label: "12 Hours", hours: 12, bucketSeconds: 300, tickMinutes: 120 },
  { key: "24h", label: "24 Hours", hours: 24, bucketSeconds: 300, tickMinutes: 240 },
  { key: "48h", label: "48 Hours", hours: 48, bucketSeconds: 900, tickMinutes: 360 },
  { key: "7d", label: "1 Week", hours: 168, bucketSeconds: 3600, tickMinutes: 1440 },
  { key: "30d", label: "1 Month", hours: 720, bucketSeconds: 14400, tickMinutes: 10080 },
  { key: "all", label: "All Time", hours: 0, bucketSeconds: 86400, tickMinutes: 43200 },
];

export default function AquariumDetailPage() {
  const router = useRouter();
  const params = useParams();
  const aquariumId = Array.isArray(params?.aquariumId)
    ? params?.aquariumId[0]
    : params?.aquariumId;

  const [isChecking, setIsChecking] = useState(true);
  const [aquarium, setAquarium] = useState<Aquarium | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [latestByDevice, setLatestByDevice] = useState<
    Record<string, LatestReading | null>
  >({});
  const [deviceStatuses, setDeviceStatuses] = useState<Record<string, DeviceStatus>>({});
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<string[]>([]);
  const [seriesPoints, setSeriesPoints] = useState<SeriesPoint[]>([]);
  const [deviceStats, setDeviceStats] = useState<DeviceStats | null>(null);
  const [isDeviceMenuOpen, setIsDeviceMenuOpen] = useState(false);
  const [timeRange, setTimeRange] = useState<TimeRangeKey>("12h");
  const [nowTick, setNowTick] = useState(() => Date.now());
  const [activeSensor, setActiveSensor] = useState<SensorKey>("temperature");
  const [hideAllSensors, setHideAllSensors] = useState(true);
  const sensorNavRef = useRef<HTMLDivElement | null>(null);
  const lastSeriesByRangeRef = useRef<Record<TimeRangeKey, SeriesPoint[]>>({
    "30m": [],
    "1h": [],
    "12h": [],
    "24h": [],
    "48h": [],
    "7d": [],
    "30d": [],
    "all": [],
  });
  const maxSpanHoursRef = useRef(0);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setNowTick(Date.now());
    }, 1000);
    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!hideAllSensors) {
      sensorNavRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [hideAllSensors]);

  useEffect(() => {
    let ignore = false;

    async function validate() {
      const token = getAuthToken();
      if (!token) {
        router.replace("/login");
        return;
      }
      try {
        await getMe(token);
        if (!ignore) setIsChecking(false);
      } catch (err) {
        clearAuthToken();
        if (!ignore) router.replace("/login");
      }
    }

    validate();
    return () => {
      ignore = true;
    };
  }, [router]);

  useEffect(() => {
    let ignore = false;

    async function loadAquarium() {
      const token = getAuthToken();
      if (!token || !aquariumId) return;
      try {
        const data = await fetchJson<Aquarium>(
          `/v1/aquariums/${aquariumId}`,
          { headers: { Authorization: `Bearer ${token}` } },
          getClientApiBaseUrl()
        );
        if (!ignore) setAquarium(data);
      } catch {
        if (!ignore) router.push("/dashboard/aquariums");
      }
    }

    if (!isChecking) loadAquarium();

    return () => {
      ignore = true;
    };
  }, [aquariumId, isChecking, router]);

  useEffect(() => {
    let ignore = false;
    let intervalId: number | undefined;

    async function loadLatestAndDevices() {
      const token = getAuthToken();
      if (!token || !aquariumId) return;
      try {
        const deviceList = await fetchJson<Device[]>(
          `/v1/aquariums/${aquariumId}/devices`,
          { headers: { Authorization: `Bearer ${token}` } },
          getClientApiBaseUrl()
        );
        if (!ignore) {
          setDevices(deviceList);
          setSelectedDeviceIds((prev) => {
            if (!deviceList.length) return [];
            if (!prev.length) return deviceList.map((device) => device.id);
            const next = prev.filter((id) =>
              deviceList.some((device) => device.id === id)
            );
            return next.length ? next : deviceList.map((device) => device.id);
          });
        }
        if (!deviceList.length) {
          if (!ignore) setLatestByDevice({});
          return;
        }
        const readings = await Promise.all(
          deviceList.map(async (device) => {
            try {
              return await fetchJson<LatestReading>(
                `/v1/readings/${device.id}/latest`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
            } catch {
              return null;
            }
          })
        );
        const latestMap: Record<string, LatestReading | null> = {};
        deviceList.forEach((device, index) => {
          latestMap[device.id] = readings[index] ?? null;
        });
        if (!ignore) setLatestByDevice(latestMap);
      } catch {
        if (!ignore) setLatestByDevice({});
      }
    }

    if (!isChecking) {
      loadLatestAndDevices();
      intervalId = window.setInterval(loadLatestAndDevices, 10000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [aquariumId, isChecking]);

  useEffect(() => {
    let ignore = false;
    let intervalId: number | undefined;

    async function loadStatuses() {
      const token = getAuthToken();
      if (!token || !devices.length) return;
      const entries = await Promise.all(
        devices.map(async (device) => {
          try {
            const status = await fetchJson<DeviceStatus>(
              `/v1/devices/${device.id}/status`,
              { headers: { Authorization: `Bearer ${token}` } },
              getClientApiBaseUrl()
            );
            return [device.id, status] as const;
          } catch {
            return [
              device.id,
              { device_id: device.id, last_seen: null, status: "unknown" },
            ] as const;
          }
        })
      );
      if (!ignore) {
        const nextStatuses = Object.fromEntries(entries);
        setDeviceStatuses(nextStatuses);
      }
    }

    if (!isChecking && devices.length) {
      loadStatuses();
      intervalId = window.setInterval(loadStatuses, 20000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [devices, isChecking]);

  const onlineDeviceIds = useMemo(
    () =>
      devices
        .map((device) => device.id)
        .filter((id) => deviceStatuses[id]?.status === "online"),
    [devices, deviceStatuses]
  );

  const effectiveSelectedIds = useMemo(
    () => selectedDeviceIds.filter((id) => onlineDeviceIds.includes(id)),
    [onlineDeviceIds, selectedDeviceIds]
  );

  useEffect(() => {
    let ignore = false;
    let intervalId: number | undefined;

    async function loadSeries() {
      const token = getAuthToken();
      if (!token || !effectiveSelectedIds.length) {
        if (!ignore) {
          setSeriesPoints([]);
          setDeviceStats(null);
        }
        return;
      }
      const rangeConfig =
        TIME_RANGE_OPTIONS.find((option) => option.key === timeRange) ??
        TIME_RANGE_OPTIONS[1];
      const to = new Date();
      const from =
        rangeConfig.hours > 0
          ? new Date(to.getTime() - rangeConfig.hours * 60 * 60 * 1000)
          : new Date("2000-01-01T00:00:00Z");
      const params = new URLSearchParams({
        bucket_seconds: String(rangeConfig.bucketSeconds),
      });
      if (rangeConfig.hours > 0) {
        params.set("from", from.toISOString());
        params.set("to", to.toISOString());
      } else {
        params.set("from", from.toISOString());
        params.set("to", to.toISOString());
      }
      try {
        const seriesList = await Promise.all(
          effectiveSelectedIds.map(async (deviceId) => {
            try {
              const series = await fetchJson<{ points: SeriesPoint[] }>(
                `/v1/readings/${deviceId}/series?${params.toString()}`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
              return { deviceId, points: series.points ?? [] };
            } catch {
              return { deviceId, points: [] as SeriesPoint[] };
            }
          })
        );

        const bucketMap = new Map<
          string,
          { temps: number[]; phs: number[]; tds: number[]; count: number }
        >();
        seriesList.forEach(({ points }) => {
          points.forEach((point) => {
            const entry = bucketMap.get(point.bucket_start) ?? {
              temps: [],
              phs: [],
              tds: [],
              count: 0,
            };
            entry.temps.push(point.temperature_median);
            entry.phs.push(point.ph_median);
            entry.tds.push(point.tds_median);
            entry.count += point.count;
            bucketMap.set(point.bucket_start, entry);
          });
        });

        const aggregatedPoints = Array.from(bucketMap.entries())
          .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
          .map(([bucket_start, entry]) => {
            const temperature_median = median(entry.temps);
            const ph_median = median(entry.phs);
            const tds_median = median(entry.tds);
            if (
              temperature_median === null ||
              ph_median === null ||
              tds_median === null
            ) {
              return null;
            }
            return {
              bucket_start,
              temperature_median,
              ph_median,
              tds_median,
              count: entry.count,
            };
          })
          .filter((point): point is SeriesPoint => Boolean(point));

        if (!ignore) {
          setSeriesPoints(aggregatedPoints);
          if (aggregatedPoints.length) {
            lastSeriesByRangeRef.current[timeRange] = aggregatedPoints;
            const first = aggregatedPoints[0];
            const last = aggregatedPoints[aggregatedPoints.length - 1];
            const spanHours =
              (new Date(last.bucket_start).getTime() -
                new Date(first.bucket_start).getTime()) /
              (1000 * 60 * 60);
            if (Number.isFinite(spanHours)) {
              maxSpanHoursRef.current = Math.max(
                maxSpanHoursRef.current,
                spanHours
              );
            }
          }
        }

        if (effectiveSelectedIds.length === 1) {
          try {
            const stats = await fetchJson<DeviceStats>(
              `/v1/devices/${effectiveSelectedIds[0]}/stats?${params.toString()}`,
              { headers: { Authorization: `Bearer ${token}` } },
              getClientApiBaseUrl()
            );
            if (!ignore) setDeviceStats(stats);
          } catch {
            if (!ignore) setDeviceStats(null);
          }
        } else {
          const tempValues = aggregatedPoints.map((point) => point.temperature_median);
          const phValues = aggregatedPoints.map((point) => point.ph_median);
          const tdsValues = aggregatedPoints.map((point) => point.tds_median);
          const temperature_median = median(tempValues);
          const ph_median = median(phValues);
          const tds_median = median(tdsValues);
          if (!ignore) {
            if (
              temperature_median === null ||
              ph_median === null ||
              tds_median === null
            ) {
              setDeviceStats(null);
            } else {
              setDeviceStats({ temperature_median, ph_median, tds_median });
            }
          }
        }
      } catch {
        if (!ignore) {
          setSeriesPoints([]);
          setDeviceStats(null);
        }
      }
    }

    if (!isChecking && effectiveSelectedIds.length) {
      loadSeries();
      intervalId = window.setInterval(loadSeries, 20000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [effectiveSelectedIds, isChecking, timeRange]);

  const aggregatedLatest = useMemo(() => {
    if (!selectedDeviceIds.length) return null;
    const readings = selectedDeviceIds
      .map((id) => latestByDevice[id])
      .filter((reading): reading is LatestReading => Boolean(reading));
    if (!readings.length) return null;
    const tempValues = readings
      .map((reading) => reading.temperature_c)
      .filter((value): value is number => value !== null && value !== undefined);
    const phValues = readings
      .map((reading) => reading.ph_value)
      .filter((value): value is number => value !== null && value !== undefined);
    const tdsValues = readings
      .map((reading) => reading.tds_ppm)
      .filter((value): value is number => value !== null && value !== undefined);
    const receivedAt = readings
      .map((reading) => reading.received_at)
      .filter((value): value is string => Boolean(value))
      .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0];
    return {
      temperature_c: median(tempValues),
      ph_value: median(phValues),
      tds_ppm: median(tdsValues),
      received_at: receivedAt ?? null,
    } satisfies LatestReading;
  }, [latestByDevice, selectedDeviceIds]);

  const isTracked = effectiveSelectedIds.length > 0;
  const temperatureStatus = isTracked
    ? statusFromRange(
        aggregatedLatest?.temperature_c ?? null,
        aquarium?.temperature_min,
        aquarium?.temperature_max
      )
    : { label: "Not being tracked", tone: "text-white/50" };
  const phStatus = isTracked
    ? statusFromRange(
        aggregatedLatest?.ph_value ?? null,
        aquarium?.ph_min,
        aquarium?.ph_max
      )
    : { label: "Not being tracked", tone: "text-white/50" };
  const tdsStatus = isTracked
    ? statusFromRange(
        aggregatedLatest?.tds_ppm ?? null,
        aquarium?.tds_min,
        aquarium?.tds_max
      )
    : { label: "Not being tracked", tone: "text-white/50" };
  const overallStatus = useMemo(() => {
    if (!isTracked) return { label: "Not tracked", tone: "text-white/60" };
    const labels = [temperatureStatus, phStatus, tdsStatus].map((status) => status.label);
    if (labels.includes("Above range") || labels.includes("Below range")) {
      return { label: "Needs attention", tone: "text-sun-300" };
    }
    if (labels.includes("Awaiting data")) {
      return { label: "Awaiting data", tone: "text-white/60" };
    }
    return { label: "Healthy", tone: "text-emerald-300" };
  }, [isTracked, phStatus, tdsStatus, temperatureStatus]);
  const updatedAt = formatAgo(aggregatedLatest?.received_at ?? null, nowTick);
  const isSnapshotFresh = Boolean(
    aggregatedLatest?.received_at &&
      nowTick - new Date(aggregatedLatest.received_at).getTime() <= 5 * 60 * 1000
  );

  function toggleDeviceSelection(deviceId: string) {
    setSelectedDeviceIds((prev) => {
      if (prev.includes(deviceId)) {
        return prev.filter((id) => id !== deviceId);
      }
      return [...prev, deviceId];
    });
  }

  function selectAllDevices() {
    setSelectedDeviceIds(devices.map((device) => device.id));
  }

function formatChartTimeLabel(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  switch (timeRange) {
    case "30m":
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    case "1h":
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    case "12h":
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    case "24h":
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    case "48h":
      return date.toLocaleString([], { weekday: "short", hour: "2-digit" });
    case "7d":
      return date.toLocaleDateString([], { weekday: "short", day: "numeric" });
    case "30d":
      return date.toLocaleDateString([], { month: "short", day: "numeric" });
    case "all":
      return date.toLocaleDateString([], { month: "short", year: "2-digit" });
    default:
      return date.toLocaleString([], { month: "short", day: "numeric" });
  }
}

  const chartRangeConfig =
    TIME_RANGE_OPTIONS.find((option) => option.key === timeRange) ??
    TIME_RANGE_OPTIONS[1];

  const chartSeriesPoints = useMemo(() => {
    const base =
      seriesPoints.length > 0
        ? seriesPoints
        : lastSeriesByRangeRef.current[timeRange] ?? [];
    if (!base.length) return [];
    const last = base[base.length - 1];
    const now = new Date();
    const lastTime = new Date(last.bucket_start);
    if (Number.isNaN(lastTime.getTime())) return base;
    const deltaSeconds = (now.getTime() - lastTime.getTime()) / 1000;
    if (deltaSeconds < chartRangeConfig.bucketSeconds) return base;
    return [
      ...base,
      {
        bucket_start: now.toISOString(),
        temperature_median: last.temperature_median,
        ph_median: last.ph_median,
        tds_median: last.tds_median,
        count: 0,
      },
    ];
  }, [chartRangeConfig.bucketSeconds, seriesPoints, timeRange]);

  const temperatureSeriesExtended = chartSeriesPoints.map(
    (point) => point.temperature_median
  );
  const phSeriesExtended = chartSeriesPoints.map((point) => point.ph_median);
  const tdsSeriesExtended = chartSeriesPoints.map((point) => point.tds_median);
  const tempRangeExtended = rangeFromSeries(temperatureSeriesExtended);
  const phRangeExtended = rangeFromSeries(phSeriesExtended);
  const tdsRangeExtended = rangeFromSeries(tdsSeriesExtended);
  const xTickIndices = useMemo(() => {
    if (!chartSeriesPoints.length) return [];
    const pointsPerTick = Math.max(
      1,
      Math.round((chartRangeConfig.tickMinutes * 60) / chartRangeConfig.bucketSeconds)
    );
    const indices: number[] = [];
    for (let index = 0; index < chartSeriesPoints.length; index += pointsPerTick) {
      indices.push(index);
    }
    const lastIndex = chartSeriesPoints.length - 1;
    if (indices[indices.length - 1] !== lastIndex) {
      indices.push(lastIndex);
    }
    return indices;
  }, [
    chartRangeConfig.bucketSeconds,
    chartRangeConfig.tickMinutes,
    chartSeriesPoints.length,
  ]);

  const timeRangeOptionsWithAvailability = useMemo(() => {
    const availableHours = maxSpanHoursRef.current;
    return TIME_RANGE_OPTIONS.map((option) => {
      if (option.hours === 0) {
        const disabled = availableHours === 0;
        return {
          ...option,
          disabled,
          hint: disabled ? "Not enough history yet" : undefined,
        };
      }
      const disabled =
        availableHours > 0 && availableHours < option.hours * 0.8;
      return {
        ...option,
        disabled,
        hint: disabled ? "Not enough history yet" : undefined,
      };
    });
  }, [chartSeriesPoints.length]);

  const sensorRows = useMemo(
    () => [
      {
        key: "temperature" as const,
        title: "Temperature",
        unit: "°C",
        insight: (() => {
          const value = aggregatedLatest?.temperature_c;
          const min = aquarium?.temperature_min;
          const max = aquarium?.temperature_max;
          const series = temperatureSeriesExtended;
          if (
            value === null ||
            value === undefined ||
            min === undefined ||
            max === undefined
          ) {
            return "Awaiting range data.";
          }
          const last = series[series.length - 1];
          const prev = series[series.length - 2];
          const delta = last !== undefined && prev !== undefined ? last - prev : 0;
          const trend =
            delta > 0.01 ? "Rising" : delta < -0.01 ? "Falling" : "Stable";
          const range = max - min || 1;
          if (value < min || value > max) {
            return `${trend} · Past target range.`;
          }
          const distance = Math.min(value - min, max - value);
          const pct = Math.max(0, Math.min(100, (distance / range) * 100));
          return `${trend} · ${Math.round(pct)}% from limit.`;
        })(),
        value:
          aggregatedLatest?.temperature_c !== null &&
          aggregatedLatest?.temperature_c !== undefined
            ? aggregatedLatest.temperature_c.toFixed(1)
            : "—",
        range: aquarium
          ? `${aquarium.temperature_min}–${aquarium.temperature_max}°C`
          : "—",
        status: temperatureStatus,
        helper: "",
        series: temperatureSeriesExtended,
        seriesRange: tempRangeExtended,
        median: deviceStats?.temperature_median ?? null,
      },
      {
        key: "ph" as const,
        title: "pH",
        unit: "",
        insight: (() => {
          const value = aggregatedLatest?.ph_value;
          const min = aquarium?.ph_min;
          const max = aquarium?.ph_max;
          const series = phSeriesExtended;
          if (
            value === null ||
            value === undefined ||
            min === undefined ||
            max === undefined
          ) {
            return "Awaiting range data.";
          }
          const last = series[series.length - 1];
          const prev = series[series.length - 2];
          const delta = last !== undefined && prev !== undefined ? last - prev : 0;
          const trend =
            delta > 0.01 ? "Rising" : delta < -0.01 ? "Falling" : "Stable";
          const range = max - min || 1;
          if (value < min || value > max) {
            return `${trend} · Past target range.`;
          }
          const distance = Math.min(value - min, max - value);
          const pct = Math.max(0, Math.min(100, (distance / range) * 100));
          return `${trend} · ${Math.round(pct)}% from limit.`;
        })(),
        value:
          aggregatedLatest?.ph_value !== null && aggregatedLatest?.ph_value !== undefined
            ? aggregatedLatest.ph_value.toFixed(1)
            : "—",
        range: aquarium ? `${aquarium.ph_min}–${aquarium.ph_max}` : "—",
        status: phStatus,
        helper: "",
        series: phSeriesExtended,
        seriesRange: phRangeExtended,
        median: deviceStats?.ph_median ?? null,
      },
      {
        key: "tds" as const,
        title: "TDS",
        unit: "ppm",
        insight: (() => {
          const value = aggregatedLatest?.tds_ppm;
          const min = aquarium?.tds_min;
          const max = aquarium?.tds_max;
          const series = tdsSeriesExtended;
          if (
            value === null ||
            value === undefined ||
            min === undefined ||
            max === undefined
          ) {
            return "Awaiting range data.";
          }
          const last = series[series.length - 1];
          const prev = series[series.length - 2];
          const delta = last !== undefined && prev !== undefined ? last - prev : 0;
          const trend =
            delta > 0.5 ? "Rising" : delta < -0.5 ? "Falling" : "Stable";
          const range = max - min || 1;
          if (value < min || value > max) {
            return `${trend} · Past target range.`;
          }
          const distance = Math.min(value - min, max - value);
          const pct = Math.max(0, Math.min(100, (distance / range) * 100));
          return `${trend} · ${Math.round(pct)}% from limit.`;
        })(),
        value:
          aggregatedLatest?.tds_ppm !== null &&
          aggregatedLatest?.tds_ppm !== undefined
            ? Math.round(aggregatedLatest.tds_ppm).toString()
            : "—",
        range: aquarium ? `${aquarium.tds_min}–${aquarium.tds_max} ppm` : "—",
        status: tdsStatus,
        helper: "",
        series: tdsSeriesExtended,
        seriesRange: tdsRangeExtended,
        median: deviceStats?.tds_median ?? null,
      },
    ],
    [
      aquarium,
      deviceStats,
      aggregatedLatest?.ph_value,
      aggregatedLatest?.tds_ppm,
      aggregatedLatest?.temperature_c,
      phStatus,
      tdsStatus,
      temperatureStatus,
        temperatureSeriesExtended,
        phSeriesExtended,
        tdsSeriesExtended,
        tempRangeExtended,
        phRangeExtended,
        tdsRangeExtended,
    ]
  );

  if (isChecking) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
          <Panel>
            <div className="flex items-center justify-between">
              <div className="text-base uppercase tracking-[0.3em] text-white/40">
                Aquarium
              </div>
              {aquarium?.id ? (
                <button
                  type="button"
                  onClick={() => router.push(`/dashboard/aquariums/${aquarium.id}/edit`)}
                  className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white/70 transition hover:border-white/30 hover:text-white"
                >
                  <span className="inline-flex items-center gap-2">
                    <span className="text-base leading-none">✎</span>
                    Edit
                  </span>
                </button>
              ) : null}
            </div>
            <h1 className="mt-2 font-display text-4xl">
              {aquarium?.name ?? "Aquarium"}
            </h1>
            <p className="mt-2 text-lg text-white/60">
              {aquarium
                ? `${aquarium.water_type} · ${aquarium.liters} L`
                : "Loading details..."}
            </p>

            <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr_0.9fr]">
              <OverviewCard title="Last snapshot">
                {!isTracked && devices.length ? (
                  <div className="rounded-xl border border-sun-500/40 bg-sun-500/10 px-3 py-2 text-sm text-sun-100">
                    Not being tracked. No online devices are reporting.
                  </div>
                ) : null}
                <div className="mt-3 grid gap-3 text-sm text-white/60">
                  <div className="flex items-center justify-between">
                    <span>Temperature</span>
                    <span className="text-lg font-semibold text-white">
                      {aggregatedLatest?.temperature_c !== null &&
                      aggregatedLatest?.temperature_c !== undefined &&
                      isSnapshotFresh
                        ? `${aggregatedLatest.temperature_c.toFixed(1)}°C`
                        : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>pH</span>
                    <span className="text-lg font-semibold text-white">
                      {aggregatedLatest?.ph_value !== null &&
                      aggregatedLatest?.ph_value !== undefined &&
                      isSnapshotFresh
                        ? aggregatedLatest.ph_value.toFixed(1)
                        : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>TDS</span>
                    <span className="text-lg font-semibold text-white">
                      {aggregatedLatest?.tds_ppm !== null &&
                      aggregatedLatest?.tds_ppm !== undefined &&
                      isSnapshotFresh
                        ? `${Math.round(aggregatedLatest.tds_ppm)} ppm`
                        : "—"}
                    </span>
                  </div>
                </div>
              </OverviewCard>

              <OverviewCard title="Target ranges">
                <StatList
                  rows={[
                    {
                      label: "Temperature",
                      value: aquarium
                        ? `${aquarium.temperature_min}–${aquarium.temperature_max}°C`
                        : "—",
                    },
                    {
                      label: "pH",
                      value: aquarium ? `${aquarium.ph_min}–${aquarium.ph_max}` : "—",
                    },
                    {
                      label: "TDS",
                      value: aquarium
                        ? `${aquarium.tds_min}–${aquarium.tds_max} ppm`
                        : "—",
                    },
                  ]}
                  valueClassNameFor={(label) => {
                    if (!isSnapshotFresh) return "text-white/40";
                    if (label === "Temperature") {
                      return rangeTone(
                        aggregatedLatest?.temperature_c ?? null,
                        aquarium?.temperature_min,
                        aquarium?.temperature_max
                      );
                    }
                    if (label === "pH") {
                      return rangeTone(
                        aggregatedLatest?.ph_value ?? null,
                        aquarium?.ph_min,
                        aquarium?.ph_max
                      );
                    }
                    if (label === "TDS") {
                      return rangeTone(
                        aggregatedLatest?.tds_ppm ?? null,
                        aquarium?.tds_min,
                        aquarium?.tds_max
                      );
                    }
                    return "text-white/60";
                  }}
                />
              </OverviewCard>

              <OverviewCard title="Tracking status">
                <div className="flex items-center justify-between text-sm text-white/60">
                  <span>Overall</span>
                  <span className={`text-sm font-semibold ${overallStatus.tone}`}>
                    {overallStatus.label}
                  </span>
                </div>
                <div className="mt-3 grid gap-2 text-sm text-white/60">
                  <div className="flex items-center justify-between">
                    <span>Devices online</span>
                    <span className="text-white">
                      {effectiveSelectedIds.length} / {devices.length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Selected</span>
                    <span className="text-white">{selectedDeviceIds.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Last update</span>
                    <span className="text-white">{updatedAt}</span>
                  </div>
                </div>
              </OverviewCard>
            </div>
          </Panel>

          <section className="flex flex-col gap-6">
            <Panel>
              <div ref={sensorNavRef} />
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  {sensorRows.map((sensor) => {
                    const isActive = !hideAllSensors && sensor.key === activeSensor;
                    return (
                      <button
                        key={sensor.key}
                        type="button"
                        onClick={() => {
                          setActiveSensor(sensor.key);
                          setHideAllSensors(false);
                        }}
                        className={
                          isActive
                            ? "inline-flex items-center justify-center rounded-full border border-ocean-300/50 bg-ocean-500/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-ocean-100 shadow-inner shadow-ocean-500/20"
                            : "inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/60 transition hover:border-white/30 hover:text-white"
                        }
                      >
                        {sensor.title}
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  onClick={() => setHideAllSensors((prev) => !prev)}
                  className={
                    hideAllSensors
                      ? "inline-flex items-center justify-center rounded-full border border-ocean-300/50 bg-ocean-500/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-ocean-100 shadow-inner shadow-ocean-500/20"
                      : "inline-flex items-center justify-center rounded-full border border-white/15 bg-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/70 transition hover:border-white/30 hover:text-white"
                  }
                  aria-label={hideAllSensors ? "Show sensor data" : "Hide sensor data"}
                >
                  <span className="inline-flex items-center gap-2">
                    <svg
                      aria-hidden="true"
                      viewBox="0 0 24 24"
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                    >
                      <path d="M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6z" />
                      <circle cx="12" cy="12" r="3.5" />
                    </svg>
                    {hideAllSensors ? "Show" : "Hide"} Sensors
                  </span>
                </button>
              </div>
            </Panel>

            {hideAllSensors ? null : (
              sensorRows
                .filter((sensor) => sensor.key === activeSensor)
                .map((sensor) => (
                  <SensorPanel
                    key={sensor.key}
                    title={sensor.title}
                    rangeLabel={
                      sensor.range !== "—"
                        ? `Target range is ${sensor.range}`
                        : "Target range unavailable"
                    }
                    latestValue={sensor.value}
                    latestUnit={sensor.unit}
                    lastUpdate={updatedAt}
                    insight={sensor.insight}
                    statusLabel={sensor.status.label}
                    statusTone={sensor.status.tone}
                    median={
                      sensor.median !== null && sensor.median !== undefined
                        ? sensor.key === "tds"
                          ? Math.round(sensor.median).toString()
                          : sensor.median.toFixed(1)
                        : "—"
                    }
                    minMax={
                      sensor.seriesRange.min !== null &&
                      sensor.seriesRange.max !== null
                        ? sensor.key === "tds"
                          ? `${Math.round(sensor.seriesRange.min)}–${Math.round(
                              sensor.seriesRange.max
                            )}`
                          : `${sensor.seriesRange.min.toFixed(
                              1
                            )}–${sensor.seriesRange.max.toFixed(1)}`
                        : "—"
                    }
                    series={sensor.series}
                    seriesTimestamps={chartSeriesPoints.map((point) => point.bucket_start)}
                    timeRangeOptions={timeRangeOptionsWithAvailability}
                    activeRange={timeRange}
                    onRangeChange={(key) => setTimeRange(key as TimeRangeKey)}
                    xTickIndices={xTickIndices}
                    formatValue={(value) =>
                      sensor.key === "tds"
                        ? Math.round(value).toString()
                        : value.toFixed(1)
                    }
                    formatTime={formatChartTimeLabel}
                  />
                ))
            )}

            <Panel>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-base font-semibold">Connected devices</div>
                  <div className="mt-1 text-sm text-white/60">
                    {selectedDeviceIds.length
                      ? `${selectedDeviceIds.length} selected · ${
                          effectiveSelectedIds.length
                            ? `${effectiveSelectedIds.length} online in view`
                            : "no online devices in view"
                        }`
                      : "No devices selected"}
                    .
                  </div>
                </div>
                {devices.length ? (
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsDeviceMenuOpen((prev) => !prev)}
                      className="inline-flex items-center justify-center rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/70 transition hover:border-white/30 hover:text-white"
                    >
                      Devices
                    </button>
                    {isDeviceMenuOpen ? (
                      <div className="absolute right-0 z-10 mt-2 w-72 rounded-2xl border border-white/10 bg-ocean-950/95 p-3 shadow-lg backdrop-blur">
                        <div className="mb-2 text-xs uppercase tracking-[0.2em] text-white/40">
                          Include devices
                        </div>
                        <div className="grid gap-2">
                          {devices.map((device) => {
                            const status = deviceStatuses[device.id];
                            const isSelected = selectedDeviceIds.includes(device.id);
                            const statusTone =
                              status?.status === "online"
                                ? "text-emerald-200"
                                : status?.status === "offline"
                                ? "text-sun-200"
                                : "text-white/60";
                            return (
                              <label
                                key={device.id}
                                className="flex items-center justify-between gap-2 rounded-xl border border-white/5 bg-white/5 px-3 py-2 text-sm text-white/80"
                              >
                                <div className="min-w-0">
                                  <div className="truncate">{device.name}</div>
                                  <div className={`text-xs ${statusTone}`}>
                                    {status?.status ?? "unknown"}
                                  </div>
                                </div>
                                <input
                                  type="checkbox"
                                  className="h-4 w-4 accent-ocean-400"
                                  checked={isSelected}
                                  onChange={() => toggleDeviceSelection(device.id)}
                                />
                              </label>
                            );
                          })}
                        </div>
                        <div className="mt-3 flex items-center justify-between">
                          <button
                            type="button"
                            onClick={selectAllDevices}
                            className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60 transition hover:text-white"
                          >
                            Select all
                          </button>
                          <button
                            type="button"
                            onClick={() => setIsDeviceMenuOpen(false)}
                            className="text-xs font-semibold uppercase tracking-[0.2em] text-white/60 transition hover:text-white"
                          >
                            Close
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
              <div className="mt-4 grid gap-3">
                {devices.length ? (
                  devices.map((device) => {
                    const status = deviceStatuses[device.id];
                    const statusTone =
                      status?.status === "online"
                        ? "bg-emerald-400/20 text-emerald-200"
                        : status?.status === "offline"
                        ? "bg-sun-500/20 text-sun-200"
                        : "bg-white/10 text-white/60";
                    return (
                      <div
                        key={device.id}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                      >
                        <div>
                          <div className="text-sm font-semibold text-white">
                            {device.name}
                          </div>
                          <div className="text-xs text-white/50">
                            {device.location ?? "No location set"}
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-xs uppercase tracking-[0.2em]">
                          <span className={`rounded-full px-3 py-1 ${statusTone}`}>
                            {status?.status ?? "unknown"}
                          </span>
                          <span className="text-white/50">
                            Last seen {formatAgo(status?.last_seen, nowTick)}
                          </span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="rounded-2xl border border-dashed border-white/15 bg-white/5 p-4 text-sm text-white/60">
                    No devices connected yet. Attach a device to start tracking live
                    metrics.
                  </div>
                )}
              </div>
            </Panel>
          </section>
        </main>
      </div>
    </div>
  );
}

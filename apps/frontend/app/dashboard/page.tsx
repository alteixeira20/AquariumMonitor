"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAuthToken, getAuthToken } from "../../lib/auth";
import { getMe } from "../../lib/auth_api";
import TopNav from "../../components/dashboard/TopNav";
import StatusBadge from "../../components/ui/StatusBadge";
import Select from "../../components/ui/Select";
import { fetchJson } from "../../lib/api";
import { getClientApiBaseUrl } from "../../lib/config";

function sensorLevel(
  value: number | null | undefined,
  min: number | undefined,
  max: number | undefined
) {
  if (value === null || value === undefined || min === undefined || max === undefined) {
    return 0;
  }
  const range = max - min || 1;
  if (value < min || value > max) {
    const delta = value < min ? min - value : value - max;
    const percent = delta / range;
    return percent > 0.10 ? 3 : 2;
  }
  const distance = Math.min(value - min, max - value);
  const closeness = 1 - distance / range;
  return closeness >= 0.75 ? 1 : 0;
}

function levelLabel(level: number) {
  if (level >= 3) return { label: "Critical", tone: "error" as const };
  if (level === 2) return { label: "Alert", tone: "waiting" as const };
  if (level === 1) return { label: "Warning", tone: "waiting" as const };
  return { label: "Healthy", tone: "success" as const };
}

export default function DashboardPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [aquariums, setAquariums] = useState<
    Array<{
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
    }>
  >([]);
  const [devices, setDevices] = useState<
    Array<{ id: string; name: string; location: string | null; is_active: boolean }>
  >([]);
  const [aquariumByDevice, setAquariumByDevice] = useState<Record<string, string>>(
    {}
  );
  const [aquariumIdByDevice, setAquariumIdByDevice] = useState<
    Record<string, string>
  >({});
  const [activeAquariumId, setActiveAquariumId] = useState("");
  const activeAquarium = aquariums.find((aq) => aq.id === activeAquariumId);
  const [trackedCount, setTrackedCount] = useState(0);
  const [latestReading, setLatestReading] = useState<{
    temperature_c: number | null;
    ph_value: number | null;
    tds_ppm: number | null;
    received_at: string | null;
  } | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [isLoadingAquariums, setIsLoadingAquariums] = useState(true);
  const [isLoadingDevices, setIsLoadingDevices] = useState(true);
  const [isLoadingLatest, setIsLoadingLatest] = useState(true);
  const [latestByAquarium, setLatestByAquarium] = useState<
    Record<
      string,
      | {
          temperature_c: number;
          ph_value: number;
          tds_ppm: number;
          received_at: string | null;
        }
      | null
    >
  >({});

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

    async function loadData() {
      const token = getAuthToken();
      if (!token) return;
      setIsLoadingAquariums(true);
      setIsLoadingDevices(true);
      try {
        const aquariumsData = await fetchJson<
          Array<{
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
          }>
        >(
          "/v1/aquariums",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
          getClientApiBaseUrl()
        );
        if (ignore) return;
        setAquariums(aquariumsData);
        if (aquariumsData.length > 0) {
          setActiveAquariumId((prev) => prev || aquariumsData[0].id);
        }

        const attachments = await Promise.all(
          aquariumsData.map(async (aq) => {
            try {
              const devicesForAquarium = await fetchJson<Array<{ id: string }>>(
                `/v1/aquariums/${aq.id}/devices`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
              return {
                aquariumId: aq.id,
                aquariumName: aq.name,
                deviceIds: devicesForAquarium.map((device) => device.id),
              };
            } catch {
              return { aquariumId: aq.id, aquariumName: aq.name, deviceIds: [] };
            }
          })
        );

        const deviceMap: Record<string, string> = {};
        const deviceIdMap: Record<string, string> = {};
        let tracked = 0;
        attachments.forEach((item) => {
          if (item.deviceIds.length > 0) tracked += 1;
          item.deviceIds.forEach((deviceId) => {
            deviceMap[deviceId] = item.aquariumName;
            deviceIdMap[deviceId] = item.aquariumId;
          });
        });
        setTrackedCount(tracked);
        setAquariumByDevice(deviceMap);
        setAquariumIdByDevice(deviceIdMap);

        const devicesData = await fetchJson<
          Array<{ id: string; name: string; location: string | null; is_active: boolean }>
        >(
          "/v1/devices/owned",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
          getClientApiBaseUrl()
        );
        if (ignore) return;
        setDevices(devicesData);

        const latestByAqEntries = await Promise.all(
          aquariumsData.map(async (aq) => {
            try {
              const devicesForAquarium = await fetchJson<Array<{ id: string }>>(
                `/v1/aquariums/${aq.id}/devices`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
              if (!devicesForAquarium.length) {
                return [aq.id, null] as const;
              }
              const readings = await Promise.all(
                devicesForAquarium.map(async (device) => {
                  try {
                    return await fetchJson<{
                      temperature_c: number;
                      ph_value: number;
                      tds_ppm: number;
                      received_at: string | null;
                    }>(
                      `/v1/readings/${device.id}/latest`,
                      { headers: { Authorization: `Bearer ${token}` } },
                      getClientApiBaseUrl()
                    );
                  } catch {
                    return null;
                  }
                })
              );
              const temps = readings
                .map((reading) => reading?.temperature_c)
                .filter((value): value is number => value !== null && value !== undefined);
              const phs = readings
                .map((reading) => reading?.ph_value)
                .filter((value): value is number => value !== null && value !== undefined);
              const tds = readings
                .map((reading) => reading?.tds_ppm)
                .filter((value): value is number => value !== null && value !== undefined);
              if (!temps.length || !phs.length || !tds.length) {
                return [aq.id, null] as const;
              }
              const median = (values: number[]) => {
                const sorted = [...values].sort((a, b) => a - b);
                const mid = Math.floor(sorted.length / 2);
                return sorted.length % 2 === 0
                  ? (sorted[mid - 1] + sorted[mid]) / 2
                  : sorted[mid];
              };
              const latestReceivedAt = readings
                .map((reading) => reading?.received_at)
                .filter((value): value is string => Boolean(value))
                .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0];
              return [
                aq.id,
                {
                  temperature_c: median(temps),
                  ph_value: median(phs),
                  tds_ppm: median(tds),
                  received_at: latestReceivedAt ?? null,
                },
              ] as const;
            } catch {
              return [aq.id, null] as const;
            }
          })
        );
        if (!ignore) {
          setLatestByAquarium(Object.fromEntries(latestByAqEntries));
        }
      } catch (err) {
        if (!ignore) {
          setAquariums([]);
          setDevices([]);
          setTrackedCount(0);
          setAquariumByDevice({});
          setAquariumIdByDevice({});
          setLatestByAquarium({});
        }
      } finally {
        if (!ignore) {
          setIsLoadingAquariums(false);
          setIsLoadingDevices(false);
        }
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;
    let intervalId: number | undefined;

    async function loadLatestReading() {
      const token = getAuthToken();
      if (!token || !activeAquariumId) return;
      setIsLoadingLatest(true);
      try {
        const devicesForAquarium = await fetchJson<Array<{ id: string }>>(
          `/v1/aquariums/${activeAquariumId}/devices`,
          { headers: { Authorization: `Bearer ${token}` } },
          getClientApiBaseUrl()
        );
        if (!devicesForAquarium.length) {
          if (!ignore) setLatestReading(null);
          return;
        }
        const readings = await Promise.all(
          devicesForAquarium.map(async (device) => {
            try {
              return await fetchJson<{
                temperature_c: number;
                ph_value: number;
                tds_ppm: number;
                received_at: string;
              }>(
                `/v1/readings/${device.id}/latest`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
            } catch {
              return null;
            }
          })
        );
        const latest = readings
          .filter((reading) => reading?.received_at)
          .sort((a, b) => {
            if (!a || !b) return 0;
            return (
              new Date(b.received_at).getTime() -
              new Date(a.received_at).getTime()
            );
          })[0];
        if (!ignore) {
          setLatestReading(
            latest
              ? {
                  temperature_c: latest.temperature_c ?? null,
                  ph_value: latest.ph_value ?? null,
                  tds_ppm: latest.tds_ppm ?? null,
                  received_at: latest.received_at ?? null,
                }
              : null
          );
        }
      } finally {
        if (!ignore) setIsLoadingLatest(false);
      }
    }

    if (!isChecking) {
      loadLatestReading();
      intervalId = window.setInterval(loadLatestReading, 10000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [activeAquariumId, isChecking]);

  useEffect(() => {
    if (!latestReading?.received_at) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [latestReading?.received_at]);

  const liveLabel = latestReading?.received_at
    ? (() => {
        const diffMs = now - new Date(latestReading.received_at).getTime();
        const seconds = Math.max(0, Math.floor(diffMs / 1000));
        if (seconds >= 180) return "Offline";
        if (seconds < 60) return `Updated ${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        return `Updated ${minutes}m ago`;
      })()
    : "Waiting for data";

  if (isChecking) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12">
        <div className="glass-panel w-full max-w-md p-6 text-center text-sm text-white/70">
          Checking session…
        </div>
      </div>
    );
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
        <section className="grid items-stretch gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="glass-panel flex h-full flex-col p-6">
            <div className="text-base uppercase tracking-[0.3em] text-white/40">
              Overview
            </div>
            <h1 className="mt-3 font-display text-4xl">
              {aquariums.length > 0
                ? "Welcome back to your aquariums"
                : "Start with your first aquarium"}
            </h1>
            <p className="mt-3 text-lg text-white/60">
              {aquariums.length > 0
                ? "Live metrics will appear here once your first device is calibrated and attached to an aquarium."
                : "Create your first aquarium to begin tracking water quality."}
            </p>
            <div className="mt-auto flex flex-wrap gap-3 pt-6">
              <button
                className="btn-primary"
                type="button"
                onClick={() => router.push("/dashboard/aquariums/new")}
              >
                Add aquarium
              </button>
              {aquariums.length > 0 ? (
                <button
                  className="rounded-full border border-white/20 px-5 py-2 text-base font-semibold transition hover:border-ocean-500/60"
                  type="button"
                  onClick={() => router.push("/dashboard/devices/new")}
                >
                  Register device
                </button>
              ) : null}
            </div>
          </div>

          <div className="glass-panel flex h-full flex-col p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-base uppercase tracking-[0.3em] text-white/40">
                  Latest reading
                </div>
                <div className="mt-1 text-base font-semibold text-white/80">
                  {aquariums.length === 0
                    ? "Not yet added"
                    : activeAquarium?.name ?? "Aquarium"}
                </div>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white/70">
                <span
                  className={[
                    "h-2 w-2 rounded-full",
                    latestReading?.received_at
                      ? now - new Date(latestReading.received_at).getTime() >=
                        180000
                        ? "bg-red-400 shadow-glow"
                        : "bg-emerald-400 shadow-glow"
                      : "bg-yellow-300",
                  ].join(" ")}
                />
                {liveLabel}
              </div>

              {aquariums.length > 1 ? (
                <div className="min-w-[200px]">
                  <Select<string>
                    value={activeAquariumId}
                    onChange={setActiveAquariumId}
                    options={aquariums.map((aq) => ({
                      value: aq.id,
                      label: aq.name,
                    }))}
                  />
                </div>
              ) : null}
            </div>
            <div className="mt-4 grid gap-3 text-base text-white/60">
              <div className="flex items-center justify-between">
                <span>Temperature</span>
                <span className="text-white/80">
                  {latestReading?.temperature_c !== null &&
                  latestReading?.temperature_c !== undefined
                    ? `${latestReading.temperature_c.toFixed(1)}°C`
                    : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>pH</span>
                <span className="text-white/80">
                  {latestReading?.ph_value !== null &&
                  latestReading?.ph_value !== undefined
                    ? latestReading.ph_value.toFixed(1)
                    : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>TDS</span>
                <span className="text-white/80">
                  {latestReading?.tds_ppm !== null &&
                  latestReading?.tds_ppm !== undefined
                    ? `${Math.round(latestReading.tds_ppm)} ppm`
                    : "—"}
                </span>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/50">
                {isLoadingLatest
                  ? "Loading latest readings…"
                  : latestReading
                    ? "Latest reading received."
                    : "No readings yet. Attach a calibrated device to start tracking."}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            {
              label: "Tracked aquariums",
              value: isLoadingAquariums ? "—" : `${trackedCount}`,
            },
            { label: "Alerts today", value: "0" },
          ].map((item) => (
            <div key={item.label} className="glass-panel p-5">
              <div className="text-base uppercase tracking-[0.3em] text-white/40">
                {item.label}
              </div>
              <div className="mt-3 text-4xl font-semibold text-white">
                {item.value}
              </div>
            </div>
          ))}
        </section>

        <section className="grid gap-6">
          <div className="glass-panel p-6 max-w-4xl mx-auto">
            <div className="text-base font-semibold">Aquariums</div>
            {aquariums.length === 0 ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
                No aquariums yet. Create your first aquarium to start tracking
                water quality.
              </div>
            ) : (
              <div className="mt-4 grid gap-3 text-base text-white/70">
                {aquariums.slice(0, 3).map((aq) => (
                  <button
                    key={aq.id}
                    type="button"
                    onClick={() => router.push(`/dashboard/aquariums/${aq.id}`)}
                    className="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left transition hover:border-ocean-500/40 hover:bg-white/8"
                  >
                    <div>
                      <div className="font-semibold text-white">{aq.name}</div>
                      <div className="text-xs uppercase tracking-[0.2em] text-white/40">
                        {aq.water_type} · {aq.liters} L
                      </div>
                    </div>
                    {(() => {
                      const latest = latestByAquarium[aq.id];
                      if (!latest) {
                        return <StatusBadge label="No data" tone="info" />;
                      }
                      const stale =
                        !latest.received_at ||
                        Date.now() - new Date(latest.received_at).getTime() > 5 * 60 * 1000;
                      if (stale) {
                        return <StatusBadge label="Critical" tone="error" />;
                      }
                      const levels = [
                        sensorLevel(latest.temperature_c, aq.temperature_min, aq.temperature_max),
                        sensorLevel(latest.ph_value, aq.ph_min, aq.ph_max),
                        sensorLevel(latest.tds_ppm, aq.tds_min, aq.tds_max),
                      ];
                      const level = Math.max(...levels);
                      const status = levelLabel(level);
                      return <StatusBadge label={status.label} tone={status.tone} />;
                    })()}
                  </button>
                ))}
                {aquariums.length > 3 ? (
                  <div className="text-sm text-white/50">
                    +{aquariums.length - 3} more aquariums
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </section>
        </main>
      </div>
    </div>
  );
}

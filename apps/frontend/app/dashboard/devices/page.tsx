"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import TopNav from "../../../components/dashboard/TopNav";
import { useToast } from "../../../components/ui/ToastProvider";
import { clearAuthToken, getAuthToken } from "../../../lib/auth";
import { getMe } from "../../../lib/auth_api";
import { fetchJson } from "../../../lib/api";
import { getClientApiBaseUrl } from "../../../lib/config";
import Select from "../../../components/ui/Select";

type Device = {
  id: string;
  name: string;
  location: string | null;
  is_active: boolean;
  created_at: string;
};
type Aquarium = { id: string; name: string };
type DeviceStatus = { device_id: string; status: "online" | "offline" };
type DeviceReading = {
  device_id: string;
  received_at: string;
  temperature_c: number;
  ph_value: number;
  tds_ppm: number;
};
type ReadingLog = {
  id: string;
  deviceName: string;
  deviceType: "Simulated" | "Manual";
  temperature: string;
  ph: string;
  tds: string;
  timestamp: string;
};
type LogView = "5" | "15" | "30" | "all";

export default function DevicesPage() {
  const router = useRouter();
  const { push } = useToast();
  const [isChecking, setIsChecking] = useState(true);
  const [devices, setDevices] = useState<Device[]>([]);
  const [aquariumByDevice, setAquariumByDevice] = useState<
    Record<string, string>
  >({});
  const [statusByDevice, setStatusByDevice] = useState<
    Record<string, "online" | "offline">
  >({});
  const [simPausedByDevice, setSimPausedByDevice] = useState<
    Record<string, boolean>
  >({});
  const [holdProgress, setHoldProgress] = useState<Record<string, number>>({});
  const holdTimers = useRef<Record<string, number>>({});
  const holdIntervals = useRef<Record<string, number>>({});
  const [logs, setLogs] = useState<ReadingLog[]>([]);
  const [logView, setLogView] = useState<LogView>("5");
  const [logPage, setLogPage] = useState(1);
  const [logTotal, setLogTotal] = useState(0);
  const [logPageSize, setLogPageSize] = useState(5);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingLogs, setIsLoadingLogs] = useState(true);

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
    let intervalId: number | undefined;

    async function loadDevices() {
      const token = getAuthToken();
      if (!token) return;
      setIsLoading(true);
      try {
        const aquariums = await fetchJson<Aquarium[]>(
          "/v1/aquariums",
          {
            headers: { Authorization: `Bearer ${token}` },
          },
          getClientApiBaseUrl()
        );
        const attachments = await Promise.all(
          aquariums.map(async (aq) => {
            try {
              const devicesForAquarium = await fetchJson<Array<{ id: string }>>(
                `/v1/aquariums/${aq.id}/devices`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
              return devicesForAquarium.map((device) => ({
                deviceId: device.id,
                aquariumName: aq.name,
              }));
            } catch {
              return [];
            }
          })
        );
        const mapping: Record<string, string> = {};
        attachments.flat().forEach((item) => {
          mapping[item.deviceId] = item.aquariumName;
        });

        const data = await fetchJson<Device[]>(
          "/v1/devices/owned",
          {
            headers: { Authorization: `Bearer ${token}` },
          },
          getClientApiBaseUrl()
        );
        const statuses = await Promise.all(
          data.map(async (device) => {
            try {
              return await fetchJson<DeviceStatus>(
                `/v1/devices/${device.id}/status`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
            } catch {
              return { device_id: device.id, status: "offline" } as DeviceStatus;
            }
          })
        );
        if (!ignore) {
          setDevices(data);
          setAquariumByDevice(mapping);
          setStatusByDevice(
            Object.fromEntries(
              statuses.map((status) => [status.device_id, status.status])
            )
          );
          setSimPausedByDevice((prev) => {
            const next = { ...prev };
            data.forEach((device) => {
              if (device.location?.startsWith("Simulated · ")) {
                if (next[device.id] === undefined) next[device.id] = false;
              }
            });
            return next;
          });
        }
      } catch (err) {
        if (!ignore) {
          setDevices([]);
          setAquariumByDevice({});
          setStatusByDevice({});
          push("Failed to load devices.", "error");
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    if (!isChecking) {
      loadDevices();
      intervalId = window.setInterval(loadDevices, 10000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [isChecking, push]);

  useEffect(() => {
    let ignore = false;
    let intervalId: number | undefined;

    async function loadLogs() {
      const token = getAuthToken();
      if (!token || devices.length === 0) return;
      setIsLoadingLogs(true);
      try {
        const pageSize =
          logView === "5"
            ? 5
            : logView === "15"
              ? 15
              : logView === "30"
                ? 30
                : logPageSize;
        const pageParam = logView === "all" ? logPage : 1;
        const readingPages = await Promise.all(
          devices.map(async (device) => {
            try {
              const response = await fetchJson<{
                readings: DeviceReading[];
                total: number;
              }>(
                `/v1/readings/${device.id}/paginated?page=${pageParam}&page_size=${pageSize}`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
              return { device, readings: response.readings, total: response.total };
            } catch {
              return { device, readings: [], total: 0 };
            }
          })
        );

        const combined = readingPages.flatMap(({ device, readings }) => {
          const deviceType = device.location?.startsWith("Simulated · ")
            ? "Simulated"
            : "Manual";
          return readings.map((reading) => {
            const temp =
              reading.temperature_c !== null &&
              reading.temperature_c !== undefined
                ? `${reading.temperature_c.toFixed(1)}°C`
                : "—";
            const ph =
              reading.ph_value !== null && reading.ph_value !== undefined
                ? reading.ph_value.toFixed(1)
                : "—";
            const tds =
              reading.tds_ppm !== null && reading.tds_ppm !== undefined
                ? `${Math.round(reading.tds_ppm)} ppm`
                : "—";
            const entry: ReadingLog & { _sort: string } = {
              id: `${device.id}-${reading.received_at}`,
              deviceName: device.name,
              deviceType,
              temperature: temp,
              ph,
              tds,
              timestamp: new Date(reading.received_at).toLocaleTimeString(),
              _sort: reading.received_at,
            };
            return entry;
          });
        });

        const sorted = combined.sort(
          (a, b) => new Date(b._sort).getTime() - new Date(a._sort).getTime()
        );

        const totalCount = readingPages.reduce((sum, item) => sum + item.total, 0);
        if (!ignore) setLogTotal(totalCount);

        if (logView === "all") {
          if (!ignore) setLogs(sorted.slice(0, pageSize));
        } else {
          if (!ignore) setLogs(sorted.slice(0, pageSize));
        }
      } finally {
        if (!ignore) setIsLoadingLogs(false);
      }
    }

    if (!isChecking) {
      loadLogs();
      intervalId = window.setInterval(loadLogs, 10000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [devices, isChecking, logPage, logPageSize, logView]);

  if (isChecking) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  function clearHold(id: string) {
    const timers = holdTimers.current;
    const intervals = holdIntervals.current;
    if (timers[id]) {
      window.clearTimeout(timers[id]);
      delete timers[id];
    }
    if (intervals[id]) {
      window.clearInterval(intervals[id]);
      delete intervals[id];
    }
    setHoldProgress((prev) => ({ ...prev, [id]: 0 }));
  }

  function startHold(id: string) {
    if (holdTimers.current[id]) return;
    const start = Date.now();
    holdIntervals.current[id] = window.setInterval(() => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / 2500, 1);
      setHoldProgress((prev) => ({ ...prev, [id]: progress }));
    }, 100);
    holdTimers.current[id] = window.setTimeout(() => {
      clearHold(id);
      handleDelete(id);
    }, 2500);
  }

  async function handleDelete(id: string) {
    const token = getAuthToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    try {
      const response = await fetch(
        `${getClientApiBaseUrl()}/v1/devices/${id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to delete device.");
      }
      setDevices((prev) => prev.filter((device) => device.id !== id));
      setStatusByDevice((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      setAquariumByDevice((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      setSimPausedByDevice((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      setLogs((prev) => prev.filter((log) => !log.id.startsWith(id)));
      push("Device deleted.", "error");
    } catch {
      push("Failed to delete device.", "error");
    }
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
          <section className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-base uppercase tracking-[0.3em] text-white/40">
                Devices
              </div>
              <h1 className="mt-2 font-display text-4xl">
                Keep every sensor in view
              </h1>
              <p className="mt-2 text-lg text-white/60">
                Register devices, attach them to tanks, and keep calibrations
                current.
              </p>
            </div>
            <button
              className="btn-primary"
              type="button"
              onClick={() => router.push("/dashboard/devices/new")}
            >
              Register device
            </button>
          </section>

          <section className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div className="text-base font-semibold">Device list</div>
              <div className="text-sm text-white/50">
                {isLoading ? "Loading…" : `${devices.length} total`}
              </div>
            </div>

            {devices.length === 0 && !isLoading ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
                No devices yet. Register a device to start streaming readings.
              </div>
            ) : (
              <div className="mt-4 overflow-hidden rounded-2xl border border-white/10">
                <div className="grid grid-cols-[1.2fr_0.8fr_0.9fr_0.5fr_0.6fr] bg-white/5 px-4 py-3 text-sm uppercase tracking-[0.2em] text-white/50">
                  <div>Name</div>
                  <div>Preset</div>
                  <div>Aquarium</div>
                  <div>Status</div>
                  <div className="text-right">Actions</div>
                </div>
                <div className="divide-y divide-white/10">
                  {devices.map((device) => {
                    const preset = device.location?.startsWith("Simulated · ")
                      ? device.location.replace("Simulated · ", "")
                      : "Manual";
                    const status = statusByDevice[device.id] ?? "offline";
                    const isSimulated = device.location?.startsWith("Simulated · ");
                    const isPaused = simPausedByDevice[device.id] ?? false;
                    const progress = holdProgress[device.id] ?? 0;
                    return (
                      <div
                        key={device.id}
                        className="grid grid-cols-[1.2fr_0.8fr_0.9fr_0.5fr_0.6fr] items-center px-4 py-4 text-base text-white/70"
                      >
                        <div className="font-semibold text-white">
                          {device.name}
                        </div>
                        <div>{preset}</div>
                      <div>{aquariumByDevice[device.id] ?? "—"}</div>
                      <div>
                          <span
                            className={[
                              "rounded-full border px-3 py-1 text-sm",
                              status === "online"
                                ? "border-emerald-500/40 text-emerald-200"
                                : "border-red-400/40 text-red-200",
                            ].join(" ")}
                          >
                            {status === "online" ? "Online" : "Offline"}
                          </span>
                        </div>
                        <div className="flex items-center justify-end gap-2">
                          {isSimulated ? (
                            <button
                              type="button"
                              className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] transition ${
                                isPaused
                                  ? "border-red-400/40 text-red-200"
                                  : "border-emerald-500/40 text-emerald-200"
                              }`}
                              onClick={async () => {
                                const token = getAuthToken();
                                if (!token) {
                                  router.replace("/login");
                                  return;
                                }
                                const nextPaused = !isPaused;
                                setSimPausedByDevice((prev) => ({
                                  ...prev,
                                  [device.id]: nextPaused,
                                }));
                                try {
                                  const response = await fetch(
                                    `${getClientApiBaseUrl()}/v1/simulator/devices/${device.id}/state`,
                                    {
                                      method: "POST",
                                      headers: {
                                        "Content-Type": "application/json",
                                        Authorization: `Bearer ${token}`,
                                      },
                                      body: JSON.stringify({
                                        enabled: !nextPaused,
                                      }),
                                    }
                                  );
                                  if (!response.ok) {
                                    throw new Error("Failed to update device state.");
                                  }
                                } catch {
                                  setSimPausedByDevice((prev) => ({
                                    ...prev,
                                    [device.id]: isPaused,
                                  }));
                                }
                              }}
                            >
                              {isPaused ? "Paused" : "Pause"}
                            </button>
                          ) : null}
                          <button
                            type="button"
                            className="relative overflow-hidden rounded-full border border-white/10 px-2 py-2 text-white/70 transition hover:border-red-400/60 hover:text-white"
                            aria-label="Delete device (hold)"
                            onMouseDown={() => startHold(device.id)}
                            onMouseUp={() => clearHold(device.id)}
                            onMouseLeave={() => clearHold(device.id)}
                            onTouchStart={() => startHold(device.id)}
                            onTouchEnd={() => clearHold(device.id)}
                          >
                            {progress > 0 ? (
                              <span
                                className="absolute inset-0 bg-red-500/35"
                                style={{
                                  transform: `scaleX(${progress})`,
                                  transformOrigin: "left",
                                }}
                              />
                            ) : null}
                            <span className="relative z-10">🗑</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>

          <section className="glass-panel p-6">
            <div className="flex items-center justify-between">
              <div className="text-base font-semibold">Device logs</div>
              <div className="flex items-center gap-3">
                <div className="text-sm text-white/50">Readings</div>
                <div className="min-w-[140px]">
                  <Select<LogView>
                    value={logView}
                    onChange={(value) => {
                      setLogView(value);
                      setLogPage(1);
                    }}
                    options={[
                      { value: "5", label: "Last 5" },
                      { value: "15", label: "Last 15" },
                      { value: "30", label: "Last 30" },
                      { value: "all", label: "All (paged)" },
                    ]}
                  />
                </div>
              </div>
            </div>
            {isLoadingLogs ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
                Loading device readings…
              </div>
            ) : logs.length === 0 ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
                Waiting for device readings…
              </div>
            ) : (
              <div className="mt-4 overflow-hidden rounded-2xl border border-white/10">
                <div className="grid grid-cols-[1.2fr_0.6fr_0.4fr_0.6fr_0.4fr] bg-white/5 px-4 py-3 text-sm uppercase tracking-[0.2em] text-white/50">
                  <div>Device</div>
                  <div>Temp</div>
                  <div>pH</div>
                  <div>TDS</div>
                  <div>Time</div>
                </div>
                <div className="divide-y divide-white/10">
                  {logs.map((log) => (
                    <div
                      key={log.id}
                      className="grid grid-cols-[1.2fr_0.6fr_0.4fr_0.6fr_0.4fr] items-center px-4 py-3 text-sm text-white/70"
                    >
                      <div>
                        <div className="font-semibold text-white">
                          {log.deviceName}
                        </div>
                        <div className="text-xs uppercase tracking-[0.2em] text-white/50">
                          {log.deviceType}
                        </div>
                      </div>
                      <div>{log.temperature}</div>
                      <div>{log.ph}</div>
                      <div>{log.tds}</div>
                      <div className="text-xs text-white/50">
                        {log.timestamp}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {logView === "all" && logTotal > 0 ? (
              <div className="mt-4 flex items-center justify-between text-sm text-white/60">
                <div>
                  Page {logPage} of {Math.max(1, Math.ceil(logTotal / logPageSize))}
                </div>
                <div className="flex items-center gap-2">
                  <div className="min-w-[140px]">
                    <Select<"5" | "15" | "30">
                      value={String(logPageSize) as "5" | "15" | "30"}
                      onChange={(value) => {
                        const size = Number(value);
                        setLogPageSize(size);
                        setLogPage(1);
                      }}
                      options={[
                        { value: "5", label: "5 per page" },
                        { value: "15", label: "15 per page" },
                        { value: "30", label: "30 per page" },
                      ]}
                    />
                  </div>
                  <button
                    type="button"
                    className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-white/70 transition hover:border-ocean-500/40"
                    onClick={() => setLogPage((p) => Math.max(1, p - 1))}
                    disabled={logPage === 1}
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-white/70 transition hover:border-ocean-500/40"
                    onClick={() =>
                      setLogPage((p) =>
                        Math.min(Math.ceil(logTotal / logPageSize), p + 1)
                      )
                    }
                    disabled={logPage >= Math.ceil(logTotal / logPageSize)}
                  >
                    Next
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        </main>
      </div>
    </div>
  );
}

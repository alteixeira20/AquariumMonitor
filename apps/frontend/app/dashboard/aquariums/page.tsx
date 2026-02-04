"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import TopNav from "../../../components/dashboard/TopNav";
import { useToast } from "../../../components/ui/ToastProvider";
import { clearAuthToken, getAuthToken } from "../../../lib/auth";
import { getMe } from "../../../lib/auth_api";
import { fetchJson } from "../../../lib/api";
import { getClientApiBaseUrl } from "../../../lib/config";

type Aquarium = {
  id: string;
  name: string;
  water_type: string;
  liters: number;
  temperature_enabled?: boolean;
  ph_enabled?: boolean;
  tds_enabled?: boolean;
};

type LatestSnapshot = {
  temperature_c: number | null;
  ph_value: number | null;
  tds_ppm: number | null;
  received_at: string | null;
  device_count: number;
};

export default function AquariumsPage() {
  const router = useRouter();
  const { push } = useToast();
  const [isChecking, setIsChecking] = useState(true);
  const [aquariums, setAquariums] = useState<Aquarium[]>([]);
  const [snapshots, setSnapshots] = useState<Record<string, LatestSnapshot>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [holdProgress, setHoldProgress] = useState<Record<string, number>>({});
  const [notificationsMuted, setNotificationsMuted] = useState<
    Record<string, boolean>
  >({});
  const [deleting, setDeleting] = useState<Record<string, boolean>>({});
  const holdTimers = useRef<Record<string, number>>({});
  const holdIntervals = useRef<Record<string, number>>({});

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
    if (deleting[id]) return;
    const token = getAuthToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setDeleting((prev) => ({ ...prev, [id]: true }));
    try {
      const response = await fetch(
        `${getClientApiBaseUrl()}/v1/aquariums/${id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to delete aquarium.");
      }
      setAquariums((prev) => prev.filter((aquarium) => aquarium.id !== id));
      setSnapshots((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      setNotificationsMuted((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      push("Aquarium deleted.", "error");
    } catch (err) {
      push("Failed to delete aquarium. Try again.", "error");
    } finally {
      setDeleting((prev) => ({ ...prev, [id]: false }));
    }
  }

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

    async function loadAquariums() {
      const token = getAuthToken();
      if (!token) return;
      setIsLoading(true);
      try {
        const data = await fetchJson<Aquarium[]>(
          "/v1/aquariums",
          {
            headers: { Authorization: `Bearer ${token}` },
          },
          getClientApiBaseUrl()
        );
        if (ignore) return;
        setAquariums(data);

        const snapshotEntries = await Promise.all(
          data.map(async (aquarium) => {
            try {
              const devices = await fetchJson<Array<{ id: string }>>(
                `/v1/aquariums/${aquarium.id}/devices`,
                {
                  headers: { Authorization: `Bearer ${token}` },
                },
                getClientApiBaseUrl()
              );

              if (!devices.length) {
                return [
                  aquarium.id,
                  {
                    temperature_c: null,
                    ph_value: null,
                    tds_ppm: null,
                    received_at: null,
                    device_count: 0,
                  },
                ] as const;
              }

              const readings = await Promise.all(
                devices.map(async (device) => {
                  try {
                    return await fetchJson<{
                      temperature_c: number;
                      ph_value: number;
                      tds_ppm: number;
                      received_at: string;
                    }>(
                      `/v1/readings/${device.id}/latest`,
                      {
                        headers: { Authorization: `Bearer ${token}` },
                      },
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

              return [
                aquarium.id,
                {
                  temperature_c: latest?.temperature_c ?? null,
                  ph_value: latest?.ph_value ?? null,
                  tds_ppm: latest?.tds_ppm ?? null,
                  received_at: latest?.received_at ?? null,
                  device_count: devices.length,
                },
              ] as const;
            } catch {
              return [
                aquarium.id,
                {
                  temperature_c: null,
                  ph_value: null,
                  tds_ppm: null,
                  received_at: null,
                  device_count: 0,
                },
              ] as const;
            }
          })
        );

        if (!ignore) {
          setSnapshots(Object.fromEntries(snapshotEntries));
        }
      } catch (err) {
        if (!ignore) setAquariums([]);
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    if (!isChecking) {
      loadAquariums();
      intervalId = window.setInterval(loadAquariums, 10000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [isChecking]);

  if (isChecking) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
          <section className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-base uppercase tracking-[0.3em] text-white/40">
                Aquariums
              </div>
              <h1 className="mt-2 font-display text-4xl">
                Track every tank in one place
              </h1>
              <p className="mt-2 text-lg text-white/60">
                Review the latest readings and keep devices calibrated.
              </p>
            </div>
            <button
              className="btn-primary"
              type="button"
              onClick={() => router.push("/dashboard/aquariums/new")}
            >
              Add aquarium
            </button>
          </section>

          <section className="glass-panel p-6">
            <div className="flex items-center justify-between">
            <div className="text-base font-semibold">Aquarium list</div>
            <div className="text-sm text-white/50">
              {isLoading ? "Loading…" : `${aquariums.length} total`}
            </div>
            </div>

            {aquariums.length === 0 && !isLoading ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
                No aquariums yet. Create your first aquarium to get started.
              </div>
            ) : (
              <div className="mt-4 overflow-hidden rounded-2xl border border-white/10">
                {(() => {
                  const showSensorColumns = aquariums.some(
                    (aq) => (snapshots[aq.id]?.device_count ?? 0) > 0
                  );
                  const headerColumns = showSensorColumns
                    ? "grid grid-cols-[1.1fr_0.5fr_0.5fr_0.5fr_0.5fr_0.5fr_0.6fr]"
                    : "grid grid-cols-[1.2fr_0.6fr_0.6fr_1fr_0.6fr]";
                  const rowColumns = showSensorColumns
                    ? "grid grid-cols-[1.1fr_0.5fr_0.5fr_0.5fr_0.5fr_0.5fr_0.6fr]"
                    : "grid grid-cols-[1.1fr_0.5fr_0.5fr_1fr_0.6fr]";
                  return (
                    <>
                      <div
                        className={`${headerColumns} bg-white/5 px-4 py-3 text-sm uppercase tracking-[0.2em] text-white/50`}
                      >
                        <div>Name</div>
                        <div>Water</div>
                        <div>Liters</div>
                        {showSensorColumns ? (
                          <>
                            <div>Temp</div>
                            <div>pH</div>
                            <div>TDS</div>
                          </>
                        ) : (
                          <div>Sensors</div>
                        )}
                        <div className="text-right">Actions</div>
                      </div>
                      <div className="divide-y divide-white/10">
                        {aquariums.map((aquarium) => {
                          const snapshot = snapshots[aquarium.id];
                          const progress = holdProgress[aquarium.id] ?? 0;
                          const isMuted =
                            notificationsMuted[aquarium.id] ?? false;
                          const deviceCount = snapshot?.device_count ?? 0;
                          const tempValue =
                            snapshot?.temperature_c !== null &&
                            snapshot?.temperature_c !== undefined
                              ? `${snapshot.temperature_c.toFixed(1)}°C`
                              : "—";
                          const phValue =
                            snapshot?.ph_value !== null &&
                            snapshot?.ph_value !== undefined
                              ? snapshot.ph_value.toFixed(1)
                              : "—";
                          const tdsValue =
                            snapshot?.tds_ppm !== null &&
                            snapshot?.tds_ppm !== undefined
                              ? `${Math.round(snapshot.tds_ppm)} ppm`
                              : "—";

                          return (
                            <div
                              key={aquarium.id}
                              className={`${rowColumns} items-center px-4 py-4 text-base text-white/70`}
                            >
                              <div className="font-semibold text-white">
                                {aquarium.name}
                              </div>
                              <div className="capitalize">
                                {aquarium.water_type}
                              </div>
                              <div>{aquarium.liters}</div>
                              {showSensorColumns ? (
                                deviceCount === 0 ? (
                                  <div className="col-span-3 text-white/40">
                                    No device connected
                                  </div>
                                ) : (
                                  <>
                                    <div className="text-white/80">
                                      {tempValue}
                                    </div>
                                    <div className="text-white/80">
                                      {phValue}
                                    </div>
                                    <div className="text-white/80">
                                      {tdsValue}
                                    </div>
                                  </>
                                )
                              ) : (
                                <div className="text-white/80">
                                  {deviceCount === 0
                                    ? "No device connected"
                                    : "Device connected"}
                                </div>
                              )}
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  type="button"
                                  className={`rounded-full border px-2 py-2 transition ${
                                    isMuted
                                      ? "border-white/10 text-white/30 hover:text-white/40"
                                      : "border-white/10 text-white/70 hover:border-ocean-500/40 hover:text-white"
                                  }`}
                                  aria-label="Toggle notifications"
                                  onClick={() =>
                                    setNotificationsMuted((prev) => ({
                                      ...prev,
                                      [aquarium.id]: !prev[aquarium.id],
                                    }))
                                  }
                                >
                                  🔔
                                </button>
                                <button
                                  type="button"
                                  className="rounded-full border border-white/10 px-2 py-2 text-white/70 transition hover:border-ocean-500/40 hover:text-white text-lg"
                                  aria-label="Edit aquarium"
                                  onClick={() =>
                                    router.push(
                                      `/dashboard/aquariums/${aquarium.id}/edit`
                                    )
                                  }
                                >
                                  ✎
                                </button>
                                <button
                                  type="button"
                                  className={`relative overflow-hidden rounded-full border px-2 py-2 transition ${
                                    deleting[aquarium.id]
                                      ? "border-white/10 text-white/30 cursor-not-allowed"
                                      : "border-white/10 text-white/70 hover:border-red-400/60 hover:text-white"
                                  }`}
                                  aria-label="Delete aquarium (hold)"
                                  onMouseDown={() => startHold(aquarium.id)}
                                  onMouseUp={() => clearHold(aquarium.id)}
                                  onMouseLeave={() => clearHold(aquarium.id)}
                                  onTouchStart={() => startHold(aquarium.id)}
                                  onTouchEnd={() => clearHold(aquarium.id)}
                                  disabled={deleting[aquarium.id]}
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
                    </>
                  );
                })()}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

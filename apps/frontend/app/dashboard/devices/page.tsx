"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import TopNav from "../../../components/dashboard/TopNav";
import { useToast } from "../../../components/ui/ToastProvider";
import { clearAuthToken, getAuthToken } from "../../../lib/auth";
import { getMe } from "../../../lib/auth_api";
import { fetchJson } from "../../../lib/api";
import { getClientApiBaseUrl } from "../../../lib/config";

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
  message: string;
  timestamp: string;
};

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
  const [logs, setLogs] = useState<ReadingLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const lastReadingByDevice = useRef<Record<string, string>>({});

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
        const readings = await Promise.all(
          data.map(async (device) => {
            try {
              return await fetchJson<DeviceReading>(
                `/v1/readings/${device.id}/latest`,
                { headers: { Authorization: `Bearer ${token}` } },
                getClientApiBaseUrl()
              );
            } catch {
              return null;
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
          readings.forEach((reading, idx) => {
            if (!reading?.received_at) return;
            const device = data[idx];
            const lastSeen = lastReadingByDevice.current[device.id];
            if (lastSeen === reading.received_at) return;
            lastReadingByDevice.current[device.id] = reading.received_at;
            const deviceType = device.location?.startsWith("Simulated · ")
              ? "Simulated"
              : "Manual";
            setLogs((prev) => {
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
              const entry: ReadingLog = {
                id: `${device.id}-${reading.received_at}`,
                deviceName: device.name,
                deviceType,
                message: `Temp ${temp} · pH ${ph} · TDS ${tds}`,
                timestamp: new Date(reading.received_at).toLocaleTimeString(),
              };
              return [entry, ...prev].slice(0, 20);
            });
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
                <div className="grid grid-cols-[1.2fr_0.9fr_0.9fr_0.5fr] bg-white/5 px-4 py-3 text-sm uppercase tracking-[0.2em] text-white/50">
                  <div>Name</div>
                  <div>Preset</div>
                  <div>Aquarium</div>
                  <div>Status</div>
                </div>
                <div className="divide-y divide-white/10">
                  {devices.map((device) => {
                    const preset = device.location?.startsWith("Simulated · ")
                      ? device.location.replace("Simulated · ", "")
                      : "Manual";
                    const status = statusByDevice[device.id] ?? "offline";
                    return (
                      <div
                        key={device.id}
                        className="grid grid-cols-[1.2fr_0.9fr_0.9fr_0.5fr] items-center px-4 py-4 text-base text-white/70"
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
              <div className="text-sm text-white/50">Live readings</div>
            </div>
            {logs.length === 0 ? (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
                Waiting for device readings…
              </div>
            ) : (
              <div className="mt-4 grid gap-3">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70"
                  >
                    <div>
                      <div className="font-semibold text-white">
                        {log.deviceName}
                      </div>
                      <div className="text-xs uppercase tracking-[0.2em] text-white/50">
                        {log.deviceType}
                      </div>
                    </div>
                    <div className="text-sm text-white/70">
                      {log.message}
                    </div>
                    <div className="text-xs text-white/50">{log.timestamp}</div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import TopNav from "../../../components/dashboard/TopNav";
import { clearAuthToken, getAuthToken } from "../../../lib/auth";
import { getMe } from "../../../lib/auth_api";
import { fetchJson } from "../../../lib/api";
import { getClientApiBaseUrl } from "../../../lib/config";

type AlertItem = {
  id: string;
  aquarium_id: string;
  device_id: string | null;
  alert_type: string;
  sensor: string | null;
  level: number;
  message: string;
  created_at: string;
  resolved_at: string | null;
};

type Aquarium = { id: string; name: string };

const ALERT_TYPES = [
  { value: "sensor_out_of_range", label: "Out of range" },
  { value: "device_offline", label: "Device offline" },
  { value: "sensor_missing_data", label: "Missing data" },
];

const LEVELS = [
  { value: "1", label: "Warning" },
  { value: "2", label: "Alert" },
  { value: "3", label: "Critical" },
];

function levelLabel(level: number) {
  if (level >= 3) return "Critical";
  if (level === 2) return "Alert";
  if (level === 1) return "Warning";
  return "Healthy";
}

function levelTone(level: number) {
  if (level >= 3) return "text-rose-300";
  if (level === 2) return "text-orange-300";
  if (level === 1) return "text-sun-300";
  return "text-emerald-300";
}

export default function AlertsPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [aquariums, setAquariums] = useState<Aquarium[]>([]);
  const [aquariumFilter, setAquariumFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [levelFilter, setLevelFilter] = useState("all");

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
      } catch {
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

    async function loadAquariums() {
      const token = getAuthToken();
      if (!token) return;
      try {
        const items = await fetchJson<Aquarium[]>(
          "/v1/aquariums",
          { headers: { Authorization: `Bearer ${token}` } },
          getClientApiBaseUrl()
        );
        if (!ignore) setAquariums(items);
      } catch {
        if (!ignore) setAquariums([]);
      }
    }

    if (!isChecking) loadAquariums();
    return () => {
      ignore = true;
    };
  }, [isChecking]);

  useEffect(() => {
    let ignore = false;

    async function loadAlerts() {
      const token = getAuthToken();
      if (!token) return;
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
        unresolved_only: "true",
      });
      if (aquariumFilter !== "all") params.set("aquarium_id", aquariumFilter);
      if (typeFilter !== "all") params.set("alert_type", typeFilter);
      if (levelFilter !== "all") params.set("level", levelFilter);

      try {
        const data = await fetchJson<{
          alerts: AlertItem[];
          total: number;
        }>(
          `/v1/alerts?${params.toString()}`,
          { headers: { Authorization: `Bearer ${token}` } },
          getClientApiBaseUrl()
        );
        if (!ignore) {
          setAlerts(data.alerts);
          setTotal(data.total);
        }
      } catch {
        if (!ignore) {
          setAlerts([]);
          setTotal(0);
        }
      }
    }

    if (!isChecking) loadAlerts();
    return () => {
      ignore = true;
    };
  }, [aquariumFilter, isChecking, levelFilter, page, typeFilter]);

  const totalPages = Math.max(1, Math.ceil(total / 20));
  const aquariumNameById = useMemo(() => {
    const map: Record<string, string> = {};
    aquariums.forEach((aq) => {
      map[aq.id] = aq.name;
    });
    return map;
  }, [aquariums]);

  if (isChecking) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
          <section className="glass-panel p-6">
            <div className="text-base uppercase tracking-[0.3em] text-white/40">
              Alerts
            </div>
            <h1 className="mt-2 font-display text-4xl">System alerts</h1>
            <p className="mt-2 text-lg text-white/60">
              Review warnings and critical events across your aquariums.
            </p>
          </section>

          <section className="glass-panel p-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <label className="text-xs uppercase tracking-[0.2em] text-white/40">
                  Aquarium
                  <select
                    value={aquariumFilter}
                    onChange={(event) => {
                      setAquariumFilter(event.target.value);
                      setPage(1);
                    }}
                    className="mt-2 w-full rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80"
                  >
                    <option value="all">All aquariums</option>
                    {aquariums.map((aq) => (
                      <option key={aq.id} value={aq.id}>
                        {aq.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs uppercase tracking-[0.2em] text-white/40">
                  Type
                  <select
                    value={typeFilter}
                    onChange={(event) => {
                      setTypeFilter(event.target.value);
                      setPage(1);
                    }}
                    className="mt-2 w-full rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80"
                  >
                    <option value="all">All types</option>
                    {ALERT_TYPES.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs uppercase tracking-[0.2em] text-white/40">
                  Level
                  <select
                    value={levelFilter}
                    onChange={(event) => {
                      setLevelFilter(event.target.value);
                      setPage(1);
                    }}
                    className="mt-2 w-full rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80"
                  >
                    <option value="all">All levels</option>
                    {LEVELS.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="text-sm text-white/50">
                {total} alert{total === 1 ? "" : "s"}
              </div>
            </div>

            <div className="mt-6 overflow-hidden rounded-2xl border border-white/10">
              <div className="grid grid-cols-[1.2fr_1fr_1fr_0.8fr_2fr] bg-white/5 px-4 py-3 text-xs uppercase tracking-[0.2em] text-white/50">
                <div>Time</div>
                <div>Aquarium</div>
                <div>Type</div>
                <div>Level</div>
                <div>Message</div>
              </div>
              {alerts.length === 0 ? (
                <div className="px-4 py-6 text-sm text-white/60">
                  No alerts found.
                </div>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="grid grid-cols-[1.2fr_1fr_1fr_0.8fr_2fr] border-t border-white/5 px-4 py-3 text-sm text-white/70"
                  >
                    <div>{new Date(alert.created_at).toLocaleString()}</div>
                    <div>{aquariumNameById[alert.aquarium_id] ?? "Unknown"}</div>
                    <div>
                      {ALERT_TYPES.find((item) => item.value === alert.alert_type)?.label ??
                        alert.alert_type}
                    </div>
                    <div className={`font-semibold ${levelTone(alert.level)}`}>
                      {levelLabel(alert.level)}
                    </div>
                    <div>{alert.message}</div>
                  </div>
                ))
              )}
            </div>

            <div className="mt-4 flex items-center justify-between text-sm text-white/60">
              <button
                type="button"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={page === 1}
                className="rounded-full border border-white/10 px-3 py-1 disabled:opacity-40"
              >
                Previous
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={page >= totalPages}
                className="rounded-full border border-white/10 px-3 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import TopNav from "../../../../components/dashboard/TopNav";
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

export default function AquariumDetailPage() {
  const router = useRouter();
  const params = useParams();
  const aquariumId = Array.isArray(params?.aquariumId)
    ? params?.aquariumId[0]
    : params?.aquariumId;

  const [isChecking, setIsChecking] = useState(true);
  const [aquarium, setAquarium] = useState<Aquarium | null>(null);
  const [latest, setLatest] = useState<LatestReading | null>(null);

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

    async function loadLatest() {
      const token = getAuthToken();
      if (!token || !aquariumId) return;
      try {
        const devices = await fetchJson<Array<{ id: string }>>(
          `/v1/aquariums/${aquariumId}/devices`,
          { headers: { Authorization: `Bearer ${token}` } },
          getClientApiBaseUrl()
        );
        if (!devices.length) {
          if (!ignore) setLatest(null);
          return;
        }
        const readings = await Promise.all(
          devices.map(async (device) => {
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
        const latestReading = readings
          .filter((reading) => reading?.received_at)
          .sort((a, b) => {
            if (!a || !b) return 0;
            return (
              new Date(b.received_at).getTime() -
              new Date(a.received_at).getTime()
            );
          })[0];
        if (!ignore) setLatest(latestReading ?? null);
      } catch {
        if (!ignore) setLatest(null);
      }
    }

    if (!isChecking) {
      loadLatest();
      intervalId = window.setInterval(loadLatest, 10000);
    }

    return () => {
      ignore = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [aquariumId, isChecking]);

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
              Aquarium
            </div>
            <h1 className="mt-2 font-display text-4xl">
              {aquarium?.name ?? "Aquarium"}
            </h1>
            <p className="mt-2 text-lg text-white/60">
              {aquarium
                ? `${aquarium.water_type} · ${aquarium.liters} L`
                : "Loading details..."}
            </p>

            <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="text-sm uppercase tracking-[0.2em] text-white/50">
                  Latest metrics
                </div>
                <div className="mt-4 grid gap-3 text-base text-white/70">
                  <div className="flex items-center justify-between">
                    <span>Temperature</span>
                    <span className="text-white/90">
                      {latest?.temperature_c !== null &&
                      latest?.temperature_c !== undefined
                        ? `${latest.temperature_c.toFixed(1)}°C`
                        : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>pH</span>
                    <span className="text-white/90">
                      {latest?.ph_value !== null &&
                      latest?.ph_value !== undefined
                        ? latest.ph_value.toFixed(1)
                        : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>TDS</span>
                    <span className="text-white/90">
                      {latest?.tds_ppm !== null &&
                      latest?.tds_ppm !== undefined
                        ? `${Math.round(latest.tds_ppm)} ppm`
                        : "—"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="text-sm uppercase tracking-[0.2em] text-white/50">
                  Target ranges
                </div>
                <div className="mt-4 grid gap-3 text-base text-white/70">
                  <div className="flex items-center justify-between">
                    <span>Temperature</span>
                    <span className="text-white/90">
                      {aquarium
                        ? `${aquarium.temperature_min}–${aquarium.temperature_max}°C`
                        : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>pH</span>
                    <span className="text-white/90">
                      {aquarium ? `${aquarium.ph_min}–${aquarium.ph_max}` : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>TDS</span>
                    <span className="text-white/90">
                      {aquarium
                        ? `${aquarium.tds_min}–${aquarium.tds_max} ppm`
                        : "—"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
            <div className="glass-panel p-6">
              <div className="text-base font-semibold">Temperature trend</div>
              <div className="mt-4 h-48 rounded-2xl border border-white/10 bg-white/5" />
            </div>
            <div className="glass-panel p-6">
              <div className="text-base font-semibold">pH + TDS trend</div>
              <div className="mt-4 h-48 rounded-2xl border border-white/10 bg-white/5" />
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

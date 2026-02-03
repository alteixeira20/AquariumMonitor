"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAuthToken, getAuthToken } from "../../lib/auth";
import { getMe } from "../../lib/auth_api";
import TopNav from "../../components/dashboard/TopNav";
import Select from "../../components/ui/Select";
import { fetchJson } from "../../lib/api";
import { getClientApiBaseUrl } from "../../lib/config";

export default function DashboardPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [aquariums, setAquariums] = useState<Array<{ id: string; name: string }>>(
    []
  );
  const [activeAquariumId, setActiveAquariumId] = useState("");
  const activeAquarium = aquariums.find((aq) => aq.id === activeAquariumId);
  const [isLoadingAquariums, setIsLoadingAquariums] = useState(true);

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

    async function loadAquariums() {
      const token = getAuthToken();
      if (!token) return;
      setIsLoadingAquariums(true);
      try {
        const data = await fetchJson<Array<{ id: string; name: string }>>(
          "/v1/aquariums",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
          getClientApiBaseUrl()
        );
        if (ignore) return;
        setAquariums(data);
        if (data.length > 0) {
          setActiveAquariumId((prev) => prev || data[0].id);
        }
      } catch (err) {
        if (!ignore) setAquariums([]);
      } finally {
        if (!ignore) setIsLoadingAquariums(false);
      }
    }

    loadAquariums();
    return () => {
      ignore = true;
    };
  }, []);

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
                <span className="text-white/80">—</span>
              </div>
              <div className="flex items-center justify-between">
                <span>pH</span>
                <span className="text-white/80">—</span>
              </div>
              <div className="flex items-center justify-between">
                <span>TDS</span>
                <span className="text-white/80">—</span>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/50">
                No readings yet. Attach a calibrated device to start tracking.
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          {[
            { label: "Tracked aquariums", value: "0" },
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

        <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div className="glass-panel p-6">
            <div className="text-base font-semibold">Aquariums</div>
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
              No aquariums yet. Create your first aquarium to start tracking
              water quality.
            </div>
          </div>
          <div className="glass-panel p-6">
            <div className="text-base font-semibold">Devices</div>
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-6 text-base text-white/60">
              No devices yet. Register a device and complete calibration to
              begin streaming readings.
            </div>
          </div>
        </section>
        </main>
      </div>
    </div>
  );
}

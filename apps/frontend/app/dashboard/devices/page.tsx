"use client";

import { useEffect, useState } from "react";
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

export default function DevicesPage() {
  const router = useRouter();
  const { push } = useToast();
  const [isChecking, setIsChecking] = useState(true);
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

    async function loadDevices() {
      const token = getAuthToken();
      if (!token) return;
      setIsLoading(true);
      try {
        const data = await fetchJson<Device[]>(
          "/v1/devices/owned",
          {
            headers: { Authorization: `Bearer ${token}` },
          },
          getClientApiBaseUrl()
        );
        if (!ignore) setDevices(data);
      } catch (err) {
        if (!ignore) {
          setDevices([]);
          push("Failed to load devices.", "error");
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    if (!isChecking) loadDevices();

    return () => {
      ignore = true;
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
                <div className="grid grid-cols-[1.2fr_1fr_0.6fr] bg-white/5 px-4 py-3 text-sm uppercase tracking-[0.2em] text-white/50">
                  <div>Name</div>
                  <div>Location</div>
                  <div>Status</div>
                </div>
                <div className="divide-y divide-white/10">
                  {devices.map((device) => (
                    <div
                      key={device.id}
                      className="grid grid-cols-[1.2fr_1fr_0.6fr] items-center px-4 py-4 text-base text-white/70"
                    >
                      <div className="font-semibold text-white">
                        {device.name}
                      </div>
                      <div>{device.location ?? "—"}</div>
                      <div>
                        <span
                          className={[
                            "rounded-full border px-3 py-1 text-sm",
                            device.is_active
                              ? "border-emerald-500/40 text-emerald-200"
                              : "border-white/10 text-white/50",
                          ].join(" ")}
                        >
                          {device.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

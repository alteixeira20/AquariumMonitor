"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import TopNav from "../../../../components/dashboard/TopNav";
import Field from "../../../../components/ui/Field";
import Select from "../../../../components/ui/Select";
import { useToast } from "../../../../components/ui/ToastProvider";
import { clearAuthToken, getAuthToken } from "../../../../lib/auth";
import { getMe } from "../../../../lib/auth_api";
import { fetchJson } from "../../../../lib/api";
import { getClientApiBaseUrl } from "../../../../lib/config";

type AquariumOption = { id: string; name: string };

type DeviceRegisterResponse = {
  id: string;
  name: string;
};

type DeviceApiKeyResponse = {
  device_id: string;
  api_key: string;
};

type Preset = {
  id: string;
  name: string;
  description: string;
};

const PRESETS: Preset[] = [
  {
    id: "reef-drift",
    name: "Reef drift",
    description: "Stable reef values with light daily oscillations.",
  },
  {
    id: "fresh-sunrise",
    name: "Fresh sunrise",
    description: "Gentle warming during the day, cooler nights.",
  },
  {
    id: "nano-stable",
    name: "Nano stable",
    description: "Tight ranges for small tanks with minor variability.",
  },
  {
    id: "salt-pulse",
    name: "Salt pulse",
    description: "Gradual salinity-driven TDS lift and recovery.",
  },
  {
    id: "planted-cycle",
    name: "Planted cycle",
    description: "Daily CO2 swings with pH dips and recoveries.",
  },
  {
    id: "cichlid-rush",
    name: "Cichlid rush",
    description: "Higher pH with steady temperature and TDS.",
  },
  {
    id: "brackish-tide",
    name: "Brackish tide",
    description: "Moderate TDS rise and slow temperature shift.",
  },
  {
    id: "tropical-rain",
    name: "Tropical rain",
    description: "Short temp drops with subtle pH dilution.",
  },
  {
    id: "desert-oasis",
    name: "Desert oasis",
    description: "Warm water with steady mid-range pH.",
  },
  {
    id: "stress-test",
    name: "Stress test",
    description: "Wide swings for alert testing and UI tuning.",
  },
];

export default function DeviceRegisterPage() {
  const router = useRouter();
  const { push } = useToast();
  const [isChecking, setIsChecking] = useState(true);
  const [mode, setMode] = useState<"simulated" | "manual">("simulated");
  const [aquariums, setAquariums] = useState<AquariumOption[]>([]);
  const [selectedAquarium, setSelectedAquarium] = useState<string>("");
  const [selectedPreset, setSelectedPreset] = useState(PRESETS[0]);
  const [deviceName, setDeviceName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingAquariums, setIsLoadingAquariums] = useState(true);
  const [manualLocation, setManualLocation] = useState("");
  const [manualDeviceId, setManualDeviceId] = useState<string | null>(null);
  const [manualApiKey, setManualApiKey] = useState<string | null>(null);
  const [ph4Voltage, setPh4Voltage] = useState("");
  const [ph7Voltage, setPh7Voltage] = useState("");
  const [ph9Voltage, setPh9Voltage] = useState("");
  const [isCalibrating, setIsCalibrating] = useState(false);

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
        const data = await fetchJson<AquariumOption[]>(
          "/v1/aquariums",
          {
            headers: { Authorization: `Bearer ${token}` },
          },
          getClientApiBaseUrl()
        );
        if (ignore) return;
        setAquariums(data);
        if (!selectedAquarium && data.length) {
          setSelectedAquarium(data[0].id);
        }
      } catch (err) {
        if (!ignore) setAquariums([]);
      } finally {
        if (!ignore) setIsLoadingAquariums(false);
      }
    }

    if (!isChecking) loadAquariums();

    return () => {
      ignore = true;
    };
  }, [isChecking]);

  useEffect(() => {
    if (mode === "simulated") {
      setDeviceName(`Sim ${selectedPreset.name}`);
    }
  }, [selectedPreset, mode]);

  const aquariumOptions = useMemo(() => {
    if (aquariums.length === 0) {
      return [
        {
          value: "" as const,
          label: "No aquariums available",
          disabled: true,
        },
      ];
    }
    return aquariums.map((aq) => ({
      value: aq.id,
      label: aq.name,
    }));
  }, [aquariums]);

  const canSubmitSimulated = useMemo(() => {
    if (mode === "manual") return false;
    return deviceName.trim().length > 0 && selectedAquarium.length > 0;
  }, [deviceName, mode, selectedAquarium]);

  const canSubmitManual = useMemo(() => {
    if (mode !== "manual") return false;
    return deviceName.trim().length > 0 && selectedAquarium.length > 0;
  }, [deviceName, mode, selectedAquarium]);

  const canSubmitCalibration = useMemo(() => {
    if (!manualDeviceId) return false;
    return ph4Voltage.trim() !== "" && ph7Voltage.trim() !== "" && ph9Voltage.trim() !== "";
  }, [manualDeviceId, ph4Voltage, ph7Voltage, ph9Voltage]);

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
              Devices
            </div>
            <h1 className="mt-2 font-display text-4xl">Register a device</h1>
            <p className="mt-2 text-lg text-white/60">
              Choose how to add hardware. Simulated devices let you test the
              full flow before real sensors are calibrated.
            </p>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {[
                {
                  key: "simulated",
                  title: "Simulated",
                  description: "Use a preset pattern to generate readings.",
                },
                {
                  key: "manual",
                  title: "Manual",
                  description: "Register real hardware and calibrate sensors.",
                },
              ].map((option) => {
                const isActive = mode === option.key;
                const isDisabled = false;
                return (
                  <button
                    key={option.key}
                    type="button"
                    className={[
                      "rounded-2xl border px-5 py-4 text-left transition",
                      isActive
                        ? "border-ocean-500/60 bg-white/5"
                        : "border-white/10 bg-white/0 hover:border-white/20",
                      isDisabled ? "cursor-not-allowed opacity-60" : "",
                    ].join(" ")}
                    onClick={() => {
                      if (!isDisabled) setMode(option.key as "simulated");
                    }}
                  >
                    <div className="text-base font-semibold text-white">
                      {option.title}
                    </div>
                    <div className="mt-1 text-sm text-white/60">
                      {option.description}
                    </div>
                  </button>
                );
              })}
            </div>

            {mode === "manual" ? (
              <div className="mt-6 grid gap-6">
                <div className="grid gap-4 md:grid-cols-[1.2fr_1fr]">
                  <Field
                    label={<span className="text-base font-semibold">Device name</span>}
                    className="text-lg"
                  >
                    <input
                      value={deviceName}
                      onChange={(event) => setDeviceName(event.target.value)}
                      placeholder="ESP32 Main Tank"
                      disabled={!!manualDeviceId}
                    />
                  </Field>

                  <Field
                    label={<span className="text-base font-semibold">Attach to aquarium</span>}
                    className="text-lg"
                  >
                    <Select
                      value={selectedAquarium}
                      onChange={setSelectedAquarium}
                      options={aquariumOptions}
                      disabled={!!manualDeviceId}
                    />
                  </Field>
                </div>

                <Field
                  label={<span className="text-base font-semibold">Location (optional)</span>}
                  className="text-lg"
                >
                  <input
                    value={manualLocation}
                    onChange={(event) => setManualLocation(event.target.value)}
                    placeholder="Stand A · Left sump"
                    disabled={!!manualDeviceId}
                  />
                </Field>

                {isLoadingAquariums ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-base text-white/60">
                    Loading aquariums…
                  </div>
                ) : aquariums.length === 0 ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-base text-white/60">
                    You need at least one aquarium before attaching a device.
                  </div>
                ) : null}

                <div className="flex flex-wrap items-center justify-between gap-3">
                  <button
                    type="button"
                    className="rounded-full border border-white/20 px-5 py-2 text-base font-semibold transition hover:border-ocean-500/60"
                    onClick={() => router.push("/dashboard/devices")}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className={[
                      "rounded-full px-5 py-2 text-base font-semibold shadow-ocean transition",
                      canSubmitManual && !manualDeviceId
                        ? "bg-gradient-to-br from-[#1f8a9b] to-ocean-500 text-white hover:-translate-y-0.5"
                        : "bg-white/10 text-white/50 cursor-not-allowed",
                    ].join(" ")}
                    disabled={!canSubmitManual || isSubmitting || !!manualDeviceId}
                    onClick={async () => {
                      if (!canSubmitManual || isSubmitting || manualDeviceId) return;
                      const token = getAuthToken();
                      if (!token) {
                        router.replace("/login");
                        return;
                      }
                      setIsSubmitting(true);
                      try {
                        const response = await fetchJson<DeviceRegisterResponse>(
                          "/v1/devices",
                          {
                            method: "POST",
                            headers: {
                              Authorization: `Bearer ${token}`,
                            },
                            body: JSON.stringify({
                              name: deviceName.trim(),
                              location: manualLocation.trim() || "Manual",
                            }),
                          },
                          getClientApiBaseUrl()
                        );
                        await fetchJson(
                          `/v1/aquariums/${selectedAquarium}/devices/${response.id}`,
                          {
                            method: "POST",
                            headers: {
                              Authorization: `Bearer ${token}`,
                            },
                          },
                          getClientApiBaseUrl()
                        );
                        const apiKey = await fetchJson<DeviceApiKeyResponse>(
                          `/v1/devices/${response.id}/api-keys`,
                          {
                            method: "POST",
                            headers: {
                              Authorization: `Bearer ${token}`,
                            },
                          },
                          getClientApiBaseUrl()
                        );
                        setManualDeviceId(response.id);
                        setManualApiKey(apiKey.api_key);
                        push("Manual device registered. Save the API key.", "success");
                      } catch (err) {
                        push("Failed to register device.", "error");
                      } finally {
                        setIsSubmitting(false);
                      }
                    }}
                  >
                    {isSubmitting ? "Registering..." : "Register device"}
                  </button>
                </div>

                {manualDeviceId && manualApiKey ? (
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                    <div className="text-base font-semibold text-white">
                      Device API key
                    </div>
                    <p className="mt-1 text-sm text-white/60">
                      Save this key in your firmware. It is shown only once.
                    </p>
                    <div className="mt-3 flex flex-wrap items-center gap-3">
                      <div className="flex-1 rounded-xl border border-white/10 bg-white/10 px-4 py-3 font-mono text-sm text-white/80">
                        {manualApiKey}
                      </div>
                      <button
                        type="button"
                        className="rounded-full border border-white/20 px-4 py-2 text-sm font-semibold text-white/80 transition hover:border-white/40"
                        onClick={() => {
                          navigator.clipboard.writeText(manualApiKey);
                          push("API key copied.", "success");
                        }}
                      >
                        Copy
                      </button>
                    </div>
                    <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/60">
                      POST readings to{" "}
                      <span className="font-mono text-white/80">
                        /v1/readings/{manualDeviceId}
                      </span>{" "}
                      using{" "}
                      <span className="font-mono text-white/80">
                        Authorization: Bearer &lt;api_key&gt;
                      </span>
                      .
                    </div>
                  </div>
                ) : null}

                {manualDeviceId ? (
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                    <div className="text-base font-semibold text-white">
                      pH calibration
                    </div>
                    <p className="mt-1 text-sm text-white/60">
                      Measure voltage at pH 4.01, 6.86, and 9.18, then activate.
                    </p>
                    <div className="mt-4 grid gap-4 md:grid-cols-3">
                      <Field
                        label={<span className="text-sm font-semibold">pH 4.01 voltage</span>}
                        className="text-lg"
                      >
                        <input
                          value={ph4Voltage}
                          onChange={(event) => setPh4Voltage(event.target.value)}
                          placeholder="3.000"
                          inputMode="decimal"
                        />
                      </Field>
                      <Field
                        label={<span className="text-sm font-semibold">pH 6.86 voltage</span>}
                        className="text-lg"
                      >
                        <input
                          value={ph7Voltage}
                          onChange={(event) => setPh7Voltage(event.target.value)}
                          placeholder="2.500"
                          inputMode="decimal"
                        />
                      </Field>
                      <Field
                        label={<span className="text-sm font-semibold">pH 9.18 voltage</span>}
                        className="text-lg"
                      >
                        <input
                          value={ph9Voltage}
                          onChange={(event) => setPh9Voltage(event.target.value)}
                          placeholder="2.000"
                          inputMode="decimal"
                        />
                      </Field>
                    </div>
                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                      <div className="text-sm text-white/60">
                        Device won’t accept readings until calibration is active.
                      </div>
                      <button
                        type="button"
                        className={[
                          "rounded-full px-5 py-2 text-base font-semibold shadow-ocean transition",
                          canSubmitCalibration && !isCalibrating
                            ? "bg-gradient-to-br from-[#1f8a9b] to-ocean-500 text-white hover:-translate-y-0.5"
                            : "bg-white/10 text-white/50 cursor-not-allowed",
                        ].join(" ")}
                        disabled={!canSubmitCalibration || isCalibrating}
                        onClick={async () => {
                          if (!manualDeviceId || !canSubmitCalibration || isCalibrating) return;
                          const token = getAuthToken();
                          if (!token) {
                            router.replace("/login");
                            return;
                          }
                          setIsCalibrating(true);
                          try {
                            await fetchJson(
                              `/v1/devices/${manualDeviceId}/calibration/start`,
                              {
                                method: "POST",
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                },
                              },
                              getClientApiBaseUrl()
                            );
                            const points = [
                              { ph_point: 4.01, voltage: Number(ph4Voltage) },
                              { ph_point: 6.86, voltage: Number(ph7Voltage) },
                              { ph_point: 9.18, voltage: Number(ph9Voltage) },
                            ];
                            for (const point of points) {
                              await fetchJson(
                                `/v1/devices/${manualDeviceId}/calibration/points`,
                                {
                                  method: "POST",
                                  headers: {
                                    Authorization: `Bearer ${token}`,
                                  },
                                  body: JSON.stringify(point),
                                },
                                getClientApiBaseUrl()
                              );
                            }
                            await fetchJson(
                              `/v1/devices/${manualDeviceId}/calibration/activate`,
                              {
                                method: "POST",
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                },
                              },
                              getClientApiBaseUrl()
                            );
                            push("Calibration activated.", "success");
                            router.push("/dashboard/devices");
                          } catch (err) {
                            push("Calibration failed. Check the voltages and retry.", "error");
                          } finally {
                            setIsCalibrating(false);
                          }
                        }}
                      >
                        {isCalibrating ? "Calibrating..." : "Activate calibration"}
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="mt-6 grid gap-6">
                <div className="grid gap-4 md:grid-cols-[1.2fr_1fr]">
                  <Field
                    label={<span className="text-base font-semibold">Device name</span>}
                    className="text-lg"
                  >
                    <input
                      value={deviceName}
                      onChange={(event) => setDeviceName(event.target.value)}
                      placeholder="Sim Reef drift"
                    />
                  </Field>

                  <Field
                    label={<span className="text-base font-semibold">Attach to aquarium</span>}
                    className="text-lg"
                  >
                    <Select
                      value={selectedAquarium}
                      onChange={setSelectedAquarium}
                      options={aquariumOptions}
                    />
                  </Field>
                </div>

                {isLoadingAquariums ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-base text-white/60">
                    Loading aquariums…
                  </div>
                ) : aquariums.length === 0 ? (
                  <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-base text-white/60">
                    You need at least one aquarium before attaching a device.
                  </div>
                ) : null}

                <div className="grid gap-3">
                  <div className="text-base font-semibold text-white">Simulation preset</div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {PRESETS.map((preset) => {
                      const active = preset.id === selectedPreset.id;
                      return (
                        <button
                          key={preset.id}
                          type="button"
                          className={[
                            "rounded-2xl border px-4 py-3 text-left transition",
                            active
                              ? "border-ocean-500/60 bg-white/5"
                              : "border-white/10 hover:border-white/20",
                          ].join(" ")}
                          onClick={() => setSelectedPreset(preset)}
                        >
                          <div className="text-base font-semibold text-white">
                            {preset.name}
                          </div>
                          <div className="mt-1 text-sm text-white/60">
                            {preset.description}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3">
                  <button
                    type="button"
                    className="rounded-full border border-white/20 px-5 py-2 text-base font-semibold transition hover:border-ocean-500/60"
                    onClick={() => router.push("/dashboard/devices")}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className={[
                      "rounded-full px-5 py-2 text-base font-semibold shadow-ocean transition",
                      canSubmitSimulated
                        ? "bg-gradient-to-br from-[#1f8a9b] to-ocean-500 text-white hover:-translate-y-0.5"
                        : "bg-white/10 text-white/50 cursor-not-allowed",
                    ].join(" ")}
                    disabled={!canSubmitSimulated || isSubmitting}
                    onClick={async () => {
                      if (!canSubmitSimulated || isSubmitting) return;
                      const token = getAuthToken();
                      if (!token) {
                        router.replace("/login");
                        return;
                      }
                      setIsSubmitting(true);
                      try {
                        const response = await fetchJson<DeviceRegisterResponse>(
                          "/v1/devices",
                          {
                            method: "POST",
                            headers: {
                              Authorization: `Bearer ${token}`,
                            },
                            body: JSON.stringify({
                              name: deviceName.trim(),
                              location: `Simulated · ${selectedPreset.name}`,
                            }),
                          },
                          getClientApiBaseUrl()
                        );
                        const queueResponse = await fetch(
                          `${getClientApiBaseUrl()}/v1/simulator/devices`,
                          {
                            method: "POST",
                            headers: {
                              "Content-Type": "application/json",
                              Authorization: `Bearer ${token}`,
                            },
                            body: JSON.stringify({
                              device_id: response.id,
                              aquarium_id: selectedAquarium,
                              preset_id: selectedPreset.id,
                            }),
                          }
                        );
                        if (!queueResponse.ok) {
                          const message = await queueResponse.text();
                          push(
                            message ||
                              "Device registered, but the simulator did not start.",
                            "error"
                          );
                        }
                        push("Simulated device registered.", "success");
                        router.push("/dashboard/devices");
                      } catch (err) {
                        push("Failed to register device.", "error");
                      } finally {
                        setIsSubmitting(false);
                      }
                    }}
                  >
                    {isSubmitting ? "Registering..." : "Register device"}
                  </button>
                </div>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

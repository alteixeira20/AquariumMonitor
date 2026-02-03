"use client";

import { useEffect, useMemo, useState } from "react";
import Field from "../ui/Field";
import Select from "../ui/Select";

export type AquariumFormPayload = {
  name: string;
  water_type: "fresh" | "salt";
  liters: number;
  temperature_enabled: boolean;
  temperature_min: number;
  temperature_max: number;
  ph_enabled: boolean;
  ph_min: number;
  ph_max: number;
  tds_enabled: boolean;
  tds_min: number;
  tds_max: number;
  filter_type: "canister" | "hang_on_back" | "sponge" | "internal" | "sump" | "other";
  filter_flow_lph: number | null;
  heater_watts: number | null;
  lighting_type: "led" | "t5" | "metal_halide" | "none";
  notes: string | null;
};

export type AquariumFormValues = {
  name: string;
  waterType: "fresh" | "salt";
  liters: string;
  temperatureMin: string;
  temperatureMax: string;
  phMin: string;
  phMax: string;
  tdsMin: string;
  tdsMax: string;
  temperatureEnabled: boolean;
  phEnabled: boolean;
  tdsEnabled: boolean;
  filterType:
    | "canister"
    | "hang_on_back"
    | "sponge"
    | "internal"
    | "sump"
    | "other";
  filterFlowLph: string;
  heaterWatts: string;
  lightingType: "led" | "t5" | "metal_halide" | "none";
  notes: string;
};

type AquariumFormProps = {
  title: string;
  description: string;
  submitLabel: string;
  onSubmit: (payload: AquariumFormPayload) => Promise<void>;
  onCancel: () => void;
  initialValues?: Partial<AquariumFormValues>;
};

export default function AquariumForm({
  title,
  description,
  submitLabel,
  onSubmit,
  onCancel,
  initialValues,
}: AquariumFormProps) {
  const [name, setName] = useState(initialValues?.name ?? "");
  const [waterType, setWaterType] = useState<"fresh" | "salt">(
    initialValues?.waterType ?? "fresh"
  );
  const [liters, setLiters] = useState(initialValues?.liters ?? "120");
  const [temperatureMin, setTemperatureMin] = useState(
    initialValues?.temperatureMin ?? "22"
  );
  const [temperatureMax, setTemperatureMax] = useState(
    initialValues?.temperatureMax ?? "26"
  );
  const [phMin, setPhMin] = useState(initialValues?.phMin ?? "6.5");
  const [phMax, setPhMax] = useState(initialValues?.phMax ?? "7.5");
  const [tdsMin, setTdsMin] = useState(initialValues?.tdsMin ?? "150");
  const [tdsMax, setTdsMax] = useState(initialValues?.tdsMax ?? "350");
  const [temperatureEnabled, setTemperatureEnabled] = useState(
    initialValues?.temperatureEnabled ?? true
  );
  const [phEnabled, setPhEnabled] = useState(initialValues?.phEnabled ?? true);
  const [tdsEnabled, setTdsEnabled] = useState(initialValues?.tdsEnabled ?? true);
  const [filterType, setFilterType] = useState<
    "canister" | "hang_on_back" | "sponge" | "internal" | "sump" | "other"
  >(initialValues?.filterType ?? "canister");
  const [filterFlowLph, setFilterFlowLph] = useState(
    initialValues?.filterFlowLph ?? "800"
  );
  const [heaterWatts, setHeaterWatts] = useState(
    initialValues?.heaterWatts ?? "150"
  );
  const [lightingType, setLightingType] = useState<
    "led" | "t5" | "metal_halide" | "none"
  >(initialValues?.lightingType ?? "led");
  const [notes, setNotes] = useState(initialValues?.notes ?? "");
  const [showErrors, setShowErrors] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!initialValues) return;
    if (initialValues.name !== undefined) setName(initialValues.name);
    if (initialValues.waterType !== undefined) setWaterType(initialValues.waterType);
    if (initialValues.liters !== undefined) setLiters(initialValues.liters);
    if (initialValues.temperatureMin !== undefined)
      setTemperatureMin(initialValues.temperatureMin);
    if (initialValues.temperatureMax !== undefined)
      setTemperatureMax(initialValues.temperatureMax);
    if (initialValues.phMin !== undefined) setPhMin(initialValues.phMin);
    if (initialValues.phMax !== undefined) setPhMax(initialValues.phMax);
    if (initialValues.tdsMin !== undefined) setTdsMin(initialValues.tdsMin);
    if (initialValues.tdsMax !== undefined) setTdsMax(initialValues.tdsMax);
    if (initialValues.temperatureEnabled !== undefined)
      setTemperatureEnabled(initialValues.temperatureEnabled);
    if (initialValues.phEnabled !== undefined) setPhEnabled(initialValues.phEnabled);
    if (initialValues.tdsEnabled !== undefined) setTdsEnabled(initialValues.tdsEnabled);
    if (initialValues.filterType !== undefined) setFilterType(initialValues.filterType);
    if (initialValues.filterFlowLph !== undefined)
      setFilterFlowLph(initialValues.filterFlowLph);
    if (initialValues.heaterWatts !== undefined)
      setHeaterWatts(initialValues.heaterWatts);
    if (initialValues.lightingType !== undefined)
      setLightingType(initialValues.lightingType);
    if (initialValues.notes !== undefined) setNotes(initialValues.notes);
  }, [initialValues]);

  const litersNumber = Number(liters);
  const tempMinNumber = Number(temperatureMin);
  const tempMaxNumber = Number(temperatureMax);
  const phMinNumber = Number(phMin);
  const phMaxNumber = Number(phMax);
  const tdsMinNumber = Number(tdsMin);
  const tdsMaxNumber = Number(tdsMax);

  const requiredValid =
    name.trim().length > 0 &&
    Number.isFinite(litersNumber) &&
    litersNumber > 0 &&
    (!temperatureEnabled ||
      (Number.isFinite(tempMinNumber) &&
        Number.isFinite(tempMaxNumber) &&
        tempMinNumber < tempMaxNumber)) &&
    (!phEnabled ||
      (Number.isFinite(phMinNumber) &&
        Number.isFinite(phMaxNumber) &&
        phMinNumber < phMaxNumber)) &&
    (!tdsEnabled ||
      (Number.isFinite(tdsMinNumber) &&
        Number.isFinite(tdsMaxNumber) &&
        tdsMinNumber < tdsMaxNumber));

  const guidance = useMemo(
    () =>
      waterType === "fresh"
        ? {
            tempMin: "22",
            tempMax: "26",
            phMin: "6.5",
            phMax: "7.5",
            tdsMin: "150",
            tdsMax: "350",
          }
        : {
            tempMin: "24",
            tempMax: "27",
            phMin: "8.0",
            phMax: "8.4",
            tdsMin: "900",
            tdsMax: "1300",
          },
    [waterType]
  );

  useEffect(() => {
    if (waterType === "fresh") {
      if (!temperatureMin) setTemperatureMin("22");
      if (!temperatureMax) setTemperatureMax("26");
      if (!phMin) setPhMin("6.5");
      if (!phMax) setPhMax("7.5");
      if (!tdsMin) setTdsMin("150");
      if (!tdsMax) setTdsMax("350");
      return;
    }
    if (!temperatureMin) setTemperatureMin("24");
    if (!temperatureMax) setTemperatureMax("27");
    if (!phMin) setPhMin("8.0");
    if (!phMax) setPhMax("8.4");
    if (!tdsMin) setTdsMin("900");
    if (!tdsMax) setTdsMax("1300");
  }, [waterType, temperatureMin, temperatureMax, phMin, phMax, tdsMin, tdsMax]);

  const InfoTooltip = ({ text }: { text: string }) => (
    <span className="group relative inline-flex items-center">
      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-white/15 bg-white/5 text-base font-semibold text-white/80">
        !
      </span>
      <span className="pointer-events-none absolute left-7 top-1/2 z-10 w-56 -translate-y-1/2 rounded-lg border border-white/10 bg-ocean-800/95 px-3 py-2 text-xs text-white/80 opacity-0 shadow-ocean transition group-hover:opacity-100">
        {text}
      </span>
    </span>
  );

  const SensorToggle = ({
    enabled,
    onToggle,
  }: {
    enabled: boolean;
    onToggle: () => void;
  }) => (
    <button
      type="button"
      onClick={onToggle}
      className="inline-flex items-center rounded-full border border-white/10 bg-white/5 p-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] transition"
      aria-pressed={enabled}
    >
      <span
        className={[
          "rounded-full px-2 py-1",
          enabled ? "bg-emerald-500/30 text-emerald-200" : "text-white/40",
        ].join(" ")}
      >
        On
      </span>
      <span
        className={[
          "rounded-full px-2 py-1",
          !enabled ? "bg-red-500/30 text-red-200" : "text-white/40",
        ].join(" ")}
      >
        Off
      </span>
    </button>
  );

  return (
    <section className="glass-panel p-6">
      <div className="text-base uppercase tracking-[0.3em] text-white/40">
        Aquariums
      </div>
      <h1 className="mt-2 font-display text-4xl">{title}</h1>
      <p className="mt-2 text-lg text-white/60">{description}</p>

      <div className="mt-6 grid gap-6">
        <div className="grid gap-4 md:grid-cols-2">
          <Field
            label={
              <span className="text-base font-semibold">
                Aquarium name
                {showErrors && !name.trim() ? (
                  <span className="text-red-300"> *</span>
                ) : null}
              </span>
            }
            hint={showErrors && !name.trim() ? "Name is required." : undefined}
            error={showErrors && !name.trim()}
            className="text-lg"
          >
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Main display, Reef cube..."
            />
          </Field>

          <Field
            label={
              <span className="text-base font-semibold">
                Size (liters)
                {showErrors && (!liters || litersNumber <= 0) ? (
                  <span className="text-red-300"> *</span>
                ) : null}
              </span>
            }
            hint={
              showErrors && (!liters || litersNumber <= 0)
                ? "Enter a positive number."
                : undefined
            }
            error={showErrors && (!liters || litersNumber <= 0)}
            className="text-lg"
          >
            <input
              type="number"
              value={liters}
              onChange={(event) => setLiters(event.target.value)}
              placeholder="120"
            />
          </Field>

          <Field
            label={<span className="text-base font-semibold">Water type</span>}
            className="text-lg"
          >
            <Select
              value={waterType}
              onChange={(value) => setWaterType(value as "fresh" | "salt")}
              options={[
                { label: "Freshwater", value: "fresh" },
                { label: "Saltwater", value: "salt" },
              ]}
            />
          </Field>

          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-base text-white/60">
            <div className="text-sm uppercase tracking-[0.2em] text-white/40">
              Suggested ranges
            </div>
            <div className="mt-2 text-white/80">
              Temp {guidance.tempMin}–{guidance.tempMax}°C · pH {guidance.phMin}–
              {guidance.phMax} · TDS {guidance.tdsMin}–{guidance.tdsMax} ppm
            </div>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <h2 className="text-lg font-semibold text-white">Target ranges</h2>
            <span className="text-sm text-white/50">
              These drive alerts and insights
            </span>
          </div>

          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-base font-semibold text-white">Temperature</div>
                <InfoTooltip text="Use Celsius targets for your tank. We'll flag values outside of the range." />
              </div>
              <SensorToggle
                enabled={temperatureEnabled}
                onToggle={() => setTemperatureEnabled((prev) => !prev)}
              />
            </div>
            {temperatureEnabled ? (
              <div className="grid gap-4 md:grid-cols-2">
                <Field
                  label={
                    <span className="text-base font-semibold">
                      Min (°C)
                      {showErrors &&
                      (!temperatureMin ||
                        !Number.isFinite(tempMinNumber) ||
                        !Number.isFinite(tempMaxNumber) ||
                        tempMinNumber >= tempMaxNumber) ? (
                        <span className="text-red-300"> *</span>
                      ) : null}
                    </span>
                  }
                  hint={
                    showErrors &&
                    (!temperatureMin ||
                      !Number.isFinite(tempMinNumber) ||
                      !Number.isFinite(tempMaxNumber) ||
                      tempMinNumber >= tempMaxNumber)
                      ? "Enter a valid min below max."
                      : undefined
                  }
                  error={
                    showErrors &&
                    (!temperatureMin ||
                      !Number.isFinite(tempMinNumber) ||
                      !Number.isFinite(tempMaxNumber) ||
                      tempMinNumber >= tempMaxNumber)
                  }
                  className="text-lg"
                >
                  <input
                    type="number"
                    value={temperatureMin}
                    onChange={(event) => setTemperatureMin(event.target.value)}
                    placeholder={guidance.tempMin}
                  />
                </Field>

                <Field
                  label={
                    <span className="text-base font-semibold">
                      Max (°C)
                      {showErrors &&
                      (!temperatureMax ||
                        !Number.isFinite(tempMinNumber) ||
                        !Number.isFinite(tempMaxNumber) ||
                        tempMinNumber >= tempMaxNumber) ? (
                        <span className="text-red-300"> *</span>
                      ) : null}
                    </span>
                  }
                  hint={
                    showErrors &&
                    (!temperatureMax ||
                      !Number.isFinite(tempMinNumber) ||
                      !Number.isFinite(tempMaxNumber) ||
                      tempMinNumber >= tempMaxNumber)
                      ? "Enter a valid max above min."
                      : undefined
                  }
                  error={
                    showErrors &&
                    (!temperatureMax ||
                      !Number.isFinite(tempMinNumber) ||
                      !Number.isFinite(tempMaxNumber) ||
                      tempMinNumber >= tempMaxNumber)
                  }
                  className="text-lg"
                >
                  <input
                    type="number"
                    value={temperatureMax}
                    onChange={(event) => setTemperatureMax(event.target.value)}
                    placeholder={guidance.tempMax}
                  />
                </Field>
              </div>
            ) : null}
          </div>

          <div className="border-t border-white/10 pt-4" />

          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-base font-semibold text-white">pH</div>
                <InfoTooltip text="Set pH alert thresholds. We'll compare readings against this band." />
              </div>
              <SensorToggle enabled={phEnabled} onToggle={() => setPhEnabled((prev) => !prev)} />
            </div>
            {phEnabled ? (
              <div className="grid gap-4 md:grid-cols-2">
                <Field
                  label={
                    <span className="text-base font-semibold">
                      Min pH
                      {showErrors &&
                      (!phMin ||
                        !Number.isFinite(phMinNumber) ||
                        !Number.isFinite(phMaxNumber) ||
                        phMinNumber >= phMaxNumber) ? (
                        <span className="text-red-300"> *</span>
                      ) : null}
                    </span>
                  }
                  hint={
                    showErrors &&
                    (!phMin ||
                      !Number.isFinite(phMinNumber) ||
                      !Number.isFinite(phMaxNumber) ||
                      phMinNumber >= phMaxNumber)
                      ? "Enter a valid min below max."
                      : undefined
                  }
                  error={
                    showErrors &&
                    (!phMin ||
                      !Number.isFinite(phMinNumber) ||
                      !Number.isFinite(phMaxNumber) ||
                      phMinNumber >= phMaxNumber)
                  }
                  className="text-lg"
                >
                  <input
                    type="number"
                    value={phMin}
                    onChange={(event) => setPhMin(event.target.value)}
                    placeholder={guidance.phMin}
                  />
                </Field>

                <Field
                  label={
                    <span className="text-base font-semibold">
                      Max pH
                      {showErrors &&
                      (!phMax ||
                        !Number.isFinite(phMinNumber) ||
                        !Number.isFinite(phMaxNumber) ||
                        phMinNumber >= phMaxNumber) ? (
                        <span className="text-red-300"> *</span>
                      ) : null}
                    </span>
                  }
                  hint={
                    showErrors &&
                    (!phMax ||
                      !Number.isFinite(phMinNumber) ||
                      !Number.isFinite(phMaxNumber) ||
                      phMinNumber >= phMaxNumber)
                      ? "Enter a valid max above min."
                      : undefined
                  }
                  error={
                    showErrors &&
                    (!phMax ||
                      !Number.isFinite(phMinNumber) ||
                      !Number.isFinite(phMaxNumber) ||
                      phMinNumber >= phMaxNumber)
                  }
                  className="text-lg"
                >
                  <input
                    type="number"
                    value={phMax}
                    onChange={(event) => setPhMax(event.target.value)}
                    placeholder={guidance.phMax}
                  />
                </Field>
              </div>
            ) : null}
          </div>

          <div className="border-t border-white/10 pt-4" />

          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-base font-semibold text-white">TDS</div>
                <InfoTooltip text="Total dissolved solids thresholds. Set a safe range for your tank." />
              </div>
              <SensorToggle enabled={tdsEnabled} onToggle={() => setTdsEnabled((prev) => !prev)} />
            </div>
            {tdsEnabled ? (
              <div className="grid gap-4 md:grid-cols-2">
                <Field
                  label={
                    <span className="text-base font-semibold">
                      Min (ppm)
                      {showErrors &&
                      (!tdsMin ||
                        !Number.isFinite(tdsMinNumber) ||
                        !Number.isFinite(tdsMaxNumber) ||
                        tdsMinNumber >= tdsMaxNumber) ? (
                        <span className="text-red-300"> *</span>
                      ) : null}
                    </span>
                  }
                  hint={
                    showErrors &&
                    (!tdsMin ||
                      !Number.isFinite(tdsMinNumber) ||
                      !Number.isFinite(tdsMaxNumber) ||
                      tdsMinNumber >= tdsMaxNumber)
                      ? "Enter a valid min below max."
                      : undefined
                  }
                  error={
                    showErrors &&
                    (!tdsMin ||
                      !Number.isFinite(tdsMinNumber) ||
                      !Number.isFinite(tdsMaxNumber) ||
                      tdsMinNumber >= tdsMaxNumber)
                  }
                  className="text-lg"
                >
                  <input
                    type="number"
                    value={tdsMin}
                    onChange={(event) => setTdsMin(event.target.value)}
                    placeholder={guidance.tdsMin}
                  />
                </Field>

                <Field
                  label={
                    <span className="text-base font-semibold">
                      Max (ppm)
                      {showErrors &&
                      (!tdsMax ||
                        !Number.isFinite(tdsMinNumber) ||
                        !Number.isFinite(tdsMaxNumber) ||
                        tdsMinNumber >= tdsMaxNumber) ? (
                        <span className="text-red-300"> *</span>
                      ) : null}
                    </span>
                  }
                  hint={
                    showErrors &&
                    (!tdsMax ||
                      !Number.isFinite(tdsMinNumber) ||
                      !Number.isFinite(tdsMaxNumber) ||
                      tdsMinNumber >= tdsMaxNumber)
                      ? "Enter a valid max above min."
                      : undefined
                  }
                  error={
                    showErrors &&
                    (!tdsMax ||
                      !Number.isFinite(tdsMinNumber) ||
                      !Number.isFinite(tdsMaxNumber) ||
                      tdsMinNumber >= tdsMaxNumber)
                  }
                  className="text-lg"
                >
                  <input
                    type="number"
                    value={tdsMax}
                    onChange={(event) => setTdsMax(event.target.value)}
                    placeholder={guidance.tdsMax}
                  />
                </Field>
              </div>
            ) : null}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <h2 className="text-lg font-semibold text-white">Equipment</h2>
            <span className="text-sm text-white/50">Optional but helpful</span>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Field
              label={<span className="text-base font-semibold">Filter type</span>}
              className="text-lg"
            >
              <Select
                value={filterType}
                onChange={(value) =>
                  setFilterType(
                    value as
                      | "canister"
                      | "hang_on_back"
                      | "sponge"
                      | "internal"
                      | "sump"
                      | "other"
                  )
                }
                options={[
                  { label: "Canister", value: "canister" },
                  { label: "Hang-on-back", value: "hang_on_back" },
                  { label: "Sponge", value: "sponge" },
                  { label: "Internal", value: "internal" },
                  { label: "Sump", value: "sump" },
                  { label: "Other", value: "other" },
                ]}
              />
            </Field>

            <Field
              label={
                <span className="text-base font-semibold">
                  Filter flow (L/h)
                </span>
              }
              className="text-lg"
            >
              <input
                type="number"
                value={filterFlowLph}
                onChange={(event) => setFilterFlowLph(event.target.value)}
                placeholder="800"
              />
            </Field>

            <Field
              label={<span className="text-base font-semibold">Heater (W)</span>}
              className="text-lg"
            >
              <input
                type="number"
                value={heaterWatts}
                onChange={(event) => setHeaterWatts(event.target.value)}
                placeholder="150"
              />
            </Field>

            <Field
              label={<span className="text-base font-semibold">Lighting</span>}
              className="text-lg"
            >
              <Select
                value={lightingType}
                onChange={(value) =>
                  setLightingType(
                    value as "led" | "t5" | "metal_halide" | "none"
                  )
                }
                options={[
                  { label: "LED", value: "led" },
                  { label: "T5", value: "t5" },
                  { label: "Metal halide", value: "metal_halide" },
                  { label: "None", value: "none" },
                ]}
              />
            </Field>

            <Field label={<span className="text-base font-semibold">Notes</span>} className="text-lg">
              <textarea
                rows={4}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Example: dosing schedule, livestock list, or special care notes."
              />
            </Field>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
          <button
            className="rounded-full border border-white/20 px-5 py-2 text-base font-semibold transition hover:border-ocean-500/60"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            className={[
              "rounded-full px-5 py-2 text-base font-semibold shadow-ocean transition",
              requiredValid
                ? "bg-gradient-to-br from-[#1f8a9b] to-ocean-500 text-white hover:-translate-y-0.5"
                : "bg-white/10 text-white/50 cursor-not-allowed",
            ].join(" ")}
            type="button"
            onClick={async () => {
              if (isSubmitting) return;
              setSubmitError(null);
              if (!requiredValid) {
                setShowErrors(true);
                return;
              }
              setIsSubmitting(true);
              try {
                await onSubmit({
                  name: name.trim(),
                  water_type: waterType,
                  liters: Number(liters),
                  temperature_enabled: temperatureEnabled,
                  temperature_min: Number(temperatureMin),
                  temperature_max: Number(temperatureMax),
                  ph_enabled: phEnabled,
                  ph_min: Number(phMin),
                  ph_max: Number(phMax),
                  tds_enabled: tdsEnabled,
                  tds_min: Number(tdsMin),
                  tds_max: Number(tdsMax),
                  filter_type: filterType,
                  filter_flow_lph: filterFlowLph ? Number(filterFlowLph) : null,
                  heater_watts: heaterWatts ? Number(heaterWatts) : null,
                  lighting_type: lightingType,
                  notes: notes.trim() ? notes.trim() : null,
                });
              } catch (err) {
                setSubmitError(
                  err instanceof Error
                    ? err.message
                    : "Something went wrong. Try again."
                );
              } finally {
                setIsSubmitting(false);
              }
            }}
          >
            {isSubmitting ? `${submitLabel}...` : submitLabel}
          </button>
        </div>
        {submitError ? (
          <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-base text-red-100">
            {submitError}
          </div>
        ) : null}
      </div>
    </section>
  );
}

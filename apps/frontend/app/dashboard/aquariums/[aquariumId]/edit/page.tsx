"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import TopNav from "../../../../../components/dashboard/TopNav";
import AquariumForm, {
  AquariumFormValues,
} from "../../../../../components/dashboard/AquariumForm";
import { useToast } from "../../../../../components/ui/ToastProvider";
import { clearAuthToken, getAuthToken } from "../../../../../lib/auth";
import { getMe } from "../../../../../lib/auth_api";
import { fetchJson } from "../../../../../lib/api";
import { getClientApiBaseUrl } from "../../../../../lib/config";

type AquariumResponse = {
  id: string;
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
  filter_type:
    | "canister"
    | "hang_on_back"
    | "sponge"
    | "internal"
    | "sump"
    | "other"
    | null;
  filter_flow_lph: number | null;
  heater_watts: number | null;
  lighting_type: "led" | "t5" | "metal_halide" | "none" | null;
  notes: string | null;
};

export default function AquariumEditPage() {
  const router = useRouter();
  const params = useParams();
  const { push } = useToast();
  const [isChecking, setIsChecking] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [aquarium, setAquarium] = useState<AquariumResponse | null>(null);

  const aquariumId = Array.isArray(params?.aquariumId)
    ? params?.aquariumId[0]
    : params?.aquariumId;

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
      if (!aquariumId) return;
      const token = getAuthToken();
      if (!token) return;
      setIsLoading(true);
      try {
        const data = await fetchJson<AquariumResponse>(
          `/v1/aquariums/${aquariumId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
          getClientApiBaseUrl()
        );
        if (!ignore) setAquarium(data);
      } catch (err) {
        if (!ignore) {
          push("Aquarium not found.", "error");
          router.push("/dashboard/aquariums");
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    if (!isChecking) loadAquarium();

    return () => {
      ignore = true;
    };
  }, [aquariumId, isChecking, push, router]);

  const initialValues: AquariumFormValues | undefined = useMemo(() => {
    if (!aquarium) return undefined;
    return {
      name: aquarium.name,
      waterType: aquarium.water_type,
      liters: String(aquarium.liters),
      temperatureMin: String(aquarium.temperature_min),
      temperatureMax: String(aquarium.temperature_max),
      phMin: String(aquarium.ph_min),
      phMax: String(aquarium.ph_max),
      tdsMin: String(aquarium.tds_min),
      tdsMax: String(aquarium.tds_max),
      temperatureEnabled: aquarium.temperature_enabled,
      phEnabled: aquarium.ph_enabled,
      tdsEnabled: aquarium.tds_enabled,
      filterType: aquarium.filter_type ?? "canister",
      filterFlowLph:
        aquarium.filter_flow_lph !== null ? String(aquarium.filter_flow_lph) : "",
      heaterWatts:
        aquarium.heater_watts !== null ? String(aquarium.heater_watts) : "",
      lightingType: aquarium.lighting_type ?? "led",
      notes: aquarium.notes ?? "",
    };
  }, [aquarium]);

  if (isChecking || isLoading || !initialValues) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
          <AquariumForm
            title="Edit aquarium"
            description="Update your tank details and sensor ranges. Changes apply immediately."
            submitLabel="Save changes"
            initialValues={initialValues}
            onCancel={() => router.push("/dashboard/aquariums")}
            onSubmit={async (payload) => {
              const token = getAuthToken();
              if (!token) {
                router.replace("/login");
                return;
              }
              await fetchJson(
                `/v1/aquariums/${aquariumId}`,
                {
                  method: "PUT",
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                  body: JSON.stringify(payload),
                },
                getClientApiBaseUrl()
              );
              push("Aquarium updated.", "success");
              router.push("/dashboard/aquariums");
            }}
          />
        </main>
      </div>
    </div>
  );
}

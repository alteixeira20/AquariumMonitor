"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import TopNav from "../../../../components/dashboard/TopNav";
import AquariumForm from "../../../../components/dashboard/AquariumForm";
import { useToast } from "../../../../components/ui/ToastProvider";
import { clearAuthToken, getAuthToken } from "../../../../lib/auth";
import { getMe } from "../../../../lib/auth_api";
import { fetchJson } from "../../../../lib/api";
import { getClientApiBaseUrl } from "../../../../lib/config";

export default function AquariumCreatePage() {
  const router = useRouter();
  const { push } = useToast();
  const [isChecking, setIsChecking] = useState(true);

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

  if (isChecking) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  return (
    <div className="pb-16">
      <div className="mx-auto flex w-full max-w-7xl gap-6 px-6 pt-12">
        <TopNav />

        <main className="flex min-w-0 flex-1 flex-col gap-8">
          <AquariumForm
            title="Create your aquarium"
            description="Start with the essentials so readings can be compared against safe ranges."
            submitLabel="Create aquarium"
            onCancel={() => router.push("/dashboard/aquariums")}
            onSubmit={async (payload) => {
              const token = getAuthToken();
              if (!token) {
                router.replace("/login");
                return;
              }
              await fetchJson(
                "/v1/aquariums",
                {
                  method: "POST",
                  headers: {
                    Authorization: `Bearer ${token}`,
                  },
                  body: JSON.stringify(payload),
                },
                getClientApiBaseUrl()
              );
              push("Aquarium created successfully.", "success");
              router.push("/dashboard/aquariums");
            }}
          />
        </main>
      </div>
    </div>
  );
}

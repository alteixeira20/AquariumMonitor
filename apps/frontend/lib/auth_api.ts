"use client";

import { fetchJson } from "./api";
import { getClientApiBaseUrl } from "./config";

export type MeResponse = {
  user_id: string;
  email: string | null;
  role: string;
  is_demo: boolean;
};

export async function getMe(token: string, baseUrl?: string) {
  const apiBaseUrl = baseUrl ?? getClientApiBaseUrl();
  return fetchJson<MeResponse>(
    "/v1/me",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
    apiBaseUrl
  );
}

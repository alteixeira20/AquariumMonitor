import { fetchJson } from "../api";

export type SetupStatus = {
  configured: boolean;
  demo_enabled: boolean;
};

export type SetupPayload = {
  email: string;
  password: string;
};

export type SetupResponse = {
  owner_user_id: string;
  access_token: string;
};

export async function getSetupStatus(baseUrl?: string, options?: RequestInit) {
  return fetchJson<SetupStatus>("/v1/setup/status", options, baseUrl);
}

export async function postSetup(payload: SetupPayload, baseUrl?: string) {
  return fetchJson<SetupResponse>("/v1/setup", {
    method: "POST",
    body: JSON.stringify(payload),
  }, baseUrl);
}

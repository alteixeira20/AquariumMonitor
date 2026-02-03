export const defaultApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function getClientApiBaseUrl() {
  if (typeof window === "undefined") {
    return defaultApiBaseUrl;
  }
  return window.localStorage.getItem("api_base_url") ?? defaultApiBaseUrl;
}

export function setClientApiBaseUrl(value: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("api_base_url", value);
}

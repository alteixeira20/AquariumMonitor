"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchJson } from "../../lib/api";
import { clearAuthToken, getAuthToken, setAuthToken } from "../../lib/auth";
import { getMe } from "../../lib/auth_api";
import { getClientApiBaseUrl } from "../../lib/config";
import { getSetupStatus } from "../../lib/setup/api";
import { isValidEmail } from "../../lib/setup/validation";

type LoginResponse = {
  access_token: string;
  token_type: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCheckingSetup, setIsCheckingSetup] = useState(true);

  const emailValid = isValidEmail(email);

  useEffect(() => {
    let ignore = false;

    async function checkSetup() {
      const token = getAuthToken();
      if (token) {
        try {
          await getMe(token);
          if (!ignore) router.replace("/dashboard");
          return;
        } catch (err) {
          clearAuthToken();
        }
      }

      try {
        const status = await getSetupStatus(getClientApiBaseUrl());
        if (ignore) return;
        if (!status.configured) {
          router.replace("/");
          return;
        }
      } catch (err) {
        if (ignore) return;
        setError("Backend unavailable. Start the backend and try again.");
      } finally {
        if (!ignore) setIsCheckingSetup(false);
      }
    }

    checkSetup();
    return () => {
      ignore = true;
    };
  }, [router]);

  async function handleLogin() {
    if (isSubmitting) return;
    setError(null);
    if (!emailValid) {
      setError("Enter a valid email address.");
      return;
    }
    if (!password) {
      setError("Enter your password.");
      return;
    }
    setIsSubmitting(true);
    try {
      const data = await fetchJson<LoginResponse>("/v1/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setAuthToken(data.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError("Login failed. Check your credentials and try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isCheckingSetup) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="glass-panel w-full max-w-md p-6">
        <div className="text-center">
          <div className="font-display text-2xl">Welcome back</div>
          <div className="mt-1 text-sm text-white/60">
            Log in to continue to your dashboard.
          </div>
        </div>

        <form
          className="mt-6 grid gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            handleLogin();
          }}
        >
          <label className="grid gap-2 text-sm text-white/70">
            Email
            <input
              type="email"
              value={email}
              placeholder="admin@example.com"
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>

          <label className="grid gap-2 text-sm text-white/70">
            Password
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                placeholder="Your password"
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword((value) => !value)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-white/60 transition hover:text-white"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </label>

          {error ? (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            onClick={handleLogin}
            disabled={isSubmitting}
            className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

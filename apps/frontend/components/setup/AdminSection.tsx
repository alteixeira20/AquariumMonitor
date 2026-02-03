"use client";

import { useMemo, useState } from "react";
import type { AdminSettings } from "../../lib/setup/types";
import { getPasswordChecks, passwordScore } from "../../lib/setup/validation";
import Field from "../ui/Field";
import Toggle from "../ui/Toggle";

type Props = {
  admin: AdminSettings;
  onChange: (next: Partial<AdminSettings>) => void;
  showErrors: boolean;
  emailValid: boolean;
  passwordSafe: boolean;
};

export default function AdminSection({
  admin,
  onChange,
  showErrors,
  emailValid,
  passwordSafe,
}: Props) {
  const [showPassword, setShowPassword] = useState(false);
  const passwordChecks = useMemo(
    () => getPasswordChecks(admin.password),
    [admin.password]
  );
  const strength = passwordScore(passwordChecks);
  const showEmailError = showErrors && (!admin.email || !emailValid);
  const showPasswordError = showErrors && (!admin.password || !passwordSafe);

  return (
    <div className="grid gap-5">
      <div className="grid gap-4 md:grid-cols-2">
        <Field
          label={
            <span>
              Admin email{showEmailError ? <span className="text-red-300"> *</span> : null}
            </span>
          }
          hint={
            showEmailError
              ? "Enter a valid email address."
              : undefined
          }
          error={showEmailError}
        >
          <input
            type="email"
            value={admin.email}
            placeholder="admin@example.com"
            onChange={(e) => onChange({ email: e.target.value })}
          />
        </Field>

        <Field
          label={
            <span>
              Admin password
              {showPasswordError ? <span className="text-red-300"> *</span> : null}
            </span>
          }
          hint={
            showPasswordError
              ? "Use a stronger password to continue."
              : undefined
          }
          error={showPasswordError}
        >
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={admin.password}
              placeholder="Create a strong password"
              onChange={(e) => onChange({ password: e.target.value })}
            />
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-semibold text-white/60 transition hover:text-white"
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </Field>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold">Password strength</div>
          <div className="text-xs text-white/60">{strength}%</div>
        </div>
        <div className="mt-2 h-2 w-full rounded-full bg-white/10">
          <div
            className={[
              "h-2 rounded-full transition-all",
              strength >= 80 ? "bg-ocean-500" : "bg-ocean-500/50",
            ].join(" ")}
            style={{ width: `${strength}%` }}
          />
        </div>
        <div className="mt-3 grid gap-1 text-xs text-white/70">
          {passwordChecks.map((check) => (
            <div key={check.label} className="flex items-center gap-2">
              <span className={check.passed ? "text-ocean-400" : "text-white/40"}>
                {check.passed ? "✓" : "•"}
              </span>
              <span>{check.label}</span>
            </div>
          ))}
        </div>
      </div>

      <Toggle
        checked={admin.demoEnabled}
        onChange={(demoEnabled) => onChange({ demoEnabled })}
        label="Enable demo login"
        description="Read-only access for dashboard previews."
      />
    </div>
  );
}

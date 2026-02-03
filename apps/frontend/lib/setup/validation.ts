"use client";

export type PasswordCheck = {
  label: string;
  passed: boolean;
};


export function isValidEmail(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
}

export function getPasswordChecks(value: string): PasswordCheck[] {
  const trimmed = value.trim();
  return [
    { label: "At least 10 characters", passed: trimmed.length >= 10 },
    { label: "Contains a lowercase letter", passed: /[a-z]/.test(trimmed) },
    { label: "Contains an uppercase letter", passed: /[A-Z]/.test(trimmed) },
    { label: "Contains a number", passed: /\d/.test(trimmed) },
    { label: "Contains a symbol", passed: /[^A-Za-z0-9]/.test(trimmed) },
  ];
}

export function passwordScore(checks: PasswordCheck[]) {
  const passed = checks.filter((check) => check.passed).length;
  return Math.round((passed / checks.length) * 100);
}

export function isPasswordSafe(value: string) {
  const checks = getPasswordChecks(value);
  return checks.every((check) => check.passed);
}

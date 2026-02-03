"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import HelpModal from "../components/HelpModal";
import SetupHeader from "../components/setup/SetupHeader";
import SetupIntro from "../components/setup/SetupIntro";
import SetupSection from "../components/setup/SetupSection";
import SetupProgressModal, {
  type SetupProgressStep,
} from "../components/setup/SetupProgressModal";
import { clearAuthToken, getAuthToken } from "../lib/auth";
import { getMe } from "../lib/auth_api";
import { getClientApiBaseUrl, setClientApiBaseUrl } from "../lib/config";
import { getSetupStatus, postSetup } from "../lib/setup/api";
import { helpContent, type HelpKey } from "../lib/setup/content";
import { setupSections } from "../lib/setup/sections";
import { useSetupDraft } from "../lib/setup/useSetupDraft";
import { isPasswordSafe, isValidEmail } from "../lib/setup/validation";

export default function SetupWizardPage() {
  const router = useRouter();
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [activeHelp, setActiveHelp] = useState<HelpKey | null>(null);
  const [statusLabel, setStatusLabel] = useState("Waiting");
  const [statusTone, setStatusTone] = useState<"info" | "ready" | "error">("info");
  const [isConfigured, setIsConfigured] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [backendReady, setBackendReady] = useState(false);
  const [isCheckingBackend, setIsCheckingBackend] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [progressSteps, setProgressSteps] = useState<SetupProgressStep[]>([]);
  const [showErrors, setShowErrors] = useState(false);
  const draftState = useSetupDraft();
  const [backendUrl, setBackendUrl] = useState(() => getClientApiBaseUrl());
  const [backendMode, setBackendMode] = useState<"single" | "team">("single");
  const emailValid = isValidEmail(draftState.draft.admin.email);
  const passwordSafe = isPasswordSafe(draftState.draft.admin.password);

  const helpDetails = useMemo(
    () => (activeHelp ? helpContent[activeHelp] : null),
    [activeHelp]
  );

  const storageErrors =
    draftState.draft.storageEngine === "sqlite"
      ? {
          databaseUrl: !draftState.draft.sqlite.databaseUrl.trim(),
          host: false,
          port: false,
          name: false,
          user: false,
          password: false,
        }
      : draftState.draft.storageEngine === "mariadb"
        ? {
            databaseUrl: false,
            host: !draftState.draft.mariadb.host.trim(),
            port: !draftState.draft.mariadb.port,
            name: !draftState.draft.mariadb.name.trim(),
            user: !draftState.draft.mariadb.user.trim(),
            password: !draftState.draft.mariadb.password.trim(),
          }
        : {
            databaseUrl: false,
            host: false,
            port: false,
            name: false,
            user: false,
            password: false,
          };

  const backupsErrors = draftState.draft.backups.enabled
    ? {
        interval: draftState.draft.backups.intervalHours <= 0,
        retention: draftState.draft.backups.retentionDays <= 0,
        directory: !draftState.draft.backups.directory.trim(),
      }
    : { interval: false, retention: false, directory: false };

  const adminHasError = !emailValid || !passwordSafe;
  const storageHasError =
    draftState.draft.storageEngine === "sqlite"
      ? storageErrors.databaseUrl
      : draftState.draft.storageEngine === "mariadb"
        ? storageErrors.host ||
          storageErrors.port ||
          storageErrors.name ||
          storageErrors.user ||
          storageErrors.password
        : false;
  const backupsHasError =
    draftState.draft.backups.enabled &&
    (backupsErrors.interval || backupsErrors.retention || backupsErrors.directory);

  const canSubmit =
    backendReady && !adminHasError && !storageHasError && !backupsHasError;
  const formReady = canSubmit && !isSubmitting;

  const validationState = {
    showErrors,
    admin: {
      emailValid,
      passwordSafe,
      hasError: adminHasError,
    },
    storage: {
      hasError: storageHasError,
      sqlite: {
        databaseUrl: storageErrors.databaseUrl,
      },
      mariadb: {
        host: storageErrors.host,
        port: storageErrors.port,
        name: storageErrors.name,
        user: storageErrors.user,
        password: storageErrors.password,
      },
    },
    backups: {
      enabled: draftState.draft.backups.enabled,
      hasError: backupsHasError,
      interval: backupsErrors.interval,
      retention: backupsErrors.retention,
      directory: backupsErrors.directory,
    },
  };

  useEffect(() => {
    let ignore = false;

    async function checkAccess() {
      const token = getAuthToken();
      if (token) {
        try {
          await getMe(token);
          if (!ignore) {
            router.replace("/dashboard");
          }
          return;
        } catch (error) {
          clearAuthToken();
        }
      }

      const baseUrl = backendUrl.trim().replace(/\/$/, "");
      if (baseUrl) {
        try {
          const controller = new AbortController();
          const timeoutId = window.setTimeout(() => controller.abort(), 4000);
          const status = await getSetupStatus(baseUrl, {
            signal: controller.signal,
          });
          window.clearTimeout(timeoutId);
          if (!ignore && status.configured) {
            router.replace("/login");
            return;
          }
        } catch (error) {
          // Ignore setup status failures here; user can manually check connection.
        }
      }

      if (!ignore) {
        setIsAuthChecked(true);
      }
    }

    checkAccess();
    return () => {
      ignore = true;
    };
  }, [backendUrl, router]);

  if (!isAuthChecked) {
    return <div className="min-h-screen bg-ocean-900" />;
  }

  async function handleCheckBackend() {
    if (!backendUrl || isCheckingBackend) return;
    const baseUrl = backendUrl.trim().replace(/\/$/, "");
    setIsCheckingBackend(true);
    setStatusError(null);
    setStatusLabel("Checking connection");
    setStatusTone("info");
    try {
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 6000);
      const status = await getSetupStatus(baseUrl, { signal: controller.signal });
      window.clearTimeout(timeoutId);
      setClientApiBaseUrl(baseUrl);
      setBackendReady(true);
      setStatusLabel("Operational");
      setStatusTone("ready");
      if (status.configured) {
        setIsConfigured(true);
        router.replace("/login");
      }
    } catch (error) {
      const detail =
        error instanceof DOMException && error.name === "AbortError"
          ? "The request timed out. The backend may be down or blocked."
          : error instanceof Error
            ? error.message || "Unexpected error."
            : "Unexpected error.";
      setBackendReady(false);
      setStatusTone("error");
      setStatusLabel("Failed");
      setStatusError(
        `Backend check failed:\n- ${detail}\n- Confirm the URL.\n- Ensure the backend is running.\n- Try again.`
      );
    } finally {
      setIsCheckingBackend(false);
    }
  }

  function initProgress() {
    const steps: SetupProgressStep[] = [
      { id: "validate", label: "Validating settings", status: "pending" },
      { id: "save", label: "Saving admin account", status: "pending" },
      { id: "db", label: "Preparing database", status: "pending" },
      { id: "final", label: "Finalizing setup", status: "pending" },
    ];
    setProgressSteps(steps);
    return steps;
  }

  function updateStep(
    steps: SetupProgressStep[],
    id: string,
    status: SetupProgressStep["status"],
    detail?: string
  ) {
    const next = steps.map((step) =>
      step.id === id ? { ...step, status, detail } : step
    );
    setProgressSteps(next);
    return next;
  }

  async function handleSetup() {
    if (isSubmitting || isConfigured) return;
    setSubmitError(null);
    setIsSubmitting(true);
    let steps = initProgress();

    steps = updateStep(steps, "validate", "active");
    if (!emailValid) {
      updateStep(steps, "validate", "error", "Email is not valid.");
      setSubmitError("Please enter a valid email address.");
      setIsSubmitting(false);
      return;
    }
    if (!passwordSafe) {
      updateStep(steps, "validate", "error", "Password does not meet requirements.");
      setSubmitError("Please use a stronger password.");
      setIsSubmitting(false);
      return;
    }
    steps = updateStep(steps, "validate", "done");

    steps = updateStep(steps, "save", "active");
    try {
      const baseUrl = backendUrl.trim().replace(/\/$/, "");
      await postSetup(
        {
          email: draftState.draft.admin.email.trim(),
          password: draftState.draft.admin.password,
        },
        baseUrl
      );
      steps = updateStep(steps, "save", "done");
    } catch (error) {
      updateStep(steps, "save", "error", "Failed to save setup.");
      setSubmitError("Setup failed. Check the backend logs and try again.");
      setIsSubmitting(false);
      return;
    }

    steps = updateStep(steps, "db", "active");
    try {
      const baseUrl = backendUrl.trim().replace(/\/$/, "");
      const response = await fetch(`${baseUrl}/v1/readiness`, {
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error("Readiness check failed");
      }
      steps = updateStep(steps, "db", "done");
    } catch (error) {
      updateStep(steps, "db", "error", "Database readiness check failed.");
      setSubmitError("Database check failed. Please retry.");
      setIsSubmitting(false);
      return;
    }

    steps = updateStep(steps, "final", "active");
    await new Promise((resolve) => setTimeout(resolve, 600));
    updateStep(steps, "final", "done");
    await new Promise((resolve) => setTimeout(resolve, 400));
    router.replace("/login");
  }

  function handleSubmitClick() {
    if (isSubmitting) return;
    if (!canSubmit) {
      setShowErrors(true);
      return;
    }
    handleSetup();
  }

  return (
    <div className="flex min-h-screen flex-col gap-8 px-6 py-8 md:px-12 md:py-10">
      <SetupHeader />

      <main className="flex flex-col items-center">
        <div className="flex w-full max-w-3xl flex-col gap-7">
          <SetupIntro
            backendUrl={backendUrl}
            backendMode={backendMode}
            onBackendUrlChange={setBackendUrl}
            onBackendModeChange={setBackendMode}
            onCheckBackend={handleCheckBackend}
            isChecking={isCheckingBackend}
            statusLabel={statusLabel}
            statusTone={statusTone}
          />

          {statusError ? (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-100 whitespace-pre-line">
              {statusError}
            </div>
          ) : null}

          {backendReady ? (
            setupSections.map((section) => (
              <SetupSection
                key={section.id}
                title={section.title}
                subtitle={section.subtitle}
                onHelp={() => setActiveHelp(section.helpKey)}
                hasError={
                  section.id === "admin"
                    ? showErrors && validationState.admin.hasError
                    : section.id === "storage"
                      ? showErrors && validationState.storage.hasError
                      : section.id === "backups"
                        ? showErrors && validationState.backups.hasError
                        : false
                }
              >
                {section.render(draftState.draft, draftState, validationState)}
              </SetupSection>
            ))
          ) : (
            <div className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-sm text-white/70">
              Connect to the backend to unlock setup options.
            </div>
          )}

          <section className="flex flex-wrap justify-end gap-3">
            <button
              type="button"
              className="rounded-full border border-white/20 px-5 py-2 text-sm font-semibold transition hover:border-ocean-500/60"
            >
              Save draft
            </button>
            <button
              type="button"
              onClick={handleSubmitClick}
              aria-disabled={!formReady}
              className={[
                "rounded-full px-5 py-2 text-sm font-semibold shadow-ocean transition",
                formReady
                  ? "bg-gradient-to-br from-[#1f8a9b] to-ocean-500 text-ocean-950 hover:-translate-y-0.5"
                  : "bg-white/10 text-white/50 cursor-not-allowed",
              ].join(" ")}
            >
              {isSubmitting ? "Setting up..." : "Complete setup"}
            </button>
          </section>

          {submitError ? (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-100">
              {submitError}
            </div>
          ) : null}
        </div>
      </main>

      {helpDetails ? (
        <HelpModal
          title={helpDetails.title}
          content={helpDetails.content}
          isOpen={Boolean(activeHelp)}
          onClose={() => setActiveHelp(null)}
        />
      ) : null}

      <SetupProgressModal
        isOpen={isSubmitting}
        title="Setting up your system"
        steps={progressSteps}
      />
    </div>
  );
}

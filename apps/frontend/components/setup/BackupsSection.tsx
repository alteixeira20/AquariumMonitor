"use client";

import type { BackupSettings } from "../../lib/setup/types";
import Field from "../ui/Field";
import Toggle from "../ui/Toggle";

type Props = {
  backups: BackupSettings;
  onChange: (next: Partial<BackupSettings>) => void;
  showErrors: boolean;
  errors: {
    interval: boolean;
    retention: boolean;
    directory: boolean;
  };
};

export default function BackupsSection({
  backups,
  onChange,
  showErrors,
  errors,
}: Props) {
  const showIntervalError = showErrors && errors.interval;
  const showRetentionError = showErrors && errors.retention;
  const showDirectoryError = showErrors && errors.directory;

  return (
    <div className="grid gap-5">
      <Toggle
        checked={backups.enabled}
        onChange={(enabled) => onChange({ enabled })}
        label="Enable automatic backups"
        description="Recommended for SQLite deployments."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Field
          label={
            <span>
              Interval (hours)
              {showIntervalError ? <span className="text-red-300"> *</span> : null}
            </span>
          }
          hint={showIntervalError ? "Interval must be greater than 0." : undefined}
          error={showIntervalError}
        >
          <input
            type="number"
            value={backups.intervalHours}
            onChange={(e) =>
              onChange({ intervalHours: Number(e.target.value) })
            }
            disabled={!backups.enabled}
          />
        </Field>

        <Field
          label={
            <span>
              Retention (days)
              {showRetentionError ? <span className="text-red-300"> *</span> : null}
            </span>
          }
          hint={showRetentionError ? "Retention must be greater than 0." : undefined}
          error={showRetentionError}
        >
          <input
            type="number"
            value={backups.retentionDays}
            onChange={(e) =>
              onChange({ retentionDays: Number(e.target.value) })
            }
            disabled={!backups.enabled}
          />
        </Field>

        <Field
          label={
            <span>
              Backup directory
              {showDirectoryError ? <span className="text-red-300"> *</span> : null}
            </span>
          }
          hint={showDirectoryError ? "Backup directory is required." : undefined}
          error={showDirectoryError}
        >
          <input
            type="text"
            value={backups.directory}
            onChange={(e) =>
              onChange({ directory: e.target.value })
            }
            disabled={!backups.enabled}
          />
        </Field>
      </div>
    </div>
  );
}

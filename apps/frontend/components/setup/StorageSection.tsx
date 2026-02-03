"use client";

import { useState } from "react";
import type {
  MariaDbSettings,
  SqliteSettings,
  StorageEngine,
} from "../../lib/setup/types";
import {
  sqliteJournalModeOptions,
  sqliteSynchronousOptions,
  storageEngineOptions,
} from "../../lib/setup/options";
import Field from "../ui/Field";
import Select from "../ui/Select";

type Props = {
  engine: StorageEngine;
  sqlite: SqliteSettings;
  mariadb: MariaDbSettings;
  onEngineChange: (next: StorageEngine) => void;
  onSqliteChange: (next: Partial<SqliteSettings>) => void;
  onMariaChange: (next: Partial<MariaDbSettings>) => void;
  showErrors: boolean;
  sqliteErrors: {
    databaseUrl: boolean;
  };
  mariadbErrors: {
    host: boolean;
    port: boolean;
    name: boolean;
    user: boolean;
    password: boolean;
  };
};

export default function StorageSection({
  engine,
  sqlite,
  mariadb,
  onEngineChange,
  onSqliteChange,
  onMariaChange,
  showErrors,
  sqliteErrors,
  mariadbErrors,
}: Props) {
  const [showSqliteAdvanced, setShowSqliteAdvanced] = useState(false);
  const showSqliteUrlError = showErrors && sqliteErrors.databaseUrl;

  return (
    <div className="grid gap-4">
      <div className="grid gap-2 md:grid-cols-[1fr_320px] md:items-center">
        <div className="text-sm font-semibold text-white/80">
          What database do you want to use?
        </div>

        <Select<StorageEngine>
          value={engine}
          onChange={onEngineChange}
          options={storageEngineOptions}
        />
      </div>

      {engine === "sqlite" ? (
        <div className="rounded-2xl border border-ocean-500/20 bg-black/20 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">SQLite settings</div>
              <div className="text-sm text-white/60">
                Best for single-node self-hosting. Recommended defaults are
                preselected.
              </div>
            </div>

            <span className="inline-flex items-center rounded-full bg-ocean-500/10 px-3 py-1 text-xs text-ocean-300">
              Recommended
            </span>
          </div>

          <div className="mt-5 grid gap-4">
            <Field
              label={
                <span>
                  Database URL
                  {showSqliteUrlError ? <span className="text-red-300"> *</span> : null}
                </span>
              }
              hint={showSqliteUrlError ? "Database URL is required." : undefined}
              error={showSqliteUrlError}
            >
              <input
                value={sqlite.databaseUrl}
                onChange={(e) => onSqliteChange({ databaseUrl: e.target.value })}
              />
            </Field>

            <button
              type="button"
              onClick={() => setShowSqliteAdvanced((v) => !v)}
              className="w-fit rounded-full border border-white/20 px-4 py-2 text-sm font-semibold transition hover:border-ocean-500/60"
            >
              {showSqliteAdvanced ? "Hide advanced" : "Show advance"}
            </button>
          </div>

          {showSqliteAdvanced ? (
            <div className="mt-4 grid gap-4 md:grid-cols-2 animate-floatIn">
              <div className="grid gap-2 text-sm text-white/70">
                <div>Journal mode</div>
                <Select<"WAL" | "DELETE">
                  value={sqlite.journalMode}
                  onChange={(next) => onSqliteChange({ journalMode: next })}
                  options={sqliteJournalModeOptions}
                />
              </div>

              <div className="grid gap-2 text-sm text-white/70">
                <div>Synchronous</div>
                <Select<"FULL" | "NORMAL">
                  value={sqlite.synchronous}
                  onChange={(next) => onSqliteChange({ synchronous: next })}
                  options={sqliteSynchronousOptions}
                />
              </div>

              <Field label="Busy timeout (ms)">
                <input
                  type="number"
                  value={sqlite.busyTimeoutMs}
                  onChange={(e) =>
                    onSqliteChange({ busyTimeoutMs: Number(e.target.value) })
                  }
                />
              </Field>
            </div>
          ) : null}
        </div>
      ) : null}

      {engine === "mariadb" ? (
        <div className="rounded-2xl border border-white/10 bg-black/20 p-5">
          <div className="text-sm font-semibold">MariaDB settings</div>
          <div className="mt-1 text-sm text-white/60">
            Good for multi-client use and larger systems.
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <Field
              label={
                <span>
                  Host
                  {showErrors && mariadbErrors.host ? (
                    <span className="text-red-300"> *</span>
                  ) : null}
                </span>
              }
              hint={
                showErrors && mariadbErrors.host ? "Host is required." : undefined
              }
              error={showErrors && mariadbErrors.host}
            >
              <input
                value={mariadb.host}
                onChange={(e) => onMariaChange({ host: e.target.value })}
              />
            </Field>

            <Field
              label={
                <span>
                  Port
                  {showErrors && mariadbErrors.port ? (
                    <span className="text-red-300"> *</span>
                  ) : null}
                </span>
              }
              hint={
                showErrors && mariadbErrors.port ? "Port is required." : undefined
              }
              error={showErrors && mariadbErrors.port}
            >
              <input
                type="number"
                value={mariadb.port}
                onChange={(e) => onMariaChange({ port: Number(e.target.value) })}
              />
            </Field>

            <Field
              label={
                <span>
                  Database name
                  {showErrors && mariadbErrors.name ? (
                    <span className="text-red-300"> *</span>
                  ) : null}
                </span>
              }
              hint={
                showErrors && mariadbErrors.name
                  ? "Database name is required."
                  : undefined
              }
              error={showErrors && mariadbErrors.name}
            >
              <input
                value={mariadb.name}
                onChange={(e) => onMariaChange({ name: e.target.value })}
              />
            </Field>

            <Field
              label={
                <span>
                  User
                  {showErrors && mariadbErrors.user ? (
                    <span className="text-red-300"> *</span>
                  ) : null}
                </span>
              }
              hint={
                showErrors && mariadbErrors.user ? "User is required." : undefined
              }
              error={showErrors && mariadbErrors.user}
            >
              <input
                value={mariadb.user}
                onChange={(e) => onMariaChange({ user: e.target.value })}
              />
            </Field>

            <Field
              label={
                <span>
                  Password
                  {showErrors && mariadbErrors.password ? (
                    <span className="text-red-300"> *</span>
                  ) : null}
                </span>
              }
              hint={
                showErrors && mariadbErrors.password
                  ? "Password is required."
                  : undefined
              }
              error={showErrors && mariadbErrors.password}
              className="md:col-span-2"
            >
              <input
                type="password"
                value={mariadb.password}
                onChange={(e) => onMariaChange({ password: e.target.value })}
              />
            </Field>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-4">
            <button
              type="button"
              className="rounded-full border border-ocean-500/40 bg-ocean-500/10 px-5 py-2 text-sm font-semibold transition hover:border-ocean-500/70"
            >
              Verify connection
            </button>
            <span className="text-sm text-white/60">Not connected</span>
          </div>
        </div>
      ) : null}

      {engine === "postgres" ? (
        <div className="rounded-2xl border border-white/10 bg-black/10 p-5 opacity-70">
          <div className="text-sm font-semibold">Postgres</div>
          <div className="mt-1 text-sm text-white/60">
            Planned for a later release.
          </div>
        </div>
      ) : null}
    </div>
  );
}

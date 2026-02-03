import { useCallback, useState } from "react";
import { defaultSetupDraft } from "./defaults";
import type {
  AdminSettings,
  BackupSettings,
  MariaDbSettings,
  SetupDraft,
  SqliteSettings,
  StorageEngine,
} from "./types";

export type SetupDraftActions = {
  setStorageEngine: (engine: StorageEngine) => void;
  updateAdmin: (next: Partial<AdminSettings>) => void;
  updateBackups: (next: Partial<BackupSettings>) => void;
  updateSqlite: (next: Partial<SqliteSettings>) => void;
  updateMaria: (next: Partial<MariaDbSettings>) => void;
  setDraft: (next: SetupDraft) => void;
};

export function useSetupDraft(initial: SetupDraft = defaultSetupDraft) {
  const [draft, setDraft] = useState<SetupDraft>(initial);

  const setStorageEngine = useCallback((engine: StorageEngine) => {
    setDraft((prev) => ({ ...prev, storageEngine: engine }));
  }, []);

  const updateAdmin = useCallback((next: Partial<AdminSettings>) => {
    setDraft((prev) => ({ ...prev, admin: { ...prev.admin, ...next } }));
  }, []);

  const updateBackups = useCallback((next: Partial<BackupSettings>) => {
    setDraft((prev) => ({ ...prev, backups: { ...prev.backups, ...next } }));
  }, []);

  const updateSqlite = useCallback((next: Partial<SqliteSettings>) => {
    setDraft((prev) => ({ ...prev, sqlite: { ...prev.sqlite, ...next } }));
  }, []);

  const updateMaria = useCallback((next: Partial<MariaDbSettings>) => {
    setDraft((prev) => ({ ...prev, mariadb: { ...prev.mariadb, ...next } }));
  }, []);

  return {
    draft,
    setDraft,
    setStorageEngine,
    updateAdmin,
    updateBackups,
    updateSqlite,
    updateMaria,
  } satisfies SetupDraftActions & { draft: SetupDraft };
}

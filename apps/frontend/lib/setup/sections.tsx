import AdminSection from "../../components/setup/AdminSection";
import BackupsSection from "../../components/setup/BackupsSection";
import StorageSection from "../../components/setup/StorageSection";
import type { HelpKey } from "./content";
import type { SetupDraft } from "./types";
import type { SetupDraftActions } from "./useSetupDraft";

export type SetupSectionValidation = {
  showErrors: boolean;
  admin: {
    emailValid: boolean;
    passwordSafe: boolean;
    hasError: boolean;
  };
  storage: {
    hasError: boolean;
    sqlite: {
      databaseUrl: boolean;
    };
    mariadb: {
      host: boolean;
      port: boolean;
      name: boolean;
      user: boolean;
      password: boolean;
    };
  };
  backups: {
    enabled: boolean;
    hasError: boolean;
    interval: boolean;
    retention: boolean;
    directory: boolean;
  };
};

export type SetupSectionConfig = {
  id: string;
  title: string;
  subtitle: string;
  helpKey: HelpKey;
  render: (
    draft: SetupDraft,
    actions: SetupDraftActions,
    validation: SetupSectionValidation
  ) => JSX.Element;
};

export const setupSections: Array<SetupSectionConfig> = [
  {
    id: "admin",
    title: "Admin account",
    subtitle:
      "Create the administrator account that controls devices and system settings.",
    helpKey: "admin",
    render: (draft, actions, validation) => (
      <AdminSection
        admin={draft.admin}
        onChange={actions.updateAdmin}
        showErrors={validation.showErrors}
        emailValid={validation.admin.emailValid}
        passwordSafe={validation.admin.passwordSafe}
      />
    ),
  },
  {
    id: "storage",
    title: "Database",
    subtitle:
      "Choose where data is stored. Switching database engines later is heavier once data exists.",
    helpKey: "storage",
    render: (draft, actions, validation) => (
      <StorageSection
        engine={draft.storageEngine}
        sqlite={draft.sqlite}
        mariadb={draft.mariadb}
        onEngineChange={actions.setStorageEngine}
        onSqliteChange={actions.updateSqlite}
        onMariaChange={actions.updateMaria}
        showErrors={validation.showErrors}
        sqliteErrors={validation.storage.sqlite}
        mariadbErrors={validation.storage.mariadb}
      />
    ),
  },
  {
    id: "backups",
    title: "Backups",
    subtitle:
      "Recommended for SQLite deployments. Configure retention so backups do not grow forever.",
    helpKey: "backups",
    render: (draft, actions, validation) => (
      <BackupsSection
        backups={draft.backups}
        onChange={actions.updateBackups}
        showErrors={validation.showErrors}
        errors={{
          interval: validation.backups.interval,
          retention: validation.backups.retention,
          directory: validation.backups.directory,
        }}
      />
    ),
  },
];

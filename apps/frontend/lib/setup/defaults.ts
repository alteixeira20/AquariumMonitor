import type { SetupDraft } from "./types";

export const defaultSetupDraft: SetupDraft = {
  storageEngine: "sqlite",
  sqlite: {
    databaseUrl: "sqlite:///./data/app.db",
    journalMode: "WAL",
    synchronous: "FULL",
    busyTimeoutMs: 5000,
  },
  mariadb: {
    host: "localhost",
    port: 3306,
    name: "aquarium",
    user: "aquarium_app",
    password: "",
  },
  backups: {
    enabled: true,
    intervalHours: 6,
    retentionDays: 7,
    directory: "backups",
  },
  admin: {
    email: "",
    password: "",
    demoEnabled: true,
  },
};

export type StorageEngine = "sqlite" | "mariadb" | "postgres";

export type SqliteSettings = {
  databaseUrl: string;
  journalMode: "WAL" | "DELETE";
  synchronous: "FULL" | "NORMAL";
  busyTimeoutMs: number;
};

export type MariaDbSettings = {
  host: string;
  port: number;
  name: string;
  user: string;
  password: string;
};

export type BackupSettings = {
  enabled: boolean;
  intervalHours: number;
  retentionDays: number;
  directory: string;
};

export type AdminSettings = {
  email: string;
  password: string;
  demoEnabled: boolean;
};

export type SetupDraft = {
  storageEngine: StorageEngine;
  sqlite: SqliteSettings;
  mariadb: MariaDbSettings;
  backups: BackupSettings;
  admin: AdminSettings;
};

export type HelpKey = "storage" | "backups" | "admin";

export const helpContent: Record<HelpKey, { title: string; content: string }> =
  {
  storage: {
    title: "Database engine",
    content:
      "SQLite is the default for single-node setups and runs well on small hardware. MariaDB is ideal if you expect multiple clients or higher write volume. Choose now because database migrations are heavier once data exists.",
  },
    backups: {
      title: "Backups",
      content:
        "Backups are recommended for SQLite. Interval controls how often snapshots are taken, and retention keeps only the most recent days. The backup directory stays inside the backend data volume unless you change it.",
    },
    admin: {
      title: "Admin account",
      content:
        "Create the administrator account that controls device settings. Demo access is optional and read-only, so visitors can view dashboards without editing anything.",
    },
  };

import type { SelectOption } from "../../components/ui/Select";
import type { StorageEngine } from "./types";

export const storageEngineOptions: Array<SelectOption<StorageEngine>> = [
  {
    value: "sqlite",
    label: "SQLite (recommended)",
    hint: "Fast, reliable, perfect for single-node",
  },
  {
    value: "mariadb",
    label: "MariaDB",
    hint: "Better concurrency for multi-client setups",
  },
  {
    value: "postgres",
    label: "Postgres (coming soon)",
    hint: "Planned for a later release",
    disabled: true,
  },
];

export const sqliteJournalModeOptions: Array<SelectOption<"WAL" | "DELETE">> = [
  {
    value: "WAL",
    label: "WAL (recommended)",
    hint: "Best durability and performance",
  },
  {
    value: "DELETE",
    label: "DELETE",
    hint: "Legacy mode, simpler but slower",
  },
];

export const sqliteSynchronousOptions: Array<SelectOption<"FULL" | "NORMAL">> =
  [
    {
      value: "FULL",
      label: "FULL (recommended)",
      hint: "Safest writes, slower",
    },
    {
      value: "NORMAL",
      label: "NORMAL",
      hint: "Faster writes, slightly less durable",
    },
  ];

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import StatusBadge from "../ui/StatusBadge";

export default function TopNav() {
  const pathname = usePathname();
  const links = [
    { label: "Overview", href: "/dashboard" },
    { label: "Aquariums", href: "/dashboard/aquariums" },
    { label: "Devices", href: "/dashboard/devices", disabled: true },
    { label: "Alerts", href: "/dashboard/alerts", disabled: true },
    { label: "Settings", href: "/dashboard/settings", disabled: true },
  ];

  return (
    <aside className="sticky top-12 w-64 shrink-0 border-r-2 border-white/5 px-5 pb-6">
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-ocean-700 to-ocean-500 shadow-glow" />
        <div>
          <div className="font-display text-2xl">AquariumMonitor</div>
          <div className="text-base uppercase tracking-[0.3em] text-white/50">
            Dashboard
          </div>
        </div>
      </div>

      <nav className="mt-8 grid gap-2">
        {links.map((item) => {
          const isActive =
            item.href === "/dashboard"
              ? pathname === item.href
              : pathname.startsWith(item.href);
          const classes = [
            "relative w-full rounded-2xl px-4 py-3 text-center text-lg font-semibold transition",
            isActive ? "text-ocean-300" : "text-white/70 hover:text-white",
            item.disabled ? "cursor-not-allowed opacity-50" : "",
          ].join(" ");

          return item.disabled ? (
            <span key={item.label} className={classes}>
              {item.label}
              <span className="pointer-events-none absolute bottom-2 left-4 right-4 h-[2px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            </span>
          ) : (
            <Link key={item.label} href={item.href} className={classes}>
              {item.label}
              <span
                className={[
                  "pointer-events-none absolute bottom-2 left-4 right-4 h-[2px] bg-gradient-to-r",
                  isActive
                    ? "from-transparent via-ocean-500/60 to-transparent"
                    : "from-transparent via-white/10 to-transparent",
                ].join(" ")}
              />
            </Link>
          );
        })}
      </nav>

      <div className="mt-10 flex flex-col gap-0">
        <button
          type="button"
          className="w-full rounded-2xl px-4 py-2 text-center text-lg font-semibold text-white/80 transition hover:text-white"
        >
          Account
        </button>
        <button
          type="button"
          disabled
          className="w-full rounded-2xl px-4 py-2 text-center text-lg font-semibold text-white/40 opacity-60"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}

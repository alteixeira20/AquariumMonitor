"use client";

import type React from "react";
import { useEffect, useMemo, useRef, useState } from "react";

export type SelectOption<T extends string> = {
  value: T;
  label: string;
  disabled?: boolean;
  hint?: string;
};

type Props<T extends string> = {
  label?: string;
  value: T;
  options: Array<SelectOption<T>>;
  onChange: (value: T) => void;
  className?: string;
};

export default function Select<T extends string>({
  label,
  value,
  options,
  onChange,
  className,
}: Props<T>) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number>(() => {
    const idx = options.findIndex((o) => o.value === value);
    return idx >= 0 ? idx : 0;
  });

  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);

  const selected = useMemo(
    () => options.find((o) => o.value === value) ?? options[0],
    [options, value]
  );

  useEffect(() => {
    function onDocMouseDown(e: MouseEvent) {
      if (!open) return;
      const target = e.target as Node;
      if (buttonRef.current?.contains(target)) return;
      if (listRef.current?.contains(target)) return;
      setOpen(false);
    }

    function onDocKeyDown(e: KeyboardEvent) {
      if (!open) return;
      if (e.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onDocMouseDown);
    document.addEventListener("keydown", onDocKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      document.removeEventListener("keydown", onDocKeyDown);
    };
  }, [open]);

  function openMenu() {
    setOpen(true);
    const idx = options.findIndex((o) => o.value === value);
    setActiveIndex(idx >= 0 ? idx : 0);
    requestAnimationFrame(() => listRef.current?.focus());
  }

  function commit(idx: number) {
    const opt = options[idx];
    if (!opt || opt.disabled) return;
    onChange(opt.value);
    setOpen(false);
    buttonRef.current?.focus();
  }

  function onButtonKeyDown(e: React.KeyboardEvent<HTMLButtonElement>) {
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      open ? setOpen(false) : openMenu();
    }
  }

  function onListKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, options.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Home") {
      e.preventDefault();
      setActiveIndex(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setActiveIndex(options.length - 1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      commit(activeIndex);
    }
  }

  return (
    <div className={className}>
      {label ? (
        <div className="mb-2 text-sm font-semibold text-white/80">{label}</div>
      ) : null}

      <div className="relative">
        <button
          ref={buttonRef}
          type="button"
          onClick={() => (open ? setOpen(false) : openMenu())}
          onKeyDown={onButtonKeyDown}
          aria-haspopup="listbox"
          aria-expanded={open}
          className={[
            "w-full text-left text-sm",
            "rounded-2xl border border-white/10",
            "bg-ocean-850/50 backdrop-blur",
            "px-4 py-3",
            "text-white/90",
            "shadow-sm",
            "transition",
            "hover:border-ocean-500/40 hover:shadow-glow",
            "focus:outline-none focus:ring-2 focus:ring-ocean-500/20 focus:border-ocean-500/60",
          ].join(" ")}
        >
          <span className="flex items-center justify-between gap-3">
            <span className="truncate">{selected?.label}</span>

            <span className="text-white/60">
              <svg
                width="18"
                height="18"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
                className={open ? "rotate-180 transition" : "transition"}
              >
                <path
                  fillRule="evenodd"
                  d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 1 1 1.06 1.06l-4.24 4.24a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08Z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
          </span>
        </button>

        {open ? (
          <div
            ref={listRef}
            tabIndex={-1}
            role="listbox"
            aria-activedescendant={`opt-${activeIndex}`}
            onKeyDown={onListKeyDown}
            className={[
              "absolute z-50 mt-2 w-full overflow-hidden rounded-2xl",
              "border border-white/10",
              "bg-ocean-800/92 backdrop-blur",
              "shadow-ocean",
              "outline-none",
              "animate-floatIn",
            ].join(" ")}
          >
            <div className="max-h-64 overflow-auto p-1.5">
              {options.map((opt, idx) => {
                const isSelected = opt.value === value;
                const isActive = idx === activeIndex;

                return (
                  <button
                    key={opt.value}
                    id={`opt-${idx}`}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    disabled={opt.disabled}
                    onMouseEnter={() => setActiveIndex(idx)}
                    onClick={() => commit(idx)}
                    className={[
                      "w-full rounded-xl px-3 py-2.5 text-left text-sm",
                      "transition",
                      opt.disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
                      isActive && !opt.disabled ? "bg-ocean-500/18 shadow-glow" : "bg-transparent",
                      !opt.disabled ? "hover:bg-ocean-500/18 hover:shadow-glow" : "",
                      isSelected ? "text-ocean-300" : "text-white/90",
                      "flex items-center justify-between gap-3",
                    ].join(" ")}
                  >
                    <span className="min-w-0">
                      <span className="block truncate">{opt.label}</span>
                      {opt.hint ? (
                        <span className="block text-xs text-white/55 truncate">
                          {opt.hint}
                        </span>
                      ) : null}
                    </span>

                    {isSelected ? (
                      <span className="text-ocean-400">
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          aria-hidden="true"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.704 5.29a1 1 0 0 1 .006 1.414l-7.5 7.57a1 1 0 0 1-1.42 0l-3.5-3.536a1 1 0 1 1 1.42-1.407l2.79 2.82 6.79-6.86a1 1 0 0 1 1.414-.006Z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

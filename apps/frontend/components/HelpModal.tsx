"use client";

import { ReactNode } from "react";

interface HelpModalProps {
  title: string;
  content: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function HelpModal({
  title,
  content,
  isOpen,
  onClose,
}: HelpModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-ocean-950/80"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <div
        className="glass-panel w-[min(420px,90vw)] animate-floatIn p-5"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-semibold">{title}</span>
          <button
            type="button"
            onClick={onClose}
            className="text-xl text-white/50 transition hover:text-white"
          >
            ×
          </button>
        </div>
        <p className="text-sm leading-relaxed text-white/70">{content}</p>
      </div>
    </div>
  );
}

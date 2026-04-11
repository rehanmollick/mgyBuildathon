"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs: ReadonlyArray<{ href: string; label: string }> = [
  { href: "/", label: "Forge" },
  { href: "/evolve", label: "Evolve" },
];

export function TabNav(): JSX.Element {
  const pathname = usePathname();
  return (
    <nav className="mb-6 flex items-center justify-between border-b border-bg-border pb-4">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold tracking-tight">
          Quant<span className="text-profit">Forge</span>
        </span>
        <span className="text-xs text-muted">stress testing, not storytelling</span>
      </div>
      <div className="flex gap-2">
        {tabs.map((tab) => {
          const active = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href as "/" | "/evolve"}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                active ? "bg-bg-card text-profit" : "text-muted hover:bg-bg-hover hover:text-white"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

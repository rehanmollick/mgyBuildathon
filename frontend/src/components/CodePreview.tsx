"use client";

import { useState } from "react";

export interface CodePreviewProps {
  readonly code: string;
}

export function CodePreview({ code }: CodePreviewProps): JSX.Element {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  return (
    <section className="animate-fade-in rounded-lg border border-bg-border bg-bg-card">
      <header className="flex items-center justify-between border-b border-bg-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">Generated strategy</h2>
          <p className="text-xs text-muted">Parsed by Claude, validated at the AST level</p>
        </div>
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className="text-xs text-muted hover:text-white"
        >
          {collapsed ? "Show" : "Hide"}
        </button>
      </header>
      {!collapsed && (
        <pre className="scrollbar-thin max-h-80 overflow-auto px-4 py-3 font-mono text-xs leading-relaxed text-muted">
          <code>{code}</code>
        </pre>
      )}
    </section>
  );
}

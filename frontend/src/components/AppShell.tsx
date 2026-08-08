/**
 * Application chrome: wordmark, navigation and the permanent disclaimer.
 *
 * The disclaimer is part of the shell rather than of any page because it must
 * be visible everywhere and cannot be dismissed. Its height is reserved with
 * bottom padding on the main column so it never covers content.
 */

import type { ReactNode } from "react";

export type PageId = "builder" | "catalog" | "equipment" | "settings";

const NAV: { id: PageId; label: string }[] = [
  { id: "builder", label: "Treinos" },
  { id: "catalog", label: "Exercícios" },
  { id: "equipment", label: "Equipamento" },
  { id: "settings", label: "Garmin" },
];

export function AppShell({
  page,
  onNavigate,
  children,
}: {
  page: PageId;
  onNavigate: (page: PageId) => void;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <header
        className="sticky top-0 z-20"
        style={{ background: "var(--bg)", borderBottom: "1px solid var(--border)" }}
      >
        <div className="mx-auto w-full max-w-6xl px-6 py-6 flex flex-wrap items-baseline gap-x-6 gap-y-3">
          <span className="myo-display" style={{ fontSize: "var(--text-32)" }}>
            MyoFit
          </span>
          <nav className="flex flex-wrap gap-2 ml-auto">
            {NAV.map((item) => (
              <button
                key={item.id}
                type="button"
                className="myo-btn"
                aria-current={page === item.id ? "page" : undefined}
                style={
                  page === item.id
                    ? {
                        background: "var(--surface-hover)",
                        borderColor: "var(--border-hover)",
                      }
                    : undefined
                }
                onClick={() => onNavigate(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-6xl px-6 pt-12 pb-24">{children}</main>

      <footer
        className="sticky bottom-0 z-20"
        style={{ background: "var(--bg)", borderTop: "1px solid var(--border)" }}
      >
        <p
          className="mx-auto w-full max-w-6xl px-6 py-3"
          style={{ fontSize: "var(--text-12)", color: "var(--muted)" }}
        >
          O MyoFit tem finalidade didática. Treinos, cargas e seleção de
          exercícios devem ter acompanhamento de profissional qualificado.
        </p>
      </footer>
    </div>
  );
}

/** Section title. The only place the display weight is used. */
export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h2 className="myo-display mb-6" style={{ fontSize: "var(--text-32)" }}>
      {children}
    </h2>
  );
}

export function Notice({ kind, children }: { kind: "error" | "info"; children: ReactNode }) {
  return (
    <p
      className="myo-card px-4 py-3 mb-6"
      style={{
        fontSize: "var(--text-13)",
        borderColor: kind === "error" ? "var(--status-critical)" : "var(--border)",
        color: kind === "error" ? "var(--status-critical)" : "var(--muted)",
      }}
      role={kind === "error" ? "alert" : undefined}
    >
      {children}
    </p>
  );
}

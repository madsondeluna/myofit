/**
 * Application chrome: wordmark, navigation and the permanent disclaimer.
 *
 * The disclaimer is part of the shell rather than of any page because it must
 * be visible everywhere and cannot be dismissed. Its height is reserved with
 * bottom padding on the main column so it never covers content.
 */

import type { ReactNode } from "react";

export type PageId = "builder" | "catalog" | "equipment" | "settings";

/** The page the wordmark returns to. */
export const HOME_PAGE: PageId = "builder";

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
      <header className="glass glass-deep myo-bar sticky top-0 z-20">
        <div className="mx-auto w-full max-w-6xl px-6 py-6 flex flex-col sm:flex-row sm:items-center gap-6">
          {/* The wordmark is the way home. A button rather than a link because
              navigation here is state, not a URL. */}
          <button
            type="button"
            className="myo-home myo-display self-start"
            style={{ fontSize: "var(--text-24)" }}
            onClick={() => onNavigate(HOME_PAGE)}
            aria-label="MyoFit, voltar ao início"
          >
            MyoFit
          </button>

          {/* A rail rather than a wrapping row: on a phone four pills do not
              fit on one line, and wrapping them pushes the page down. */}
          <nav className="myo-rail sm:ml-auto">
            {NAV.map((item) => (
              <button
                key={item.id}
                type="button"
                className="pill glass-lift"
                aria-current={page === item.id ? "page" : undefined}
                onClick={() => onNavigate(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-6xl px-6 pt-12 pb-24">{children}</main>

      <footer className="glass glass-deep myo-bar sticky bottom-0 z-20">
        <p
          className="mx-auto w-full max-w-6xl px-6 py-3 text-center"
          style={{ fontSize: "var(--text-12)" }}
        >
          O MyoFit tem finalidade didática. Treinos, cargas e seleção de
          exercícios devem ter acompanhamento de profissional qualificado.
        </p>
      </footer>
    </div>
  );
}

/**
 * Section title with the hairline rule under it. Uses Prussian's
 * .section-header so every screen opens with the same spacing.
 */
export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <header className="section-header">
      <h2 className="myo-display" style={{ fontSize: "var(--text-32)" }}>
        {children}
      </h2>
    </header>
  );
}

export function Notice({ kind, children }: { kind: "error" | "info"; children: ReactNode }) {
  return (
    <p
      className="card-glass glass-lift myo-card px-6 py-3 mb-12"
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

/**
 * The six-dot grip that marks a reorderable row. Drawn rather than labelled:
 * the word "arrastar" named the gesture without saying what the control did.
 */
export function GripIcon() {
  return (
    <svg width="10" height="16" viewBox="0 0 10 16" aria-hidden="true" focusable="false">
      {[3, 8, 13].map((y) =>
        [2, 8].map((x) => <circle key={`${x}-${y}`} cx={x} cy={y} r="1.4" fill="currentColor" />),
      )}
    </svg>
  );
}

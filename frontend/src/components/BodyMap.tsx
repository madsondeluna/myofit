/**
 * Interactive body map.
 *
 * Two modes share one renderer:
 *   - highlight: a single exercise, primary muscles saturated and secondary
 *     muscles a lighter step of the same ramp.
 *   - heat: a whole workout, each muscle taking a ramp step from its
 *     normalised intensity.
 *
 * Colours come from the --heat-* aliases in index.css, a cool-to-warm ramp
 * built on Prussian's diverging palette where --heat-7 is the most worked step. Interface colours are never used here: a muscle must not read as a
 * focus ring, and a focus ring must not read as a worked muscle.
 */

import { useId, useState } from "react";
import type { MuscleId, MuscleLoad, ViewId } from "../api";
import { muscleLabel } from "../api";
// Geometry, mirror transform and canvas all come from the figure module, so a
// change to the drawing cannot leave the renderer on a stale viewBox.
import { BASE_HALF, HEAD, MIRROR, MUSCLES_BY_VIEW, VIEW_BOX } from "./figures";

/** Ramp step for a primary target and for a supporting one. */
const PRIMARY_STEP = 7;
const SECONDARY_STEP = 3;

export interface BodyMapProps {
  /** Muscles worked as the main target of the current selection. */
  primary?: MuscleId[];
  /** Muscles assisting the current selection. */
  secondary?: MuscleId[];
  /** Aggregated load; when present it overrides primary/secondary. */
  load?: MuscleLoad[];
  /** Called when a muscle is clicked, for catalog filtering. */
  onSelect?: (muscle: MuscleId) => void;
  /** Muscle currently used as a catalog filter. */
  selected?: MuscleId | null;
}

/** Map a 0..1 intensity onto the seven discrete ramp steps.
 *
 * Discrete rather than interpolated: the ramp was validated as seven steps,
 * and mixing between them would produce colours nobody checked. */
function stepForIntensity(intensity: number): number {
  if (intensity <= 0) return 0;
  return Math.min(7, Math.max(1, Math.ceil(intensity * 7)));
}

function buildFills(
  primary: MuscleId[],
  secondary: MuscleId[],
  load: MuscleLoad[] | undefined,
): Map<MuscleId, number> {
  const fills = new Map<MuscleId, number>();

  if (load && load.length > 0) {
    for (const entry of load) {
      const step = stepForIntensity(entry.intensity);
      if (step > 0) fills.set(entry.muscle, step);
    }
    return fills;
  }

  for (const muscle of secondary) fills.set(muscle, SECONDARY_STEP);
  // Primary is applied second so an exercise listing a muscle in both places
  // still renders it at full strength.
  for (const muscle of primary) fills.set(muscle, PRIMARY_STEP);
  return fills;
}

interface FigureProps {
  view: ViewId;
  fills: Map<MuscleId, number>;
  onSelect?: (muscle: MuscleId) => void;
  selected?: MuscleId | null;
  titleId: string;
}

function Figure({ view, fills, onSelect, selected, titleId }: FigureProps) {
  const muscles = MUSCLES_BY_VIEW[view];

  return (
    <svg
      viewBox={`0 0 ${VIEW_BOX.width} ${VIEW_BOX.height}`}
      className="myo-figure w-full h-auto"
      role="img"
      aria-labelledby={titleId}
      preserveAspectRatio="xMidYMid meet"
    >
      <title id={titleId}>
        {view === "front" ? "Mapa corporal, vista frontal" : "Mapa corporal, vista posterior"}
      </title>

      {/* Silhouette. Drawn first so muscle shapes sit on top of it. */}
      <g className="myo-base">
        <ellipse cx={HEAD.cx} cy={HEAD.cy} rx={HEAD.rx} ry={HEAD.ry} />
        {BASE_HALF.map((d, index) => (
          <g key={index}>
            <path d={d} />
            <path d={d} transform={MIRROR} />
          </g>
        ))}
      </g>

      {/* Muscle groups. The id carries the muscle enum value; the test suite
          asserts every taxonomy member has a path here in each view it claims. */}
      {(Object.entries(muscles) as [MuscleId, string][]).map(([muscle, d]) => {
        const step = fills.get(muscle) ?? 0;
        const interactive = Boolean(onSelect);
        return (
          <g
            key={muscle}
            id={`${view}-${muscle}`}
            data-muscle={muscle}
            className={`myo-muscle${interactive ? " is-interactive" : ""}`}
            style={step > 0 ? { fill: `var(--heat-${step})` } : undefined}
            stroke={selected === muscle ? "var(--text)" : undefined}
            strokeWidth={selected === muscle ? 1.6 : undefined}
            onClick={interactive ? () => onSelect?.(muscle) : undefined}
            role={interactive ? "button" : undefined}
            tabIndex={interactive ? 0 : undefined}
            aria-label={interactive ? muscleLabel(muscle) : undefined}
            onKeyDown={
              interactive
                ? (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect?.(muscle);
                    }
                  }
                : undefined
            }
          >
            <title>{muscleLabel(muscle)}</title>
            <path d={d} />
            <path d={d} transform={MIRROR} />
          </g>
        );
      })}
    </svg>
  );
}

export function BodyMap({
  primary = [],
  secondary = [],
  load,
  onSelect,
  selected = null,
}: BodyMapProps) {
  // On a phone the two figures cannot sit side by side, so the narrow layout
  // shows one at a time behind this toggle. On a wide viewport both render and
  // the toggle is hidden.
  const [view, setView] = useState<ViewId>("front");
  const baseId = useId();
  const fills = buildFills(primary, secondary, load);

  return (
    <div>
      <div className="flex gap-2 sm:hidden mb-6">
        {(["front", "back"] as ViewId[]).map((candidate) => (
          <button
            key={candidate}
            type="button"
            className="myo-btn flex-1"
            aria-pressed={view === candidate}
            style={
              view === candidate
                ? { background: "var(--surface-hover)", borderColor: "var(--border-hover)" }
                : undefined
            }
            onClick={() => setView(candidate)}
          >
            {candidate === "front" ? "Frente" : "Costas"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div className={view === "front" ? "" : "hidden sm:block"}>
          <Figure
            view="front"
            fills={fills}
            onSelect={onSelect}
            selected={selected}
            titleId={`${baseId}-front`}
          />
        </div>
        <div className={view === "back" ? "" : "hidden sm:block"}>
          <Figure
            view="back"
            fills={fills}
            onSelect={onSelect}
            selected={selected}
            titleId={`${baseId}-back`}
          />
        </div>
      </div>
    </div>
  );
}

/** Ramp legend. Shown under the aggregate map so the steps are readable. */
export function HeatLegend() {
  return (
    <div className="flex items-center gap-3 mt-6">
      <span className="myo-eyebrow">Menos</span>
      <div className="flex flex-1 h-2 max-w-40">
        {[1, 2, 3, 4, 5, 6, 7].map((step) => (
          <div key={step} className="flex-1" style={{ background: `var(--heat-${step})` }} />
        ))}
      </div>
      <span className="myo-eyebrow">Mais</span>
    </div>
  );
}

/**
 * Catalog browser. The catalog holds ~1850 exercises derived from the FIT SDK,
 * so it is always filtered and paginated; hovering a row previews its muscles
 * on the body map.
 */

import { useEffect, useMemo, useState } from "react";
import type { Exercise, Facets, MuscleId } from "../api";
import { api, muscleLabel } from "../api";
import { BodyMap } from "./BodyMap";
import { Notice, SectionTitle } from "./AppShell";

const PAGE_SIZE = 25;

function label(value: string): string {
  const spaced = value.replace(/_/g, " ").toLowerCase();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function ExerciseCatalog({
  facets,
  onAdd,
}: {
  facets: Facets | null;
  onAdd?: (exercise: Exercise) => void;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [equipment, setEquipment] = useState("");
  const [muscle, setMuscle] = useState<MuscleId | "">("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<{ items: Exercise[]; total: number } | null>(null);
  const [hovered, setHovered] = useState<Exercise | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Debounced so typing in the search box does not fire a request per keystroke.
  useEffect(() => {
    const handle = window.setTimeout(() => {
      setLoading(true);
      api
        .exercises({ q: query, category, equipment, muscle, offset, limit: PAGE_SIZE })
        .then((result) => {
          setPage({ items: result.items, total: result.total });
          setError(null);
        })
        .catch((err: Error) => setError(err.message))
        .finally(() => setLoading(false));
    }, 200);
    return () => window.clearTimeout(handle);
  }, [query, category, equipment, muscle, offset]);

  // Any filter change returns to the first page; keeping the offset would show
  // an empty page whenever the new result set is smaller.
  useEffect(() => setOffset(0), [query, category, equipment, muscle]);

  const preview = hovered;
  const total = page?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  const muscles = useMemo(() => facets?.muscles.map((entry) => entry.id) ?? [], [facets]);

  return (
    <section>
      <SectionTitle>Exercise catalog</SectionTitle>
      {error && <Notice kind="error">{error}</Notice>}

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-12">
        <div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
            <label className="block">
              <span className="myo-eyebrow block mb-2">Search</span>
              <input
                className="myo-field"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Bench press"
              />
            </label>
            <label className="block">
              <span className="myo-eyebrow block mb-2">Category</span>
              <select
                className="myo-field"
                value={category}
                onChange={(event) => setCategory(event.target.value)}
              >
                <option value="">All categories</option>
                {facets?.categories.map((item) => (
                  <option key={item} value={item}>
                    {label(item)}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="myo-eyebrow block mb-2">Equipment</span>
              <select
                className="myo-field"
                value={equipment}
                onChange={(event) => setEquipment(event.target.value)}
              >
                <option value="">Any equipment</option>
                {facets?.equipment.map((item) => (
                  <option key={item} value={item}>
                    {label(item)}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="myo-eyebrow block mb-2">Muscle</span>
              <select
                className="myo-field"
                value={muscle}
                onChange={(event) => setMuscle(event.target.value as MuscleId | "")}
              >
                <option value="">Any muscle</option>
                {muscles.map((item) => (
                  <option key={item} value={item}>
                    {muscleLabel(item)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <p className="myo-eyebrow mb-6">
            {loading ? "Loading" : `${total} exercises`}
          </p>

          <ul className="myo-card divide-y" style={{ borderColor: "var(--border)" }}>
            {page?.items.map((exercise) => (
              <li
                key={exercise.id}
                className="px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-2"
                style={{ borderColor: "var(--border)" }}
                onMouseEnter={() => setHovered(exercise)}
                onFocus={() => setHovered(exercise)}
              >
                <div className="min-w-0 flex-1">
                  <p style={{ fontSize: "var(--text-15)" }}>{exercise.display_name}</p>
                  <p className="myo-mono" style={{ color: "var(--muted)" }}>
                    {exercise.garmin_category} / {exercise.garmin_exercise_name}
                  </p>
                  <p className="myo-mono mt-1" style={{ color: "var(--muted)" }}>
                    {exercise.primary_muscles.map(muscleLabel).join(", ") || "No muscle data"}
                    {exercise.is_compound ? " · compound" : ""}
                  </p>
                </div>
                {onAdd && (
                  <button type="button" className="myo-btn" onClick={() => onAdd(exercise)}>
                    Add
                  </button>
                )}
              </li>
            ))}
            {page?.items.length === 0 && (
              <li className="px-4 py-6" style={{ color: "var(--muted)" }}>
                No exercise matches these filters.
              </li>
            )}
          </ul>

          <div className="flex items-center gap-4 mt-6">
            <button
              type="button"
              className="myo-btn"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Previous
            </button>
            <span className="myo-mono" style={{ color: "var(--muted)" }}>
              {currentPage} / {pageCount}
            </span>
            <button
              type="button"
              className="myo-btn"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </div>

        <aside>
          <p className="myo-eyebrow mb-6">
            {preview ? preview.display_name : "Hover an exercise"}
          </p>
          <BodyMap
            primary={preview?.primary_muscles ?? []}
            secondary={preview?.secondary_muscles ?? []}
            onSelect={(item) => setMuscle(item)}
            selected={muscle || null}
          />
          {preview && (
            <dl className="mt-6" style={{ fontSize: "var(--text-13)" }}>
              <dt className="myo-eyebrow">Primary</dt>
              <dd className="mb-3">
                {preview.primary_muscles.map(muscleLabel).join(", ") || "None"}
              </dd>
              <dt className="myo-eyebrow">Secondary</dt>
              <dd>{preview.secondary_muscles.map(muscleLabel).join(", ") || "None"}</dd>
            </dl>
          )}
        </aside>
      </div>
    </section>
  );
}

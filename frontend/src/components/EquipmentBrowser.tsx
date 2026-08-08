/**
 * "What can I train with this?"
 *
 * Pick a piece of equipment and see every muscle the catalog can reach with
 * it, aggregated onto the body map, plus the exercises behind that coverage.
 * The aggregation is done client side because it summarises the catalog, not a
 * workout: there are no sets to weight it by.
 */

import { useEffect, useMemo, useState } from "react";
import type { Exercise, Facets, MuscleId, MuscleLoad } from "../api";
import { api, equipmentLabel, muscleLabel } from "../api";
import { BodyMap, HeatLegend } from "./BodyMap";
import { Notice, SectionTitle } from "./AppShell";

/** Same weighting the backend uses for workouts, so the two maps read alike. */
const SECONDARY_WEIGHT = 0.5;

/** Count how many catalog exercises reach each muscle with this equipment. */
function aggregate(exercises: Exercise[]): MuscleLoad[] {
  const scores = new Map<MuscleId, number>();
  const primary = new Map<MuscleId, number>();
  const secondary = new Map<MuscleId, number>();

  for (const exercise of exercises) {
    for (const muscle of exercise.primary_muscles) {
      scores.set(muscle, (scores.get(muscle) ?? 0) + 1);
      primary.set(muscle, (primary.get(muscle) ?? 0) + 1);
    }
    for (const muscle of exercise.secondary_muscles) {
      scores.set(muscle, (scores.get(muscle) ?? 0) + SECONDARY_WEIGHT);
      secondary.set(muscle, (secondary.get(muscle) ?? 0) + 1);
    }
  }

  const peak = Math.max(0, ...scores.values());
  return [...scores.entries()]
    .map(([muscle, score]) => ({
      muscle,
      score: Math.round(score * 100) / 100,
      primary_count: primary.get(muscle) ?? 0,
      secondary_count: secondary.get(muscle) ?? 0,
      intensity: peak > 0 ? score / peak : 0,
    }))
    .sort((a, b) => b.score - a.score || a.muscle.localeCompare(b.muscle));
}

export function EquipmentBrowser({ facets }: { facets: Facets | null }) {
  const [equipment, setEquipment] = useState("");
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!equipment) {
      setExercises([]);
      return;
    }
    setLoading(true);
    // 200 is the API's page cap; it is enough to characterise the coverage of
    // one equipment type, and the count below reports the true total.
    api
      .exercises({ equipment, limit: 200 })
      .then((page) => {
        setExercises(page.items);
        setTotal(page.total);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [equipment]);

  const load = useMemo(() => aggregate(exercises), [exercises]);
  const compound = exercises.filter((item) => item.is_compound);

  return (
    <section>
      <SectionTitle>Treine com o que você tem</SectionTitle>
      <p className="prose prose-justify mb-12">
        Escolha um equipamento para ver quais grupos musculares o catálogo
        alcança com ele.
      </p>

      {error && <Notice kind="error">{error}</Notice>}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-7">
          <div className="myo-rail mb-12">
            {facets?.equipment.map((item) => (
              <button
                key={item}
                type="button"
                className="pill glass-lift"
                aria-pressed={equipment === item}
                onClick={() => setEquipment(equipment === item ? "" : item)}
              >
                {equipmentLabel(item)}
              </button>
            ))}
          </div>

          {equipment && (
            <>
              <p className="eyebrow mb-6">
                {loading
                  ? "Carregando"
                  : `${total} exercícios, ${compound.length} compostos entre os ${exercises.length} analisados`}
              </p>
              <ul className="card-glass glass-lift myo-card divide-y" style={{ borderColor: "var(--border)" }}>
                {exercises.slice(0, 40).map((exercise) => (
                  <li key={exercise.id} className="px-4 py-3">
                    <p style={{ fontSize: "var(--text-15)" }}>{exercise.display_name}</p>
                    <p className="mono" style={{ color: "var(--muted)", fontSize: "var(--text-12)" }}>
                      {exercise.primary_muscles.map(muscleLabel).join(", ") || "Sem dados musculares"}
                    </p>
                  </li>
                ))}
              </ul>
              {exercises.length > 40 && (
                <p className="eyebrow mt-6">
                  Mostrando os 40 primeiros. Use o catálogo para filtrar mais.
                </p>
              )}
            </>
          )}
        </div>

        <aside className="card-glass glass-lift myo-card lg:col-span-4 lg:col-start-9 p-6 self-start">
          <p className="eyebrow mb-6">
            {equipment ? `Cobertura: ${equipmentLabel(equipment)}` : "Escolha um equipamento"}
          </p>
          <BodyMap load={load} />
          <HeatLegend />
        </aside>
      </div>
    </section>
  );
}

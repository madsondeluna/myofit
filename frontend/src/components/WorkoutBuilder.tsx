/**
 * Workout builder: create, edit, reorder, export and sync.
 *
 * The exercise list is held in local state and written whole on save. The API
 * derives position from list order, so drag and drop only has to reorder the
 * array; there is no separate position bookkeeping to keep in sync.
 */

import { useEffect, useState } from "react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import type { Exercise, Facets, Workout, WorkoutSummary } from "../api";
import { DEFAULT_PRESCRIPTION, api, muscleLabel } from "../api";
import { BodyMap, HeatLegend } from "./BodyMap";
import { ExerciseCatalog } from "./ExerciseCatalog";
import { GripIcon, Notice, SectionTitle } from "./AppShell";

/** One row of the editable list, before it is sent to the API. */
interface DraftEntry {
  /** Stable key for drag and drop; not the database id. */
  key: string;
  exercise: Exercise;
  sets: number;
  reps: number;
  rest_seconds: number;
  load_kg: number | null;
}

let keyCounter = 0;
const nextKey = () => `entry-${keyCounter++}`;

function toDraft(workout: Workout): DraftEntry[] {
  return workout.exercises.map((entry) => ({
    key: nextKey(),
    exercise: entry.exercise,
    sets: entry.sets,
    reps: entry.reps,
    rest_seconds: entry.rest_seconds,
    load_kg: entry.load_kg,
  }));
}

function SortableRow({
  entry,
  position,
  onChange,
  onRemove,
  warning,
}: {
  entry: DraftEntry;
  /** One-based place in the list, shown so the order is readable at rest. */
  position: number;
  onChange: (patch: Partial<DraftEntry>) => void;
  onRemove: () => void;
  warning?: string;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: entry.key,
  });

  return (
    <li
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.6 : 1,
        borderColor: "var(--border)",
      }}
      className="px-4 py-4 border-b"
    >
      <div className="flex flex-wrap items-start gap-x-4 gap-y-2">
        {/* Grip, with the purpose in the accessible name and the tooltip.
            The previous label said "arrastar", which named the gesture but
            not what dragging would accomplish. */}
        <button
          type="button"
          className="pill glass-lift myo-grip"
          aria-label={`Mudar a ordem de ${entry.exercise.display_name}`}
          title="Arraste para mudar a ordem"
          {...attributes}
          {...listeners}
        >
          <GripIcon />
        </button>
        <div className="min-w-0 flex-1">
          <p style={{ fontSize: "var(--text-15)" }}>
            <span className="eyebrow mr-2">{position}</span>
            {entry.exercise.display_name}
          </p>
          <p className="mono" style={{ color: "var(--muted)", fontSize: "var(--text-12)" }}>
            {entry.exercise.primary_muscles.map(muscleLabel).join(", ")}
          </p>
        </div>
        <button type="button" className="pill glass-lift" onClick={onRemove}>
          Remover
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-6">
        <label className="myo-label">
          <span className="eyebrow">Séries</span>
          <input
            className="myo-field"
            type="number"
            min={1}
            max={99}
            value={entry.sets}
            onChange={(event) => onChange({ sets: Number(event.target.value) })}
          />
        </label>
        <label className="myo-label">
          <span className="eyebrow">Repetições</span>
          <input
            className="myo-field"
            type="number"
            min={1}
            max={999}
            value={entry.reps}
            onChange={(event) => onChange({ reps: Number(event.target.value) })}
          />
        </label>
        <label className="myo-label">
          <span className="eyebrow">Descanso s</span>
          <input
            className="myo-field"
            type="number"
            min={0}
            max={3600}
            value={entry.rest_seconds}
            onChange={(event) => onChange({ rest_seconds: Number(event.target.value) })}
          />
        </label>
        <label className="myo-label">
          <span className="eyebrow">Carga kg</span>
          <input
            className="myo-field"
            type="number"
            min={0}
            max={1000}
            step="0.5"
            value={entry.load_kg ?? ""}
            onChange={(event) =>
              onChange({ load_kg: event.target.value === "" ? null : Number(event.target.value) })
            }
          />
        </label>
      </div>

      {warning && (
        <p className="status status-warning mt-6" style={{ fontSize: "var(--text-12)" }}>
          {warning}
        </p>
      )}
    </li>
  );
}

export function WorkoutBuilder({ facets }: { facets: Facets | null }) {
  const [summaries, setSummaries] = useState<WorkoutSummary[]>([]);
  const [workoutId, setWorkoutId] = useState<number | null>(null);
  const [name, setName] = useState("Novo treino");
  const [entries, setEntries] = useState<DraftEntry[]>([]);
  const [saved, setSaved] = useState<Workout | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showCatalog, setShowCatalog] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const refreshList = () =>
    api
      .listWorkouts()
      .then(setSummaries)
      .catch((err: Error) => setError(err.message));

  useEffect(() => {
    refreshList();
  }, []);

  const load = async (id: number) => {
    try {
      const workout = await api.getWorkout(id);
      setWorkoutId(workout.id);
      setName(workout.name);
      setEntries(toDraft(workout));
      setSaved(workout);
      setError(null);
      setStatus(null);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const reset = () => {
    setWorkoutId(null);
    setName("Novo treino");
    setEntries([]);
    setSaved(null);
    setStatus(null);
  };

  const addExercise = (exercise: Exercise) => {
    setEntries((current) => [
      ...current,
      { key: nextKey(), exercise, ...DEFAULT_PRESCRIPTION, load_kg: null },
    ]);
    setShowCatalog(false);
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    const body = {
      name,
      exercises: entries.map((entry) => ({
        exercise_id: entry.exercise.id,
        sets: entry.sets,
        reps: entry.reps,
        rest_seconds: entry.rest_seconds,
        load_kg: entry.load_kg,
      })),
    };
    try {
      const workout = workoutId
        ? await api.updateWorkout(workoutId, body)
        : await api.createWorkout(body);
      setWorkoutId(workout.id);
      setSaved(workout);
      setEntries(toDraft(workout));
      setStatus("Salvo");
      await refreshList();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!workoutId) return;
    setBusy(true);
    try {
      await api.deleteWorkout(workoutId);
      reset();
      await refreshList();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const sync = async () => {
    if (!workoutId) return;
    setBusy(true);
    setStatus(null);
    try {
      const result = await api.syncWorkout(workoutId);
      if (result.ok) {
        setStatus(`Enviado ao Garmin como treino ${result.garmin_workout_id}`);
        setError(null);
        await refreshList();
      } else {
        setError(result.detail ?? "Falha no envio");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setEntries((current) => {
      const from = current.findIndex((entry) => entry.key === active.id);
      const to = current.findIndex((entry) => entry.key === over.id);
      return arrayMove(current, from, to);
    });
  };

  // Warnings come from the saved workout, so they describe what is on the
  // server rather than unsaved edits.
  const warningFor = (index: number) =>
    saved?.warnings.find((warning) => warning.exercise_position === index)?.message;
  const globalWarnings = saved?.warnings.filter((w) => w.exercise_position === null) ?? [];
  const dirty =
    saved === null ||
    saved.name !== name ||
    saved.exercises.length !== entries.length ||
    entries.some((entry, index) => {
      const stored = saved.exercises[index];
      return (
        !stored ||
        stored.exercise.id !== entry.exercise.id ||
        stored.sets !== entry.sets ||
        stored.reps !== entry.reps ||
        stored.rest_seconds !== entry.rest_seconds ||
        stored.load_kg !== entry.load_kg
      );
    });

  return (
    <section>
      <SectionTitle>Montagem de treino</SectionTitle>
      {error && <Notice kind="error">{error}</Notice>}
      {status && <Notice kind="info">{status}</Notice>}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-7">
          <div className="flex flex-wrap gap-6 items-end mb-12">
            <label className="myo-label flex-1 min-w-48">
              <span className="eyebrow">Nome</span>
              <input
                className="myo-field"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </label>
            <button type="button" className="pill glass-lift" onClick={reset}>
              Novo
            </button>
            <button
              type="button"
              className="pill glass-lift pill-primary"
              disabled={busy || entries.length === 0}
              onClick={save}
            >
              {busy ? "Salvando" : "Salvar"}
            </button>
          </div>

          {summaries.length > 0 && (
            <div className="mb-6">
              <span className="eyebrow block mb-2">Treinos salvos</span>
              <div className="myo-rail">
                {summaries.map((summary) => (
                  <button
                    key={summary.id}
                    type="button"
                    className="pill glass-lift"
                    aria-pressed={summary.id === workoutId}
                    onClick={() => load(summary.id)}
                  >
                    {summary.name} ({summary.exercise_count})
                  </button>
                ))}
              </div>
            </div>
          )}

          {globalWarnings.map((warning) => (
            <p
              key={warning.code}
              className="mb-6"
              style={{ fontSize: "var(--text-13)", color: "var(--status-warning)" }}
            >
              {warning.message}
            </p>
          ))}

          <div className="card-glass glass-lift myo-card mb-12">
            {entries.length === 0 ? (
              <p className="px-4 py-6" style={{ color: "var(--muted)" }}>
                Nenhum exercício ainda. Adicione um pelo catálogo.
              </p>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={onDragEnd}
              >
                <SortableContext
                  items={entries.map((entry) => entry.key)}
                  strategy={verticalListSortingStrategy}
                >
                  <ul>
                    {entries.map((entry, index) => (
                      <SortableRow
                        key={entry.key}
                        entry={entry}
                        position={index + 1}
                        warning={dirty ? undefined : warningFor(index)}
                        onChange={(patch) =>
                          setEntries((current) =>
                            current.map((item) =>
                              item.key === entry.key ? { ...item, ...patch } : item,
                            ),
                          )
                        }
                        onRemove={() =>
                          setEntries((current) =>
                            current.filter((item) => item.key !== entry.key),
                          )
                        }
                      />
                    ))}
                  </ul>
                </SortableContext>
              </DndContext>
            )}
          </div>

          <div className="flex flex-wrap gap-6">
            <button
              type="button"
              className="pill glass-lift"
              onClick={() => setShowCatalog((value) => !value)}
            >
              {showCatalog ? "Fechar catálogo" : "Adicionar exercício"}
            </button>
            {workoutId && (
              <>
                <a className="pill glass-lift" href={api.exportUrl(workoutId)} download>
                  Exportar .FIT
                </a>
                <button type="button" className="pill glass-lift" disabled={busy} onClick={sync}>
                  Enviar ao Garmin
                </button>
                <button type="button" className="pill glass-lift" disabled={busy} onClick={remove}>
                  Excluir
                </button>
              </>
            )}
          </div>

          {dirty && entries.length > 0 && (
            <p className="eyebrow mt-6">Alterações não salvas. Salve para atualizar o mapa muscular.</p>
          )}
        </div>

        <aside className="card-glass glass-lift myo-card lg:col-span-4 lg:col-start-9 p-6 self-start">
          <p className="eyebrow mb-6">Mapa muscular do treino</p>
          <BodyMap load={saved?.muscle_load ?? []} />
          <HeatLegend />
          {saved && saved.muscle_load.length > 0 && (
            <ul className="mt-6" style={{ fontSize: "var(--text-13)" }}>
              {saved.muscle_load.slice(0, 8).map((entry) => (
                <li key={entry.muscle} className="flex justify-between gap-4 py-1">
                  <span>{muscleLabel(entry.muscle)}</span>
                  <span className="mono" style={{ color: "var(--muted)", fontSize: "var(--text-12)" }}>
                    {entry.score}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>

      {showCatalog && (
        <div className="mt-24">
          <ExerciseCatalog facets={facets} onAdd={addExercise} />
        </div>
      )}
    </section>
  );
}

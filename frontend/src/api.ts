/** Wire types and fetch helpers. Mirrors backend/app/schemas.py. */

export type ViewId = "front" | "back";

/**
 * The 19 muscle groups. This union must stay identical to MuscleGroup in
 * backend/app/muscles.py; the /api/exercises/facets response is checked
 * against it at runtime by the body map legend.
 */
export type MuscleId =
  | "quadriceps"
  | "hamstrings"
  | "glutes"
  | "adductors"
  | "abductors"
  | "calves"
  | "erector_spinae"
  | "lats"
  | "traps"
  | "rhomboids"
  | "rear_delts"
  | "front_delts"
  | "side_delts"
  | "chest"
  | "biceps"
  | "triceps"
  | "forearms"
  | "abs"
  | "obliques";

export interface Exercise {
  id: number;
  garmin_category: string;
  garmin_exercise_name: string;
  display_name: string;
  primary_muscles: MuscleId[];
  secondary_muscles: MuscleId[];
  equipment_type: string;
  is_compound: boolean;
  is_strength: boolean;
}

export interface ExercisePage {
  items: Exercise[];
  total: number;
  offset: number;
  limit: number;
}

export interface WorkoutExerciseIn {
  exercise_id: number;
  sets: number;
  reps: number;
  rest_seconds: number;
  load_kg: number | null;
  notes?: string | null;
}

export interface WorkoutExercise extends WorkoutExerciseIn {
  id: number;
  position: number;
  exercise: Exercise;
}

export interface MuscleLoad {
  muscle: MuscleId;
  score: number;
  primary_count: number;
  secondary_count: number;
  intensity: number;
}

export interface ValidationWarning {
  code: string;
  message: string;
  exercise_position: number | null;
}

export interface Workout {
  id: number;
  name: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  garmin_workout_id: string | null;
  garmin_synced_at: string | null;
  exercises: WorkoutExercise[];
  muscle_load: MuscleLoad[];
  warnings: ValidationWarning[];
}

export interface WorkoutSummary {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  garmin_workout_id: string | null;
  exercise_count: number;
}

export interface Facets {
  categories: string[];
  equipment: string[];
  equipment_types: string[];
  muscles: { id: MuscleId; views: ViewId[] }[];
}

export interface GarminStatus {
  authenticated: boolean;
  profile_name: string | null;
  detail: string | null;
}

export interface SyncResult {
  ok: boolean;
  garmin_workout_id: string | null;
  detail: string | null;
}

/** Default prescription from the project brief. */
export const DEFAULT_PRESCRIPTION = { sets: 3, reps: 12, rest_seconds: 75 };

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });

  if (!response.ok) {
    // FastAPI puts the reason in `detail`, which may be a string or a list of
    // per-field validation errors.
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) {
        message = body.detail
          .map((item: { loc?: string[]; msg?: string }) =>
            `${item.loc?.slice(1).join(".") ?? ""}: ${item.msg ?? ""}`.trim(),
          )
          .join("; ");
      }
    } catch {
      /* response had no JSON body; keep the status line */
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  facets: () => request<Facets>("/api/exercises/facets"),

  exercises: (params: Record<string, string | number | boolean | undefined>) => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") query.set(key, String(value));
    }
    return request<ExercisePage>(`/api/exercises?${query.toString()}`);
  },

  listWorkouts: () => request<WorkoutSummary[]>("/api/workouts"),
  getWorkout: (id: number) => request<Workout>(`/api/workouts/${id}`),

  createWorkout: (body: { name: string; notes?: string | null; exercises: WorkoutExerciseIn[] }) =>
    request<Workout>("/api/workouts", { method: "POST", body: JSON.stringify(body) }),

  updateWorkout: (
    id: number,
    body: { name: string; notes?: string | null; exercises: WorkoutExerciseIn[] },
  ) => request<Workout>(`/api/workouts/${id}`, { method: "PUT", body: JSON.stringify(body) }),

  deleteWorkout: (id: number) =>
    request<void>(`/api/workouts/${id}`, { method: "DELETE" }),

  syncWorkout: (id: number) =>
    request<SyncResult>(`/api/workouts/${id}/sync`, { method: "POST" }),

  exportUrl: (id: number) => `/api/workouts/${id}/export.fit`,

  garminStatus: () => request<GarminStatus>("/api/garmin/status"),
  garminLogin: (body: { email: string; password: string; mfa_code?: string | null }) =>
    request<GarminStatus>("/api/garmin/login", { method: "POST", body: JSON.stringify(body) }),
  garminLogout: () => request<GarminStatus>("/api/garmin/logout", { method: "POST" }),
};

/** quadriceps -> Quadriceps, erector_spinae -> Erector spinae. Sentence case. */
export function muscleLabel(muscle: string): string {
  const spaced = muscle.replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

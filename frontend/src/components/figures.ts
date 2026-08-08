/**
 * Original stylized anatomy for the body map.
 *
 * Every shape is drawn as the LEFT half of the figure inside a 200x440 box and
 * mirrored at render time with `matrix(-1 0 0 1 200 0)`. Drawing one side has
 * two payoffs: symmetry is exact rather than eyeballed, and a muscle group is
 * one entry here instead of two that can drift apart.
 *
 * Paths are hand-authored stylized forms, not traced from any anatomical
 * illustration.
 */

import type { MuscleId, ViewId } from "../api";

/** Neutral body shapes drawn under the muscle groups, for silhouette only. */
export const BASE_HALF: string[] = [
  // neck
  "M92 46 L100 46 L100 68 L92 68 Z",
  // torso
  "M100 62 C 84 62, 70 66, 62 72 C 54 84, 50 104, 50 128 C 50 156, 54 182, 58 200 C 60 208, 64 212, 72 212 L 100 212 Z",
  // upper arm
  "M60 76 C 48 84, 41 106, 40 130 C 39 142, 41 150, 43 156 L 57 154 C 55 142, 55 118, 58 100 C 60 88, 63 80, 66 76 Z",
  // forearm
  "M43 158 C 38 176, 35 196, 35 210 L 49 212 C 49 196, 51 176, 56 158 Z",
  // hand
  "M35 214 C 31 222, 32 232, 38 234 C 44 234, 48 226, 47 216 Z",
  // thigh
  "M72 214 L 99 214 L 99 250 C 99 276, 97 296, 95 310 L 69 310 C 67 292, 66 268, 68 240 C 69 228, 70 220, 72 214 Z",
  // shin
  "M70 314 L 94 314 C 94 340, 92 370, 90 392 L 72 392 C 70 370, 69 340, 70 314 Z",
  // foot
  "M71 396 L 90 396 L 92 410 C 92 414, 88 416, 82 416 L 66 416 C 63 416, 62 412, 64 408 Z",
];

/** Head is on the centre line, so it is drawn once rather than mirrored. */
export const HEAD = { cx: 100, cy: 30, rx: 18, ry: 22 };

export const FRONT_MUSCLES: Partial<Record<MuscleId, string>> = {
  traps:
    "M99 48 L99 58 C 94 62, 86 70, 80 78 L 68 73 C 78 63, 90 52, 99 48 Z",
  front_delts:
    "M66 74 C 55 80, 49 96, 51 112 C 60 116, 69 108, 70 94 C 70 84, 69 78, 66 74 Z",
  side_delts:
    "M51 82 C 44 92, 43 106, 47 118 L 54 114 C 50 104, 50 92, 54 84 Z",
  chest:
    "M99 82 C 88 80, 76 84, 70 90 C 66 98, 67 110, 72 116 C 80 122, 92 122, 99 116 Z",
  abs: "M99 126 L 87 126 C 85 148, 85 172, 88 192 L 99 192 Z",
  obliques:
    "M85 128 C 79 130, 76 140, 76 152 C 76 170, 79 184, 84 192 L 86.5 192 C 83 172, 83 148, 85 128 Z",
  biceps:
    "M57 108 C 51 120, 49 136, 51 150 L 62 148 C 61 134, 62 120, 65 110 Z",
  forearms:
    "M50 156 C 45 174, 42 192, 42 206 L 52 206 C 52 190, 54 172, 58 158 Z",
  abductors:
    "M72 198 C 63 204, 58 216, 60 230 L 72 226 C 71 214, 73 204, 77 198 Z",
  quadriceps:
    "M78 214 C 71 234, 68 264, 70 300 L 92 300 C 93 266, 93 236, 92 214 Z",
  adductors:
    "M94 214 L 99 214 L 99 282 L 95 282 C 92 262, 92 236, 94 214 Z",
  // Front of the lower leg: the shin, which is what shows from this side.
  calves:
    "M74 318 C 71 340, 71 366, 74 386 L 87 384 C 87 362, 86 340, 85 318 Z",
};

export const BACK_MUSCLES: Partial<Record<MuscleId, string>> = {
  traps:
    "M99 46 C 90 50, 78 60, 68 72 L 74 96 C 82 106, 92 114, 99 118 Z",
  rear_delts:
    "M66 74 C 55 80, 49 96, 51 112 C 60 116, 69 108, 70 94 C 70 84, 69 78, 66 74 Z",
  side_delts:
    "M51 82 C 44 92, 43 106, 47 118 L 54 114 C 50 104, 50 92, 54 84 Z",
  rhomboids: "M99 76 L 99 110 L 84 101 C 81 92, 81 84, 84 78 Z",
  lats:
    "M80 106 C 70 116, 65 134, 68 154 C 71 172, 80 186, 90 192 L 99 188 L 99 118 C 92 114, 85 110, 80 106 Z",
  erector_spinae:
    "M99 120 L 92 122 C 90 148, 90 174, 92 198 L 99 198 Z",
  triceps:
    "M57 106 C 50 118, 48 136, 50 150 L 61 148 C 60 134, 61 118, 64 108 Z",
  forearms:
    "M50 156 C 45 174, 42 192, 42 206 L 52 206 C 52 190, 54 172, 58 158 Z",
  glutes:
    "M72 208 C 64 214, 60 228, 63 242 C 68 254, 82 258, 92 252 C 97 248, 99 240, 99 230 L 99 208 Z",
  hamstrings:
    "M70 258 C 67 276, 66 292, 68 310 L 92 310 C 93 292, 93 274, 92 258 Z",
  // Back of the lower leg: the gastrocnemius.
  calves:
    "M72 316 C 68 332, 68 352, 72 368 C 78 374, 88 372, 90 362 C 91 346, 89 330, 86 316 Z",
};

export const MUSCLES_BY_VIEW: Record<ViewId, Partial<Record<MuscleId, string>>> = {
  front: FRONT_MUSCLES,
  back: BACK_MUSCLES,
};

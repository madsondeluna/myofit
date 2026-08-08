/**
 * Original stylized anatomy for the body map.
 *
 * Every shape is the LEFT half of the figure inside a 240x560 box, mirrored at
 * render time with `matrix(-1 0 0 1 240 0)`. Drawing one side makes symmetry
 * exact rather than eyeballed and keeps a muscle group to a single entry that
 * cannot drift between sides.
 *
 * Proportions follow the seven-and-a-half head canon: the head is 66 units
 * tall on a 560 unit figure, shoulders span about two head widths, the waist
 * is the narrowest point of the torso and the knee sits at three quarters of
 * the way down. The earlier version ignored this and read as stacked slabs.
 *
 * Paths are hand-authored, not traced from any anatomical illustration.
 */

import type { MuscleId, ViewId } from "../api";

export const VIEW_BOX = { width: 240, height: 560 };
export const MIRROR = "matrix(-1 0 0 1 240 0)";

/** Head sits on the centre line, so it is drawn once instead of mirrored. */
export const HEAD = { cx: 120, cy: 42, rx: 23, ry: 31 };

/**
 * Silhouette. The torso and leg are one continuous outline so the body reads
 * as a single form; the arm and foot are separate because they detach from
 * that contour.
 */
export const BASE_HALF: string[] = [
  // neck
  "M105 60 L135 60 L135 94 L105 94 Z",
  // torso down the side, into the leg, back up the inside to the crotch
  "M120 76 L107 80 C 99 84, 90 90, 82 97 C 74 103, 67 114, 65 129 " +
    "C 66 145, 69 160, 73 174 C 74 192, 79 216, 82 240 " +
    "C 83 252, 82 262, 78 272 C 73 282, 69 292, 68 304 " +
    "C 68 314, 71 319, 76 322 C 76 348, 75 372, 74 396 " +
    "C 73 410, 75 419, 77 427 C 79 450, 81 478, 82 504 " +
    "C 82 516, 81 524, 80 531 L 98 531 " +
    "C 99 505, 101 470, 103 436 C 104 418, 106 392, 108 362 " +
    "C 110 340, 112 328, 114 322 L 120 322 Z",
  // arm: shoulder to hand, down the outside and back up the inside
  "M63 124 C 52 134, 43 156, 39 180 C 36 200, 36 218, 39 234 " +
    "C 36 254, 32 280, 30 306 C 29 326, 30 342, 32 352 " +
    "C 29 362, 29 374, 34 380 C 40 384, 46 380, 47 370 " +
    "C 48 360, 47 350, 46 344 C 47 322, 50 296, 53 272 " +
    "C 55 254, 57 240, 58 230 C 60 208, 62 180, 64 156 " +
    "C 65 142, 65 130, 64 124 Z",
  // foot
  "M80 533 C 76 542, 66 548, 58 550 C 52 551, 50 554, 54 557 " +
    "L 96 557 C 99 557, 100 552, 99 546 L 98 533 Z",
];

export const FRONT_MUSCLES: Partial<Record<MuscleId, string>> = {
  // Upper trapezius: the slope from neck to shoulder.
  traps:
    "M118 76 L118 100 C 106 102, 94 108, 86 116 C 81 111, 79 103, 83 97 C 93 87, 106 80, 118 76 Z",
  front_delts:
    "M89 105 C 76 109, 66 122, 64 140 C 63 153, 68 162, 77 162 C 88 160, 95 147, 96 131 C 97 118, 94 108, 89 105 Z",
  side_delts:
    "M65 126 C 59 136, 57 152, 60 164 C 64 168, 70 166, 72 159 C 67 150, 65 137, 68 126 Z",
  chest:
    "M118 108 C 104 107, 92 113, 86 123 C 81 134, 82 152, 88 163 C 97 173, 111 175, 118 171 Z",
  abs:
    "M118 178 L98 182 C 95 200, 94 222, 95 242 C 96 258, 100 270, 104 278 L118 280 Z",
  obliques:
    "M95 183 C 87 188, 82 200, 81 216 C 80 234, 84 254, 90 270 C 93 275, 96 277, 98 276 C 94 260, 92 240, 93 218 C 94 200, 94 190, 95 183 Z",
  biceps:
    "M62 158 C 53 170, 48 190, 47 212 C 46 226, 49 236, 54 240 C 60 241, 64 234, 65 220 C 66 200, 68 176, 71 163 Z",
  forearms:
    "M51 248 C 45 266, 40 290, 38 312 C 36 328, 37 342, 41 350 C 46 352, 50 347, 51 336 C 52 315, 55 289, 59 264 Z",
  // Tensor fasciae latae and gluteus medius, which show on the outer hip.
  abductors:
    "M80 274 C 73 280, 69 292, 69 306 C 69 314, 72 320, 77 321 C 79 313, 80 302, 83 290 Z",
  quadriceps:
    "M83 316 C 77 336, 74 364, 75 390 C 76 404, 80 414, 86 415 C 97 415, 104 405, 106 388 C 108 362, 108 334, 107 316 Z",
  adductors:
    "M109 318 C 107 336, 106 356, 107 374 C 108 384, 110 390, 113 390 L 117 388 C 117 362, 117 338, 117 318 Z",
  // Front of the lower leg: the tibialis, which is what shows from this side.
  calves:
    "M83 430 C 79 450, 77 476, 78 500 C 79 514, 82 522, 87 522 C 92 520, 94 512, 94 498 C 94 474, 92 450, 91 430 Z",
};

export const BACK_MUSCLES: Partial<Record<MuscleId, string>> = {
  // Full trapezius: the diamond from neck across the shoulders into mid back.
  traps:
    "M118 76 C 106 80, 94 88, 84 99 C 80 104, 80 111, 84 116 C 92 123, 103 131, 111 141 C 115 147, 117 152, 118 156 Z",
  rear_delts:
    "M89 105 C 76 109, 66 122, 64 140 C 63 153, 68 162, 77 162 C 88 160, 95 147, 96 131 C 97 118, 94 108, 89 105 Z",
  side_delts:
    "M65 126 C 59 136, 57 152, 60 164 C 64 168, 70 166, 72 159 C 67 150, 65 137, 68 126 Z",
  lats:
    "M86 148 C 76 158, 71 176, 71 196 C 71 216, 77 238, 87 254 C 96 264, 109 268, 118 265 L118 210 C 111 194, 102 176, 94 160 C 91 153, 88 149, 86 148 Z",
  rhomboids:
    "M118 146 C 110 148, 103 152, 100 158 C 98 164, 101 171, 107 176 C 112 180, 116 182, 118 182 Z",
  erector_spinae:
    "M118 186 L107 190 C 103 210, 102 234, 104 256 C 105 268, 108 278, 112 284 L118 284 Z",
  triceps:
    "M60 156 C 51 170, 46 190, 45 212 C 44 226, 47 236, 52 240 C 58 241, 62 234, 63 220 C 64 200, 66 176, 69 162 Z",
  forearms:
    "M51 248 C 45 266, 40 290, 38 312 C 36 328, 37 342, 41 350 C 46 352, 50 347, 51 336 C 52 315, 55 289, 59 264 Z",
  glutes:
    "M118 266 C 107 266, 95 271, 87 280 C 79 289, 75 302, 78 314 C 83 325, 95 329, 106 324 C 114 320, 118 311, 118 300 Z",
  hamstrings:
    "M81 330 C 77 350, 75 374, 76 394 C 77 406, 81 414, 87 415 C 97 414, 104 404, 106 388 C 107 366, 108 346, 107 330 Z",
  // Back of the lower leg: the gastrocnemius.
  calves:
    "M81 428 C 76 446, 74 466, 76 486 C 78 500, 85 508, 92 505 C 97 502, 99 492, 98 480 C 97 460, 94 442, 90 428 Z",
};

export const MUSCLES_BY_VIEW: Record<ViewId, Partial<Record<MuscleId, string>>> = {
  front: FRONT_MUSCLES,
  back: BACK_MUSCLES,
};

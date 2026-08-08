# MyoFit

Strength workout builder with an interactive muscle map, FIT file export and
Garmin Connect sync.

The exercise catalog is derived from the Garmin FIT SDK exercise enums rather
than typed by hand, so a workout built here resolves to the correct movement on
the watch. On top of that identity MyoFit adds what the SDK does not carry:
which muscles each exercise trains, what equipment it needs, and whether it is
a compound or an isolation movement.

MyoFit is an educational tool. Training programmes, loads and exercise
selection should be reviewed by a qualified professional before use. The
application shows this notice on every screen.

## Setup

Requires Python 3.12, Node 20 or newer, and [uv](https://docs.astral.sh/uv/).

```
make install
make dev
```

`make dev` starts the API on port 8000 and the Vite dev server on port 5173.
Open http://localhost:5173. Vite proxies `/api` to the backend, so the browser
sees a single origin and no CORS preflight is involved.

Other targets:

```
make api      # API only, with reload
make web      # frontend only
make build    # production frontend bundle into frontend/dist
make test     # backend test suite
```

When `frontend/dist` exists, the API process serves it directly, which is the
shape used in production.

## Architecture

```
backend/app/
  muscles.py        muscle taxonomy, the view each group is drawn in, equipment enum
  catalog_data.py   muscle and equipment knowledge layered on the FIT enums
  seed.py           walks the FIT SDK enums into catalog rows
  models.py         SQLModel tables
  schemas.py        Pydantic v2 wire types
  analysis.py       muscle aggregation and the ordering heuristic
  crud.py           workout reads and writes shared by the routers
  fit_export.py     FIT workout encoding
  garmin.py         Garmin Connect client and workout-service payload
  routers/          HTTP endpoints
frontend/src/
  api.ts            wire types and fetch helpers
  components/
    figures.ts      the body map geometry
    BodyMap.tsx     the SVG renderer, highlight and heat modes
    WorkoutBuilder.tsx, ExerciseCatalog.tsx, EquipmentBrowser.tsx, GarminSettings.tsx
  prussian/         vendored copy of the Prussian design language
```

Backend is FastAPI with SQLModel over SQLite. Frontend is React, Vite and
TypeScript, with Tailwind used only for layout: colour, type and spacing come
from the design tokens.

### Exercise identity

The FIT profile models strength exercises as a two-level enum. There is one
`ExerciseCategory` with 53 members, and a separate exercise-name enum per
category, following a strict naming convention: `HIP_STABILITY` maps to
`HipStabilityExerciseName`. 51 categories resolve this way; `UNKNOWN` and
`CARDIO_SENSORS` have no name enum and are skipped.

Name values are unique only within their category. Value 0 is `LEG_PRESS` under
`SQUAT` and `BENCH_PRESS` under `BENCH_PRESS`, so the identity of an exercise is
the pair, never the name alone. Seeding produces 1846 exercises, of which 1489
are strength work.

A consequence worth stating: several exercises are not where their common name
suggests. The leg press is `SQUAT/LEG_PRESS`, the hack squat is
`SQUAT/BARBELL_HACK_SQUAT`, and hip abduction is
`HIP_STABILITY/STANDING_HIP_ABDUCTION`. The seeder reads these from the SDK, so
the catalog cannot drift from what the watch accepts. A test resolves every
seeded row back to its enum pair to keep it that way.

### Muscle taxonomy

Nineteen groups, fixed, shared by the database, the API and the SVG path ids:

```
quadriceps  hamstrings  glutes      adductors  abductors  calves
erector_spinae  lats    traps       rhomboids  rear_delts
front_delts     side_delts  chest   biceps     triceps
forearms        abs     obliques
```

Each group declares which anatomical views draw it. Most belong to one view;
`traps`, `calves`, `side_delts` and `forearms` are drawn in both, because they
are visible from both sides of the body. A test asserts that every group
declared for a view has a matching path in that view's figure, and that no
figure draws an id outside the taxonomy. Without it, a mismatch produces a body
map that renders correctly and highlights nothing.

Muscle assignment comes from a per-category baseline plus keyword overrides
scoped to a movement family. The scoping is not cosmetic:
`DECLINE_HAMMER_CURL` is a curl, and an unscoped "decline" rule would paint it
as chest work.

### Muscle map colour

The map runs cool to warm: blue for a lightly worked muscle, red for the most
worked one. The steps are `--heat-1` to `--heat-7` in `frontend/src/index.css`,
built on the diverging ramp of the Prussian design language, which already runs
blue to amber.

Its two neutral middle steps are skipped deliberately. They sit within a couple
of points of the page background, so a muscle at mid intensity would have read
as unworked. The seven steps kept all clear 3:1 against the background.

Intensity maps onto those seven discrete steps rather than interpolating
between them, because the ramp was validated as discrete steps and intermediate
values would be colours nobody checked. Interface colours are never used for
muscles: a highlighted muscle must not read as a focus ring.

### Muscle aggregation

For a single exercise, primary muscles take the strongest step and secondary
muscles a lighter one. For a whole workout, each muscle scores the sum over the
exercises that hit it of `sets x weight`, where weight is 1.0 as a primary
target and 0.5 as a secondary one. Scaling by sets is what makes five sets of
squats outweigh one set of calf raises. Scores are normalised against the
hardest-worked muscle of the workout, so the map always uses its full range.

### Ordering heuristic

Two advisory warnings, both derived from the `is_compound` flag. A workout of
only isolation movements is flagged, and each isolation movement placed before
the last compound lift is flagged individually. Neither rejects the workout.

## FIT export

Every workout can be downloaded as a `.FIT` file and copied into
`GARMIN/Workouts` on the watch over USB. This is the fallback path when the
Connect API is unavailable.

Each set is written as its own step followed by a rest step. The FIT profile
also allows a repeat step that loops back over a range, which is what Garmin
Connect itself exports, but that step encodes its target as a raw message index
and a wrong index yields a file that decodes without error while running the
wrong number of sets. Expanded steps cannot fail that way.

The round-trip test writes with `fit-tool` and reads back with the official
`garmin-fit-sdk` decoder, then asserts set for set that the category, exercise
name, rep count, load and rest duration survive. Two independent
implementations agreeing is the evidence that matters; one library
round-tripping its own output would only prove it is self-consistent.

## Garmin Connect sync

Two ways in, because there is no third-party authorisation flow to redirect
to. Garmin publishes no consumer OAuth: the developer programme covers the
Health API under an approved agreement and does not reach the workout service,
and the endpoints MyoFit uses are the ones the mobile app calls, which
authenticate with an email and a password over SSO. A "connect with Garmin"
button has nowhere to send the user.

The default path avoids putting a password in MyoFit at all: authenticate
wherever you already trust, and paste the resulting token. MyoFit adopts it
exactly as it would one it obtained itself.

The other path posts the credentials once to exchange them for tokens. Only the
tokens are written to disk, in the directory named by `GARMINTOKENS` (default
`.garth`, which is gitignored); the password is never stored. Accounts with
two-factor authentication come back asking for a code, and the pending attempt
is held in memory for five minutes so the code resumes the login it was issued
for.

### Limitations of the unofficial API

Garmin publishes no public workout API. MyoFit posts to the same internal
workout-service endpoints the Garmin Connect website uses, through the
`garminconnect` library, and Garmin can change or restrict them at any time
without notice. Sync failures are reported with the underlying message rather
than retried, and every failure path points back at the FIT export, which
depends on the published file format and is unaffected by API changes.

Sync has been implemented against the library's typed strength-workout builders
so that the `category` and `exerciseName` fields carry the same enum member
names used for seeding. It has not been exercised against a live account in
this repository, because doing so requires real credentials.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MYOFIT_DB` | `sqlite:///~/.local/share/myofit/myofit.db` | Database URL |
| `GARMINTOKENS` | `.garth` | Directory holding garth session tokens |
| `MYOFIT_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed origins |
| `PORT` | `8000` | Port the container listens on |

The database defaults outside the checkout because it is runtime state, and
because SQLite requires byte-range locks that some mounted filesystems do not
provide. On exFAT in particular every write fails with "attempt to write a
readonly database", so a checkout on such a volume could not run the app if the
database lived beside the source.

## Deployment

`render.yaml` is a Render blueprint using the multi-stage `Dockerfile`: Node
builds the frontend, Python serves it alongside the API from one service.

A persistent disk is mounted at `/data` and holds both the SQLite database and
the Garmin tokens. Without a disk, both are recreated empty on every deploy:
the catalog reseeds automatically, but saved workouts and the Garmin session do
not survive.

## Tests

```
make test
```

51 tests covering catalog seeding against the SDK enums, the muscle taxonomy
and its SVG coverage, the FIT round trip through the official decoder, workout
CRUD, reordering, the ordering heuristic, muscle aggregation, the static file
guard, and the failure path when no Garmin session is stored.

The Docker image has not been built in this environment, because no Docker
daemon was available. Its two non-obvious lines were checked another way: the
`uv` binary path matches the one the official image documents, and
`uv pip install -r pyproject.toml` was run locally and resolves the full
dependency set.

## Design language

The interface follows Prussian. `frontend/src/prussian/` is a vendored copy of
`web/tokens.css` and `web/patterns.css` from the language repository, taken
2026-08-08 and not edited: MyoFit's own rules live in `frontend/src/index.css`,
so the copies can be diffed against the source and any difference read as drift
to correct.

The application ships in the light mode, Prussian's default. The layout is
responsive: on a narrow viewport the two anatomical views collapse behind a
front and back toggle and the side panels stack under the main column.

Components come from `patterns.css` wherever the language ships one: `.pill`
for controls, `.surface` for cards, `.eyebrow` for metadata, `.section-header`
for the top of a screen. Only a form field and the body map are written from
scratch, because the language has no equivalent for either.

Every surface is glass: controls, cards, panels, form fields, and the header
and footer bars. Each takes the texture its size calls for, which is the
language's own rule rather than a preference. Pills and cards blur at 16 and
32 pixels, fields take the frosted texture because it is the most opaque of
the four and keeps a value legible, and the two full-width bars take
`.glass-deep` at 56 pixels. Controls carry `.glass-lift`, so under the pointer
they rise 2px and their top edge lights instead of changing colour.

Glass needs something behind it to refract, and the language says as much:
over a flat ground it shows nothing. `body::before` supplies that ground, three
very soft radial washes drawn from the slate ramp, wide enough that no edge is
visible and the page still reads as plain.

One deliberate divergence, recorded in `index.css` beside the rule that
implements it: Prussian reserves Cormorant Garamond for section titles and the
wordmark, and MyoFit uses Geist at weight 600 for that role, so the interface
runs on two families rather than three.

Layout follows the two vertical axes of the twelve column grid, content on
column 1 and the body map on column 9, and the three spacing steps of 24, 48
and 96. Smaller values appear only inside a control, between a label and its
field.

The interface is in Portuguese. The muscle and equipment enum values stay in
English because they are the contract with the API, the database and the SVG
path ids; only the text a user reads is translated. Garmin exercise identifiers
are never shown in the interface, though they are what gets written to the FIT
file and sent to Garmin.

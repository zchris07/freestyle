# Freestyle Rhyme Trainer

Single-file browser app (`index.html`, no build step, no dependencies) for practicing rap freestyle.
The user picks a rhyme scheme and a beat from a built-in library of notated hip hop beats; the game
scrolls 2 prep bars + 32 bars with the rhyme words landing on a chosen beat. The beats are synthesized
from notation, so the beat grid is exact.

Published as a private Claude artifact: https://claude.ai/artifact/CMVgF6WScPG74TWukdbjG5
(republishing `index.html` as that artifact keeps the URL).

## User preferences (decided, don't re-litigate)

- Palette: off-white cream background (`#faf3e3`), very dark green text (`#0f2a1a`), Spotify green
  accents (`#1DB954`, hover `#1ed760`, readable green text `#0e7a32`, selected tint `#c8f3d6`).
- Font: Georgia (serif fallback) for ALL text, including buttons and numbers. No icon fonts.
- Rhyme cells: slightly brighter cream (`#fdf8ea`) with a clear 2px black outline; unoccupied cells are
  a clearly grayer tan (`#ddd5b8`). Rhyme word TEXT is colored, and words that rhyme share a color
  (orange `#b5480c`, teal `#0a6a5a`).
- NO user uploads for now (decided): the beat library is curated by us. Wants trap and boom bap beats and a
  correctly structured metronome indicator (4 dots, beat 1 dark).

## Architecture

- **`index.html`**: the whole app.
  - *Setup screen*: scheme pills (AABB / AAAA / AA_A), word visibility (first/last/all), draggable 4x4 grid to
    choose which beat the rhyme lands on, beat library (list + drum-tab of the selected beat + Preview with
    metronome dots + optional click track), PLAY.
  - *Performance screen*: 2 prep bars then 32 bars, 4 cells per bar; current cell highlights, rhyme word
    reveals on its beat.
  - *Engine*: Web Audio synth (kick, snare, clap, rim, hat, open hat, shaker, sine/808 bass). `barEvents` turns one
    bar of notation into timed events (swing applied to off-beat 16ths), `scheduleBar` plays them. The player
    schedules whole bars 0.5 s ahead from a 20 ms poll and derives beat callbacks from `AudioContext.currentTime`.
    Not `setInterval` ticks. `renderBeat` renders N bars offline (used by `tools/verify.mjs`).
  - The library is inlined as `<script id="beat-library" type="application/json">` (CSP blocks fetch).
- **`beats/library.json`**: source of truth for the notated beats; format is described in its `legend`. One string
  per bar per track (`X` accent, `x` hit, `o` ghost, `.` rest; 16 chars = 16th notes, 12 = triplets, 32 = 32nds).
  Bass is `step:note:length`. Beats are synthesized, so there is no audio to license or load.
- **`beats/library.md`**: generated readable drum-tab of every beat. Don't edit by hand.
- **`tools/build-library.mjs`**: validates `library.json`, inlines it into `index.html`, regenerates `library.md`.
  **Run it after every edit to library.json** (`--check` reports staleness).
- **`tools/detect.mjs <audio...> [--out dir]`**: offline beat detector CLI (Node + ffmpeg, no npm deps). Writes
  `<name>.grid.json` (bpm, confidence, half/double alternatives, downbeat, per-bar beat times) and `.grid.csv`.
  Algorithm in `tools/detector.mjs`: 1024-pt FFT at 100 fps -> 3-band log spectral flux -> local-mean subtraction ->
  comb-filter sweep 60-180 BPM with a log-normal prior (center 120, sigma 0.6 octave, `ALPHA=0.5`) -> fine refine ->
  octave check of tempo/2, tempo, tempo*2 on a kick+snare-only envelope -> downbeat by matching per-beat kick (low
  flux) and snare (mid flux) strength to backbeat / half-time templates.
- **`tools/verify.mjs [--bars N] [--export dir]`**: renders every library beat with the app's synth in headless
  Chromium (needs playwright), runs the detector on it, compares with the notation. Prints OK / OCTAVE / FAIL.

## Known limits

- Detector is verified only on our own synthetic beats: `node tools/verify.mjs` currently gives 6 OK, 1 OCTAVE
  (dusty-boom-bap found as 180 with 90 as the alternative) and 3 wrong (lazy-bounce and lo-fi-chill found at 2x with
  a wrong downbeat on the 1x alternative; trap-dark downbeat one beat off). Treat its output on real tracks as a
  draft to review, not ground truth. Known causes: hi-hat 8ths and swing make 2x look like the beat; kick/snare
  clicks leak into each other's bands, so the downbeat templates can pick the wrong beat.
- Octave ambiguity is inherent (boom bap at 90 looks like half-time at 180; trap at 140 looks like backbeat at 70).
  Prior favors ~120. The grid JSON lists the half/double alternatives.
- Only the first 150 s of a track is analyzed. Assumes constant tempo and 4/4.
- Output latency of the audio device is not compensated.

## Ideas not yet built

- Better detection: Beat This! (github.com/CPJKU/beat_this, MIT) offline, written into the same grid JSON format.
- Real-audio beats in the library (needs a licensed source and a way to ship audio past the artifact CSP).
- Variable-tempo grids, bar-count/length options, saved presets, more beats.

## Working on this project

- Local preview: serve the folder over HTTP (the in-app browser blocks `file://`; headless Playwright can open it
  directly). On the user's Windows machine there was no Python/Node; a PowerShell `System.Net.HttpListener`
  script worked.
- Add a beat: edit `beats/library.json`, run `node tools/build-library.mjs`, then `node tools/verify.mjs`.
- Test the detector: `node tools/verify.mjs`, or `node tools/detect.mjs some.mp3`.
- Artifact constraints: external stylesheets/fetches are blocked by CSP, so keep everything inline
  and use text glyphs for icons. The page must work at phone width.
- Commits end with: `Co-Authored-By: Claude <noreply@anthropic.com>`.

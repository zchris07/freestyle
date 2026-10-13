# Freestyle Rhyme Trainer

Single-file browser app (`index.html`, no build step, no dependencies) for practicing rap freestyle.
The user picks a rhyme scheme and a beat; the game scrolls 2 prep bars + 32 bars with the rhyme
words landing on a chosen beat, synced to the uploaded track via a detected beat grid.

Published as a private Claude artifact: https://claude.ai/artifact/CMVgF6WScPG74TWukdbjG5
(republishing `index.html` as that artifact keeps the URL).

## User preferences (decided, don't re-litigate)

- Palette: off-white cream background (`#faf3e3`), very dark green text (`#0f2a1a`), Spotify green
  accents (`#1DB954`, hover `#1ed760`, readable green text `#0e7a32`, selected tint `#c8f3d6`).
- Font: Georgia (serif fallback) for ALL text, including buttons and numbers. No icon fonts.
- Rhyme cells: slightly brighter cream (`#fdf8ea`) with a clear 2px black outline; unoccupied cells are
  a clearly grayer tan (`#ddd5b8`). Rhyme word TEXT is colored, and words that rhyme share a color
  (orange `#b5480c`, teal `#0a6a5a`).
- Wants to upload many trap and boom bap beats and have the metronome indicator structured correctly.

## Architecture (all in `index.html`)

- **Setup screen**: scheme pills (AABB / AAAA / AA_A), word visibility (first/last/all), draggable
  4x4 grid to choose which beat the rhyme lands on, beat library, PLAY.
- **Performance screen**: 2 prep bars then 32 bars, 4 cells per bar; current cell highlights, rhyme
  word reveals on its beat.
- **Beat analysis** (`analyzeBuffer`, `refit`): own JS implementation, NOT Beat This!/madmom.
  1024-pt FFT at 100 fps -> 3-band log spectral flux (low 1.0 / mid 0.7 / high 0.3) -> local-mean
  subtraction -> comb-filter sweep over 60-180 BPM with a log-normal prior (center 120, sigma 0.6
  octave, `ALPHA=0.5` length normalization) -> fine refine at 0.02 BPM / 0.25 frame -> downbeat =
  the one of 4 beat phases with the most low-band energy (ties prefer the earliest phase).
  Stores `bpm`, `fd` (first downbeat, seconds), plus the onset/low envelopes so half/double-tempo
  and nudges can refit without re-decoding.
- **Player**: Web Audio. Source starts at `fd` and loops on whole bars; beats are derived from
  `AudioContext.currentTime` in a 20 ms poll (clicks scheduled 100 ms ahead). Not `setInterval` ticks.
- **Library storage**: IndexedDB `freestyle-beats` (blob + analysis), selected id in localStorage.
  All storage access is try/catch'd; falls back to session-only.

## Known limits

- Detector verified only on synthetic loops (tempo exact, downbeat within ~2 ms). Real tracks will
  be messier; the UI has half/2x tempo, BPM +-0.1, downbeat +-10 ms and "Next beat = 1" for fixes.
- Octave ambiguity is inherent (a 70 BPM trap beat is detected as 140). Prior favors ~120.
- Only the first 150 s of a track is analyzed. Assumes constant tempo and 4/4.
- Output latency of the audio device is not compensated.

## Ideas not yet built

- Offline import of Beat This! (github.com/CPJKU/beat_this, MIT) JSON grids for better accuracy
  (needs Python/PyTorch; the user's Windows machine had neither Python nor Node).
- Tap-tempo correction, variable-tempo grids, bar-count/length options, saved presets.

## Working on this project

- Local preview: serve the folder over HTTP (the in-app browser blocks `file://`). On the user's
  Windows machine there was no Python/Node; a PowerShell `System.Net.HttpListener` script worked.
- Test the detector without real audio by synthesizing kick/snare/hat loops into an `AudioBuffer`
  and calling `analyzeBuffer(buf)` from the console (globals are top-level in `index.html`).
- Artifact constraints: external stylesheets/fetches are blocked by CSP, so keep everything inline
  and use text glyphs for icons. The page must work at phone width.
- Commits end with: `Co-Authored-By: Claude <noreply@anthropic.com>`.

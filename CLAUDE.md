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
- **Beat analysis, two engines.** (1) **Beat This! small** (CPJKU, MIT) running in the browser via
  `onnxruntime-web` (wasm, in a worker); (2) the built-in detector below. Both run on upload: the built-in one
  always (it supplies the onset envelopes for the tempo buttons), Beat This! on top when it can load. See
  "Beat This! in the browser".
- **Built-in detector** (`analyzeBuffer`, `refit`): own JS implementation.
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

## Beat This! in the browser

- Model: `models/beat_this_small.onnx` (2.1M params, 9.4 MB, fp32, dynamic time axis), exported by
  `tools/export_onnx.py` (rotary-embedding cache must be disabled before tracing, see the script).
  Verified against PyTorch to ~1e-6.
- JS pipeline (`const BT` in index.html) reimplements `beat_this.preprocessing` + `inference` + the "minimal"
  postprocessor: 22.05 kHz mono -> 1024-pt FFT, hop 441 (50 fps), 128 Slaney mel bins 30-11000 Hz, magnitude,
  divide by sqrt(n_fft) (torchaudio `normalized="frame_length"`, NOT window energy), `log1p(1000x)`; 1500-frame chunks with
  6-frame borders; peak pick +-3 frames with logit > 0. Matches Python: mel 6e-5, logits 8e-5, identical beats.
- `btToGrid` fits a constant-tempo line to the beats (per-interval index assignment, outlier-trimmed LS) and picks the
  downbeat phase by vote; `snapPhase` then refines the downbeat against the 10 ms onset envelope (+-30 ms) because
  the model's output is quantized to 20 ms. The item stores `engine: "beat-this" | "builtin"`.
- Needs a normal web origin: `import()` of ORT from jsdelivr and `fetch("models/...")`. The Claude artifact's CSP
  blocks both, so there it silently falls back to the built-in detector (UI says so; "Re-analyze with Beat This!"
  button appears for non-Beat-This items). Real use = GitHub Pages: https://zchris07.github.io/freestyle/ (when enabled).
- Cost: ~16 s for a 40 s track on one wasm thread (GitHub Pages cannot send COOP/COEP headers, so no threads);
  150 s cap means up to ~1 min. Runs in an ORT worker (`env.wasm.proxy`), UI stays responsive, progress shown on the row.
- Tested only on synthetic loops (92 BPM boom-bap-ish, 140 BPM trap-ish with a 6 s silent intro, 44.1 kHz stereo):
  tempo within 0.03 BPM, downbeat within ~4 ms. Needs real tracks.

## Known limits

- Detector verified only on synthetic loops (tempo exact, downbeat within ~2 ms). Real tracks will
  be messier; the UI has half/2x tempo, BPM +-0.1, downbeat +-10 ms and "Next beat = 1" for fixes.
- Octave ambiguity for the built-in detector (a 70 BPM trap beat is detected as 140; prior favors ~120). Beat This! mostly avoids it.
- Only the first 150 s of a track is analyzed. Assumes constant tempo and 4/4.
- Output latency of the audio device is not compensated.

## Ideas not yet built

- Smaller model download (fp16/int8 quantization), WebGPU provider for speed, caching the model in IndexedDB.
- Using Beat This!'s per-beat times directly (variable tempo) instead of a constant-tempo fit.
- Tap-tempo correction, variable-tempo grids, bar-count/length options, saved presets.

## Working on this project

- Local preview: serve the folder over HTTP (the in-app browser blocks `file://`). On the user's
  Windows machine there was no Python/Node; a PowerShell `System.Net.HttpListener` script worked.
- Test the detector without real audio by synthesizing kick/snare/hat loops into an `AudioBuffer`
  and calling `analyzeBuffer(buf)` from the console (globals are top-level in `index.html`).
- Artifact constraints: external stylesheets/fetches are blocked by CSP, so keep everything inline
  and use text glyphs for icons. The page must work at phone width.
- Commits end with: `Co-Authored-By: Claude <noreply@anthropic.com>`.

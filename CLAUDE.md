# Freestyle Rhyme Trainer

Single-file browser app (`index.html`, no build step, no dependencies) for practicing rap freestyle.
The user picks a rhyme scheme and a beat; the game scrolls 2 prep bars + 32 bars with the rhyme
words landing on a chosen beat, synced to the uploaded track via a detected beat grid.

Published as a private Claude artifact: https://claude.ai/artifact/CMVgF6WScPG74TWukdbjG5
(republishing `index.html` as that artifact keeps the URL).

## User preferences (decided, don't re-litigate)

- Palette: Spotify dark theme (changed from the old cream look on 2026-10-20), as CSS tokens in `:root`. Page and header
  `#121212`, panels `#181818`, cells `#1f1f1f`, pills/raised `#282828` (hover `#3e3e3e`), performance
  screen `#191414` (Spotify brand black, its official playback-view fallback). Text `#ffffff` / secondary `#b3b3b3` /
  subdued `#7c7c7c`. Accent Spotify green `#1ed760` (hover `#1db954`) with black text on it; selected pills are green.
  Pill-shaped buttons (radius 500px). Warning `#ffa42b`, error `#f3727f`, toast blue `#539df5`.
- Font: Fraunces (Google Fonts, same as the "football explained." page), Georgia fallback, for ALL text incl. buttons, numbers and the grid canvas. No icon fonts.
- Rhyme groups are colored, in order: green `#1ed760`, orange `#ffa42b`, blue `#539df5`, pink `#f3727f`, lavender
  `#b49bc8`, white. A rhyme cell has a 2px outline and word text in its group's color. On the setup grid a hidden
  word ("First only" / "Last only") keeps a dashed outline and shows no text; in the builder it is faded and struck.
- No panel numbering.
- Layout: the top bar with the "freestyle.wtf" wordmark top-left (".wtf" in green, no caption) has no colour of its
  own: it sits on the page background (`#121212`). At 1000px and wider, setup is two columns (rhyme scheme | beat
  library + START SESSION) with bigger grids. The session screen (`#perf-screen`, `#191414`) is a full-window overlay
  with its own wordmark row, content centred at about 1040px. Phones (640px and below) get edge-to-edge content and a 50px top bar.
- Keep it minimal: no caption under the scheme pills, no "Beat timing" label or drag instructions (just "← drag →"
  under the rhyme column), no upload instructions (the button says "+ Upload beat"), no notes under the library.
  Under the library only TEMPO (+ DOWNBEAT for uploads) and CHECK (Preview, "Click track during session") remain:
  no click-only tempos, no feel / drop / grid-by rows. Button labels: "Preview", "START SESSION". The session screen shows only the beat name and STOP on top, then
  the bar grid with no bar/prep labels, no beat numbers in the cells and no status texts (no PREPARE / SPIT IT!).
  The lit outline is the beat indicator; STOP turns into BACK after bar 32.
- Wants to upload many trap and boom bap beats and have the metronome indicator structured correctly.
- Motion: on every load the page grows into place (each element scales up out of a blur, staggered from the top
  left) while all text writes itself in with the football explainer's writing animation (`runIntro`, `writeWord`:
  an SVG copy of each word, each letter's outline stroked on then inked; words 1/60 s apart, letters 14 ms). The
  session opens and closes like the builder, as a clip-path circle from the START SESSION button.
- Dragging (presets): the rhyme column is its own layer (`.rhyme-col`) above a full grid of empty boxes, so the
  boxes it leaves stay visible. While held it moves through magnetic detents (sticky near each column, then it
  snaps across), resists past the ends, leans with its speed, and a spring settles it on release (rAF in
  `setupDrag`). The target column's boxes light up in dashed green. The drag hint is a "← DRAG →" capsule below
  the rhyme scheme panel, centred under the column (`placeHint`); it fades out on grab and back in after landing.
- Session beat indicator: the current box lights up its outline (border + glow) and is never filled, so a rhyme
  word stays readable (a plain beat in green, a rhyme in its group's color).

## Architecture (all in `index.html`)

- **Setup screen**: one "RHYME SCHEME" panel (scheme pills from `SCHEMES`: AABB (default), AAAA, ABAB, AA_A, A_A_,
  aAaA, aAbB, aBaB, aA_A, _AaA, _A_A_B_B, plus saved custom schemes; one letter per bar, same letter = same rhyme,
  UPPERCASE = word shown, lowercase = outline with the word hidden, _ = no rhyme; "_A_A_B_B" is written over 8 bars
  and is "_A_A" on the repeating 4-bar grid. Word visibility all/first/last applies to the all-uppercase presets
  only (hidden for lowercase ones). A single "2-syllable rhymes" toggle button makes every preset rhyme 2-syllable (`G.multi`,
  localStorage `fs-syl`); custom schemes set it per rhyme in Build. 4x4 grid, drag the column for presets) with a **Build**
  button, then the beat library (Trap / Boom bap tabs: `LIB_TAB`, by each beat's `feel`; uploads with no feel yet
  show in both) and START SESSION.
- **Scheme model**: every scheme is a list of rhyme groups `{cells:[{r,c,show}]}` over the 4x4 grid (rows = bars 1-4,
  cols = beats 1-4), repeated every 4 bars. Presets are generated as groups (`presetGroups`); custom ones live in
  `G.custom`. `cellMap` + `wordFor` give each cell its word: each group draws from one `BANK` rhyme family, and each
  4-bar block moves on to fresh families. Saved schemes are kept in localStorage `fs-schemes`.
  A group with `multi:true` uses 2-syllable words from `BANK2` instead. `BANK2` is generated by
  `tools/build_rhymes.py`, which overwrites the `// RHYME2-BEGIN` ... `// RHYME2-END` block in index.html
  (see "2-syllable rhyme bank" below). It picks a family with at least min(group size, 6) words.
  Every PLAY calls `rerollWords()`: it shuffles the family order for both banks (no repeats until a bank runs out)
  and sets a random rotation inside each family, limited to its group-size + 2 most common words. So every session
  gets different rhymes, and the setup grid shows the last session's words.
- **Rhyme builder** (`#build-screen`): a full-page overlay that opens with a clip-path circle growing out of the Build
  button. It starts with an empty Rhyme A. Clicking an empty box adds it to the active rhyme (shown); clicking a shown
  word hides it; clicking a hidden one removes it. "+ Create new rhyme" starts the next group, and chips switch or
  delete groups. A "2-syllable" toggle switches the active group to `BANK2` words. Confirm applies the scheme;
  Save rhyme scheme stores or updates it by name.
- **Session screen**: 2 prep bars then 32 bars, 4 cells per bar; current cell highlights, rhyme
  word reveals on its beat. Esc or STOP closes it.
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

## 2-syllable rhyme bank

- Only pure single-word feminine rhymes for now (fiction/friction, autumn/bottom). Slant, near and multi-word
  rhymes are planned later.
- Sources (cached in gitignored `tools/.cache/`): CMU Pronouncing Dictionary (pronunciations), Hunspell en_US
  (lowercase stems only, which drops names and inflected duplicates), the `wordfreq` package (Zipf >= 2.5), and
  the LDNOOBW blocklist plus `EXTRA_BLOCK`.
- Rhyme key = the phones from the primary-stressed second-to-last vowel to the end (the last vowel must be
  unstressed). Stressed AO counts as AA except before R (cot-caught merger). Unstressed AH0/IH0/UH0 count as
  one schwa.
- Each family keeps one word per onset (the consonants before the stressed vowel), the most common one, so no
  pair is an identical rhyme. That is why diction is dropped in favour of addiction.
- Regenerate with `pip install wordfreq` then `python tools/build_rhymes.py`. Currently 800 families,
  3233 words, 26 KB.

## Drop detection (long intros)
- Every song gets exactly 8 prep beats (PREP_BARS=2) right before the drop: playback starts at drop - 2 bars, bar 1
  of the 32 lands on the drop, and the loop repeats from the drop (never the intro). If the drop comes less than
  8 beats into the song, the missing prep beats are a click count-in (`P.countIn`).
- detectDrop(it,anchor) works per beat on the stored kick/hat/low bands (beatScores). "Full level" = the 75th
  percentile of 4-bar averages. The drop is the first beat whose next 4 bars reach DROP_FULL x full and
  DROP_JUMP x the 4 bars before, with no 4-bar stretch before it above DROP_QUIET (0.65) x full. A song that starts full
  gets no drop, so a later breakdown is never picked. Refined to the sharpest 4-beat step.
- anchor=true on fresh analysis (upload, Re-analyze): drops land on a "1", so the grid's downbeat moves onto the
  drop, as far as the groove allows: trap (snare on 3) keeps the grid; boom bap may move the "1" by 2 beats
  (kick 1/3 ambiguity) but never 1; an unclear groove follows the drop. A bar line within a beat of the sharpest
  step wins if it is nearly as sharp (fills and risers). anchor=false after hand edits, Auto and old saved beats: the
  grid stays, and the drop snaps to its nearest bar line.
- Stored as `dropT` (seconds) plus `dropManual`. The DROP row (+-1/+-4 bars, Auto) was removed from the UI on
  2026-11-06 at Chris's request; the code paths (`dropManual`, `regridDrop`) stay. The waveform shades P1/P2 and
  marks "1 DROP".
- Tested on synthetic beats (boom bap 85-95, trap 140-150, intros of 0/1/4/8/16 bars, hats-only or 25% drums in the
  intro, breakdowns in songs that start full): drop within 2 ms. Drums at half volume in the intro read as "beat
  already in". Not yet tuned on real songs.

## Default beats (for everyone)
- Audio lives in `beats/`. `const DEFAULTS` in index.html holds each beat's pre-analyzed grid: bpm, fd (first downbeat),
  dropT, feel, engine, duration. The library lists them under DEFAULT BEATS, between your uploads and the
  metronomes. New visitors start on the first one.
- ensureBuf() fetches a default's audio the first time it is picked (row shows "loading..."), then caches it in
  BUF for the session. Default beats are read-only: no delete, and `#detail.ro` hides the edit buttons
  (preview and click toggle stay). The fetch needs a web origin, so they don't play in the Claude artifact.
- To add one: copy the mp3 into beats/, run analyzeBuffer + runBT + checkFeel + detectDrop(it,true) on it in the
  browser (localhost), check the result, and add a row to DEFAULTS.
- Current set (analyzed 2026-11-06 with Beat This!): Ominous 134.01 trap, drop bar 9 (14.44 s); J. Cole type 1 93.03
  boom bap, drop bar 7 (18.05 s); J. Cole type 2 89.17 boom bap, drop bar 5 (10.92 s); Guitar 137.98 trap, drop bar 17
  (28.04 s); 93 103.09 boom bap, drop bar 9 (19.38 s); Still Tippin' 143.16 trap, no intro. Guitar and Still Tippin'
  were re-timed as trap by hand (Beat This! counted them at half speed): setFeel(it,"trap") doubled the tempo and put
  the snare on 3 (confirmed: snare strongest on beat 3).
  J. Cole type 2 was hand-corrected: checkFeel read its busy hi-hats as half-time trap and doubled it to 178.
  Ominous, Guitar and both J. Cole type beats are Chris's own Suno tracks.

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
  blocks both, so there it silently falls back to the built-in detector (the "Re-analyze with Beat This!" button
  was removed from the UI on 2026-11-06). Real use = GitHub Pages: https://zchris07.github.io/freestyle/ and the custom domain https://freestyle.wtf (CNAME file in repo root; domain bought by Chris on Nov 6 2026).
  Pages was enabled 2026-11-05 and deploys from `main` /, so every push to main updates the site within a minute or two.
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

- Local preview: serve the folder over HTTP (the in-app browser blocks `file://`):
  `python -m http.server 8000`, saved as the `freestyle` config in `.claude/launch.json`.
- Test the detector without real audio by synthesizing kick/snare/hat loops into an `AudioBuffer`
  and calling `analyzeBuffer(buf)` from the console (globals are top-level in `index.html`).
- Artifact constraints: external stylesheets/fetches are blocked by CSP, so keep everything inline
  and use text glyphs for icons. The page must work at phone width.
- Link preview: `og-image.png` (1200x630) is rendered from `tools/og-image.html` with headless Chrome (the command is in
  that file). It shows only the freestyle.wtf wordmark and a rhyme grid, no tagline. `og:title` is "freestyle.wtf".
- Commits end with: `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Feel check (trap vs boom bap)
- analyzeBuffer keeps 3 onset bands per item: kick (<150 Hz), snr (150-3000 Hz), hat (3-8 kHz).
- checkFeel(it) runs after every detection (built-in and Beat This!). grooveProfile() gives per-beat kick/snare
  strength and hi-hat strength at each 1/8 of a beat.
- Trap counted at half speed: bpm<100, snare on 2+4 (FEEL_SNARE24) and hats in the 1/8-beat gaps (FEEL_HAT_FILL,
  i.e. 16ths of the real tempo) -> tempo doubled, then trapDownbeat() puts kick on 1 and snare on 3.
- Boom bap counted at double speed: bpm>=120, hats only on the beat (FEEL_HAT8_MAX), one snare per bar -> halved.
- Known gap: trap with only 8th-note hats looks identical to 16th-hat boom bap at half the tempo; the FEEL toggle
  (Trap / Boom bap) in the detail panel fixes it by hand. Older saved beats get the bands via upgradeFeel() on load.
- Tested on synthetic loops only (trap 140/150, boom bap 75/85/90/98); thresholds not yet tuned on real songs.

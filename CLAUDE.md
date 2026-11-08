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
  `#b49bc8`, white. A rhyme cell has a 2px outline and word text in its group's color. A hidden ("improvised")
  rhyme box has a fainter, thinner outline in its group's colour (1px at 50%) and shows no word on the setup grid
  and in sessions (in the builder its word is faded and struck).
- No panel numbering.
- Layout: the top bar with the "freestyle.wtf" wordmark top-left (".wtf" in green, no caption) has no colour of its
  own: it sits on the page background (`#121212`). At 1000px and wider, setup is two columns (rhyme scheme | beat
  library + START SESSION, 1.45fr : 1fr, max 1440px, centred) with bigger grids; below that a single 840px column. The session screen (`#perf-screen`, `#191414`) is a full-window overlay
  with its own wordmark row, content centred at about 1040px. Phones (640px and below) get edge-to-edge content and a 50px top bar.
- Keep it minimal: no caption under the scheme pills, no "Beat timing" label or drag instructions (just "← drag →"
  under the rhyme column), no upload instructions (the button says "+ Upload beat"), no notes under the library.
  Under the library only TEMPO (+ DOWNBEAT for uploads) and CHECK (Preview, "Play metronome during session") remain:
  no click-only tempos, no feel / drop / grid-by rows. Button labels: "Preview", "START SESSION". The session screen shows only the beat name and STOP on top, then
  the bar grid with no bar/prep labels, no beat numbers in the cells and no status texts (no PREPARE / SPIT IT!).
  The lit outline is the beat indicator; STOP turns into BACK after bar 32.
- Wants to upload many trap and boom bap beats and have the metronome indicator structured correctly.
- Motion: on every load the page is carved out, not grown. Containers and buttons (`CARVE_SEL`) get a rounded
  outline drawn on as an SVG stroke, then their fill and real border fade in, and the drawn line fades away. Small
  pieces (`ASSEMBLE_SEL`: beat dots, checkbox, drag arrows) fly in and lock into place, and the waveform wipes on.
  All text writes itself in with the football explainer's writing animation (`runIntro`, `carveOutline`, `writeWord`:
  an SVG copy of each word, each letter's outline stroked on then inked; words 1/60 s apart, letters 14 ms).
  Everything is staggered from the top left, and children start 180 ms after their container.
  Each outline starts at a random point on its edge (rect `pathLength="100"`, a growing dash from a random
  `--off`), about half run counter-clockwise (mirrored rect), and each takes 0.65-0.9 s. A shape fills in when its
  own outline completes (`g.dataset.dur`).
  The intro must end exactly where the page rests: each text run is wrapped in one inline `.wl` span (words as
  `.w` inside it), so in flex boxes like START SESSION or the metronome label the words stay one flex item and don't
  pick up the box's gap. Nothing shifts when the intro hands back plain text.
  Assemble selectors must target icons only (`.tab > svg:not(.carve-svg)`, `.drop > svg:not(.carve-svg)`): a loose
  `.x svg` also catches the drawn copies of words and the outline overlays, which then fly in and snap at the end.
  Once written, the drawn SVG letters stay on screen, inked (`inkWords`), like the football explainer does: swapping
  them for real text made the words look a touch bolder at the last moment. Real text takes over only on a window
  resize (`plainWords`) or when an element's text is replaced. The upload dialog does the same.
  The intro must start from a blank page: the empty starting state is set with transitions switched off (`.notrans`),
  otherwise the finished page visibly fades away first. Outline colours are read before an element is emptied. A
  1px `.paint-dot` in the page colour gives the browser an early paint, so a refresh doesn't keep showing the
  previous page. The session opens as a clip-path circle growing out of START SESSION and collapses into
  the STOP button, or into the freestyle.wtf logo when that is clicked during a session (it goes home).
  The session's logo (`#p-home`) never animates: it has no rise-in, and `startPerf` copies the page logo's
  inked letters into it, so it sits on the same pixels and the bubble's edge passes over it with no visible change.
  `sessionOrigin(el)` snaps the circle's centre onto the element with transitions off first, so it never slides
  across the screen from where it last closed.
- Upload: no upload panel in the library. An upload chip (inline SVG icon) next to the Trap / Boom bap tabs opens
  `#upload-modal` over the page. The page doesn't move or darken: it is only blurred by a frosted-glass overlay
  (`backdrop-filter`), and the dialog is drawn in like the intro (`drawIn`: outlines, fill, written text). Drop files or click to browse.
  Beat style Auto (default, reset each time) / Trap / Boom bap: Auto runs checkFeel, the others setFeel
  (`addFiles(files,feel)`).
- wtf? button top right (plain green text, no outline; hover only darkens the green) opens `#guide`, a full-page guide that grows as a circle out of the button with its
  sections rising in: how to use every part of the site, plus "every other freestyle app out there right now is ass"
  under "Why tf does this exist?" (plain body text) and "Who tf made ts?" with "christopher" linking to
  https://github.com/zchris07. The sections are plain text on the background, no boxes. All text (title, lead,
  headings, paragraphs, Got it) shares one left edge; the X close button and the section numbers (green 36px
  circles: 1-4, "?" for the why and who sections) sit in a 36px gutter 14px to its left (`--gut`, `--gap`).
  The guide has its own static logo (`#g-home`, a copy of the page logo's inked letters made in `openGuide`, same spot,
  no animation). It closes around whatever closed it (`closeGuide(e)`, `guideOrigin(el)` snaps the centre): the X, Got
  it, or the logo (home); Esc closes into the wtf? button.
- Session title: the beat name is large (26px, 34px wide, 21px phone). The session's boxes pop in, staggered like
  the builder grid (`.bars-scroll.pop`).
- Session controls: PAUSE / RESUME next to STOP (Space toggles it). Pause suspends the AudioContext, so the beat,
  the clicks and the beat clock stop together. Both "2 syllable" toggles say only "2 syllable" and show their state
  by colour (main: green when on; builder: filled in the active rhyme's colour when on).
- Dragging (every preset, incl. the extras under "more"): the rhymes are their own layer (`.rhyme-col`) above a full
  grid of empty boxes, so the boxes they leave stay visible. The layer spans the scheme's columns (`shapeOf`: [0] for
  column schemes, [0,2] for two-beat ones, `--n` columns wide with the middle one empty; only rhyme boxes catch the
  pointer). `G.rhymeCol` is the scheme's last rhyme column (default 3); `lastCol()`/`firstCol()` clamp it per scheme. While held it glides through strong magnetic detents (clings to each column, exponent
  3.4, then jumps across) and resists hard past the ends (x0.12). On release it drops straight into the nearest column
  with no settling motion; only a tap on the hint glides one step. No lean, wobble, vibration or overshoot (Chris asked).
  One state and one rAF loop per column, so a quick re-grab carries on (`setupDrag`). While held, the column it would
  land in, the one it came from included, is shaded green (`.gcell.target`, background only, no outline). The drag hint is a "← DRAG →" capsule below
  the rhyme scheme panel, under the column (`placeHint`; kept inside the panel, with its pointer tip shifted over
  the column). It can be dragged to move the column, and a tap on its left or right half steps the column one beat.
  It fades out on grab and back in after landing.
- Tiles (`.gcell`, `.bcell`, `.pcell`) lift under the cursor by growing to scale(1.05) with a deeper shadow, as if
  brought closer to the viewer (`@media (hover:hover)` only). No sideways or upward movement.
- No text cursor or text selection anywhere (`body{cursor:default;user-select:none}`), except real text inputs.
- Preview beat indicator: during the 8 prep beats no box is lit. Instead, once as the preview starts, a wave lifts
  the tiles (flat, no tilt: each grows to scale(1.08) as if brought toward the viewer, with a deeper shadow, the same
  kind of lift as the hover; Web Animations) diagonally from one corner to the opposite one (crossing in ~0.8
  of a beat, each tile's lift ~1.35 beats, max 780 ms; `waveTiles`). Each Preview click moves the starting corner clockwise (TL, TR, BR, BL; `WAVE_CORNER`). From the
  drop, the current beat's box lights its outline (`lightGridBeat`), starting top left and looping round the 4 bars. The draggable
  rhyme column's box lights in its colour. While the column is held mid-preview, the indicator treats it as resting in
  the column it hovers over (`DRAG_COL`, `relightGrid`) and lights the rhyme box there instead of the empty box.
- Hover audition: hovering a library row for 0.5 s plays that beat from where a session's first prep bar starts
  (8 beats before the drop, or the top if the drop comes sooner), without selecting it
  (`audHover`; default beats start loading on hover, quietly). It works during Preview too, which is ducked to 12%
  through `playerBus()`. The row's background becomes a live mirrored silhouette of the sound (`.lwave` canvas, an
  AnalyserNode's frequency bands with a travelling ripple). The silhouette first draws its own quiet floor (amplitude
  0.04, a ~1.4px line) from the row's left edge to its right edge from 0.15 s to 0.5 s (ease in-out), then the beat
  swells it into the waveform. No glow, no separate brighter line. While drawing, the line is evenly green (.30) so
  it reads to the right edge; from the beat's start the right end eases to the original fade (.30 -> .12) in 0.4 s,
  after which it is pixel-identical to the original waveform (Chris asked for that original look to stay). Clicking the
  beat being heard selects it and keeps it playing. It survives list re-renders (`audReattach`) and stops
  on leaving the row or on a click elsewhere in the list. On phones a long press is the hover: hold a row 0.5 s to
  play it, lift (or scroll) to stop; a press of 500 ms+ doesn't select on release (`AUD.noClick`), a quick tap does. Rows
  suppress the long-press menu. Phones only unlock audio on a tap, so the first tap anywhere wakes the
  AudioContext; until then a hover or long press stays silent.
- Session beat indicator: the current box lights up its outline (border + glow) and is never filled, so a rhyme
  word stays readable (a plain beat in green, a rhyme in its group's color).

## Architecture (all in `index.html`)

- **Setup screen**: one "RHYME SCHEME" panel. Its top is two columns (`.scheme-controls`): scheme chips on the left,
  and on the right a fixed "Show words" cluster with "2 syllable rhyme" under it, behind a divider that never moves.
  The first chip row never changes: AABB (default), AAAA, ABAB, AA_A and a green "more" chip, which turns into "<" in
  place. The extras (A_A_, aAaA, aAbB, aBaB, aA_A, _AaA) open in their own row below (`#scheme-more`, only its height
  glides, `toggleMore`). There is no delay either way, and opening or folding can interrupt each other. Saved custom schemes sit in a row under that. For custom schemes the right cluster dims
  instead of hiding. Below 700px of panel width (a container query) the cluster stacks under the chips. Column schemes (AABB, AAAA, ABAB, AA_A, A_A_): one letter per bar, same letter = same rhyme, _ = none.
  All presets are draggable (see "Dragging"); A_A_ starts on beat 4 like the others. Two-beat schemes (`SCHEMES[k]` is an array of 2 bars):
  per bar the beat-2 letter (lowercase) then the beat-4 letter (UPPERCASE); bars 3-4 repeat the shape with fresh
  rhymes. aAaA = beats 2+4 of both bars one rhyme; aAbB = a new rhyme each bar; aBaB = the 2s rhyme, the 4s rhyme;
  aA_A = bar 2 has no beat-2 rhyme; _AaA = bar 1 has no beat-2 rhyme. Draggable as a pair of columns two beats
  apart: beats 2+4 (default) or 1+3. "Show words" all/first/last
  works per rhyme group for every preset. A single "2-syllable rhymes" button (`#syl-main`, `G.multi`, localStorage
  `fs-syl`) makes preset rhymes 2-syllable; custom schemes set it per rhyme in Build (`#syl-btn`). 4x4 grid, with a
  **Build**
  button, then the beat library (Trap / Boom bap tabs: `LIB_TAB`, by each beat's `feel`; uploads with no feel yet
  show in both) and START SESSION.
- **Scheme model**: every scheme is a list of rhyme groups `{cells:[{r,c,show}]}` over the 4x4 grid (rows = bars 1-4,
  cols = beats 1-4), repeated every 4 bars. Presets are generated as groups (`presetGroups`); custom ones live in
  `G.custom`. `cellMap` + `wordFor` give each cell its word: each group draws from one rhyme family of `BANK`
  (true one-syllable words only, no "routine" or "guarantee": 215 families / 2000 words, generated by
  tools/build_rhymes.py between the `// RHYME1-BEGIN` markers). With "2 syllable" off, every word comes from `BANK`,
  and each 4-bar block moves on to fresh families. Saved schemes are kept in localStorage `fs-schemes`.
  A group with `multi:true` uses 2-syllable words from `BANK2` instead. `BANK2` is generated by
  `tools/build_rhymes.py`, which overwrites the `// RHYME2-BEGIN` ... `// RHYME2-END` block in index.html
  (see "2-syllable rhyme bank" below). It picks a family with at least min(group size, 6) words.
  Every PLAY calls `rerollWords()`: it shuffles the family order for both banks (no repeats until a bank runs out),
  and for each family it uses, a fresh random order of its best-known words (a window of max(group size + 4, 8)).
  A group draws from families with enough words for it (up to 8 for 1-syllable, 6 for 2-syllable). So every
  session deals different rhymes in a different order, and the setup grid shows the last session's words.
- **Rhyme builder** (`#build-screen`): a full-page overlay that opens with a clip-path circle growing out of the Build
  button. It starts with an empty Rhyme A. Clicking an empty box adds it to the active rhyme (shown); clicking a shown
  word hides it; clicking a hidden one removes it. "+ Create new rhyme" starts the next group, and chips switch or
  delete groups. The "2 syllable" toggle switches only the active rhyme group to `BANK2` words. No instruction text. Confirm applies the scheme;
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
  DROP_JUMP x the 4 bars before, with no full 4-bar stretch before it above DROP_QUIET (0.65) x full (a single loud
  opening hit doesn't count). A song that starts full
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
  boom bap, drop bar 8 (20.63 s, moved one bar later by ear); J. Cole type 2 89.17 boom bap, drop bar 5 (10.92 s); Guitar 137.98 trap, drop bar 17
  (28.04 s); 93 103.09 boom bap, drop bar 9 (19.38 s); Still Tippin' 143.16 trap, no intro. Guitar and Still Tippin'
  were re-timed as trap by hand (Beat This! counted them at half speed): setFeel(it,"trap") doubled the tempo and put
  the snare on 3 (confirmed: snare strongest on beat 3).
  J. Cole type 2 was hand-corrected: checkFeel read its busy hi-hats as half-time trap and doubled it to 178.
  Memphis 128.81 trap, drop bar 9 (15.26 s): Beat This! tracks its intro at half speed and the rest at full speed,
  so its grid fails the steadiness check. The built-in grid is used, and was checked against Beat This!'s
  main-section beats (they line up, and 40 of 49 of its downbeats fall on beat 1). Minor 134.8 trap (Beat This!
  said 67.4), snare on 3, drop bar 9 (14.47 s).
  NYSOM 84.48 boom bap, drop bar 9 (22.81 s), set by hand from Chris's ear (~23 s) (checkFeel misread it as half-time trap and doubled it to 169, like J. Cole type 2;
  set to boom bap by hand). Probably the "N.Y. State of Mind" instrumental, a commercial track like Still Tippin'
  and 93; Chris chose to host those.
  Molly 109.95 trap (Beat This! and the built-in detector agree; snare strongly on 3), drop bar 9 (17.46 s).
  Downloaded from a streaming site like Still Tippin'.
  P.I.M.P. 85.17 boom bap (first downbeat at 1.9 s after a pickup, so 6 clicks lead in), no intro. C.R.E.A.M. 90.09
  boom bap, drop bar 9 (21.34 s), set by hand from Chris's ear: its first 8 bars sit at ~72% of full energy, which
  the detector reads as "drums already in".
  Both are commercial instrumentals (50 Cent, Wu-Tang) that Chris chose to host.
  Electric 98.03 boom bap (Beat This!, the built-in detector and checkFeel all agree), drop bar 7 (15.41 s), set by
  hand from Chris's ear (~16 s). The intro is only slightly quieter than the rest, so the detector can't see it.
  From a streaming site, no tags; possibly ATCQ's "Electric Relaxation" (unconfirmed).
- Drop detection only sees intros that are clearly quieter than the beat (below 65% of full energy). Drums-in
  intros like C.R.E.A.M., Electric and NYSOM need the drop set by hand in DEFAULTS.
  Ominous, Guitar, both J. Cole type beats, Memphis and Minor are Chris's own Suno tracks.
- Known issue: checkFeel's hi-hat test (FEEL_HAT_FILL) misreads busy-hat boom bap as half-time trap (2 of 4 real
  boom bap beats so far), which doubles the tempo and files an upload under Trap.

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

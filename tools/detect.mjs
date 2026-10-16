#!/usr/bin/env node
// Usage: node tools/detect.mjs <audio file...> [--out <dir>]
// Decodes with ffmpeg, runs the beat detector, and writes for each input:
//   <name>.grid.json  tempo, downbeat, per-bar beat times (human-readable)
//   <name>.grid.csv   one row per beat: time_sec,bar,beat
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { basename, extname, join } from "node:path";
import { analyze } from "./detector.mjs";

const SR = 44100;

export function decode(file) {
  const r = spawnSync("ffmpeg", ["-v", "error", "-i", file, "-t", "150", "-ac", "1", "-ar", String(SR), "-f", "f32le", "-"],
    { maxBuffer: 1 << 29 });
  if (r.status !== 0) throw new Error("ffmpeg failed: " + String(r.stderr).trim());
  const b = r.stdout;
  return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength - (b.byteLength % 4)));
}

const r3 = (x) => Math.round(x * 1000) / 1000;

export function buildGrid(file, samples) {
  const a = analyze(samples, SR);
  const spb = 60 / a.bpm, barLen = 4 * spb, span = samples.length / SR;
  const bars = [], rows = ["time_sec,bar,beat"];
  for (let k = 0; a.firstDownbeat + k * barLen + 0.001 < span; k++) {
    const start = a.firstDownbeat + k * barLen;
    const beats = [0, 1, 2, 3].map((i) => start + i * spb).filter((t) => t < span).map(r3);
    bars.push({ bar: k + 1, start_sec: r3(start), beats_sec: beats });
    beats.forEach((t, i) => rows.push(`${t},${k + 1},${i + 1}`));
  }
  const json = {
    file: basename(file),
    detector: "freestyle-comb-v1",
    duration_sec: r3(span),
    analyzed_sec: r3(a.analyzedSeconds),
    tempo: {
      bpm: a.bpm,
      confidence: r3(a.confidence),
      alternatives: a.alternatives.map((x) => ({ label: x.label, bpm: x.bpm, first_downbeat_sec: r3(x.firstDownbeat) })),
    },
    meter: { beats_per_bar: 4, first_downbeat_sec: r3(a.firstDownbeat), downbeat_confidence: r3(a.downbeatConfidence) },
    notes: "Constant tempo and 4/4 assumed. If bpm is half or double the felt tempo, use an alternative.",
    bars,
  };
  return { json, csv: rows.join("\n") + "\n" };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2), files = [];
  let out = "beats/grids";
  for (let i = 0; i < args.length; i++) { if (args[i] === "--out") out = args[++i]; else files.push(args[i]); }
  if (!files.length) { console.error("usage: node tools/detect.mjs <audio file...> [--out dir]"); process.exit(1); }
  mkdirSync(out, { recursive: true });
  for (const f of files) {
    const { json, csv } = buildGrid(f, decode(f));
    const stem = join(out, basename(f, extname(f)));
    writeFileSync(stem + ".grid.json", JSON.stringify(json, null, 2) + "\n");
    writeFileSync(stem + ".grid.csv", csv);
    console.log(`${json.file}: ${json.tempo.bpm} BPM (conf ${json.tempo.confidence}), downbeat at ${json.meter.first_downbeat_sec}s -> ${stem}.grid.json`);
  }
}

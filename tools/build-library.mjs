#!/usr/bin/env node
// Validates beats/library.json, inlines it into index.html (the app has no fetch: CSP blocks it
// when published as an artifact), and writes beats/library.md, a readable drum-tab of every beat.
// Usage: node tools/build-library.mjs [--check]
import { readFileSync, writeFileSync } from "node:fs";

const lib = JSON.parse(readFileSync("beats/library.json", "utf8"));
const VOICES = new Set(["kick", "snare", "clap", "rim", "hat", "ohat", "shaker"]);
const LENGTHS = new Set([8, 12, 16, 24, 32]);
const errors = [];
const ids = new Set();

for (const b of lib.beats) {
  const at = (m) => errors.push(`${b.id}: ${m}`);
  if (ids.has(b.id)) at("duplicate id"); ids.add(b.id);
  if (!(b.bpm >= 40 && b.bpm <= 260)) at("bpm out of range");
  if (!(b.swing >= 0 && b.swing <= 0.5)) at("swing must be 0..0.5");
  if (!Number.isInteger(b.bars) || b.bars < 1) at("bars must be a positive integer");
  for (const [name, bars] of Object.entries(b.tracks)) {
    if (!VOICES.has(name.replace(/\d+$/, ""))) at(`unknown voice ${name}`);
    if (!Array.isArray(bars) || b.bars % bars.length) at(`${name}: needs a divisor of ${b.bars} bar strings`);
    for (const s of bars) {
      if (!LENGTHS.has(s.length)) at(`${name}: "${s}" has ${s.length} steps (allowed ${[...LENGTHS]})`);
      if (/[^Xxo.]/.test(s)) at(`${name}: "${s}" has an invalid symbol`);
    }
  }
  if (b.bass) {
    if (b.bars % b.bass.length) at(`bass: needs a divisor of ${b.bars} bars`);
    for (const bar of b.bass) for (const n of bar) {
      const m = /^(\d+):([A-G][b#]?\d):(\d+)$/.exec(n);
      if (!m || +m[1] > 15 || +m[1] + +m[3] > 16) at(`bass note "${n}" is malformed or runs past the bar`);
    }
  }
}
if (errors.length) { console.error(errors.join("\n")); process.exit(1); }

// readable drum tab
const md = ["# Notated beat library", "", "Generated from `beats/library.json` by `tools/build-library.mjs`. Do not edit by hand.", "",
  "`X` accent · `x` hit · `o` ghost · `.` rest. One row per track, one block per bar, `|` marks each beat.", ""];
const beatsOf = (s) => { const n = s.length / 4; return [0, 1, 2, 3].map((i) => s.slice(i * n, (i + 1) * n)).join("|"); };
for (const b of lib.beats) {
  md.push(`## ${b.name}`, "", `${b.bpm} BPM · ${b.style} · swing ${b.swing} · ${b.bars}-bar loop · ${b.count}`, "", "```");
  for (let bar = 0; bar < b.bars; bar++) {
    md.push(`bar ${bar + 1}`);
    for (const [name, bars] of Object.entries(b.tracks)) md.push(`  ${name.padEnd(7)} ${beatsOf(bars[bar % bars.length])}`);
    if (b.bass) md.push(`  ${"bass".padEnd(7)} ${b.bass[bar % b.bass.length].join("  ")}`);
  }
  md.push("```", "");
}
const check = process.argv.includes("--check");
const mdText = md.join("\n");
const html = readFileSync("index.html", "utf8");
const re = /(<script id="beat-library" type="application\/json">)[\s\S]*?(<\/script>)/;
if (!re.test(html)) { console.error('index.html has no <script id="beat-library"> block'); process.exit(1); }
const next = html.replace(re, (_, a, z) => a + "\n" + JSON.stringify(lib.beats) + "\n" + z);
if (check) {
  const stale = next !== html || readFileSync("beats/library.md", "utf8") !== mdText;
  console.log(stale ? "library is out of date: run node tools/build-library.mjs" : "library is up to date");
  process.exit(stale ? 1 : 0);
}
writeFileSync("index.html", next);
writeFileSync("beats/library.md", mdText);
console.log(`${lib.beats.length} beats validated; index.html and beats/library.md updated`);

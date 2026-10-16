#!/usr/bin/env node
// Renders every notated beat with the app's own synth (headless Chromium, OfflineAudioContext), runs the
// beat detector on the audio, and compares the result with the notation's bpm and downbeat.
// OK = primary result matches; OCTAVE = the notated tempo is the half/double-time alternative (inherent ambiguity);
// FAIL = neither matches. Only FAIL (or a page error) gives a non-zero exit code.
// Usage: node tools/verify.mjs [--bars 16] [--export <dir>]   (--export also writes each render as a 16-bit mono WAV)
// Needs playwright; a global install works.
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { analyze } from "./detector.mjs";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = require(require("node:child_process").execSync("npm root -g").toString().trim() + "/playwright")); }

const bi = process.argv.indexOf("--bars"), BARS = bi > 0 ? +process.argv[bi + 1] : 16;
const SR = 44100;
const ei = process.argv.indexOf("--export"), EXPORT = ei > 0 ? process.argv[ei + 1] : null;
if (EXPORT) mkdirSync(EXPORT, { recursive: true });
function wav(x) {
  const n = x.length, b = Buffer.alloc(44 + n * 2);
  b.write("RIFF", 0); b.writeUInt32LE(36 + n * 2, 4); b.write("WAVEfmt ", 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write("data", 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.max(-1, Math.min(1, x[i])) * 32767 | 0, 44 + i * 2);
  return b;
}
const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
const page = await browser.newPage();
const pageErrors = [];
page.on("pageerror", (e) => pageErrors.push(e.message));
await page.goto("file://" + resolve("index.html"));

const beats = await page.evaluate(() => BEATS.map((b) => ({ id: b.id, name: b.name, bpm: b.bpm })));
let fails = 0, octave = 0;
console.log("beat".padEnd(18), "notated".padEnd(9), "detected".padEnd(9), "downbeat(ms)".padEnd(13), "alt tempos");
for (const b of beats) {
  const b64 = await page.evaluate(async ([id, bars, sr]) => {
    const buf = await renderBeat(BEATS.find((x) => x.id === id), bars, sr);
    const d = buf.getChannelData(0), u8 = new Uint8Array(d.buffer, d.byteOffset, d.byteLength);
    let s = ""; for (let i = 0; i < u8.length; i += 0x8000) s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    return btoa(s);
  }, [b.id, BARS, SR]);
  const raw = Buffer.from(b64, "base64");
  const x = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
  if (EXPORT) writeFileSync(join(EXPORT, b.id + ".wav"), wav(x));
  const a = analyze(x, SR), bar = 4 * 60 / b.bpm;
  // distance of a detected downbeat to bar 1 (the render starts on the downbeat), wrapping around the bar
  const dist = (fd) => Math.min(fd, bar - fd) * 1000;
  const good = (t) => Math.abs(t.bpm - b.bpm) <= 0.3 && dist(t.firstDownbeat) <= 15;
  const alt = a.alternatives.find((t) => Math.abs(t.bpm - b.bpm) <= 0.3);
  const status = good({ bpm: a.bpm, firstDownbeat: a.firstDownbeat }) ? "OK"
    : alt && good(alt) ? "OCTAVE" : "FAIL";
  if (status === "FAIL") fails++;
  if (status === "OCTAVE") octave++;
  console.log(b.id.padEnd(18), String(b.bpm).padEnd(9), String(a.bpm).padEnd(9), dist(a.firstDownbeat).toFixed(1).padEnd(13),
    a.alternatives.map((t) => t.bpm).join("/").padEnd(14), status);
}
await browser.close();
if (pageErrors.length) { console.log("page errors:", pageErrors.join("; ")); fails++; }
console.log(`${beats.length - fails - octave} ok, ${octave} found only as the half/double-tempo alternative, ${fails} wrong`);
process.exit(fails ? 1 : 0);

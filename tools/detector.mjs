// Beat detector: the same algorithm the app used to run in-browser, as a pure function
// over mono samples. 1024-pt FFT at 100 fps -> 3-band log spectral flux -> local-mean
// subtraction -> comb-filter tempo sweep (log-normal prior) -> fine refine -> downbeat
// from low-band energy. Assumes constant tempo and 4/4.

const FFT_N = 1024;
const PRIOR_CENTER = 120, PRIOR_SIGMA = 0.6, ALPHA = 0.5;
const MAX_SECONDS = 150;

const rev = new Uint16Array(FFT_N), cosT = new Float32Array(FFT_N / 2), sinT = new Float32Array(FFT_N / 2), win = new Float32Array(FFT_N);
(() => {
  const bits = Math.log2(FFT_N);
  for (let i = 0; i < FFT_N; i++) { let r = 0; for (let b = 0; b < bits; b++) if (i & (1 << b)) r |= 1 << (bits - 1 - b); rev[i] = r; }
  for (let i = 0; i < FFT_N / 2; i++) { cosT[i] = Math.cos(2 * Math.PI * i / FFT_N); sinT[i] = -Math.sin(2 * Math.PI * i / FFT_N); }
  for (let i = 0; i < FFT_N; i++) win[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (FFT_N - 1));
})();

function fft(re, im) {
  const n = FFT_N;
  for (let i = 0; i < n; i++) { const j = rev[i]; if (j > i) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
  for (let size = 2; size <= n; size <<= 1) {
    const half = size >> 1, step = n / size;
    for (let i = 0; i < n; i += size) {
      for (let j = 0, k = 0; j < half; j++, k += step) {
        const wr = cosT[k], wi = sinT[k], a = i + j, b = a + half;
        const tr = re[b] * wr - im[b] * wi, ti = re[b] * wi + im[b] * wr;
        re[b] = re[a] - tr; im[b] = im[a] - ti; re[a] += tr; im[a] += ti;
      }
    }
  }
}

function combSum(o, period, phase) {
  let s = 0, c = 0; const L = o.length - 1;
  for (let t = phase; t < L; t += period) { const i = t | 0, f = t - i; s += o[i] * (1 - f) + o[i + 1] * f; c++; }
  return c ? s / Math.pow(c, ALPHA) : 0;
}
const prior = (bpm) => { const x = Math.log2(bpm / PRIOR_CENTER) / PRIOR_SIGMA; return Math.exp(-0.5 * x * x); };

function bestPhase(o, fps, bpm, fine) {
  const p = 60 / bpm * fps; let bs = -1, bp = 0;
  const step = fine ? 0.25 : 1;
  for (let ph = 0; ph < p; ph += step) { const sc = combSum(o, p, ph); if (sc > bs) { bs = sc; bp = ph; } }
  return { ph: bp, score: bs };
}

// Which of the 4 beat phases is "one"? Per-phase kick (low flux) and snare (mid flux) onset strength is matched
// against the two usual hip hop layouts: backbeat (snare on 2 and 4) and half-time (snare on 3), Kick favors 1.
const TEMPLATES = [
  { K: [1, 0, 0.6, 0], S: [0, 1, 0, 1] },   // backbeat
  { K: [1, 0, 0.2, 0], S: [0, 0, 1, 0] },   // half-time
];
function pickDownbeat(lo, mi, fps, bpm, ph) {
  const p = 60 / bpm * fps;
  const L = [0, 0, 0, 0], M = [0, 0, 0, 0], cnt = [0, 0, 0, 0];
  let k = 0;
  for (let t = ph; t < lo.length - 2; t += p, k++) {
    const f = Math.round(t); let l = 0, m = 0;
    for (let d = -1; d <= 1; d++) { const i = f + d; if (i >= 0 && i < lo.length) { if (lo[i] > l) l = lo[i]; if (mi[i] > m) m = mi[i]; } }
    L[k % 4] += l; M[k % 4] += m; cnt[k % 4]++;
  }
  const norm = (a) => { const v = a.map((s, q) => cnt[q] ? s / cnt[q] : 0), tot = v.reduce((x, y) => x + y, 0) || 1; return v.map((x) => x / tot); };
  const Ln = norm(L), Mn0 = norm(M);
  // snare-ness: mid onsets that are not just the click/overtone of a kick or bass hit on the same beat
  const Mn = (() => { const r = Mn0.map((m, i) => m / (m + Ln[i] || 1)), t = r.reduce((x, y) => x + y, 0) || 1; return r.map((x) => x / t); })();
  const scores = [0, 0, 0, 0];
  for (let q = 0; q < 4; q++) for (const T of TEMPLATES) {
    let sc = 0; for (let i = 0; i < 4; i++) sc += T.K[i] * Ln[(q + i) % 4] + T.S[i] * Mn[(q + i) % 4];
    if (sc > scores[q]) scores[q] = sc;
  }
  const mx = Math.max(...scores);
  for (let q = 0; q < 4; q++) if (scores[q] >= mx * 0.999) return { q, strength: scores };
  return { q: 0, strength: scores };
}

const normFd = (fd, spb) => { const bar = 4 * spb; fd %= bar; if (fd < 0) fd += bar; return fd; };

/** @param {Float32Array} x mono samples  @param {number} sr sample rate */
export function analyze(x, sr) {
  const N = FFT_N;
  const maxLen = Math.min(x.length, Math.floor(sr * MAX_SECONDS));
  const hop = Math.round(sr / 100), fps = sr / hop;
  const T = Math.floor((maxLen - N) / hop);
  if (T < 500) throw new Error("Track is too short to analyze (need 5s+).");
  const binW = sr / N;
  const kLow = Math.max(2, Math.floor(150 / binW)), kMid = Math.floor(3000 / binW), kHigh = Math.min(N / 2 - 1, Math.floor(8000 / binW));
  const re = new Float32Array(N), im = new Float32Array(N), prev = new Float32Array(N / 2);
  const lo = new Float32Array(T), mi = new Float32Array(T), hi = new Float32Array(T);
  for (let t = 0; t < T; t++) {
    const s = t * hop;
    for (let i = 0; i < N; i++) { re[i] = x[s + i] * win[i]; im[i] = 0; }
    fft(re, im);
    let l = 0, m = 0, h = 0;
    for (let k = 1; k <= kHigh; k++) {
      const mag = Math.sqrt(re[k] * re[k] + im[k] * im[k]);
      const lm = Math.log1p(1000 * mag / N);
      const d = lm - prev[k];
      if (t > 0 && d > 0) { if (k <= kLow) l += d; else if (k <= kMid) m += d; else h += d; }
      prev[k] = lm;
    }
    lo[t] = l; mi[t] = m; hi[t] = h;
  }
  const norm = (a) => { let s = 0; for (let i = 0; i < a.length; i++) s += a[i]; const mu = s / a.length || 1; for (let i = 0; i < a.length; i++) a[i] /= mu; };
  norm(lo); norm(mi); norm(hi);
  const W = Math.round(fps * 0.4);
  const makeEnv = (wl, wm, wh) => {
    const raw = new Float32Array(T);
    for (let t = 0; t < T; t++) raw[t] = wl * lo[t] + wm * mi[t] + wh * hi[t];
    const o = new Float32Array(T), cum = new Float64Array(T + 1);
    for (let t = 0; t < T; t++) cum[t + 1] = cum[t] + raw[t];
    let tot = 0;
    for (let t = 0; t < T; t++) {
      const i0 = Math.max(0, t - W), i1 = Math.min(T, t + W + 1);
      const v = raw[t] - (cum[i1] - cum[i0]) / (i1 - i0); o[t] = v > 0 ? v : 0; tot += o[t];
    }
    const om = tot / T || 1; for (let t = 0; t < T; t++) o[t] /= om;
    return o;
  };
  const o = makeEnv(1.0, 0.7, 0.3);
  const oKS = makeEnv(1.0, 1.0, 0);   // kick + snare only: hats don't vote on the tempo octave

  // coarse tempo sweep; also keep prior-free scores for the confidence figure
  let best = { sc: -1, bpm: 120, ph: 0, raw: 0 };
  const rawScores = [];
  for (let bpm = 60; bpm <= 180; bpm += 0.25) {
    const r = bestPhase(o, fps, bpm, false);
    rawScores.push(r.score);
    const sc = r.score * prior(bpm);
    if (sc > best.sc) best = { sc, bpm, ph: r.ph, raw: r.score };
  }
  let fine = { sc: -1, bpm: best.bpm, ph: best.ph };
  for (let bpm = best.bpm - 0.4; bpm <= best.bpm + 0.4; bpm += 0.02) {
    const p = 60 / bpm * fps;
    for (let ph = best.ph - 2; ph <= best.ph + 2; ph += 0.25) {
      let pp = ph; if (pp < 0) pp += p; if (pp >= p) pp -= p;
      const sc = combSum(o, p, pp);
      if (sc > fine.sc) fine = { sc, bpm, ph: pp };
    }
  }
  // Hi-hat 8ths/16ths can make 2x look like the beat. Re-score tempo/2, tempo, tempo*2 on the
  // kick+snare envelope (with the prior) and keep the winner; the phase is then refit on the full mix.
  const fitAt = (env, b) => {
    const r1 = bestPhase(env, fps, b, false), p = 60 / b * fps;
    let bs = -1, bp = r1.ph;
    for (let ph = r1.ph - 1.5; ph <= r1.ph + 1.5; ph += 0.25) { let pp = ph; if (pp < 0) pp += p; if (pp >= p) pp -= p; const sc = combSum(env, p, pp); if (sc > bs) { bs = sc; bp = pp; } }
    return { ph: bp, score: bs };
  };
  let chosen = fine.bpm, bestKS = -1;
  for (const b of [fine.bpm / 2, fine.bpm, fine.bpm * 2]) {
    if (b < 55 || b > 200) continue;
    const sc = fitAt(oKS, b).score * prior(b);
    if (sc > bestKS) { bestKS = sc; chosen = b; }
  }
  if (chosen !== fine.bpm) fine = { sc: fitAt(o, chosen).score, bpm: chosen, ph: fitAt(o, chosen).ph };

  const sorted = rawScores.slice().sort((a, b) => a - b);
  const median = sorted[sorted.length >> 1];
  const confidence = Math.max(0, Math.min(1, 1 - median / Math.max(fine.sc, 1e-9)));

  const tOff = (N / 2) / sr, toTime = (f) => f * hop / sr + tOff;
  const bpm = Math.round(fine.bpm * 100) / 100, spb = 60 / bpm;
  const { q, strength } = pickDownbeat(lo, mi, fps, bpm, fine.ph);
  const firstDownbeat = normFd(toTime(fine.ph) + q * spb, spb);
  const dbSum = strength.reduce((a, b) => a + b, 0) || 1;
  const downbeatConfidence = Math.max(...strength) / dbSum; // 0.25 = no preference, 1 = all energy on one phase

  const alt = (b) => {
    const r1 = bestPhase(o, fps, b, false), p = 60 / b * fps;
    let bs = -1, bp = r1.ph;
    for (let ph = r1.ph - 1.5; ph <= r1.ph + 1.5; ph += 0.25) { let pp = ph; if (pp < 0) pp += p; if (pp >= p) pp -= p; const sc = combSum(o, p, pp); if (sc > bs) { bs = sc; bp = pp; } }
    const d = pickDownbeat(lo, mi, fps, b, bp).q;
    return { bpm: Math.round(b * 100) / 100, firstDownbeat: normFd(toTime(bp) + d * 60 / b, 60 / b), score: bs };
  };
  const alternatives = [];
  if (bpm / 2 >= 40) alternatives.push({ label: "half-time", ...alt(bpm / 2) });
  if (bpm * 2 <= 260) alternatives.push({ label: "double-time", ...alt(bpm * 2) });

  return { bpm, firstDownbeat, confidence, downbeatConfidence, alternatives, analyzedSeconds: T * hop / sr };
}

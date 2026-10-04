/*
 * breath_core.js — camera breathing-rate counter for a resting pet.
 *
 * Pure functions, no DOM: the same file runs in the browser component and in
 * node for testing (module.exports at the bottom).
 *
 * Idea: when a dog/cat sleeps, the chest and belly rise and fall. A phone that
 * is propped up and pointed at the chest sees that as a tiny periodic shift of
 * the image (fur texture, blanket, body outline). We track that shift, not the
 * colour, so it works through fur and in ordinary room light.
 *
 * Pipeline (per recording):
 *   1. per frame   : grey image (48 x 36) of the centre region → row profile
 *                    (mean of every row) and column profile (mean of every column)
 *   2. shift       : cross-correlate each profile with the previous frame's over
 *                    ±3 pixels, sub-pixel by parabolic interpolation → dy, dx
 *   3. integrate   : cumulative sum of dy / dx = displacement signal over time
 *   4. resample    : even 10 Hz grid from real frame timestamps
 *   5. band-pass   : 2nd-order Butterworth 0.10-1.20 Hz (6-72 breaths/min),
 *                    forward + backward (zero phase), removes drift / slow sway
 *   6. spectral    : Hann-windowed DFT scan 6-60 breaths/min on both axes;
 *                    the axis with the more concentrated peak wins
 *   7. count       : local maxima with refractory time from the spectral rate,
 *                    sub-sample refinement; breaths/min from the median interval
 *   8. quality     : spectral prominence, agreement between spectral and counted
 *                    rate, share of jerky frames (pet moved / phone bumped)
 */
(function (root) {
  "use strict";

  var FS = 10; // Hz, resampling rate
  var SHIFT = 3; // search ±3 px between two frames

  function mean(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return a.length ? s / a.length : 0; }
  function std(a) { var m = mean(a), s = 0; for (var i = 0; i < a.length; i++) s += (a[i] - m) * (a[i] - m); return a.length > 1 ? Math.sqrt(s / (a.length - 1)) : 0; }
  function median(a) { if (!a.length) return 0; var b = a.slice().sort(function (x, y) { return x - y; }), n = b.length; return n % 2 ? b[(n - 1) / 2] : (b[n / 2 - 1] + b[n / 2]) / 2; }

  /** Mean of every row (axis 'y') or column (axis 'x') of a grey image w×h (Float/Uint8 array). */
  function profile(grey, w, h, axis) {
    var out, i, j, s;
    if (axis === "y") { out = new Array(h); for (j = 0; j < h; j++) { s = 0; for (i = 0; i < w; i++) s += grey[j * w + i]; out[j] = s / w; } }
    else { out = new Array(w); for (i = 0; i < w; i++) { s = 0; for (j = 0; j < h; j++) s += grey[j * w + i]; out[i] = s / h; } }
    return out;
  }

  /** Sub-pixel shift of profile b relative to a (positive = content moved to higher index). */
  function shiftBetween(a, b) {
    var n = a.length, best = 0, bestC = -Infinity, cs = {}, d, i, c, cnt, am = mean(a), bm = mean(b);
    for (d = -SHIFT; d <= SHIFT; d++) {
      c = 0; cnt = 0;
      for (i = SHIFT; i < n - SHIFT; i++) { c += (a[i] - am) * (b[i + d] - bm); cnt++; }
      c /= cnt; cs[d] = c;
      if (c > bestC) { bestC = c; best = d; }
    }
    var off = 0;
    if (best > -SHIFT && best < SHIFT) {
      var l = cs[best - 1], m = cs[best], r = cs[best + 1], den = l - 2 * m + r;
      off = den !== 0 ? 0.5 * (l - r) / den : 0;
      if (off > 0.5 || off < -0.5) off = 0;
    }
    // reject flat / textureless profiles: no reliable shift
    var sd = std(a);
    if (sd < 0.4) return { v: 0, ok: false };
    return { v: best + off, ok: true, edge: Math.abs(best) === SHIFT };
  }

  /** Streaming tracker: feed grey frames, get displacement signals. */
  function Tracker() {
    this.prevY = null; this.prevX = null; this.t = []; this.dy = []; this.dx = [];
    this.accY = 0; this.accX = 0; this.jerk = 0; this.n = 0; this.flat = 0;
  }
  Tracker.prototype.push = function (tms, grey, w, h) {
    var py = profile(grey, w, h, "y"), px = profile(grey, w, h, "x");
    if (this.prevY) {
      var sy = shiftBetween(this.prevY, py), sx = shiftBetween(this.prevX, px);
      if (!sy.ok && !sx.ok) this.flat++;
      // a jump of ≥ 2.5 px between two consecutive frames is a bump, not breathing
      if ((sy.ok && Math.abs(sy.v) >= 2.5) || (sx.ok && Math.abs(sx.v) >= 2.5)) this.jerk++;
      else { this.accY += sy.ok ? sy.v : 0; this.accX += sx.ok ? sx.v : 0; }
      this.n++;
    }
    this.prevY = py; this.prevX = px;
    this.t.push(tms); this.dy.push(this.accY); this.dx.push(this.accX);
  };

  function resample(ts, vs, fs) {
    fs = fs || FS;
    if (ts.length < 2) return { t0: ts[0] || 0, v: vs.slice() };
    var dt = 1000 / fs, t0 = ts[0], t1 = ts[ts.length - 1], n = Math.floor((t1 - t0) / dt) + 1, out = new Array(n), j = 0, i, t;
    for (i = 0; i < n; i++) {
      t = t0 + i * dt;
      while (j < ts.length - 2 && ts[j + 1] < t) j++;
      var ta = ts[j], tb = ts[j + 1], va = vs[j], vb = vs[j + 1];
      out[i] = tb === ta ? va : va + (vb - va) * (t - ta) / (tb - ta);
    }
    return { t0: t0, v: out };
  }

  function biquad(type, fc, fs) {
    var w0 = 2 * Math.PI * fc / fs, cw = Math.cos(w0), sw = Math.sin(w0), Q = Math.SQRT1_2, al = sw / (2 * Q);
    var b0, b1, b2, a0 = 1 + al, a1 = -2 * cw, a2 = 1 - al;
    if (type === "lp") { b0 = (1 - cw) / 2; b1 = 1 - cw; b2 = (1 - cw) / 2; }
    else { b0 = (1 + cw) / 2; b1 = -(1 + cw); b2 = (1 + cw) / 2; }
    return [b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0];
  }
  function runBiquad(c, x) {
    var y = new Array(x.length), x1 = x[0], x2 = x[0], y1 = x[0] * (c[0] + c[1] + c[2]) / (1 + c[3] + c[4]), y2 = y1;
    if (!isFinite(y1)) { y1 = 0; y2 = 0; }
    for (var i = 0; i < x.length; i++) {
      var yi = c[0] * x[i] + c[1] * x1 + c[2] * x2 - c[3] * y1 - c[4] * y2;
      x2 = x1; x1 = x[i]; y2 = y1; y1 = yi; y[i] = yi;
    }
    return y;
  }
  function filtfilt(c, x) { return runBiquad(c, runBiquad(c, x).reverse()).reverse(); }
  function bandpass(x, fs, lo, hi) {
    fs = fs || FS; lo = lo || 0.10; hi = hi || 1.20;
    var m = mean(x), d = x.map(function (v) { return v - m; });
    return filtfilt(biquad("lp", hi, fs), filtfilt(biquad("hp", lo, fs), d));
  }

  /** Dominant rate in breaths/min between lo and hi, with peak prominence 0-1. */
  function spectral(x, fs, lo, hi) {
    fs = fs || FS; lo = lo || 6; hi = hi || 60;
    var n = x.length; if (n < fs * 15) return { bpm: 0, prominence: 0 };
    var w = new Array(n), i, j;
    for (i = 0; i < n; i++) w[i] = x[i] * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (n - 1)));
    var best = 0, bestP = 0, total = 0, powers = [];
    for (var bpm = lo; bpm <= hi; bpm += 0.25) {
      var f = bpm / 60, re = 0, im = 0, k = 2 * Math.PI * f / fs;
      for (j = 0; j < n; j++) { re += w[j] * Math.cos(k * j); im -= w[j] * Math.sin(k * j); }
      var p = re * re + im * im; powers.push([bpm, p]); total += p;
      if (p > bestP) { bestP = p; best = bpm; }
    }
    var near = 0;
    for (i = 0; i < powers.length; i++) if (Math.abs(powers[i][0] - best) <= 3) near += powers[i][1];
    return { bpm: best, prominence: total ? near / total : 0 };
  }

  /** Breath peaks (ms) with sub-sample refinement. */
  function countPeaks(x, fs, rateGuess) {
    fs = fs || FS;
    var minDist = Math.max(Math.round(fs * 60 / (rateGuess > 0 ? rateGuess : 24) * 0.6), Math.round(fs * 0.6));
    var sd = std(x), thr = 0.2 * sd, peaks = [], i;
    for (i = 1; i < x.length - 1; i++) {
      if (x[i] > x[i - 1] && x[i] >= x[i + 1] && x[i] > thr) {
        if (peaks.length && i - peaks[peaks.length - 1] < minDist) { if (x[i] > x[peaks[peaks.length - 1]]) peaks[peaks.length - 1] = i; }
        else peaks.push(i);
      }
    }
    return peaks.map(function (p) {
      var a = x[p - 1], b = x[p], c = x[p + 1], den = a - 2 * b + c, off = den !== 0 ? 0.5 * (a - c) / den : 0;
      if (off > 0.5 || off < -0.5) off = 0;
      return (p + off) * 1000 / fs;
    });
  }

  /** Full analysis of one recording from a Tracker. */
  function analyse(tr) {
    var n = tr.t.length;
    if (n < 40 || tr.t[n - 1] - tr.t[0] < 20000) return { ok: false, reason: "too_short" };
    var durS = (tr.t[n - 1] - tr.t[0]) / 1000, jerkShare = tr.n ? tr.jerk / tr.n : 0, flatShare = tr.n ? tr.flat / tr.n : 0;
    var best = null;
    ["dy", "dx"].forEach(function (axis) {
      var rs = resample(tr.t, tr[axis], FS), f = bandpass(rs.v, FS), edge = 2 * FS, core = f.slice(edge, f.length - edge);
      if (core.length < FS * 15) return;
      var sp = spectral(core, FS), amp = std(core);
      if (!best || sp.prominence > best.prominence) best = { axis: axis, core: core, bpm: sp.bpm, prominence: sp.prominence, amp: amp };
    });
    if (!best) return { ok: false, reason: "too_short" };
    var peaks = countPeaks(best.core, FS, best.bpm), ibi = [], i;
    for (i = 1; i < peaks.length; i++) ibi.push(peaks[i] - peaks[i - 1]);
    var med = median(ibi), counted = med ? 60000 / med : 0;
    var good = ibi.filter(function (v) { return Math.abs(v - med) <= 0.35 * med; }).length;
    var regular = ibi.length ? good / ibi.length : 0;
    var agree = counted && best.bpm ? Math.abs(counted - best.bpm) / best.bpm : 1;
    var bpm = Math.round(agree <= 0.15 ? (counted + best.bpm) / 2 : best.bpm);
    var quality = (best.prominence >= 0.3 && agree <= 0.12 && jerkShare < 0.05 && regular >= 0.7) ? "good"
                : (best.prominence >= 0.18 && agree <= 0.2 && jerkShare < 0.12) ? "fair" : "poor";
    var out = { ok: quality !== "poor", quality: quality, bpm: bpm, bpmSpectral: Math.round(best.bpm), bpmCounted: Math.round(counted),
                axis: best.axis, prominence: +best.prominence.toFixed(2), regular: +regular.toFixed(2),
                jerkShare: +jerkShare.toFixed(3), flatShare: +flatShare.toFixed(3), breaths: peaks.length, durationS: +durS.toFixed(1),
                amplitudePx: +best.amp.toFixed(2) };
    if (quality === "poor") out.reason = flatShare > 0.4 ? "no_texture" : (jerkShare >= 0.12 ? "moving" : "noisy");
    return out;
  }

  var api = { Tracker: Tracker, analyse: analyse, profile: profile, shiftBetween: shiftBetween, resample: resample,
              bandpass: bandpass, spectral: spectral, countPeaks: countPeaks, FS: FS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.BreathCore = api;
})(typeof window !== "undefined" ? window : this);

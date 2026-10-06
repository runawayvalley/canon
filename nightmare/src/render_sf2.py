"""Sample-based renderer: plays a Score through a SoundFont (GeneralUser GS) with TinySoundFont.

Each track is rendered to its own stem (per-note detune via pitch bend), stems are level-balanced
to a target loudness per role, panned, mixed, then tape-stop -> reverb -> hard cuts -> soft limiter.

Needs:  /data/tools/pylib (tinysoundfont) and /data/tools/soundfonts/GeneralUser-GS.sf2
        (see nightmare/README-render.md)
"""
import os, sys, subprocess, wave
import numpy as np
sys.path.insert(0, os.environ.get("NIGHTMARE_PYLIB", "/data/tools/pylib"))
import tinysoundfont as tsf
from lib import _reverb

SR = 44100
SF2 = os.environ.get("NIGHTMARE_SF2", "/data/tools/soundfonts/GeneralUser-GS.sf2")

def render_stem(t, score, n_samples):
    syn = tsf.Synth(samplerate=SR)
    sf = syn.sfload(SF2)
    syn.program_select(0, sf, 0, t["program"])
    syn.pitchbend_range(0, 2.0)
    ev = []
    for b, d, n, vel, cents in t["notes"]:
        s0, s1 = int(score.seconds(b) * SR), int(score.seconds(b + d) * SR)
        ev.append((s0, 1, n, int(max(1, min(127, vel))), cents))
        ev.append((max(s0 + 1, s1), 0, n, 0, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    out = np.zeros((n_samples, 2), np.float32); pos = 0
    for s, on, n, vel, cents in ev:
        s = min(s, n_samples)
        if s > pos:
            out[pos:s] = np.frombuffer(syn.generate(s - pos), np.float32).reshape(-1, 2); pos = s
        if on:
            if cents: syn.pitchbend(0, int(np.clip(8192 + cents / 200 * 8192, 0, 16383)))
            syn.noteon(0, n, vel)
        else:
            syn.noteoff(0, n)
    if pos < n_samples:
        out[pos:] = np.frombuffer(syn.generate(n_samples - pos), np.float32).reshape(-1, 2)
    return out.astype(np.float64)

def active_rms_db(x):
    mono = np.abs(x).mean(1)
    win = SR // 10
    e = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, "same"))
    act = e > e.max() * .05
    return 20 * np.log10(np.sqrt((mono[act] ** 2).mean()) + 1e-12)

def render(path, score, levels, tail=7.0, wet=.30, log=print):
    n = int((score.seconds(score.end_beat()) + tail) * SR)
    mix = np.zeros((n, 2))
    for name, t in score.tracks.items():
        if not t["notes"]: continue
        stem = render_stem(t, score, n)
        g = 10 ** ((levels.get(name, -24) - active_rms_db(stem)) / 20)
        pan = t["pan"]; L, R = np.sqrt((1 - pan) / 2) * 1.414, np.sqrt((1 + pan) / 2) * 1.414
        mix[:, 0] += g * L * stem[:, 0]; mix[:, 1] += g * R * stem[:, 1]
        log(f"  stem {name:10s} target {levels.get(name, -24):4d} dB  gain {20*np.log10(g):+6.1f} dB")
    for kind, b, d in score.effects:                      # tape stops (pre-reverb)
        if kind != "tapestop": continue
        s0 = int(score.seconds(b) * SR); m = int((score.seconds(b + d) - score.seconds(b)) * SR)
        stop = min(m, int(1.1 * SR)); i = np.arange(stop)
        pos = s0 + i - i ** 2 / (2 * stop); fade = np.minimum(1, (stop - i) / (.05 * SR))
        for c in (0, 1):
            seg = np.interp(pos, np.arange(n), mix[:, c]) * fade
            mix[s0:s0 + m, c] = 0; mix[s0:s0 + stop, c] = seg
    mix = np.stack([_reverb(mix[:, 0], wet=wet, seed=3), _reverb(mix[:, 1], wet=wet, seed=4)], 1)
    for kind, b, d in score.effects:                      # hard cuts (post-reverb)
        if kind != "cut": continue
        s0, s1 = int(score.seconds(b) * SR), int(score.seconds(b + d) * SR); f = int(.01 * SR)
        mix[s0:s0 + f] *= np.linspace(1, 0, f)[:, None]; mix[s0 + f:s1] = 0
    mix /= np.abs(mix).max() / 1.25                        # drive into a gentle tanh limiter
    mix = np.tanh(mix); mix /= np.abs(mix).max() / .89    # peak about -1 dBFS
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    mp3 = path[:-4] + ".mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-b:a", "256k", mp3], check=True)
    return n / SR

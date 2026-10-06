"""Milestone 5: expression (CC11 dynamics + phrase swells, sustain pedal), final mix and render.

Run from sky/:  python3 src/milestone5.py
  midi/sky_canon_in_d.mid + renders/sky_canon_in_d.mp3   (final piece)
  renders/sky_canon_in_d_climax_excerpt.mp3               (from just before the climax)
"""
import math, os, subprocess, sys, importlib.util
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import material  # noqa: F401  (puts nightmare/src on the path)
from lib import count_midi_notes
import render_sky

def _load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod); return mod
M4 = _load("milestone4")
C = 8

# Section-level dynamics (CC11), piecewise linear over beats. The Flight sits lower so the climax opens up.
DYN = [(0, 110), (64, 104), (93, 118), (96, 106), (128, 108), (159, 112), (160, 100), (186, 108),
       (192, 127), (232, 127), (248, 118), (256, 110), (272, 100), (300, 96)]
SUSTAINED = {"flute", "oboe", "vn1", "vn2", "vn3", "pad", "cello", "bass", "horn", "tutti", "trumpet"}
SWELL = 5                                        # +/- CC11 phrase breathing over each 2-bar cycle

def dyn(b):
    for (b0, v0), (b1, v1) in zip(DYN, DYN[1:]):
        if b0 <= b <= b1: return v0 + (v1 - v0) * (b - b0) / (b1 - b0)
    return DYN[-1][1]

def apply_expression(s):
    end = s.end_beat()
    for name, t in s.tracks.items():
        if not t["notes"]: continue
        cc, last = [], None
        if name in SUSTAINED:
            b = 0.0
            while b <= end + 1:
                v = dyn(b) + SWELL * math.sin(math.pi * (b % C) / C) - SWELL / 2
                v = int(round(max(0, min(127, v))))
                if v != last: cc.append((b, 11, v)); last = v
                b += .25
        else:
            cc.append((0.0, 11, 127))
        t["cc"] = cc
    # Piano: legato pedal, changed on every beat (the harmony changes every beat); held on the final chord.
    for name in ("piano_lh", "piano_rh"):
        beats = sorted({int(x[0] + 1e-6) for x in s.tracks[name]["notes"]})
        final = M4.END
        t = s.tracks[name]
        t["pedal"] = [(b + .08, b + 1.02) for b in beats if b < final] + [(final + .02, final + 12)]
        # the pedal now provides the sustain, so the left hand's overlap emulation is trimmed
        t["notes"] = [(b, min(d, 1.0) if name == "piano_lh" and b < final and d < 1.5 else d, n, v, c)
                      for b, d, n, v, c in t["notes"]]

LEVELS = M4.LEVELS

def rms_arc(path, step=10):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "22050",
                                      "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    w = 22050 * step
    return [round(float(20 * np.log10(np.sqrt((x[i * w:(i + 1) * w] ** 2).mean()) + 1e-9))) for i in range(len(x) // w)]

if __name__ == "__main__":
    os.chdir(ROOT)
    M4.checks(M4.build(False))                     # expression doesn't change pitches; same checks
    s = M4.build(True); apply_expression(s)
    out = "sky_canon_in_d"
    render_sky.write_midi(f"midi/{out}.mid", s)
    n = sum(len(t["notes"]) for t in s.tracks.values())
    ncc = sum(len(t.get("cc", [])) for t in s.tracks.values())
    print(f"== MIDI: {n} notes written, {count_midi_notes(f'midi/{out}.mid')} re-parsed; {ncc} CC11 points, "
          f"{sum(len(t.get('pedal', [])) for t in s.tracks.values())} pedal strokes")
    dur = render_sky.render(f"renders/{out}.wav", s, LEVELS, tail=8.0, wet=.32, log=lambda *a: None)
    st = s.seconds(M4.ABOVE) - 12
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.1f}", "-i", f"renders/{out}.wav",
                    "-af", "afade=t=in:d=1.5", "-b:a", "256k", f"renders/{out}_climax_excerpt.mp3"], check=True)
    os.remove(f"renders/{out}.wav")
    print(f"== rendered renders/{out}.mp3 ({dur:.1f} s) + climax excerpt from {st:.0f} s")
    print("== RMS per 10 s:", rms_arc(f"renders/{out}.mp3"))

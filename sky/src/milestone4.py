"""Milestone 4: sections 6-7 (cycles 25-36): Above the Clouds (climax, F) and Landing.

Run from sky/:  python3 src/milestone4.py
  midi/m4_sections1-7.mid + renders/m4_sections1-7.mp3   (the whole piece)
  renders/m4_sections6-7_excerpt.mp3                      (starts just before the climax)
"""
import os, subprocess, sys, importlib.util
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from material import *                      # noqa: F403
from checks import clashes
from lib import write_midi, count_midi_notes
import render_sf2

def _load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod); return mod
M3 = _load("milestone3"); M2 = M3.M2

C = 8
ABOVE, LANDING, END = 24 * C, 32 * C, 36 * C
F = 3                                         # semitones above D
REV_CYMBAL_PEAK = 1.3                         # seconds from note-on to the peak of GM 119 (Reverse Cymbal)

# Climax-only tweaks: on beat 7.5 of a cycle the slow Theme A holds C# (in D); V3/V5 had a D there.
V3_CL = V3[:-3] + [("B4", 1), ("C#5", 1)]
V5_CL = V5_RUN[:-3] + [("C#5", .5), ("E5", .5), ("C#5", .5)]
CLIMAX_SUB = {id(V3): V3_CL, id(V5_RUN): V5_CL}

def build(humanize):
    s = M3.build(humanize)
    for t in s.tracks.values(): t["notes"] = [x for x in t["notes"] if x[0] < ABOVE - 1e-6]
    s.tempo = [x for x in s.tempo if x[0] < ABOVE]
    B = M2.Builder(humanize); B.s = s; B.rng.seed(31)
    t = s.track
    t("tutti", 48, "strings", 0.0); t("trumpet", 56, "brass", .15); t("cymbal", 119, "perc", 0.0)

    # ---------------------------------------------------------------- tempo
    for c in range(24, 31): s.set_tempo(c * C, 78 if c in (28, 29) else 76)
    s.set_tempo(31 * C, 76); s.set_tempo(31 * C + 6, 70); s.set_tempo(31 * C + 7, 64)
    for off, bpm in [(0, 70), (8, 66), (12, 63), (16, 60), (20, 58), (24, 55), (28, 50), (30, 46), (31, 42), (32, 38)]:
        s.set_tempo(LANDING + off, bpm)

    def swell(target, v=70):                  # reverse cymbal timed so its peak lands on `target`
        bpm = [x[1] for x in s.tempo if x[0] <= target - 1][-1]
        on = target - REV_CYMBAL_PEAK * bpm / 60
        B.add("cymbal", on, target - on + .2, "C4", v, jit=0)

    # ---------------------------------------------------------------- 6. Above the Clouds (cycles 25-32)
    for c in range(24, 32):
        for k in range(3):
            var = FULL_LINE[(c - 8 - k) % 8]; var = CLIMAX_SUB.get(id(var), var)
            v = 78 + 2 * min(c - 24, 5) - 3 * k - (4 if c == 31 else 0)
            B.phrase(f"vn{k+1}", tp(var, F), c * C, v, v + 2)
        for i in range(8):
            b = c * C + i; g = m(GROUND[i]) + F
            B.add("cello", b, 1.0, g, 82); B.add("bass", b, 1.0, g, 74)
            if i % 4 == 0:
                B.add("bass", b, 2.0, g - 12, 70)
                B.add("timp", b, 1.0, g if g < m("A3") else g - 12, 66 + 4 * (c in (28, 29)), jit=.004)
            if i % 2 == 0:
                for n in VOICING[i]: B.add("pad", b, 2.0, m(n) + F, 58)
    # Theme A in half notes: horns + strings in octaves (25-26), again with trumpet at the peak (29-30)
    for start, vh, extra in [(24 * C, (84, 92), False), (28 * C, (92, 100), True)]:
        B.phrase("horn", tp(THEME_A_SLOW, F - 12), start, *vh)
        B.phrase("tutti", tp(THEME_A_SLOW, F), start, vh[0] - 6, vh[1] - 4)
        if extra: B.phrase("trumpet", tp(THEME_A_SLOW, F - 12), start, 80, 92)
    B.phrase("tutti", tp(V4_THEME_B, F), 26 * C, 80, 86)            # Theme B against the canon (27)
    B.phrase("horn", tp(V4_THEME_B[4:6], F - 12), 27 * C + 4, 84, 88)            # doubles violin 1's 2nd half (28)
    B.add("horn", 27 * C + 6, 2.0, "D4", 86)                        # (A4 would rub against violin 3's B-flat)
    for k, n in enumerate(["Bb2", "F3", "D4", "F4", "A4", "D5"]): B.add("harp", 28 * C + .07 * k, 3.0, n, 72)
    B.phrase("horn", tp(V6_SOAR, F - 12), 30 * C, 84, 76)           # doubles violin 2 (31)
    B.phrase("horn", tp(V8_RISE, F - 12), 31 * C, 74, 66)           # doubles violin 1 (32), easing off
    B.phrase("glock", tp(ORNAMENT, F + 12), 31 * C, 50)
    swell(ABOVE, 76); swell(28 * C, 84)
    for k, n in enumerate(["F2", "C3", "A3", "C4", "F4", "G4", "A4", "C5"]): B.add("harp", ABOVE + .07 * k, 3.0, n, 72)
    for j in range(8): B.add("timp", 28 * C - 2 + j * .25, .3, "C3", 40 + 7 * j, jit=.004)  # roll into the peak

    # ---------------------------------------------------------------- 7. Landing (cycles 33-36)
    # Voices fall away one by one; the piano takes Theme A home.
    for c in (32, 33):
        for k in range(3 if c == 32 else 2):
            var = FULL_LINE[(c - 8 - k) % 8]
            v = (66 if c == 32 else 56) - 4 * k
            B.phrase(f"vn{k+1}", tp(var, F), c * C, v, v - 6)
        for i in range(8):
            b = c * C + i; g = m(GROUND[i]) + F
            B.add("cello", b, 1.0, g, 64 if c == 32 else 52)
            if i % 2 == 0:
                if c == 32: B.add("bass", b, 2.0, g, 56)
                for n in VOICING[i]: B.add("pad", b, 2.0, m(n) + F, 44 if c == 32 else 34)
    for c in (34, 35):
        for i in range(8):
            b = c * C + i
            B.add("piano_lh", b, 1.15, m(GROUND[i]) + F, 48 - 4 * (c - 34))
            if i % 2 == 0:
                for k, n in enumerate(VOICING[i][1:]): B.add("piano_lh", b + .25 + .06 * k, 1.8, m(n) + F, 32)
                if c == 34: 
                    for n in VOICING[i]: B.add("pad", b, 2.0, m(n) + F, 26 - i)
    B.phrase("piano_rh", tp(THEME_A_SLOW, F), 34 * C, 60, 52, legato=1.08, grace=m("G5") + F)
    for k, n in enumerate(["F2", "C3", "A3", "G4", "C5", "F5", "A5"]):          # final rolled F(add9)
        B.add("piano_lh" if k < 3 else "piano_rh", END + .08 * k, 4.0, m(n), 44 if k < 3 else 50 - k)
    return s

def checks(s):
    upper = {k: [(b, d, n) for b, d, n, *_ in t["notes"] if b >= ABOVE - 2] for k, t in s.tracks.items()
             if k not in ("cello", "bass", "timp", "piano_lh", "cymbal")}
    upper["piano_lh_dyads"] = [(b, d, n) for b, d, n, *_ in s.tracks["piano_lh"]["notes"] if b >= ABOVE and n >= 60]
    cl = clashes(upper, END + 4, strong_only=False)
    print(f"== Clash check, cycles 25-36, all upper voices, 8th-note grid: {len(cl)}")
    for c in cl[:15]: print("   ", c)
    for name, a, b in [("6 Climax", ABOVE, LANDING), ("7 Landing", LANDING, END)]:
        notes = [x for k, t in s.tracks.items() if k != "trem" for x in t["notes"] if a <= x[0] < b]
        sec = s.seconds(b) - s.seconds(a); att = len({round(x[0] * 4) for x in notes})
        print(f"== Section {name:10s} {sec:5.1f} s  {len(notes) / sec:4.1f} notes/s, {att / sec:3.1f} attack points/s  (starts at {s.seconds(a):.0f} s)")
    print(f"== Final chord at {s.seconds(END):.1f} s")

LEVELS = dict(M3.LEVELS, tutti=-24, trumpet=-26, cymbal=-30)

if __name__ == "__main__":
    os.chdir(ROOT)
    checks(build(False))
    if "--check" in sys.argv: sys.exit()
    s = build(True)
    out = "m4_sections1-7"
    write_midi(f"midi/{out}.mid", s)
    n = sum(len(t["notes"]) for t in s.tracks.values())
    print(f"== MIDI: {n} notes written, {count_midi_notes(f'midi/{out}.mid')} re-parsed")
    dur = render_sf2.render(f"renders/{out}.wav", s, LEVELS, tail=8.0, wet=.32, log=lambda *a: None)
    st = s.seconds(ABOVE) - 12
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.1f}", "-i", f"renders/{out}.wav",
                    "-af", "afade=t=in:d=1.5", "-b:a", "256k", "renders/m4_sections6-7_excerpt.mp3"], check=True)
    os.remove(f"renders/{out}.wav")
    print(f"== rendered renders/{out}.mp3 ({dur:.1f} s) + excerpt from {st:.0f} s")

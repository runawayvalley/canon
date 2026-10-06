"""Milestone 2: sections 1-3 (cycles 1-12): On the Hill, The Breeze, Take-off (D -> E-flat lift).

Run from sky/:  python3 src/milestone2.py
  midi/m2_sections1-3.mid + renders/m2_sections1-3.mp3
The score is built twice: once un-humanized for the checks, once humanized for the render.
"""
import os, random, sys
sys.dont_write_bytecode = True  # keep nightmare/src/__pycache__ (tracked) untouched
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from material import *                      # noqa: F403
from checks import clashes, NAMES
from lib import Score, write_midi, count_midi_notes
import render_sf2

C = 8                                        # beats per cycle
HILL, BREEZE, TAKEOFF, ARRIVAL = 0, 4 * C, 8 * C, 12 * C
LIFT = ARRIVAL - 2                           # last 2 beats of cycle 12: B-flat7, the dominant of E-flat

def up(phrase, octs=1):
    return [(None if n is None else n[:-1] + str(int(n[-1]) + octs), d) for n, d in phrase]

class Builder:
    def __init__(self, humanize):
        self.s = Score(); self.rng = random.Random(11); self.h = humanize
        t = self.s.track
        t("piano_lh", 0, "piano", -.15); t("piano_rh", 0, "piano", .15)
        t("flute", 73, "wind", .30);     t("oboe", 68, "wind", .20)
        t("vn1", 40, "strings", -.45);   t("vn2", 40, "strings", 0.0); t("vn3", 40, "strings", .45)
        t("pad", 49, "strings", 0.0);    t("trem", 44, "strings", 0.0)
        t("harp", 46, "harp", -.30);     t("cello", 42, "strings", -.10); t("bass", 43, "strings", .10)
        t("timp", 47, "perc", 0.0)
    def add(self, tr, b, d, n, v, jit=.010):
        if self.h:
            b = max(0.0, b + self.rng.uniform(-jit, jit)); v = v + self.rng.randint(-4, 4)
        self.s.add(tr, b, d, n, int(max(1, min(127, v))))
    def phrase(self, tr, phrase, start, v0, v1=None, legato=1.05, grace=None, stop=None):
        """Velocity ramps v0 -> v1 across the phrase (crescendo emulation; no CC yet)."""
        v1 = v0 if v1 is None else v1
        total = sum(d for _, d in phrase); b = start
        for j, (n, d) in enumerate(phrase):
            if stop is not None and b >= stop: break
            if n is not None:
                v = v0 + (v1 - v0) * (b - start) / total
                if grace and j == 0: self.add(tr, b - .18, .18, grace, v - 12)
                self.add(tr, b, d * legato, n, v)
            b += d
        return b

def build(humanize):
    B = Builder(humanize); s = B.s
    # ---------------------------------------------------------------- tempo map
    for c in range(4):                                   # Hill: rubato 58-62, breath at cycle ends
        for off, bpm in [(0, 58), (2, 61), (4, 62), (6, 59), (7.5, 53)]:
            s.set_tempo(c * C + off, bpm)
    s.set_tempo(30, 57); s.set_tempo(31, 54)
    for c in range(4, 8):                                # Breeze: steady 62, a small breath per cycle
        s.set_tempo(c * C, 62); s.set_tempo(c * C + 7.5, 59)
    for k, c in enumerate(range(8, 12)):                 # Take-off: 62 -> 70
        s.set_tempo(c * C, 62 + 2 * k); s.set_tempo(c * C + 4, 63 + 2 * k)
    s.set_tempo(LIFT, 66); s.set_tempo(LIFT + 1, 62); s.set_tempo(LIFT + 1.5, 52)  # the breath before
    s.set_tempo(ARRIVAL, 70); s.set_tempo(ARRIVAL + 2, 64)

    # ---------------------------------------------------------------- 1. On the Hill (cycles 1-4)
    for c in range(4):
        for i in range(8):
            b = c * C + i
            B.add("piano_lh", b, 1.15, GROUND[i], 50 if c else 44)
            if i % 2 == 0:
                for k, n in enumerate(VOICING[i][1:]):
                    B.add("piano_lh", b + .25 + .06 * k, 1.8, n, 34 if c else 30)
    B.add("piano_rh", 6, 2.0, "A5", 30); B.add("piano_rh", 6.5, 1.5, "F#6", 26)
    B.phrase("piano_rh", THEME_A_SLOW, 8, 60, 66, legato=1.08, grace="G5")
    B.phrase("piano_rh", V4_THEME_B, 24, 64, 58, legato=1.08)

    # ---------------------------------------------------------------- 2. The Breeze (cycles 5-8)
    # piano hands over to cello + harp; strings pad enters; flute sings Theme A slow, violin Theme B,
    # then the lyrical V3 with flute bird-calls above.
    B.add("piano_lh", BREEZE, 3.0, "D2", 40); B.add("piano_lh", BREEZE, 3.0, "A2", 36)
    for c in range(4, 12):
        for i in range(8):
            b = c * C + i; g = GROUND[i]
            B.add("cello", b, 1.0, g, 50 + (c - 4) * 3)
            if i % 2 == 0 and c >= 6: B.add("bass", b, 2.0, g, 46 + (c - 6) * 3)
            if i % 2 == 0 and c < 8:                     # Breeze: harp carries the harmony (soft roll / 2 beats)
                for k, n in enumerate(VOICING[i]): B.add("harp", b + .17 * k, 2.0 - .17 * k, n, 46)
            if i % 2 == 0 and c >= 7:                    # pad fades in under the last Breeze cycle, holds in Take-off
                for n in VOICING[i]: B.add("pad", b, 2.0, n, 32 + (c - 7) * 4)
    B.phrase("flute", THEME_A_SLOW, BREEZE, 56, 64)
    B.phrase("vn1", V4_THEME_B, BREEZE + 2 * C, 58, 64)
    B.phrase("vn1", V3, BREEZE + 3 * C, 60, 56)
    B.phrase("flute", ORNAMENT, BREEZE + 3 * C, 50)

    # ---------------------------------------------------------------- 3. Take-off (cycles 9-12)
    # The strict canon: vn1 at cycle 9, vn2 at 10 (+2 bars), vn3 at 11 (+4 bars). Crescendo throughout.
    for k in range(3):
        b = TAKEOFF + k * C
        for var in CANON_LINE:
            if b >= LIFT: break
            v0 = 58 + 4 * (b - TAKEOFF) / C; B.phrase(f"vn{k+1}", var, b, v0, v0 + 4, stop=LIFT); b += C
    # The lift: last 2 beats become B-flat7 (ground A -> B-flat); voices hold, tremolo + timpani swell,
    # harp glissando, a breath, then E-flat.
    for tr, n in [("vn1", "F5"), ("vn2", "D5"), ("vn3", "Ab4")]: B.add(tr, LIFT, 2.0, n, 72)
    s.tracks["cello"]["notes"] = [x for x in s.tracks["cello"]["notes"] if x[0] < LIFT + 1 - .2]
    s.tracks["bass"]["notes"] = [x for x in s.tracks["bass"]["notes"] if x[0] < LIFT - .2]
    s.tracks["pad"]["notes"] = [x for x in s.tracks["pad"]["notes"] if x[0] < LIFT - .2]
    B.add("cello", LIFT + 1, 1.0, "Bb2", 70); B.add("bass", LIFT, 2.0, "G2", 60)
    for j in range(8):                                    # tremolo crescendo on B-flat7 (re-struck = swell)
        for n in ["Bb3", "D4", "Ab4"]: B.add("trem", LIFT + j * .25, .3, n, 40 + 6 * j)
        B.add("timp", LIFT + j * .25, .3, "Bb2", 30 + 7 * j, jit=.004)
    for j, n in enumerate(["Bb3", "D4", "F4", "Ab4", "Bb4", "D5", "F5", "Ab5", "Bb5", "D6", "F6", "Ab6"]):
        B.add("harp", LIFT + .3 + j * .1, ARRIVAL - (LIFT + .3 + j * .1) - .15, n, 50 + 2 * j, jit=.003)

    # ---------------------------------------------------------------- arrival in E-flat (cycle 13, beat 1)
    for tr, notes, v in [("bass", ["Eb2"], 80), ("cello", ["Eb3"], 82), ("pad", ["Bb3", "G4", "F4"], 70),
                         ("vn3", ["Bb4"], 84), ("vn2", ["Eb5"], 84), ("vn1", ["G5"], 86), ("flute", ["Bb5"], 74),
                         ("timp", ["Eb2"], 92)]:
        for n in notes: B.add(tr, ARRIVAL, 1.0 if tr == "timp" else 4.0, n, v)
    for k, n in enumerate(["Eb3", "Bb3", "F4", "G4", "Bb4", "Eb5", "F5", "G5"]):
        B.add("harp", ARRIVAL + .08 * k, 4.0, n, 64)
    return s

def checks(s):
    upper = {k: [(b, d, n) for b, d, n, *_ in t["notes"]] for k, t in s.tracks.items()
             if k not in ("cello", "bass", "timp", "piano_lh")}
    upper["piano_lh_dyads"] = [(b, d, n) for b, d, n, *_ in s.tracks["piano_lh"]["notes"] if n >= 57]
    cl = clashes(upper, ARRIVAL + 4, strong_only=False)
    print(f"== Clash check, all upper voices, 8th-note grid: {len(cl)}")
    for c in cl[:12]: print("   ", c)
    # canon spacing check: each voice's Theme A starts exactly one cycle after the previous one
    starts = []
    for k in range(3):
        ns = s.tracks[f"vn{k+1}"]["notes"]; target = [m(n) for n in ORIGINAL_THEME]
        for i in range(len(ns) - 7):
            if ns[i][0] >= TAKEOFF and [x[2] for x in ns[i:i + 8]] == target: starts.append(ns[i][0]); break
    print("== Canon: Theme A entries at beats", starts, "-> spacing", [b - a for a, b in zip(starts, starts[1:])], "(8 = 2 bars)")
    for name, a, b in [("1 Hill", HILL, BREEZE), ("2 Breeze", BREEZE, TAKEOFF), ("3 Take-off", TAKEOFF, ARRIVAL)]:
        notes = [x for t in s.tracks.values() for x in t["notes"] if a <= x[0] < b and t is not s.tracks["trem"]]
        sec = s.seconds(b) - s.seconds(a)
        print(f"== Section {name:11s} {sec:5.1f} s  {len(notes) / sec:4.1f} notes/s")
    print(f"== Total length to the E-flat arrival: {s.seconds(ARRIVAL):.1f} s")

LEVELS = {"piano_lh": -28, "piano_rh": -25, "flute": -23, "oboe": -24, "vn1": -22, "vn2": -23, "vn3": -24,
          "pad": -30, "trem": -29, "harp": -28, "cello": -25, "bass": -28, "timp": -27}

if __name__ == "__main__":
    os.chdir(ROOT)
    checks(build(False))
    s = build(True)
    write_midi("midi/m2_sections1-3.mid", s)
    n = sum(len(t["notes"]) for t in s.tracks.values())
    print(f"== MIDI: {n} notes written, {count_midi_notes('midi/m2_sections1-3.mid')} re-parsed")
    dur = render_sf2.render("renders/m2_sections1-3.wav", s, LEVELS, wet=.32, log=lambda *a: None)
    os.remove("renders/m2_sections1-3.wav")
    print(f"== rendered renders/m2_sections1-3.mp3 ({dur:.1f} s incl. tail)")

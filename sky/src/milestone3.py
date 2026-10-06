"""Milestone 3: sections 4-5 (cycles 13-24): Flight (E-flat) and Through the Clouds (bridge), lift to F.

Run from sky/:  python3 src/milestone3.py
  midi/m3_sections1-5.mid + renders/m3_sections1-5.mp3   (sections 1-3 from milestone 2 + the new ones)
  renders/m3_sections4-5_excerpt.mp3                      (starts just before Flight)
"""
import os, subprocess, sys, importlib.util
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from material import *                      # noqa: F403
from checks import clashes, chord_report
from lib import write_midi, count_midi_notes
import render_sf2

def _load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod); return mod
M2 = _load("milestone2")

C = 8
FLIGHT, CLOUDS, ABOVE = 12 * C, 20 * C, 24 * C
EB, F = 1, 3                                  # semitones above D
LIFT2 = ABOVE - 2

# Bridge harmony (E-flat): IV-V-vi-iii | IV-iii-ii-V | IV-V-vi-iii | IV-V-bVII(Db)-I(Eb)->F.  2 beats each.
BRIDGE = [  # (chord, cello root, voicing below the melody)
    [("Abmaj7", "Ab2", ["Ab3", "C4", "Eb4", "G4"]), ("Bb", "Bb2", ["Bb3", "D4", "F4"]),
     ("Cm7", "C3", ["G3", "C4", "Eb4", "Bb4"]), ("Gm7", "G2", ["G3", "Bb3", "D4", "F4"])],
    [("Abmaj7", "Ab2", ["Ab3", "C4", "Eb4", "G4"]), ("Gm7", "G2", ["G3", "Bb3", "D4", "F4"]),
     ("Fm7", "F2", ["Ab3", "C4", "Eb4"]), ("Bb", "Bb2", ["Bb3", "D4", "F4"])],
    [("Abmaj7", "Ab2", ["Ab3", "C4", "Eb4", "G4"]), ("Bb", "Bb2", ["Bb3", "D4", "F4"]),
     ("Cm7", "C3", ["G3", "C4", "Eb4", "Bb4"]), ("Gm7", "G2", ["G3", "Bb3", "D4", "F4"])],
    [("Abmaj7", "Ab2", ["Ab3", "C4", "Eb4", "G4"]), ("Bb", "Bb2", ["Bb3", "D4", "F4"]),
     ("Db", "Db3", ["Ab3", "Db4", "F4"]), ("Eb", "Eb3", ["Bb3", "Eb4", "G4"])],
]
# Theme A in half notes, reharmonized (cycles 21-22), its answer (23), then a stepwise rise to A (= F's 3rd).
BRIDGE_MELODY = [("G5", 2), ("F5", 2), ("Eb5", 2), ("D5", 2), ("C5", 2), ("Bb4", 2), ("C5", 2), ("D5", 2),
                 ("Eb5", 2), ("D5", 2), ("C5", 2), ("Bb4", 2), ("C5", 2), ("D5", 2), ("F5", 2), ("G5", 2)]

def build(humanize):
    s = M2.build(humanize)
    # drop milestone 2's arrival chord + tempo points: the Flight takes over at the same beat
    for t in s.tracks.values(): t["notes"] = [x for x in t["notes"] if x[0] < FLIGHT - 1e-6]
    s.tempo = [x for x in s.tempo if x[0] < FLIGHT]
    B = M2.Builder(humanize); B.s = s; B.rng.seed(23)
    t = s.track
    t("horn", 60, "brass", -.20); t("celesta", 8, "keys", .35); t("glock", 9, "keys", .40)

    # ---------------------------------------------------------------- tempo
    for k, c in enumerate(range(12, 20)):              # Flight: 72 -> 76, tiny breath at the halfway point
        s.set_tempo(c * C, 72 + k * .5)
    s.set_tempo(16 * C - .5, 70); s.set_tempo(16 * C, 74)
    s.set_tempo(CLOUDS - 1, 68)
    s.set_tempo(CLOUDS, 72); s.set_tempo(22 * C - 1, 68); s.set_tempo(22 * C, 72)
    s.set_tempo(LIFT2, 70); s.set_tempo(LIFT2 + 1, 64); s.set_tempo(LIFT2 + 1.5, 54)
    s.set_tempo(ABOVE, 76); s.set_tempo(ABOVE + 2, 66)

    # ---------------------------------------------------------------- 4. Flight (cycles 13-20, E-flat)
    # Canon continues where Take-off left it: in cycle c voice k plays FULL_LINE[(c - 8 - k) % 8].
    for c in range(12, 20):
        for k in range(3):
            var = FULL_LINE[(c - 8 - k) % 8]
            v = 64 + 2 * (c - 12) - 3 * k
            B.phrase(f"vn{k+1}", tp(var, EB), c * C, v, v + 3)
            if var is V4_THEME_B and c in (13, 19):     # horns sing Theme B (an octave below)
                B.phrase("horn", tp(var, EB - 12), c * C, 66, 72, stop=c * C + 6)
                B.add("horn", c * C + 6, 2.0, "C4", 70)      # (G4 would rub against violin 3's A-flat)
            if var is V1_THEME_A and c == 16:            # ...and Theme A when it returns in violin 1
                B.phrase("horn", tp(var, EB - 12), c * C, 70, 74)
        for i in range(8):
            b = c * C + i; g = m(GROUND[i]) + EB
            B.add("cello", b, 1.0, g, 66 + (c - 12))
            if i % 2 == 0: B.add("bass", b, 2.0, g, 60 + (c - 12))
            if c >= 16 and i % 4 == 0: B.add("timp", b, 1.0, g if g >= m("F2") else g + 12, 52 + 2 * (c - 16), jit=.004)
    for k, n in enumerate(["Eb2", "Bb2", "G3", "Bb3", "Eb4", "F4", "G4", "Bb4"]):   # downbeat of the Flight
        B.add("harp", FLIGHT + .06 * k, 3.0, n, 66)
    B.add("timp", FLIGHT, 1.5, "Eb2", 84, jit=0)
    for c in (18, 19):                                  # glockenspiel sparkle (sparse pentatonic)
        B.phrase("glock", tp(ORNAMENT, EB + 12), c * C, 44)

    # ---------------------------------------------------------------- 5. Through the Clouds (21-24)
    # The ground stops (the one allowed exception): slower harmonic rhythm, high strings, celesta, oboe.
    for ci, cyc in enumerate(BRIDGE):
        for j, (name, root, voicing) in enumerate(cyc):
            b = CLOUDS + ci * C + 2 * j
            last = ci == 3 and j == 3
            B.add("cello", b, 2.0, root, 36 + 6 * ci)
            if j % 2 == 0: B.add("bass", b, 4.0 if not (ci == 3 and j == 2) else 2.0, m(root) - 12, 32 + 5 * ci)
            if last: continue                            # the lift is written separately below
            for n in voicing: B.add("pad", b, 2.0, n, 26 + 5 * ci)
            top = sorted(m(n) for n in voicing)
            B.add("celesta", b, 1.5, top[-1] + 12, 36); B.add("celesta", b + 1, 1.0, top[-2] + 12, 30)
    B.phrase("oboe", BRIDGE_MELODY[:8], CLOUDS, 46, 54, legato=1.02)
    B.phrase("oboe", BRIDGE_MELODY[8:], CLOUDS + 2 * C, 50, 74, legato=1.02)
    B.phrase("vn1", BRIDGE_MELODY[8:], CLOUDS + 2 * C, 34, 70, legato=1.02)      # violins join the answer
    B.phrase("vn2", tp(BRIDGE_MELODY[12:], -12), CLOUDS + 3 * C, 42, 66, legato=1.02)

    # The lift to F: E-flat sus4 -> E-flat (= bVII of F), tremolo + timpani swell, harp glissando, breath.
    for j in range(8):
        for n in ["Bb3", "Eb4", "G4"]: B.add("trem", LIFT2 + j * .25, .3, n, 40 + 7 * j)
        B.add("timp", LIFT2 + j * .25, .3, "Bb2", 32 + 8 * j, jit=.004)
    gl = ["Eb4", "F4", "G4", "Bb4", "C5", "Eb5", "F5", "G5", "Bb5", "C6", "Eb6", "F6"]
    for j, n in enumerate(gl):
        on = LIFT2 + .3 + j * .1; B.add("harp", on, ABOVE - on - .15, n, 50 + 2 * j, jit=.003)

    # ---------------------------------------------------------------- arrival in F (cycle 25, beat 1)
    for tr, notes, v in [("bass", ["F1"], 84), ("cello", ["F2"], 86), ("pad", ["C4", "F4", "G4"], 72),
                         ("vn3", ["C5"], 88), ("vn2", ["F5"], 88), ("vn1", ["A5"], 92), ("oboe", ["A5"], 80),
                         ("horn", ["A3", "C4"], 84), ("timp", ["F2"], 96)]:
        for n in notes: B.add(tr, ABOVE, 1.0 if tr == "timp" else 4.0, n, v)
    for k, n in enumerate(["F2", "C3", "G3", "A3", "C4", "F4", "G4", "A4", "C5"]):
        B.add("harp", ABOVE + .07 * k, 4.0, n, 68)
    return s

def checks(s):
    print("== Chord-tone check, new variations V5-V8 (on-beat non-chord tones):",
          sum(1 for v in FULL_LINE[4:] for r in chord_report(v) if r[3] == "NCT" and r[4]))
    upper = {k: [(b, d, n) for b, d, n, *_ in t["notes"] if b >= FLIGHT - 2] for k, t in s.tracks.items()
             if k not in ("cello", "bass", "timp", "piano_lh")}
    cl = clashes(upper, ABOVE + 4, strong_only=False)
    print(f"== Clash check, cycles 13-25, all upper voices, 8th-note grid: {len(cl)}")
    for c in cl[:15]: print("   ", c)
    for name, a, b in [("4 Flight", FLIGHT, CLOUDS), ("5 Clouds", CLOUDS, ABOVE)]:
        notes = [x for k, t in s.tracks.items() if k != "trem" for x in t["notes"] if a <= x[0] < b]
        sec = s.seconds(b) - s.seconds(a); att = len({round(x[0] * 4) for x in notes})
        print(f"== Section {name:9s} {sec:5.1f} s  {len(notes) / sec:4.1f} notes/s, {att / sec:3.1f} attack points/s  (starts at {s.seconds(a):.0f} s)")
    print(f"== F arrival at {s.seconds(ABOVE):.1f} s")

LEVELS = dict(M2.LEVELS, horn=-24, celesta=-32, glock=-29, oboe=-27)

if __name__ == "__main__":
    os.chdir(ROOT)
    checks(build(False))
    s = build(True)
    out = "m3_sections1-5"
    write_midi(f"midi/{out}.mid", s)
    n = sum(len(t["notes"]) for t in s.tracks.values())
    print(f"== MIDI: {n} notes written, {count_midi_notes(f'midi/{out}.mid')} re-parsed")
    dur = render_sf2.render(f"renders/{out}.wav", s, LEVELS, wet=.32, log=lambda *a: None)
    st = s.seconds(FLIGHT) - 8
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.1f}", "-i", f"renders/{out}.wav",
                    "-af", "afade=t=in:d=1.5", "-b:a", "256k", "renders/m3_sections4-5_excerpt.mp3"], check=True)
    os.remove(f"renders/{out}.wav")
    print(f"== rendered renders/{out}.mp3 ({dur:.1f} s) + excerpt from {st:.0f} s")

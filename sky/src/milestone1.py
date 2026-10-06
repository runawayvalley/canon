"""Milestone 1: themes, ground bass, recolored harmony, canon check, piano sketch (cycles 1-4).

Outputs (run from sky/):  python3 src/milestone1.py
  midi/m1_piano_sketch.mid   + renders/m1_piano_sketch.mp3   section 1 "On the Hill" (solo piano, rubato)
  midi/m1_canon_study.mid    + renders/m1_canon_study.mp3    3-voice canon of V1-V4 over the recolored harmony
and prints the chord-tone, pentatonic and clash report.
"""
import os, random, sys
sys.dont_write_bytecode = True  # keep nightmare/src/__pycache__ (tracked) untouched
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from material import *                      # noqa: F403
from checks import chord_report, clashes, ground_notes
from lib import Score, write_midi, count_midi_notes
import render_sf2

rng = random.Random(7)

def human(beat, amt=.010):                  # ~10 ms at 58 BPM
    return max(0.0, beat + rng.uniform(-amt, amt))

def vel(v, amt=4):
    return int(max(1, min(127, v + rng.randint(-amt, amt))))

def up(phrase, octs=1):
    return [(None if n is None else n[:-1] + str(int(n[-1]) + octs), d) for n, d in phrase]

THIRDS_BELOW = {"F#5": "D5", "E5": "C#5", "D5": "B4", "C#5": "A4", "B4": "G4", "A4": "F#4"}

# ======================================================== piano sketch (section 1, cycles 1-4)
def piano_sketch():
    s = Score()
    s.track("lh", 0, "piano", pan=-.15); s.track("rh", 0, "piano", pan=.15)
    # Rubato tempo map: gentle push-pull inside each cycle, a breath at each cycle end, final ritardando.
    for c in range(4):
        b = c * 8
        for off, bpm in [(0, 58), (2, 61), (4, 62), (6, 59), (7.5, 53)]:
            s.set_tempo(b + off, bpm)
    for off, bpm in [(28, 57), (29, 54), (30, 51), (31, 47), (31.5, 43), (32, 40)]:
        s.set_tempo(off, bpm)
    # Left hand: ground note on the beat, warm dyad on the off-beat; pedal emulated by overlapping
    for c in range(4):
        for i in range(8):
            b = c * 8 + i
            s.add("lh", human(b), 1.15, GROUND[i], vel(50 if c else 44))
            if i % 2 == 0:                                 # held dyad every 2 beats, slightly rolled
                for k, n in enumerate(VOICING[i][1:]):
                    s.add("lh", human(b + .25 + .06 * k), 1.8, n, vel(34 if c else 30))
    # Right hand
    def melody(phrase, start, base, arch=10, thirds=False, grace=None):
        b = start
        for j, (n, d) in enumerate(phrase):
            if n is None: b += d; continue
            v = base + arch * (1 - abs(j - len(phrase) / 2) / (len(phrase) / 2))
            if grace and j == 0:
                s.add("rh", human(b - .18), .18, grace, vel(v - 12))
            s.add("rh", human(b), d * 1.08, n, vel(v))
            if thirds and n in THIRDS_BELOW:
                s.add("rh", human(b + .02), d * 1.05, THIRDS_BELOW[n], vel(v - 14))
            b += d
    s.add("rh", human(6), 2.0, "A5", 30); s.add("rh", human(6.5), 1.5, "F#6", 26)   # far-off sparkle
    melody(THEME_A_SLOW, 8, 62, grace="G5")                   # cycles 2-3: Theme A in half notes
    melody(V4_THEME_B, 24, 64, arch=10)                       # cycle 4: Theme B (the flight to come)
    # Final rolled Dadd9 (fermata through the slow tempo)
    for k, n in enumerate(["D2", "A2", "F#3", "E4", "A4", "D5", "F#5"]):
        s.add("lh" if k < 3 else "rh", 32 + .07 * k, 4.0, n, 46 if k < 3 else 52 - k)
    return s

# ======================================================== canon study (harmony + canon test)
def canon_study():
    s = Score()
    s.set_tempo(0, 64)
    s.track("vn1", 40, "strings", pan=-.45); s.track("vn2", 40, "strings", pan=.0)
    s.track("vn3", 40, "strings", pan=.45);  s.track("cello", 42, "strings", pan=-.1)
    s.track("bass", 43, "strings", pan=.1);  s.track("pad", 49, "strings", pan=.0)
    s.track("flute", 73, "wind", pan=.3)
    line = CANON_LINE + [up(V1_THEME_A)]
    for k in range(3):                                  # voice k enters at cycle k+1 (2-bar spacing)
        for ci, var in enumerate(line):
            c = k + 1 + ci
            if c >= 6: break
            b = c * 8
            for n, d in var:
                if n is not None: s.add(f"vn{k+1}", human(b, .02), d * 1.02, n, vel(70 - 6 * k))
                b += d
    for on, d, n in ground_notes(6):
        s.add("cello", on, 1.0, n + 12, vel(60))
        if on % 2 == 0: s.add("bass", on, 2.0, n, vel(54))       # contrabass: every other ground note, held
    for c in range(6):
        for i in range(8):
            if i % 2 == 0:
                for n in VOICING[i]:
                    s.add("pad", c * 8 + i, 2.0, n, 42)
    for c in (4, 5):
        b = c * 8
        for n, d in ORNAMENT:
            s.add("flute", human(b, .015), d * .95, n, vel(62)); b += d
    for n in ["D2", "D3", "A3", "F#4", "E5", "A5", "D6"]:          # final chord
        s.add("pad" if n[-1] in "34" else "vn1" if n == "D6" else "cello", 48, 4, n, 56)
    s.add("bass", 48, 4, "D2", 56); s.add("vn2", 48, 4, "A5", 56); s.add("vn3", 48, 4, "F#5", 56)
    s.set_tempo(46, 60); s.set_tempo(47, 54); s.set_tempo(48, 48)
    return s, line

# ======================================================== report
def report(line):
    print("== Chord-tone check (notes on the beat must be chord or colour tones)")
    for name, v in [("V1 Theme A", V1_THEME_A), ("Theme A slow", THEME_A_SLOW[:4]), ("(2nd half)", THEME_A_SLOW[4:]), ("V2", V2), ("V3", V3), ("V4 Theme B", V4_THEME_B),
                    ("Ornament", ORNAMENT)]:
        rows = chord_report(v)
        on = [r for r in rows if r[4]]
        nct = [r for r in on if r[3] == "NCT"]
        col = [f"{r[1]} over {r[2]}" for r in on if r[3] == "colour"]
        print(f"  {name:11s} {len(on):2d} on-beat notes, NCT {len(nct)}, colour: {', '.join(col) or '-'}")
    print("  Ornament strictly yonanuki pentatonic (D E F# A B):", all(pc(n) in YONANUKI for n, _ in ORNAMENT))
    same = [n for n, _ in V1_THEME_A] == ORIGINAL_THEME
    print("== Recognizability: Theme A pitches identical to Pachelbel's opening line:", same)
    voices = {}
    for k in range(3):
        voices[f"vn{k+1}"] = [x for ci, var in enumerate(line) for x in notes_of(var, (k + 1 + ci) * 8) if x[0] < 48]
    voices["flute"] = notes_of(ORNAMENT, 32) + notes_of(ORNAMENT, 40)
    voices["pad"] = [(c * 8 + i, 2.0, m(n)) for c in range(6) for i in range(0, 8, 2) for n in VOICING[i]]
    print("== Canon clash check, 3 voices + flute + pad, 8th-note grid:",
          len(clashes(voices, 48, strong_only=False)), "semitone/minor-9th clashes")
    pv = {"rh": notes_of(THEME_A_SLOW, 8) + notes_of(V4_THEME_B, 24),
          "lh": [(c * 8 + i, 2.0, m(n)) for c in range(4) for i in range(0, 8, 2) for n in VOICING[i][1:]]}
    print("== Piano sketch clash check (melody vs left-hand dyads):", len(clashes(pv, 32, strong_only=False)))

LEVELS_PIANO = {"lh": -24, "rh": -21}
LEVELS_CANON = {"vn1": -22, "vn2": -23, "vn3": -24, "cello": -24, "bass": -27, "pad": -29, "flute": -24}

if __name__ == "__main__":
    os.chdir(ROOT)
    sk = piano_sketch(); st, line = canon_study()
    report(line)
    for name, sc, lv, wet in [("m1_piano_sketch", sk, LEVELS_PIANO, .28), ("m1_canon_study", st, LEVELS_CANON, .32)]:
        write_midi(f"midi/{name}.mid", sc)
        n = sum(len(t["notes"]) for t in sc.tracks.values())
        ons = {round(b * 4) for t in sc.tracks.values() for b, *_ in t["notes"]}
        print(f"== {name}: {n / sc.seconds(sc.end_beat()):.1f} notes/s, {len(ons) / sc.seconds(sc.end_beat()):.1f} attack points/s")
        print(f"== {name}: {n} notes written, {count_midi_notes(f'midi/{name}.mid')} re-parsed")
        dur = render_sf2.render(f"renders/{name}.wav", sc, lv, wet=wet, log=lambda *a: None)
        os.remove(f"renders/{name}.wav")
        print(f"   rendered renders/{name}.mp3 ({dur:.1f} s incl. tail)")

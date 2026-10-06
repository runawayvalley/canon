"""Milestone 3: Sections 4-5 (cycles 17-30), appended to sections 1-3.

  4 Descent   cycles 17-24  diminished / arpeggio 16th runs, A7b9 + Gm(addb6) colours,
                            tritone (Eb7) endings on even cycles, choir chromatic lament,
                            violin 2 displaced by an 8th note.
  5 Fracture  cycles 25-30  violin 3 plays in Eb minor against D minor (polytonal canon),
                            downbeat clusters, a 7-beat and a 9-beat cycle (3/4, 5/4 bars),
                            unstable tempo, tape-stops (end of cycle 26 and 30).

Run from nightmare/:  python3 src/milestone3.py
"""
import os, sys, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Score, write_midi, render, count_midi_notes, m, NOTE
import milestone2 as m2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LO, HI = m("G3"), m("C6")                      # violin range used here

# Pitch-class sets per beat of the ground (standard canonic harmony).
def pcs(*names): return {NOTE[n] for n in names}
SETS = [pcs("D", "F", "A"), pcs("C#", "E", "G", "Bb"), pcs("Bb", "D", "F"), pcs("F", "A", "C#"),
        pcs("G", "Bb", "D"), pcs("D", "F", "A"), pcs("G", "Bb", "D", "Eb"), pcs("C#", "E", "G", "Bb")]
DIM7 = pcs("C#", "E", "G", "Bb")
THEME = ["F5", "E5", "D5", "C#5", "Bb4", "A4", "Bb4", "C#5"]
THEME_B = ["D5", "C#5", "Bb4", "A4", "G4", "F4", "G4", "E4"]

def snap(p, pcset):
    return min((q for q in range(p - 6, p + 7) if q % 12 in pcset), key=lambda q: (abs(q - p), q))

def step(p, pcset, up):
    q = p + (1 if up else -1)
    while q % 12 not in pcset: q += 1 if up else -1
    return q

# A phrase = 8 cells (one per beat of the ground); a cell = [(midi|None, beats)].
def run_phrase(guide, shape, sets=SETS, octave=0):
    cells = []
    for i in range(8):
        p = snap(m(guide[i]) + 12 * octave, sets[i]); notes = [p]
        for k in range(3):
            up = {"fall": False, "rise": True, "zig": k == 2}[shape]
            q = step(notes[-1], sets[i], up)
            if not LO <= q <= HI: q = step(notes[-1], sets[i], not up)
            notes.append(q)
        cells.append([(n, .25) for n in notes])
    return cells

def cells_of(names, dur=1.0):
    return [[(m(n), dur)] for n in names]

PHRASES = {   # canon index -> 8 cells (indices 0-7 live in milestone 2)
    8:  run_phrase(THEME, "fall"),                                            # I  falling 16ths
    9:  run_phrase(THEME, "rise", octave=-1),                                 # J  rising 16ths
    10: run_phrase(THEME_B, "zig"),                                           # K  zig-zag
    11: [[(m(a), .5 if b else 1)] + ([(m(b), .5)] if b else []) for a, b in   # L  b2 appoggiaturas
         [("A5", None), ("Bb5", "A5"), ("F5", None), ("Gb5", "F5"),
          ("D5", None), ("Eb5", "D5"), ("Bb4", None), ("C5", "C#5")]],
    12: run_phrase(THEME, "fall", sets=[DIM7] * 8),                           # M  pure dim7 cascade
    13: [[(m(n), .25), (m(n) - 1, .25), (m(n), .25), (None, .25)] for n in THEME],  # N  shudder
    14: cells_of(["F5", "Eb5", "D5", "C#5", "Bb4", "A4", "Bb4", "C#5"]),      # O  theme, E -> Eb
    15: cells_of(["A5", "Ab5", "G5", "F#5", "F5", "E5", "Eb5", "D5"]),        # P  chromatic lament
    16: [[(m(n), .25), (m(n), .25), (m(n), .5)] for n in THEME],              # Q  stutter
    17: run_phrase(["A5"] * 8, "fall", sets=[DIM7] * 8),                      # R  dim7 from the top
    18: [[(m(n), .5), (m(n) - 12, .5)] for n in THEME],                       # S  octave leaps
    19: [[(m(n), .25), (m(n) - 1, .25)] * 2 for n in THEME_B],                # T  semitone trills
    20: run_phrase(["A3"] * 8, "rise", sets=[DIM7] * 8),                      # U  dim7 climbing
    21: [[(m(n), .5), (None, .5)] for n in THEME_B],                          # V  broken
}

# ---------------------------------------------------------------- build
def build():
    s = m2.build()
    for t in ("cello", "contrabass"):     # drop milestone 2's provisional final hold
        s.tracks[t]["notes"] = [n for n in s.tracks[t]["notes"] if n[0] < 128]
    s.track("choir", 52, "choir", pan=-.05)
    rng = np.random.default_rng(23)
    beat, starts = 128, {}
    bass_min = [m2.bass_note(m2.BASS_MIN, i) for i in range(8)]

    for c in range(17, 31):
        starts[c] = beat
        descent, fracture = c <= 24, c >= 25
        bmap = {27: [0, 1, 2, 3, 4, 5, 6], 28: [0, 1, 2, 3, 3, 4, 5, 6, 7]}.get(c, list(range(8)))
        n_beats = len(bmap)
        # tempo + metre
        s.set_tempo(beat, 54 if descent else {25: 54, 26: 50, 27: 57, 28: 48, 29: 56, 30: 52}[c])
        if c in (27, 28):
            s.set_timesig(beat, 4); s.set_timesig(beat + 4, n_beats - 4)
        elif c == 29:
            s.set_timesig(beat, 4)
        tritone_end = descent and c % 2 == 0 or c in (26, 29, 30)
        dyn = 58 + 3 * (c - 17) if descent else int(rng.integers(58, 100))

        # ground: cello + contrabass + pad (with toolbox colours)
        for j, i in enumerate(bmap):
            b = beat + j
            bn = m("Eb2") if (i == 7 and tritone_end) else bass_min[i]
            s.add("cello", b, 1, bn, dyn); s.add("contrabass", b, 1, bn - 12, dyn - 4)
            chord = list(m2.CHORDS_MIN[i])
            if i == 1: chord = ["C#4", "G4", "Bb4"]                 # A7b9
            if i == 6: chord = ["D4", "G4", "Bb4", "Eb5"]           # Gm(add b6)
            if i == 7 and tritone_end: chord = ["Db4", "G4", "Bb4"] # Eb7
            if fracture and j == 0:
                chord = ["D4", "Eb4", "E4", "F4"]                   # downbeat cluster
                s.add("pad", b, 2, "D3", 96)
            for n in chord:
                s.add("pad", b, 2 if (fracture and j == 0) else 1, n,
                      96 if (fracture and j == 0) else dyn - 20)

        # drones
        s.add("drone", beat, n_beats, "D2", 72); s.add("drone", beat, n_beats, "D1", 62)
        if fracture: s.add("drone", beat, n_beats, "Eb2", 50)

        # choir
        if descent:
            lament = ["A4", "Ab4", "G4", "F#4"] if c % 2 else ["F4", "E4", "Eb4", "D4"]
            for k, n in enumerate(lament):
                s.add("choir", beat + 2 * k, 2, n, 55 + 3 * (c - 17))
            s.add("choir", beat, 8, "D4", 45 + 3 * (c - 17))
        else:
            pair = ["D4", "A4"] if c % 2 else ["Eb4", "Bb4"]
            for n in pair: s.add("choir", beat, n_beats, n, 70)

        # canon voices
        for v in range(3):
            idx = c - 9 - v
            cells = PHRASES.get(idx)
            if cells is None:        # phrases 6-7 (G, H) still in flight for voices 2-3
                cells = [[]] * 8
                ph = m2.CANON[idx]; pos = 0.0
                for note, d in ph:
                    cells[int(pos)] = cells[int(pos)] + [(m(note), d)]; pos += d
            shift = (.5 if (v == 1 and c >= 19) else 0) if descent else (.25 if v == 1 else 0)
            transpose = 1 if (fracture and v == 2) else 0           # violin 3 -> Eb minor
            for j, i in enumerate(bmap):
                t = beat + j + shift
                for note, d in cells[i]:
                    if note is not None:
                        cents = rng.uniform(-9, 9) if fracture else [-4, 0, 4][v]
                        s.add(f"violin{v + 1}", t, d, note + transpose, dyn + 4, cents)
                    t += d
        if c in (26, 30):
            s.tapestop(beat + n_beats - 2, 2)
        beat += n_beats
    return s, starts

def tension(s, starts):
    rows = []
    names = ("violin1", "violin2", "violin3", "cello")
    for c, b0 in starts.items():
        b1 = starts.get(c + 1, b0 + 8); semi = tri = 0
        for t in np.arange(b0, b1, .25):
            snd = [n for nm in names for b, d, n, *_ in s.tracks[nm]["notes"] if b <= t < b + d]
            for i in range(len(snd)):
                for j in range(i + 1, len(snd)):
                    iv = abs(snd[i] - snd[j]) % 12
                    semi += iv in (1, 11); tri += iv == 6
        rows.append((c, b1 - b0, semi, tri))
    return rows

if __name__ == "__main__":
    os.chdir(ROOT)
    s, starts = build()
    write_midi("midi/m3_sections1-5.mid", s)
    total = render("renders/m3_sections1-5.wav", s)
    t15 = s.seconds(14 * 8)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t15:.2f}", "-i",
                    "renders/m3_sections1-5.mp3", "-af", "afade=t=in:d=1.5", "-b:a", "192k",
                    "renders/m3_sections4-5_excerpt.mp3"], check=True)
    print("notes:", sum(len(t["notes"]) for t in s.tracks.values()),
          "| re-parsed:", count_midi_notes("midi/m3_sections1-5.mid"))
    print(f"total {total:.0f}s | excerpt from cycle 15 at {t15:.1f}s | "
          f"Descent {s.seconds(starts[17]):.1f}s | Fracture {s.seconds(starts[25]):.1f}s")
    print("cycle beats semitone tritone (16th samples)")
    for r in tension(s, starts): print("  %2d   %d    %3d     %3d" % r)

"""Milestone 2: Sections 1-3 (cycles 1-16).

  1 Lullaby            cycles 1-4   D major, music box alone, faintly out of tune
  2 Something's Wrong  cycles 5-8   bass slips B->Bb, F#->F one note at a time; pitch drifts; tempo sags
  3 The Canon Wakes    cycles 9-16  D minor; 3 violins in canon (+2 bars each), cello/bass ground, drone

Run from nightmare/:  python3 src/milestone2.py
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Score, write_midi, render, count_midi_notes, m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q, E = 1.0, 0.5
def quarters(*ns): return [(n, Q) for n in ns]
def eighths(*ns): return [(n, E) for n in ns]

# ---------------------------------------------------------------- material
BASS_MAJ = ["D", "A", "B", "F#", "G", "D", "G", "A"]
BASS_MIN = ["D", "A", "Bb", "F", "G", "D", "G", "A"]
BASS_OCT = [3, 2, 2, 2, 2, 2, 2, 2]          # D3 A2 B2 F#2 G2 D2 G2 A2

CHORDS_MIN = [["D4", "F4", "A4"], ["C#4", "E4", "A4"], ["D4", "F4", "Bb4"], ["C4", "F4", "A4"],
              ["D4", "G4", "Bb4"], ["D4", "F4", "A4"], ["D4", "G4", "Bb4"], ["C#4", "E4", "A4"]]

# Section 1 phrases (original, D major)
MAJ_A = quarters("F#5", "E5", "D5", "C#5", "B4", "A4", "B4", "C#5")
MAJ_B = quarters("D5", "C#5", "B4", "A4", "G4", "F#4", "G4", "E4")
MAJ_C = eighths("D5", "F#5", "A5", "G5", "F#5", "D5", "F#5", "E5",
                "D5", "B4", "D5", "A5", "G5", "B5", "A5", "G5")

# Canon line (D minor): phrases A-C are Pachelbel's first three, in minor;
# D-H are new phrases written over the same progression so every entry fits.
CANON = [
    quarters("F5", "E5", "D5", "C#5", "Bb4", "A4", "Bb4", "C#5"),                       # A  theme
    quarters("D5", "C#5", "Bb4", "A4", "G4", "F4", "G4", "E4"),                          # B
    eighths("D4", "F4", "A4", "G4", "F4", "D4", "F4", "E4",
            "D4", "Bb3", "D4", "A4", "G4", "Bb4", "A4", "G4"),                           # C
    eighths("F4", "D4", "E4", "C#5", "D5", "F5", "A5", "A4",
            "Bb4", "G4", "A4", "F4", "Bb4", "D5", "C#5", "E5"),                          # D  climbing
    eighths("A5", "F5", "E5", "C#5", "D5", "Bb4", "C5", "A4",
            "Bb4", "G4", "A4", "F4", "G4", "Bb4", "A4", "C#5"),                          # E  falling arpeggios
    [("A5", 2), ("F5", 2), ("D5", 2), ("Bb4", 1), ("C#5", 1)],                           # F  long cries
    eighths("Eb5", "D5", "F5", "E5", "Eb5", "D5", "C5", "C#5",
            "Bb4", "A4", "Bb4", "A4", "D5", "Bb4", "C#5", "A4"),                         # G  sighing semitones
    quarters("F4", "E4", "D4", "C#4", "Bb3", "A3", "Bb3", "C#4"),                        # H  theme, low
]

def bass_note(names, i, octave_shift=0):
    return m(names[i] + str(BASS_OCT[i] + octave_shift))

# ---------------------------------------------------------------- build
def build():
    s = Score()
    s.track("musicbox", 10, "musicbox", pan=.15)
    for i, p in enumerate((-.55, .05, .55), 1):
        s.track(f"violin{i}", 40, "violin", pan=p)
    s.track("pad", 49, "pad", pan=0)
    s.track("cello", 42, "cello", pan=-.2)
    s.track("contrabass", 43, "cello", pan=.2, gain=.8)
    s.track("drone", 89, "drone", pan=0)
    rng = np.random.default_rng(11)

    # -- Section 1: Lullaby (cycles 1-4) ------------------------------------
    for c in range(4):
        b0 = c * 8
        for i in range(8):           # music-box plays the ground itself, an octave up
            s.add("musicbox", b0 + i, Q, bass_note(BASS_MAJ, i, +1), 58, rng.uniform(-5, 5))
        if c >= 1:
            s.phrase("musicbox", b0, [MAJ_A, MAJ_B, MAJ_C][c - 1], vel=70, cents=rng.uniform(-5, 5))
    for c, bpm in enumerate([60, 60, 60, 60]):
        s.set_tempo(c * 8, bpm)

    # -- Section 2: Something's Wrong (cycles 5-8) ---------------------------
    # each cycle: which bass degrees have slipped to minor, theme, detune spread, downward drift
    slips = [{2}, {2, 3}, {2, 3}, {2, 3}]
    themes = [MAJ_A,                                                     # major theme over a Bb...
              quarters("F5", "E5", "D5", "C#5", "B4", "A4", "B4", "C#5"),  # F# -> F, B still natural
              CANON[1],                                                  # fully minor
              CANON[0][:5]]                                              # winds down mid-phrase
    spread, drift = [8, 14, 20, 26], [-8, -18, -30, -45]
    for c in range(4):
        b0 = (4 + c) * 8
        s.set_tempo(b0, [58, 56, 55, 54][c])
        for i in range(8):
            names = BASS_MIN if i in slips[c] else BASS_MAJ
            s.add("musicbox", b0 + i, Q, bass_note(names, i, +1), 56,
                  drift[c] + rng.uniform(-spread[c], spread[c]))
        beat = b0
        for note, d in themes[c]:
            s.add("musicbox", beat, d, m(note), 68 - 4 * c, drift[c] + rng.uniform(-spread[c], spread[c]))
            beat += d
        if c >= 2:                   # strings and cello creep in, minor
            for i in range(8):
                for n in CHORDS_MIN[i]:
                    s.add("pad", b0 + i, Q, n, 40 + 10 * (c - 2))
                s.add("cello", b0 + i, Q, bass_note(BASS_MIN, i), 50 + 8 * (c - 2))
    s.add("drone", 7 * 8, 8, "D2", 45)            # drone fades in under cycle 8

    # -- Section 3: The Canon Wakes (cycles 9-16) ----------------------------
    start = 8 * 8
    s.add("drone", start, 64, "D2", 70); s.add("drone", start, 64, "D1", 60)
    for c in range(8):
        b0 = start + c * 8
        for i in range(8):
            s.add("cello", b0 + i, Q, bass_note(BASS_MIN, i), 72 + 2 * c)
            s.add("contrabass", b0 + i, Q, bass_note(BASS_MIN, i) - 12, 70 + 2 * c)
            for n in CHORDS_MIN[i]:
                s.add("pad", b0 + i, Q, n, 50 + 2 * c)
    for v in range(3):               # canon: voice v enters 2 bars (one cycle) after the previous
        for k, c in enumerate(range(v, 8)):
            s.phrase(f"violin{v + 1}", start + c * 8, CANON[k], vel=62 + 4 * c,
                     cents=[-4, 0, 4][v])
    s.add("cello", start + 64, 4, "D2", 70); s.add("contrabass", start + 64, 4, "D1", 66)
    return s

def dissonance_report(s):
    """Count semitone/tritone clashes between sounding canon voices + bass, per cycle of section 3."""
    rows = []
    for c in range(8):
        b0, clash = 64 + c * 8, {"semitone": 0, "tritone": 0}
        for t in np.arange(b0, b0 + 8, .5):
            sounding = [n for name in ("violin1", "violin2", "violin3", "cello")
                        for b, d, n, *_ in s.tracks[name]["notes"] if b <= t < b + d]
            for i in range(len(sounding)):
                for j in range(i + 1, len(sounding)):
                    iv = abs(sounding[i] - sounding[j]) % 12
                    if iv in (1, 11): clash["semitone"] += 1
                    if iv == 6: clash["tritone"] += 1
        rows.append((9 + c, clash["semitone"], clash["tritone"]))
    return rows

if __name__ == "__main__":
    os.chdir(ROOT)
    s = build()
    write_midi("midi/m2_sections1-3.mid", s)
    secs = render("renders/m2_sections1-3.wav", s)
    print("notes written:", sum(len(t["notes"]) for t in s.tracks.values()),
          "| re-parsed from MIDI:", count_midi_notes("midi/m2_sections1-3.mid"))
    print(f"duration: {secs:.0f}s")
    for b in (0, 32, 64):
        print(f"section start beat {b}: {s.seconds(b):.1f}s")
    print("cycle  semitone-clashes  tritones  (8th-note samples, section 3)")
    for r in dissonance_report(s):
        print("  %2d        %2d            %2d" % r)

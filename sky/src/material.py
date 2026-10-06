"""Sky Edition core material (shown in D major). One cycle = 8 quarter notes = 2 bars of 4/4.

Everything is in pitch names in D; use transpose() for the E-flat / F sections later.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "nightmare", "src"))
from lib import m  # noqa: E402

# ---------------------------------------------------------------- ground + harmony
GROUND = ["D3", "A2", "B2", "F#2", "G2", "D2", "G2", "A2"]          # identity anchor 1 (unchanged)

# Recolored chords, one per beat. Bass is always the ground note (anchor), so slash chords from the
# plan (A/C#, D/F#) become tenor-voice colour instead of bass notes.
CHORDS = [  # (name, chord tones, allowed colour tones)  -- pitch classes as names
    ("Dadd9",  ["D", "F#", "A"],       ["E", "C#", "B"]),   # add9 / maj7 / 6
    ("A(add9)", ["A", "C#", "E"],      ["B", "F#"]),        # 9 / 6
    ("Bm7",    ["B", "D", "F#", "A"],  ["C#", "E"]),
    ("F#m7",   ["F#", "A", "C#", "E"], ["B"]),
    ("Gmaj7",  ["G", "B", "D", "F#"],  ["A", "C#", "E"]),   # 9 / #11 (Lydian) / 13
    ("Dadd9",  ["D", "F#", "A"],       ["E", "B", "C#"]),
    ("Gmaj9",  ["G", "B", "D", "F#"],  ["A", "E", "C#"]),     # C# = Lydian #11
    ("A7",     ["A", "C#", "E", "G"],  ["B", "F#"]),        # A7sus4 only when no melody C# on the beat
]
# Piano left-hand / pad voicings (above the ground): warm, open, the tenor carries C# - B - A ...
VOICING = [["A3", "E4", "F#4"], ["C#4", "E4", "A4"], ["D4", "F#4", "A4"], ["C#4", "E4", "A4"],
           ["B3", "D4", "A4"], ["A3", "E4", "F#4"], ["B3", "E4", "A4"], ["C#4", "G4", "A4"]]

# ---------------------------------------------------------------- canon line (identity anchor 3/4)
# Each variation = 8 beats: list of (note | None, beats).
V1_THEME_A = [("F#5", 1), ("E5", 1), ("D5", 1), ("C#5", 1), ("B4", 1), ("A4", 1), ("B4", 1), ("C#5", 1)]
V2 = [("D5", 1), ("C#5", 1), ("B4", 1), ("A4", 1), ("G4", 1), ("F#4", 1), ("G4", 1), ("E4", 1)]
# Hisaishi-style lyrical line: mostly quarters / dotted notes, one chord tone per beat, few passing notes.
V3 = [("D5", 1), ("E5", 1), ("F#5", 1.5), ("E5", .5), ("D5", 1), ("A4", 1), ("B4", .5), ("D5", .5), ("C#5", 1)]
# Theme B (flight): rising 6th, long held note, stepwise fall that echoes Theme A.
V4_THEME_B = [("A4", .5), ("F#5", 2), ("E5", .5), ("C#5", 1), ("D5", 1.5), ("E5", .5), ("F#5", 1), ("E5", 1)]
CANON_LINE = [V1_THEME_A, V2, V3, V4_THEME_B]

# Flight variations (milestone 3). Contrast in note values so that at most one voice runs in 8ths:
V5_RUN = [("F#5", .5), ("A5", .5), ("E5", .5), ("A5", .5), ("F#5", .5), ("D5", .5), ("C#5", .5), ("E5", .5),
          ("D5", .5), ("B4", .5), ("A4", .5), ("D5", .5), ("B4", .5), ("D5", .5), ("E5", .5), ("C#5", .5)]
V6_SOAR = [("A5", 2), ("F#5", 2), ("G5", 1), ("F#5", 1), ("E5", 2)]
V7_SKIP = [("D5", .75), ("E5", .25), ("F#5", 1), ("D5", .75), ("E5", .25), ("F#5", 1),
           ("B4", .75), ("C#5", .25), ("D5", 1), ("E5", 1.5), ("C#5", .5)]
V8_RISE = [("A4", 1), ("C#5", 1), ("F#5", 2), ("E5", 1), ("D5", 1), ("E5", 2)]
FULL_LINE = CANON_LINE + [V5_RUN, V6_SOAR, V7_SKIP, V8_RISE]          # loops after V8

# Ornamental flute / glockenspiel line: strictly yonanuki pentatonic (D E F# A B), sparse "bird calls".
YONANUKI = {"D", "E", "F#", "A", "B"}
ORNAMENT = [("A5", 1.5), ("B5", .5), ("A5", 2), ("F#5", 1), ("E5", 1), ("D6", 1), ("B5", 1)]

# Theme A stretched to half notes (2 cycles) - the calm, singing version for piano / horns.
THEME_A_SLOW = [(n, 2) for n, _ in V1_THEME_A]

ORIGINAL_THEME = ["F#5", "E5", "D5", "C#5", "B4", "A4", "B4", "C#5"]

def tp(phrase, semis):
    """Transpose a phrase -> [(midi | None, beats)]."""
    return [(None if n is None else (n if isinstance(n, int) else m(n)) + semis, d) for n, d in phrase]

def pc(note):
    return note.rstrip("0123456789")

def notes_of(phrase, start=0.0):
    """-> [(onset, dur, midi)]"""
    out, b = [], start
    for n, d in phrase:
        if n is not None:
            out.append((b, d, m(n)))
        b += d
    return out

"""Milestone 4: Sections 6-7 (cycles 31-42), appended to sections 1-5.

  6 Climax / Chase  cycles 31-38  everything together; brass blares the theme; driving 8th-note
                                  octave bass; taiko on every chord change; accelerando 56 -> 104;
                                  cycles 35-38 lurch down a semitone to C# minor; hard cut to silence.
  7 Waking Up?      cycles 39-42  music box alone in D minor, winding down (ritardando, going flat),
                                  ends on an unresolved A-Eb tritone.

Run from nightmare/:  python3 src/milestone4.py
"""
import os, sys, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import write_midi, render, count_midi_notes, m
import milestone2 as m2
import milestone3 as m3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME, THEME_B = m3.THEME, m3.THEME_B

def tremolo(names, octave=0): return [[(m(n) + 12 * octave, .25)] * 4 for n in names]

PHRASES = dict(m3.PHRASES)
PHRASES.update({   # climax: recap of the figurations + tremolo theme statements
    22: m3.run_phrase(THEME, "fall"),
    23: m3.run_phrase(THEME, "rise", octave=-1),
    24: tremolo(THEME),
    25: m3.run_phrase(THEME_B, "zig"),
    26: tremolo(THEME_B),
    27: m3.run_phrase(THEME, "fall", sets=[m3.DIM7] * 8),
    28: tremolo(THEME),
    29: m3.run_phrase(["A5"] * 8, "fall", sets=[m3.DIM7] * 8),
})

def build():
    s, starts = m3.build()
    s.track("brass", 61, "brass", pan=-.1)
    s.track("taiko", 116, "taiko", pan=.1)
    rng = np.random.default_rng(42)
    beat = starts[30] + 8
    bass_min = [m2.bass_note(m2.BASS_MIN, i) for i in range(8)]

    # ---------------- Section 6: Climax / Chase ----------------
    for c in range(31, 39):
        starts[c] = beat
        tr = -1 if c >= 35 else 0                     # C# minor from cycle 35
        k = c - 31
        for i in range(8):                            # accelerando, per beat
            s.set_tempo(beat + i, 56 + (104 - 56) * (k * 8 + i) / 63)
        s.set_timesig(beat, 4) if c == 31 else None
        dyn = 84 + 2 * k
        for i in range(8):
            b = beat + i
            bn = bass_min[i] + tr
            for h in (0, .5):                         # driving 8th-note octaves
                s.add("cello", b + h, .5, bn, dyn); s.add("contrabass", b + h, .5, bn - 12, dyn)
            chord = list(m2.CHORDS_MIN[i])
            if i == 1: chord = ["C#4", "G4", "Bb4"]
            if i == 6: chord = ["D4", "G4", "Bb4", "Eb5"]
            for n in chord: s.add("pad", b, 1, m(n) + tr, dyn - 15)
            for n in [chord[0], chord[-1]]: s.add("choir", b, 1, m(n) + tr, dyn - 10)
            s.add("taiko", b, .5, m("D2") + tr, 110 if i == 0 else 88)        # every chord change
            if c >= 35: s.add("taiko", b + .5, .5, m("A2") + tr, 70)           # 8th pulses when it lurches
        theme = THEME if c % 2 else THEME_B           # brass: the theme, unmistakable
        for i, n in enumerate(theme):
            s.add("brass", beat + i, 1, m(n) - 12 + tr, dyn + 6)
            s.add("brass", beat + i, 1, m(n) - 24 + tr, dyn)
        s.add("drone", beat, 8, m("D1") + tr, 80); s.add("drone", beat, 8, m("D2") + tr, 80)
        for v in range(3):                            # canon continues, voices back in step and in key
            cells = PHRASES[c - 9 - v]
            for i in range(8):
                t = beat + i
                for note, d in cells[i]:
                    if note is not None:
                        s.add(f"violin{v + 1}", t, d, note + tr, dyn + 6, rng.uniform(-5, 5))
                    t += d
        beat += 8
    # final hit: cluster + everything on one stab, then hard silence
    for n in ["C#2", "C#3", "D3", "D4", "Eb4", "E4", "F4"]:
        for t in ("pad", "brass", "choir"): s.add(t, beat, 1, n, 120)
    s.add("taiko", beat, 1, "C#2", 127); s.add("contrabass", beat, 1, "C#1", 120)
    s.set_tempo(beat, 104)
    s.cut(beat + .75, 3.25)
    beat += 4                                         # ~2s of silence (3.25 beats at 104 + 0.75)
    starts["silence"] = beat - 4

    # ---------------- Section 7: Waking Up? ----------------
    mb_bass = [m2.bass_note(m2.BASS_MIN, i, +1) for i in range(8)]
    plan = [  # (theme cells, how many of the 8 ground notes still play)
        (m2.CANON[0], 8), (m2.CANON[1], 8), (m2.CANON[0], 6), (m2.CANON[0][:3], 3)]
    for k, (theme, keep) in enumerate(plan):
        c = 39 + k; starts[c] = beat
        for i in range(8):
            s.set_tempo(beat + i, 50 - 14 * (k * 8 + i) / 31)       # 50 -> 36 BPM
        drift = -20 - 15 * k                                        # going flat as it unwinds
        for i in range(keep):
            s.add("musicbox", beat + i, 1, mb_bass[i], 52 - 4 * k, drift + rng.uniform(-18, 18))
        t = beat
        for note, d in theme:
            s.add("musicbox", t, d, m(note), 64 - 5 * k, drift + rng.uniform(-18, 18)); t += d
        beat += 8
    # last breath: the music box stops on A against Eb, never reaching D
    s.set_tempo(beat - 4, 34)
    s.add("musicbox", beat - 3, 6, "A3", 50, -80); s.add("musicbox", beat - 3, 6, "Eb4", 46, -80)
    s.add("musicbox", beat - 1.5, 6, "Eb5", 38, -85)
    starts["end"] = beat + 3
    return s, starts

if __name__ == "__main__":
    os.chdir(ROOT)
    s, starts = build()
    write_midi("midi/m4_sections1-7.mid", s)
    total = render("renders/m4_sections1-7.wav", s, tail=7)
    t = s.seconds(starts[29])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i",
                    "renders/m4_sections1-7.mp3", "-af", "afade=t=in:d=1.5", "-b:a", "192k",
                    "renders/m4_sections6-7_excerpt.mp3"], check=True)
    print("notes:", sum(len(x["notes"]) for x in s.tracks.values()),
          "| re-parsed:", count_midi_notes("midi/m4_sections1-7.mid"))
    fmt = lambda x: f"{int(x // 60)}:{x % 60:04.1f}"
    print("total", fmt(total), "| excerpt from cycle 29 at", fmt(t))
    for key in (31, 35, "silence", 39, 42, "end"):
        print(f"  {key}: {fmt(s.seconds(starts[key]))}")

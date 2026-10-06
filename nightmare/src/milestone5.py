"""Milestone 5: orchestration + sample-based render of the complete piece.

Orchestration additions on top of milestone 4:
  * tubular bell tolls marking the section turns (cycles 9, 17, 25, 31, 35)
  * celesta doubling the music box an octave up in the Lullaby (sweeter -> more unsettling later)
  * a full string section doubling the canon in the Climax
  * per-role mix levels (auto-balanced stems)

Run from nightmare/:  python3 src/milestone5.py   (see README-render.md for dependencies)
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import write_midi, count_midi_notes, m
import milestone4 as m4
import render_sf2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEVELS = {  # target active-RMS per stem (dB, pre-master)
    "musicbox": -25, "celesta": -33, "violin1": -21, "violin2": -21, "violin3": -21,
    "strings": -22, "pad": -28, "cello": -22, "contrabass": -24, "drone": -30,
    "choir": -25, "brass": -16, "taiko": -17, "bells": -23,
}

def build():
    s, starts = m4.build()
    starts.setdefault(9, 64)
    s.track("bells", 14, "musicbox", pan=.3)
    s.track("celesta", 8, "musicbox", pan=-.3)
    s.track("strings", 48, "violin", pan=0)
    for c, note, vel in [(9, "D4", 60), (17, "D4", 80), (25, "Eb4", 90), (31, "D4", 110), (35, "C#4", 120)]:
        s.add("bells", starts[c], 4, note, vel); s.add("bells", starts[c], 4, m(note) - 12, vel - 10)
    for b, d, n, vel, cents in list(s.tracks["musicbox"]["notes"]):
        if b < 32 and n >= m("A4"):                      # lullaby melody only
            s.add("celesta", b, d, n + 12, vel - 18, cents)
    c31, c39 = starts[31], starts[39] - 4
    for v in ("violin1", "violin2", "violin3"):
        for b, d, n, vel, cents in s.tracks[v]["notes"]:
            if c31 <= b < c39:
                s.add("strings", b, d, n, vel - 8, 0)
    return s, starts

if __name__ == "__main__":
    os.chdir(ROOT)
    s, starts = build()
    write_midi("midi/nightmare_canon_in_d.mid", s)
    print("notes:", sum(len(t["notes"]) for t in s.tracks.values()),
          "| re-parsed:", count_midi_notes("midi/nightmare_canon_in_d.mid"))
    secs = render_sf2.render("renders/nightmare_canon_in_d.wav", s, LEVELS)
    t = s.seconds(starts[29])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i",
                    "renders/nightmare_canon_in_d.wav", "-af", "afade=t=in:d=1.5", "-b:a", "256k",
                    "renders/nightmare_canon_in_d_climax_excerpt.mp3"], check=True)
    os.remove("renders/nightmare_canon_in_d.wav")
    print(f"rendered {secs:.0f}s")

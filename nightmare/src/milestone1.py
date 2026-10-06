"""Milestone 1: ground bass, reharmonized progression and theme in D minor.

Generates (dependency-free MIDI + numpy preview render):
  midi/m1_reference_dmajor.mid   original material, for A/B comparison
  midi/m1_nightmare_core.mid     same material in D minor (+ variant cycles)
  renders/*.wav                  quick synth previews (converted to mp3 if ffmpeg exists)
and prints a recognizability report.

Run from the nightmare/ directory:  python3 src/milestone1.py
"""
import os, struct, subprocess, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
        "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

def m(name):  # "F#5" -> MIDI number
    p, o = name[:-1], int(name[-1])
    return 12 * (o + 1) + NOTE[p]

# ---------------------------------------------------------------- material
# One cycle = 8 quarter notes = 2 bars of 4/4. Everything below is per cycle.
ORIG_BASS   = ["D3", "A2", "B2", "F#2", "G2", "D2", "G2", "A2"]
ORIG_CHORDS = [["D4", "F#4", "A4"], ["C#4", "E4", "A4"], ["D4", "F#4", "B4"], ["C#4", "F#4", "A4"],
               ["D4", "G4", "B4"], ["D4", "F#4", "A4"], ["D4", "G4", "B4"], ["C#4", "E4", "A4"]]
ORIG_THEME  = ["F#5", "E5", "D5", "C#5", "B4", "A4", "B4", "C#5"]

NM_BASS     = ["D3", "A2", "Bb2", "F2", "G2", "D2", "G2", "A2"]
NM_CHORDS   = [["D4", "F4", "A4"],          # Dm
               ["C#4", "E4", "A4"],         # A  (harmonic-minor dominant)
               ["D4", "F4", "Bb4"],         # Bb
               ["C4", "F4", "A4"],          # F  (theme's C# turns it into F+)
               ["D4", "G4", "Bb4"],         # Gm
               ["D4", "F4", "A4"],          # Dm
               ["D4", "G4", "Bb4"],         # Gm
               ["C#4", "E4", "A4"]]         # A
NM_THEME    = ["F5", "E5", "D5", "C#5", "Bb4", "A4", "Bb4", "C#5"]

# "Wrongness" variants from the toolbox, used in the last two cycles only.
NM_CHORDS_VAR = list(NM_CHORDS)
NM_CHORDS_VAR[1] = ["C#4", "G4", "Bb4"]               # A7b9 (rootless, bass has A)
NM_CHORDS_VAR[6] = ["D4", "G4", "Bb4", "Eb5"]         # Gm(add b6)
NM_CHORDS_VAR[7] = ["Db4", "G4", "Bb4"]               # Eb7 (tritone sub of A)
NM_BASS_VAR = list(NM_BASS); NM_BASS_VAR[7] = "Eb2"

# ---------------------------------------------------------------- arrangement
def arrange(bass, chords, theme, bass_v=None, chords_v=None, variant_cycles=0, octave_bass=False):
    """4 plain cycles (+ optional variant cycles). Returns {track: [(beat, dur, midi)]}."""
    t = {"bass": [], "chords": [], "theme": []}
    cycles = 4 + variant_cycles
    for c in range(cycles):
        var = c >= 4
        b, ch = (bass_v, chords_v) if var else (bass, chords)
        for i in range(8):
            beat = c * 8 + i
            t["bass"].append((beat, 1.0, m(b[i])))
            if octave_bass:
                t["bass"].append((beat, 1.0, m(b[i]) - 12))
            if c >= 1:                       # cycle 1 = bass alone
                for n in ch[i]:
                    t["chords"].append((beat, 1.0, m(n)))
            if c >= 2:                       # theme from cycle 3
                t["theme"].append((beat, 1.0, m(theme[i])))
    # final tonic (reference) / unresolved stop (nightmare handled by caller)
    return t, cycles * 8

# ---------------------------------------------------------------- MIDI writer
def vlq(n):
    out = [n & 0x7F]; n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80); n >>= 7
    return bytes(out)

def write_midi(path, tracks, bpm, programs, tpq=480):
    def chunk(tag, data): return tag + struct.pack(">I", len(data)) + data
    tempo = vlq(0) + b"\xff\x51\x03" + struct.pack(">I", int(60e6 / bpm))[1:]
    tempo += vlq(0) + b"\xff\x58\x04\x04\x02\x18\x08" + vlq(0) + b"\xff\x2f\x00"
    out = [chunk(b"MTrk", tempo)]
    for ch, (name, notes) in enumerate(tracks.items()):
        ev = []
        for beat, dur, n in notes:
            ev.append((int(beat * tpq), 0x90 | ch, n, 80))
            ev.append((int((beat + dur) * tpq) - 1, 0x80 | ch, n, 0))
        ev.sort(key=lambda e: (e[0], e[1] & 0xF0))
        data = vlq(0) + b"\xff\x03" + vlq(len(name)) + name.encode()
        data += vlq(0) + bytes([0xC0 | ch, programs[name]])
        last = 0
        for tick, st, n, v in ev:
            data += vlq(tick - last) + bytes([st, n, v]); last = tick
        data += vlq(0) + b"\xff\x2f\x00"
        out.append(chunk(b"MTrk", data))
    hdr = chunk(b"MThd", struct.pack(">HHH", 1, len(out), tpq))
    with open(path, "wb") as f:
        f.write(hdr + b"".join(out))

PROGRAMS = {"bass": 42, "chords": 48, "theme": 10}   # cello, strings, music box

# ---------------------------------------------------------------- preview synth
SR = 44100
def hz(n, cents=0.0): return 440.0 * 2 ** ((n - 69 + cents / 100) / 12)

def voice(kind, n, dur, cents=0.0):
    length = dur + (1.5 if kind == "theme" else 0.3)
    tt = np.arange(int(length * SR)) / SR
    f = hz(n, cents)
    if kind == "theme":      # music box: bright partials, fast decay
        sig = sum(a * np.sin(2 * np.pi * f * k * tt) for k, a in [(1, 1), (2.76, .35), (5.4, .15)])
        env = np.exp(-tt * 3.0) * np.minimum(1, tt / .003)
        g = .22
    elif kind == "chords":   # soft string pad
        sig = sum(np.sin(2 * np.pi * f * k * tt + k) / k for k in range(1, 6))
        env = np.minimum(1, tt / .12) * np.clip((length - tt) / .3, 0, 1)
        g = .05
    else:                    # bass
        sig = np.sin(2 * np.pi * f * tt) + .4 * np.sin(4 * np.pi * f * tt)
        env = np.minimum(1, tt / .02) * np.clip((length - tt) / .3, 0, 1)
        g = .25
    return g * sig * env

def render(path, tracks, total_beats, bpm, detune_theme=False):
    spb = 60.0 / bpm
    buf = np.zeros(int((total_beats * spb + 3) * SR))
    rng = np.random.default_rng(7)
    for kind, notes in tracks.items():
        for beat, dur, n in notes:
            cents = rng.uniform(-14, 14) if (detune_theme and kind == "theme") else 0.0
            v = voice(kind, n, dur * spb, cents)
            s = int(beat * spb * SR)
            buf[s:s + len(v)] += v[:len(buf) - s]
    buf /= max(1e-9, np.abs(buf).max()) / 0.8
    pcm = (buf * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    mp3 = path[:-4] + ".mp3"
    if subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-b:a", "160k", mp3]).returncode == 0:
        os.remove(path)

# ---------------------------------------------------------------- recognizability
def report():
    def contour(seq): return ["up" if b > a else "down" if b < a else "same"
                              for a, b in zip(seq[:-1], seq[1:])]
    def letters(seq): return [s.rstrip("0123456789").replace("#", "").replace("b", "") for s in seq]
    lines = []
    for label, o, n in [("Theme", ORIG_THEME, NM_THEME), ("Ground bass", ORIG_BASS, NM_BASS)]:
        om, nm = [m(x) for x in o], [m(x) for x in n]
        cm = sum(a == b for a, b in zip(contour(om), contour(nm)))
        lm = sum(a[0] == b[0] for a, b in zip(letters(o), letters(n)))
        same = sum(a == b for a, b in zip(om, nm))
        maxdev = max(abs(a - b) for a, b in zip(om, nm))
        lines.append(f"{label}: contour {cm}/{len(om)-1} identical, note letters {lm}/{len(om)} identical, "
                     f"exact pitches {same}/{len(om)} kept, max shift {maxdev} semitone, rhythm identical")
    return "\n".join(lines)

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    os.chdir(ROOT)
    ref, ref_beats = arrange(ORIG_BASS, ORIG_CHORDS, ORIG_THEME)
    ref["bass"].append((ref_beats, 2.0, m("D2"))); ref["chords"] += [(ref_beats, 2.0, m(x)) for x in ["D4", "F#4", "A4"]]
    write_midi("midi/m1_reference_dmajor.mid", ref, 60, PROGRAMS)
    render("renders/m1_reference_dmajor.wav", ref, ref_beats + 2, 60)

    nm, nm_beats = arrange(NM_BASS, NM_CHORDS, NM_THEME, NM_BASS_VAR, NM_CHORDS_VAR,
                           variant_cycles=2, octave_bass=True)
    # end hanging on the A–Eb tritone instead of resolving to D minor
    nm["bass"] += [(nm_beats, 3.0, m("A1")), (nm_beats, 3.0, m("Eb2"))]
    nm["theme"].append((nm_beats, 3.0, m("Eb5")))
    write_midi("midi/m1_nightmare_core.mid", nm, 54, PROGRAMS)
    render("renders/m1_nightmare_core.wav", nm, nm_beats + 3, 54, detune_theme=True)
    print(report())

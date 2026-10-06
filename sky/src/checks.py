"""Analysis helpers: chord-tone check per line, and clash check between simultaneous voices."""
from material import CHORDS, GROUND, YONANUKI, notes_of, pc, m

PCN = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
NAMES = {v: k for k, v in PCN.items()}

def chord_report(phrase):
    """For each note starting on a beat: chord tone / colour / NON-chord."""
    rows = []
    for on, d, n in notes_of(phrase):
        beat = int(on) % 8
        name, tones, colour = CHORDS[beat]
        p = NAMES[n % 12]
        kind = "chord" if p in tones else "colour" if p in colour else "NCT"
        rows.append((on, p, name, kind, on == int(on)))
    return rows

def sounding(voices, t, tail=.1):
    """voices: {name: [(onset, dur, midi)]} -> [(name, midi, onset_here)].
    The last `tail` beats of a note are ignored (legato overlap / release, not a real clash)."""
    out = []
    for v, ns in voices.items():
        for on, d, n in ns:
            if on <= t + 1e-9 < on + max(d - tail, .05):
                out.append((v, n, abs(on - t) < 1e-9))
    return out

def clashes(voices, length, grid=.5, strong_only=True):
    """Semitone / minor-9th clashes between upper voices (major 7ths are allowed: maj7 harmony).
    A clash counts when at least one of the two notes starts at t; strong = on a quarter beat."""
    found = []
    t = 0.0
    while t < length - 1e-9:
        strong = abs(t - round(t)) < 1e-9
        if strong or not strong_only:
            s = sounding(voices, t)
            for i in range(len(s)):
                for j in range(i + 1, len(s)):
                    (a, na, oa), (b, nb, ob) = s[i], s[j]
                    if a == b or not (oa or ob): continue
                    iv = abs(na - nb)
                    if iv in (1, 13, 25):
                        found.append((t, a, NAMES[na % 12], b, NAMES[nb % 12], iv))
        t += grid
    return found

def ground_notes(cycles, start=0):
    return [(start + c * 8 + i, 1.0, m(GROUND[i])) for c in range(cycles) for i in range(8)]

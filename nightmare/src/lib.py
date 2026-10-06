"""Shared helpers: note parsing, multi-track MIDI writer with tempo map, stereo preview synth."""
import os, struct, subprocess, wave
import numpy as np

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
        "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

def m(name):
    return 12 * (int(name[-1]) + 1) + NOTE[name[:-1]]

class Score:
    """Notes are (beat, dur_beats, midi, velocity, cents). Tempo map = [(beat, bpm)]."""
    def __init__(self):
        self.tracks = {}      # name -> dict(program, pan, kind, notes)
        self.tempo = [(0, 60)]
        self.timesigs = [(0, 4, 4)]     # (beat, numerator, denominator)
        self.effects = []               # ("tapestop", beat, dur_beats)
    def track(self, name, program, kind, pan=0.0, gain=1.0):
        self.tracks.setdefault(name, dict(program=program, kind=kind, pan=pan, gain=gain, notes=[]))
        return self.tracks[name]["notes"]
    def add(self, name, beat, dur, note, vel=80, cents=0.0):
        n = m(note) if isinstance(note, str) else note
        self.tracks[name]["notes"].append((beat, dur, n, vel, cents))
    def phrase(self, name, beat, phrase, vel=80, cents=0.0, octave=0):
        """phrase = [(note|None, beats)]; returns end beat."""
        for note, d in phrase:
            if note is not None:
                self.add(name, beat, d, m(note) + 12 * octave, vel, cents)
            beat += d
        return beat
    def set_timesig(self, beat, num, den=4):
        self.timesigs = [t for t in self.timesigs if t[0] != beat] + [(beat, num, den)]
        self.timesigs.sort()
    def cut(self, beat, dur):
        """Hard silence (applied after reverb, so nothing rings through)."""
        self.effects.append(("cut", beat, dur))
    def tapestop(self, beat, dur):
        self.effects.append(("tapestop", beat, dur))
    def set_tempo(self, beat, bpm):
        self.tempo = [t for t in self.tempo if t[0] != beat] + [(beat, bpm)]
        self.tempo.sort()
    def seconds(self, beat):
        s, prev_b, prev_bpm = 0.0, 0, self.tempo[0][1]
        for b, bpm in self.tempo[1:]:
            if b >= beat: break
            s += (b - prev_b) * 60 / prev_bpm; prev_b, prev_bpm = b, bpm
        return s + (beat - prev_b) * 60 / prev_bpm
    def end_beat(self):
        return max(b + d for t in self.tracks.values() for b, d, *_ in t["notes"])

# ---------------------------------------------------------------- MIDI
def _vlq(n):
    out = [n & 0x7F]; n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80); n >>= 7
    return bytes(out)

def _chunk(tag, data): return tag + struct.pack(">I", len(data)) + data

def write_midi(path, score, tpq=480):
    meta = []
    for b, bpm in score.tempo:
        meta.append((int(b * tpq), b"\xff\x51\x03" + struct.pack(">I", int(60e6 / bpm))[1:]))
    for b, num, den in score.timesigs:
        meta.append((int(b * tpq), b"\xff\x58\x04" + bytes([num, den.bit_length() - 1, 24, 8])))
    meta.sort(key=lambda e: e[0])
    data, last = b"", 0
    for tick, ev in meta:
        data += _vlq(tick - last) + ev; last = tick
    out = [_chunk(b"MTrk", data + _vlq(0) + b"\xff\x2f\x00")]
    for ch, (name, t) in enumerate(score.tracks.items()):
        ch = ch if ch < 9 else ch + 1                # skip GM drum channel
        ev = []
        for beat, dur, n, vel, _ in t["notes"]:
            ev.append((int(beat * tpq), 1, bytes([0x90 | ch, n, max(1, min(127, int(vel)))])))
            ev.append((int((beat + dur) * tpq) - 1, 0, bytes([0x80 | ch, n, 0])))
        for kind, b, d in score.effects:          # tape stop -> pitch-bend dive, then reset
            if kind != "tapestop": continue
            t0, steps = int(b * tpq), 16
            for k in range(steps + 1):
                v = int(8192 - 8191 * k / steps)
                ev.append((t0 + int(d * tpq * .6 * k / steps), 2, bytes([0xE0 | ch, v & 0x7F, v >> 7])))
            ev.append((int((b + d) * tpq), 2, bytes([0xE0 | ch, 0, 64])))
        ev.sort(key=lambda e: (e[0], e[1]))
        pan = int(64 + t["pan"] * 63)
        data = _vlq(0) + b"\xff\x03" + _vlq(len(name)) + name.encode()
        data += _vlq(0) + bytes([0xC0 | ch, t["program"]]) + _vlq(0) + bytes([0xB0 | ch, 10, pan])
        last = 0
        for tick, _, e in ev:
            data += _vlq(tick - last) + e; last = tick
        out.append(_chunk(b"MTrk", data + _vlq(0) + b"\xff\x2f\x00"))
    with open(path, "wb") as f:
        f.write(_chunk(b"MThd", struct.pack(">HHH", 1, len(out), tpq)) + b"".join(out))

def count_midi_notes(path):
    """Minimal re-parse to validate a written file: returns note-on count."""
    d = open(path, "rb").read(); i, n = 14, 0
    while i < len(d):
        ln = struct.unpack(">I", d[i + 4:i + 8])[0]; j, end, run = i + 8, i + 8 + ln, 0
        while j < end:
            while d[j] & 0x80: j += 1
            j += 1
            st = d[j]
            if st == 0xFF:
                j += 2; l = 0
                while d[j] & 0x80: l = (l << 7) | (d[j] & 0x7F); j += 1
                l = (l << 7) | d[j]; j += 1 + l; continue
            if st & 0x80: run = st; j += 1
            if run & 0xF0 == 0x90 and d[j + 1] > 0: n += 1
            j += 1 if run & 0xF0 in (0xC0, 0xD0) else 2
        i = end
    return n

# ---------------------------------------------------------------- synth
SR = 44100
def _hz(n, cents): return 440.0 * 2 ** ((n - 69 + cents / 100) / 12)

def _voice(kind, n, dur, vel, cents):
    tail = {"musicbox": 1.8, "violin": .35, "pad": .6, "cello": .3, "drone": 1.5, "choir": .8,
            "brass": .35, "taiko": 1.2}[kind]
    tt = np.arange(int((dur + tail) * SR)) / SR
    f, L = _hz(n, cents), dur + tail
    rel = np.clip((L - tt) / tail, 0, 1)
    if kind == "musicbox":
        sig = sum(a * np.sin(2 * np.pi * f * k * tt) for k, a in [(1, 1), (2.76, .35), (5.4, .15), (8.9, .05)])
        env, g = np.exp(-tt * 2.6) * np.minimum(1, tt / .003), .30
    elif kind == "violin":
        vib = 1 + .004 * np.sin(2 * np.pi * 5.3 * tt) * np.clip((tt - .25) / .4, 0, 1)
        ph = 2 * np.pi * f * np.cumsum(vib) / SR
        sig = sum(np.sin(k * ph) / k ** 1.3 for k in range(1, 11))
        env, g = np.minimum(1, tt / .09) * np.where(tt < dur, 1, rel), .10
    elif kind == "pad":
        sig = sum(np.sin(2 * np.pi * f * (1 + d) * tt * k) / k ** 1.6 for k in range(1, 5) for d in (-.002, .002))
        env, g = np.minimum(1, tt / .5) * np.where(tt < dur, 1, rel), .035
    elif kind == "cello":
        sig = sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.2 for k in range(1, 9))
        env, g = np.minimum(1, tt / .05) * np.where(tt < dur, 1, rel), .11
    elif kind == "choir":    # "ooh": harmonics shaped by two formants, slow vibrato, 3 detuned singers
        sig = np.zeros_like(tt)
        for d in (-.004, 0, .005):
            vib = 1 + d + .005 * np.sin(2 * np.pi * (4.6 + 40 * d) * tt)
            ph = 2 * np.pi * f * np.cumsum(vib) / SR
            for k in range(1, 14):
                fk = f * k
                a = np.exp(-((fk - 320) / 140) ** 2) + .5 * np.exp(-((fk - 800) / 200) ** 2) + .02
                sig += a * np.sin(k * ph)
        env, g = np.minimum(1, tt / .6) * np.where(tt < dur, 1, rel), .05
    elif kind == "brass":    # low brass: saw-ish, brightness opens with the attack
        bright = np.minimum(1, tt / .12)
        sig = sum(np.sin(2 * np.pi * f * k * tt) / k ** (2.2 - 1.1 * bright) for k in range(1, 15))
        env, g = np.minimum(1, tt / .04) * np.where(tt < dur, 1, rel), .07
    elif kind == "taiko":    # pitch-drop body + noise skin hit
        body = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * np.exp(-tt / .03))) / SR)
        noise = np.random.default_rng(n).standard_normal(len(tt)) * np.exp(-tt / .025)
        sig = body * np.exp(-tt / .45) + .35 * noise
        env, g = np.minimum(1, tt / .002), .55
    else:  # drone: two slightly beating sines, slow swell
        sig = np.sin(2 * np.pi * f * tt) + np.sin(2 * np.pi * f * 1.003 * tt) + .3 * np.sin(4 * np.pi * f * tt)
        env, g = np.minimum(1, tt / 4.0) * np.where(tt < dur, 1, rel) * (1 + .25 * np.sin(2 * np.pi * .13 * tt)), .12
    return g * (vel / 100) * sig * env

def _reverb(x, seconds=3.2, wet=.28, seed=3):
    rng = np.random.default_rng(seed)
    ir_len = int(seconds * SR)
    ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / SR * 6.9 / seconds)
    ir[:int(.02 * SR)] = 0
    nfft = 1 << int(np.ceil(np.log2(len(x) + ir_len)))
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    y /= max(1e-9, np.abs(y).max()) / max(1e-9, np.abs(x).max())
    return (1 - wet) * x + wet * y

def render(path, score, tail=6.0):
    total = score.seconds(score.end_beat()) + tail
    L = np.zeros(int(total * SR)); R = np.zeros_like(L)
    for t in score.tracks.values():
        pl, pr = np.sqrt((1 - t["pan"]) / 2), np.sqrt((1 + t["pan"]) / 2)
        for beat, dur, n, vel, cents in t["notes"]:
            s0 = score.seconds(beat); d = score.seconds(beat + dur) - s0
            v = t["gain"] * _voice(t["kind"], n, d, vel, cents)
            s = int(s0 * SR); v = v[:len(L) - s]
            L[s:s + len(v)] += pl * v; R[s:s + len(v)] += pr * v
    for kind, b, d in score.effects:
        if kind != "tapestop": continue
        s0 = int(score.seconds(b) * SR); n = int((score.seconds(b + d) - score.seconds(b)) * SR)
        stop = min(n, int(1.1 * SR)); i = np.arange(stop)
        pos = s0 + i - i ** 2 / (2 * stop)              # speed ramps 1 -> 0
        fade = np.minimum(1, (stop - i) / (.05 * SR))
        for ch in (L, R):
            seg = np.interp(pos, np.arange(len(ch)), ch) * fade
            ch[s0:s0 + n] = 0; ch[s0:s0 + stop] = seg
    L, R = _reverb(L, seed=3), _reverb(R, seed=4)
    for kind, b, d in score.effects:
        if kind != "cut": continue
        s0, s1 = int(score.seconds(b) * SR), int(score.seconds(b + d) * SR)
        f = int(.01 * SR)
        for ch in (L, R):
            ch[s0:s0 + f] *= np.linspace(1, 0, len(ch[s0:s0 + f])); ch[s0 + f:s1] = 0
    peak = max(np.abs(L).max(), np.abs(R).max())
    st = (np.stack([L, R], 1) / peak * .85 * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
    mp3 = path[:-4] + ".mp3"
    if subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-b:a", "192k", mp3]).returncode == 0:
        os.remove(path)
    return total

"""Sky renderer + MIDI writer with expression: per-track CC11 automation and a sustain pedal.

TinySoundFont applies CC11 but ignores CC64, so the pedal is applied here: a note-off that falls
while the pedal is down is deferred to the pedal release. Both are also written to the MIDI file.
Track dict extras:  t["cc"] = [(beat, controller, value)],  t["pedal"] = [(down_beat, up_beat)]
Mixing/reverb/limiter are reused from nightmare/src/render_sf2.py.
"""
import struct
import numpy as np
import render_sf2
from render_sf2 import tsf, SF2, SR
from lib import _vlq, _chunk

def pedalled(t):
    """Notes with offs deferred by the pedal -> [(beat, dur, midi, vel, cents)]"""
    ped = sorted(t.get("pedal", []))
    out = []
    for b, d, n, v, c in t["notes"]:
        e = b + d
        for down, up in ped:
            if down <= e < up: e = up; break
        out.append((b, e - b, n, v, c))
    return out

def render_stem(t, score, n_samples):
    syn = tsf.Synth(samplerate=SR); sf = syn.sfload(SF2)
    syn.program_select(0, sf, 0, t["program"]); syn.pitchbend_range(0, 2.0)
    ev = []
    for b, d, n, vel, cents in pedalled(t):
        s0, s1 = int(score.seconds(b) * SR), int(score.seconds(b + d) * SR)
        ev.append((s0, 2, n, int(max(1, min(127, vel))), cents))
        ev.append((max(s0 + 1, s1), 0, n, 0, 0))
    for b, ctl, val in t.get("cc", []):
        ev.append((int(score.seconds(b) * SR), 1, ctl, val, 0))
    ev.sort(key=lambda e: (e[0], e[1]))
    out = np.zeros((n_samples, 2), np.float32); pos = 0
    for s, kind, a, v, cents in ev:
        s = min(s, n_samples)
        if s > pos:
            out[pos:s] = np.frombuffer(syn.generate(s - pos), np.float32).reshape(-1, 2); pos = s
        if kind == 2:
            if cents: syn.pitchbend(0, int(np.clip(8192 + cents / 200 * 8192, 0, 16383)))
            syn.noteon(0, a, v)
        elif kind == 1:
            if a != 64: syn.control_change(0, a, int(v))
        else:
            syn.noteoff(0, a)
    if pos < n_samples:
        out[pos:] = np.frombuffer(syn.generate(n_samples - pos), np.float32).reshape(-1, 2)
    return out.astype(np.float64)

def render(*a, **k):
    render_sf2.render_stem = render_stem          # the mixer calls the module-level render_stem
    return render_sf2.render(*a, **k)

def write_midi(path, score, tpq=480):
    meta = [(int(b * tpq), b"\xff\x51\x03" + struct.pack(">I", int(60e6 / bpm))[1:]) for b, bpm in score.tempo]
    meta += [(int(b * tpq), b"\xff\x58\x04" + bytes([n, d.bit_length() - 1, 24, 8])) for b, n, d in score.timesigs]
    meta.sort(key=lambda e: e[0]); data, last = b"", 0
    for tick, e in meta: data += _vlq(tick - last) + e; last = tick
    out = [_chunk(b"MTrk", data + _vlq(0) + b"\xff\x2f\x00")]
    for ch, (name, t) in enumerate(score.tracks.items()):
        ch = ch if ch < 9 else ch + 1
        ev = []
        for b, d, n, v, _ in t["notes"]:                     # raw notes: the pedal is written as CC64
            ev.append((int(b * tpq), 2, bytes([0x90 | ch, n, max(1, min(127, int(v)))])))
            ev.append((int((b + d) * tpq) - 1, 0, bytes([0x80 | ch, n, 0])))
        for b, ctl, val in t.get("cc", []):
            ev.append((int(b * tpq), 1, bytes([0xB0 | ch, ctl, int(val)])))
        for down, up in t.get("pedal", []):
            ev.append((int(down * tpq), 1, bytes([0xB0 | ch, 64, 127])))
            ev.append((int(up * tpq), 1, bytes([0xB0 | ch, 64, 0])))
        ev.sort(key=lambda e: (e[0], e[1]))
        data = _vlq(0) + b"\xff\x03" + _vlq(len(name)) + name.encode()
        data += _vlq(0) + bytes([0xC0 | ch, t["program"]]) + _vlq(0) + bytes([0xB0 | ch, 10, int(64 + t["pan"] * 63)])
        last = 0
        for tick, _, e in ev: data += _vlq(max(0, tick - last)) + e; last = max(last, tick)
        out.append(_chunk(b"MTrk", data + _vlq(0) + b"\xff\x2f\x00"))
    with open(path, "wb") as f:
        f.write(_chunk(b"MThd", struct.pack(">HHH", 1, len(out), tpq)) + b"".join(out))

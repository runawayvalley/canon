# Rendering the Sky Edition

```bash
cd sky
python3 src/milestone5.py      # -> midi/sky_canon_in_d.mid + renders/sky_canon_in_d*.mp3
```

Earlier milestones (`milestone1–4.py`) render their own previews the same way. Each builds on the previous one.

## Dependencies

The same as the nightmare edition (see `../nightmare/README-render.md`):
- Python 3 + numpy, plus `ffmpeg` on PATH.
- TinySoundFont: `pip install --no-deps --target /data/tools/pylib tinysoundfont`
- GeneralUser GS v2.0.3 SoundFont at `/data/tools/soundfonts/GeneralUser-GS.sf2` (<https://github.com/mrbumpy409/GeneralUser-GS>).

Override the locations with `NIGHTMARE_PYLIB=/path` and `NIGHTMARE_SF2=/path/file.sf2`.

The scripts import `../nightmare/src/lib.py` and `render_sf2.py`, and set `sys.dont_write_bytecode` so the tracked `nightmare/src/__pycache__` isn't modified.

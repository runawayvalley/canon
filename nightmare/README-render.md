# Rendering the piece

```bash
cd nightmare
python3 src/milestone5.py      # -> midi/nightmare_canon_in_d.mid + renders/nightmare_canon_in_d*.mp3
```

## Dependencies

- Python 3 + numpy, plus `ffmpeg` on PATH.
- **TinySoundFont** (Python bindings). Install with:
  `pip install --no-deps --target /data/tools/pylib tinysoundfont`
  Use `--no-deps` because the live-audio extra (`pyaudio`) isn't needed.
- **GeneralUser GS v2.0.3** SoundFont, by S. Christian Collins: <https://github.com/mrbumpy409/GeneralUser-GS>.
  Download it to `/data/tools/soundfonts/GeneralUser-GS.sf2`. Its license allows free use in your own music.

To use other locations, override them with `NIGHTMARE_PYLIB=/path` and `NIGHTMARE_SF2=/path/file.sf2`.

Earlier milestone scripts (`milestone1–4.py`) use the built-in numpy synth and need only numpy.

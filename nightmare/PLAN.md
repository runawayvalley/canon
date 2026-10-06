# Canon in D — Nightmare Edition: Plan

## Goal

Reimagine Pachelbel's *Canon in D* as a nightmare / horror piece, with an unsettling, dreamlike sound that slowly gets worse. The melody can be changed, but listeners must still recognize it as *Canon in D*.

## What must stay (identity anchors)

These keep it "Canon in D" no matter how dark it gets:

1. **The ground bass.** The 8-note, 2-bar ostinato loops the whole piece. In the original: `D – A – B – F# – G – D – G – A`.
2. **The 8-chord progression.** It's the harmonic backbone (reharmonized, but the same shape).
3. **The canon itself.** 3 upper voices play the same line, each entering **2 bars** after the previous one.
4. **The famous opening line.** The descending `F# – E – D – C# – B – A – B – C#` motif, recognizable even when altered.
5. **Variation-over-a-ground form.** Each cycle adds or changes something over the repeating bass.

## Key

- **Main key: D minor.** It keeps the "D" and gives the darkest result with the least distortion of the original.
- Use the **harmonic minor** (C#), so the dominant stays **A major**. This keeps the strong pull back to D and gives the theme the augmented-second sound (B♭–C#), which reads as eerie.
- **Option for later:** C# minor, or a sudden semitone drop in the climax, if D minor feels too "safe". Decide after the first draft.

### Reharmonized progression (D minor)

One chord per quarter note, so one pass of the ground = 2 bars of 4/4.

| Bar.beat | Original (D major) | Nightmare (D minor) | Notes |
| --- | --- | --- | --- |
| 1.1 | D | **Dm** | tonic |
| 1.2 | A | **A** (or A7♭9) | harmonic-minor dominant |
| 1.3 | Bm | **B♭** | VI, the darkest substitution |
| 1.4 | F#m | **F** (melody's C# makes it F+) | III, augmented colour |
| 2.1 | G | **Gm** | iv |
| 2.2 | D | **Dm** | tonic |
| 2.3 | G | **Gm** (or Gm(add♭6)) | iv |
| 2.4 | A | **A** → later **E♭7** | tritone sub in later cycles = "wrongness" |

New bass: `D – A – B♭ – F – G – D – G – A`

### Opening theme (D minor)

`F – E – D – C# – B♭ – A – B♭ – C#`

It's the same contour as the original, just in minor, so it's instantly recognizable.

## Nightmare techniques (toolbox)

Bring these in gradually, not all at once.

**Harmony and melody**
- Phrygian ♭2 (E♭) inflections in the melody.
- Tritone substitutions at cycle endings (A → E♭).
- Chromatic passing tones and *slow* chromatic descents in inner voices.
- Cluster chords (e.g., D–E♭–E) on downbeats in the climax.
- **Polytonal canon:** in the "Fracture" section, one voice plays its entry a semitone off (E♭ minor) against the D-minor bass.
- Diminished-7th runs replacing the original's flowing 16th-note variations.

**Rhythm and time**
- Slow base tempo (~50–56 BPM) for dread.
- Rhythmic displacement: one canon voice shifted by an 8th note, so it sounds "out of sync".
- Bars dropped or added (a 3/4 or 5/4 bar) to break the loop's predictability.
- Gradual accelerando into the climax, then a sudden halt.

**Sound and texture**
- Detuned music box / celesta (a lullaby gone wrong).
- Low strings, contrabassoon, sub-bass drones on D.
- Whisper / choir pads on "ooh" in the minor.
- Reversed piano and reverse-reverb swells into downbeats.
- Pitch drift (slight, slow detuning over a cycle).
- Glitchy tape-stop effects in transitions.

## Structure (draft, ~4–5 min)

Each "cycle" = one 2-bar pass of the ground bass.

| # | Section | Cycles | Key | Content |
| --- | --- | --- | --- | --- |
| 1 | **Lullaby** | 1–4 | D major | Music box alone plays the original theme, innocent and slightly out of tune. |
| 2 | **Something's Wrong** | 5–8 | D major → D minor | The bass slips: B → B♭ and F# → F, one note at a time. Pitch drift begins. |
| 3 | **The Canon Wakes** | 9–16 | D minor | Voice 1, then voice 2 (+2 bars), then voice 3 (+4 bars) in the minor. Low strings and drone. |
| 4 | **Descent** | 17–24 | D minor | Diminished runs, tritone cycle endings, choir pads, displaced voice. |
| 5 | **Fracture** | 25–30 | D minor + E♭ minor | Polytonal canon, odd-meter bars, tape-stops, clusters. |
| 6 | **Climax / Chase** | 31–38 | D minor (maybe a drop to C# minor) | Full texture, bass in octaves, accelerando, percussion hits on chord changes. |
| 7 | **Waking Up?** | 39–42 | D minor | Sudden silence, then the music box alone again, now in minor, slowing. Ends on an **unresolved A–E♭ tritone** (no final tonic). |

## Instrumentation (initial)

- Music box / celesta (lead, opening and ending)
- Violin I, II, III (the 3 canon voices) → later processed or distorted
- Cello + contrabass (ground bass)
- Choir pad
- Sub drone (D)
- Low percussion (taiko / impacts) for the climax only

## Deliverables

Proposed layout in `nightmare/`:

```
nightmare/
├── PLAN.md            # this file
├── score/             # notation (MusicXML / LilyPond)
├── midi/              # generated MIDI per section + full piece
├── src/               # scripts that generate the MIDI
└── renders/           # audio previews (wav/mp3)
```

## Milestones

1. ✅ **Theme and bass in D minor** (done, see `MILESTONE1.md`). Write the ground bass, the reharmonized progression, and the minor theme, then sanity-check that it's still recognizable.
2. ✅ **Sections 1–3** (done, see `MILESTONE2.md`). Build the lullaby, the major→minor transition, and the canon entries.
3. ✅ **Sections 4–5** (done, see `MILESTONE3.md`). Add the nightmare techniques and the polytonal fracture.
4. **Sections 6–7.** Write the climax and the unresolved ending.
5. **Orchestration and render.** Assign instruments, render an audio preview.
6. **Review and iterate.** Check recognizability vs. scariness, adjust the key (D minor vs. C# minor), then commit and push.

## Open questions

- **Output format:** MIDI + audio render, sheet music, a DAW project, or all of them?
- **Tooling:** generate with Python (e.g., `mido` / `music21`) and render with FluidSynth + a soundfont, or something else?
- **Style flavor:** orchestral horror (film score), dark ambient, or industrial / metal for the climax?
- **Length:** is ~4–5 min right, or shorter (~2–3 min)?

# MixFriend

Generate Logic Pro X Channel EQ presets (`.pst`) that simulate how your mix sounds on different speakers and devices.

Drop the presets into Logic's Channel EQ and quickly A/B your mix through iPhone speakers, laptop speakers, car stereos, club PAs, and more.

## Presets

| Device | HP | LP | Character |
|---|---|---|---|
| iPhone Speaker | 250 Hz | 11 kHz | No bass, -8dB shelf, +4dB peak at 2.5kHz, dead above 11kHz |
| MacBook Speakers | 80 Hz | 16 kHz | Weak sub-bass, 1.5kHz recession, 5-8kHz brightness peak |
| HomePod | 35 Hz | 16 kHz | +4dB bass, 800Hz dip (no midrange driver), 3kHz presence dip |
| HomePod Mini | 80 Hz | 15 kHz | Bass to ~80Hz, 3.5kHz presence dip, warm/mid-forward |
| Amazon Echo | 50 Hz | 14 kHz | 40-100Hz emphasis, muddy mids, aggressive high-mids |
| Car Stereo | 60 Hz | 16 kHz | +4dB cabin boom at 100Hz, -5dB midrange suckout, +3dB presence |
| Cheap Earbuds | 100 Hz | 14 kHz | Thin bass, +6dB harsh peak at 3kHz, 5kHz dip, 7kHz peak |
| Club PA | 30 Hz | 16 kHz | +5dB sub at 70Hz, -3dB scoop at 315Hz, +3dB horn presence at 3kHz, HF rolloff from 8kHz |
| Bluetooth Speaker | 70 Hz | 16 kHz | +5dB bass at 120Hz, -3dB mid recession, presence at 4kHz |
| Flat Reference | — | — | All bands off (bypass) |

## Usage

```
python3 mixfriend.py                     # generate all presets
python3 mixfriend.py -d iphone           # generate one (substring match)
python3 mixfriend.py -o ~/presets        # output to a specific directory
python3 mixfriend.py --list              # show available devices
```

## Install presets in Logic Pro

Copy the contents of the `Presets` folder to:

```
~/Library/Audio/Presets/Apple/Logic Pro X/Channel EQ/
```

The `:` in the filename displays as `/` in Finder and Logic's preset menu, so they appear as a "MixFriend" submenu (e.g. `MixFriend / iPhone Speaker`).

## Add a new device

Edit `devices.json` and add an entry. Each device has 8 bands:

```
HP Filter → Low Shelf → Parametric 1–4 → High Shelf → LP Filter
```

Band properties:

| Field | Default | Notes |
|---|---|---|
| `frequency` | (required) | Frequency in Hz |
| `gain` | `0.0` | Gain in dB |
| `q` | `0.71` | Q factor (0.71 = Butterworth) |
| `enabled` | `true` | Set `false` to bypass |

## Project files

| File | Purpose |
|---|---|
| `mixfriend.py` | Preset generator script (Python 3, no dependencies) |
| `devices.json` | Device EQ profiles — edit this to add/modify devices |
| `Presets/` | Generated `.pst` output folder. Files are named `MixFriend : Name.pst` — the `:` displays as `/` in Finder and Logic's preset menu (macOS swaps `:` ↔ `/` in filenames). |
| `--sample.pst` | A real Logic Pro Channel EQ preset for reference/testing. Load in Logic and hex-compare against generated files to verify the binary format. |

## Binary format

The Channel EQ `.pst` format was reverse-engineered. Total size is 240 bytes:

| Offset | Size | Content |
|---|---|---|
| 0 | 24 | Header: file size (240), version (1), unknown (52), magic `GAMETSPP`, data size (236) — all uint32 LE |
| 24 | 128 | 8 EQ bands, 16 bytes each: `[Q, enabled, freq, gain]` as little-endian float32 |
| 152 | 88 | Footer: analyzer settings, output gain, etc. — constant across all presets |

Band order: HP Filter, Low Shelf, Parametric 1–4, High Shelf, LP Filter.

`enabled` is a float: `1.0` = on, `0.0` = off. HP/LP bands always have `gain = 0.0`.

The `[Q, enabled, freq, gain]` field order is a best-guess interpretation. If presets load in Logic with wrong values, the fields may need reordering — change `BAND_FIELD_ORDER` in `mixfriend.py` (one-line fix).

The 88-byte footer is hardcoded in `mixfriend.py` as `FOOTER`. It was verified identical across all tested presets. If Logic adds new footer fields in a future update, hex-dump a fresh preset and compare against `--sample.pst`.

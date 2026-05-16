# Merlin Editor

GUI to edit the SD card of the **Merlin** storytelling speaker (Bayard / Radio France).
Add, rename, reorder, and delete stories without running command-line scripts.

Built on top of [IArchi/Merlin-jailbreak](https://github.com/IArchi/Merlin-jailbreak)
(vendored in `vendor/`).

## Install (end users)

Grab the latest release from the **[Releases page](../../releases)**.

**ffmpeg is bundled** — no extra install required.

### macOS

1. Download `merlin-editor-macos.zip`, unzip.
2. Drag **Merlin Editor.app** into `/Applications`.
3. First launch: **right-click the app → Open** (Gatekeeper blocks unsigned apps; this confirms you trust it).

### Linux

1. Download `merlin-editor-linux.tar.gz`, extract.
2. Run `./merlin-editor/merlin-editor`.

### Windows

1. Download `merlin-editor-windows.zip`, extract.
2. Run `merlin-editor\merlin-editor.exe`.

## Workflow

1. Remove the 4 screws on the back of the Merlin speaker, take out the microSD.
2. Plug the SD into your computer.
3. **Open…** (or pick it from the **SD card ▾** menu) → select `playlist.bin` at the SD root.
4. Edit:
   - **+ Story** or drop an audio file (and an image) from your file manager — auto-converted to MP3 stereo 128 kbps + JPEG 128×128.
   - **+ Folder** — create a category.
   - Drag stories/folders inside the tree to reorder or move.
   - Rename, delete, replace audio/image.
5. **Save** — writes `playlist.bin` and all media back to the SD.

## Develop

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/merlin-gui
```

Requires Python 3.10+, PySide6, Pillow. For local dev, install ffmpeg via your
package manager (`brew install ffmpeg`, `apt install ffmpeg`, etc.) — the
released bundles ship their own ffmpeg.

## Release

Releases are built automatically by GitHub Actions on every tag matching `v*`:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow (`.github/workflows/release.yml`) builds on macOS / Linux / Windows
runners, uploads the artifacts, and publishes a GitHub Release.

You can also trigger a build manually from the **Actions** tab without creating
a release (artifacts only).

## Project layout

```
merlin_gui/
  app.py           # QApplication entry point
  main_window.py   # main window, tree + editor panel + scrubber
  playlist.py      # binary read/write + in-memory tree model
  converters.py    # ffmpeg + Pillow conversion helpers
  tree.py          # QTreeWidget subclass with drag-and-drop (internal + files)
  styles.py        # macOS-style QSS for light + dark mode
vendor/
  merlin-jailbreak/  # snapshot of the original CLI tool (reference)
merlin-editor.spec   # PyInstaller config (cross-platform)
.github/workflows/
  release.yml      # macOS/Linux/Windows build + release
THIRD_PARTY_NOTICES.md  # FFmpeg/PySide6/Pillow attributions
```

## Third-party

See [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md). The bundles ship
FFmpeg (LGPLv2.1+ on macOS/Windows, GPLv3 on Linux); source for FFmpeg is
available at <https://github.com/FFmpeg/FFmpeg>.

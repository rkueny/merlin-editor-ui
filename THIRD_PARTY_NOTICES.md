# Third-party notices

## FFmpeg

This application ships a binary build of **FFmpeg** (https://ffmpeg.org) used
for audio conversion.

- **License**: GNU Lesser General Public License (LGPL) v2.1+ for the macOS and
  Windows builds, GNU General Public License (GPL) v3 for the Linux build.
- **Source code**: <https://github.com/FFmpeg/FFmpeg>
- **Full license texts**:
  - LGPL v2.1: <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt>
  - GPL v3: <https://www.gnu.org/licenses/gpl-3.0.txt>

Build sources:
- macOS: <https://evermeet.cx/ffmpeg/>
- Linux: <https://johnvansickle.com/ffmpeg/>
- Windows: <https://github.com/BtbN/FFmpeg-Builds>

The FFmpeg binary is unmodified and used as-is. Per LGPL/GPL terms, you may
replace the bundled `ffmpeg` binary with your own build at any time.

## Merlin-jailbreak

The binary format read/write logic was originally published in
<https://github.com/IArchi/Merlin-jailbreak> by IArchi (with the playlist.bin
codec contributed by Djokeur). MIT license. A snapshot is vendored in
`vendor/merlin-jailbreak/`.

## PySide6 / Qt

PySide6 ships with Qt for Python, licensed under LGPL v3. See
<https://doc.qt.io/qtforpython/licenses.html>.

## Pillow

PIL fork, MIT-CMU License. See <https://github.com/python-pillow/Pillow>.

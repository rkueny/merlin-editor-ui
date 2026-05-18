"""Convert arbitrary user files into Merlin's required formats.

- Audio: any format → MP3 stereo 128kbps (via ffmpeg)
- Image: any format → JPEG 128x128 (via Pillow, padded to square)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


class FFmpegMissing(RuntimeError):
    pass


class ConversionError(RuntimeError):
    pass


def _bundled_ffmpeg() -> Path | None:
    """Look for an ffmpeg binary shipped next to the running executable."""
    if getattr(sys, "frozen", False):
        candidates = [Path(sys.executable).parent]
        # PyInstaller adds _MEIPASS for the temp extraction dir of one-file builds.
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass))
    else:
        candidates = [Path(__file__).resolve().parent.parent / "bin"]

    name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    for d in candidates:
        p = d / name
        if p.is_file():
            return p
    return None


def ffmpeg_path() -> str | None:
    bundled = _bundled_ffmpeg()
    if bundled is not None:
        return str(bundled)
    return shutil.which("ffmpeg")


def ffmpeg_available() -> bool:
    return ffmpeg_path() is not None


def to_merlin_audio(src: Path, dst: Path) -> None:
    """Convert any audio file to MP3 stereo 128kbps at dst."""
    binary = ffmpeg_path()
    if binary is None:
        raise FFmpegMissing(
            "ffmpeg not found. The app should ship with a bundled ffmpeg — "
            "if you see this in a packaged build, please file an issue."
        )

    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        binary,
        "-y",
        "-i", str(src),
        "-vn",
        "-ac", "2",
        "-b:a", "128k",
        "-f", "mp3",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ConversionError(f"ffmpeg failed for {src.name}:\n{result.stderr[-2000:]}")


def extract_embedded_cover(audio_src: Path, dst: Path) -> bool:
    """Extract embedded cover art (ID3v2 APIC, etc.) from an audio file.
    Returns True if a cover was written to dst, False otherwise.
    """
    binary = ffmpeg_path()
    if binary is None:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    cmd = [
        binary,
        "-y",
        "-i", str(audio_src),
        "-an",
        "-vframes", "1",
        "-c:v", "mjpeg",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0 and dst.exists() and dst.stat().st_size > 0


def to_merlin_image(src: Path, dst: Path) -> None:
    """Convert any image to JPEG 128x128 padded to square (black background)."""
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(src).convert("RGB")
    w, h = img.size
    if w == h:
        squared = img
    elif w > h:
        squared = Image.new(img.mode, (w, w), (0, 0, 0))
        squared.paste(img, (0, (w - h) // 2))
    else:
        squared = Image.new(img.mode, (h, h), (0, 0, 0))
        squared.paste(img, ((h - w) // 2, 0))

    squared.resize((128, 128), Image.LANCZOS).save(dst, "JPEG", quality=95)


AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus", ".wma", ".aiff", ".aif"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".heic", ".heif"}


def is_audio(path: Path) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTS


def is_image(path: Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS

"""Convert arbitrary user files into Merlin's required formats.

- Audio: any format → MP3 stereo 128kbps (via ffmpeg)
- Image: any format → JPEG 128x128 (via Pillow, padded to square)
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image


class FFmpegMissing(RuntimeError):
    pass


class ConversionError(RuntimeError):
    pass


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def to_merlin_audio(src: Path, dst: Path) -> None:
    """Convert any audio file to MP3 stereo 128kbps at dst."""
    if not ffmpeg_available():
        raise FFmpegMissing("ffmpeg not found in PATH. Install with `brew install ffmpeg`.")

    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
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

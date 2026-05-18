"""In-memory model for a Merlin playlist.

The Merlin SD card contains:
- playlist.bin (binary tree of items, ~154 bytes per item)
- <uuid>.jpg and <uuid>.mp3 for each story/folder
- optional .cfg files (preserved verbatim)

This module reads/writes playlist.bin and tracks each node's current media
location on disk. Saving copies/renames media to <uuid>.jpg/.mp3 in the
target directory and rewrites playlist.bin.
"""

from __future__ import annotations

import shutil
import time
import uuid as uuid_lib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# Type codes used in playlist.bin
TYPE_ROOT = 1
TYPE_FOLDER = 2
TYPE_STORY = 4
TYPE_FAVORITES = 10
TYPE_STORY_ALT = 36  # observed on read for some terminal items

ITEM_SIZE = 152  # 20 header + 65 uuid block + 67 title block
UUID_MAX_BYTES = 64
TITLE_MAX_BYTES = 66
FAVORITES_TITLE = "Merlin_favorite"


def _truncate_utf8(s: str, max_bytes: int) -> str:
    """Return s truncated so its UTF-8 encoding is ≤ max_bytes, never
    splitting a multi-byte char. Returns s unchanged when it already fits."""
    encoded = s.encode("utf-8")
    if len(encoded) <= max_bytes:
        return s
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def is_story(type_code: int) -> bool:
    return type_code in (TYPE_STORY, TYPE_STORY_ALT)


def is_folder(type_code: int) -> bool:
    return type_code in (TYPE_ROOT, TYPE_FOLDER, TYPE_FAVORITES)


@dataclass
class Node:
    uuid: str
    title: str
    type: int
    children: list["Node"] = field(default_factory=list)
    parent: "Node | None" = None

    # Path to the current source file on disk (None if no asset yet).
    image_path: Path | None = None
    audio_path: Path | None = None

    # Metadata preserved verbatim across load/save.
    fav_order: int = 0
    limit_time: int = 0
    add_time: int = 0

    @property
    def is_story(self) -> bool:
        return is_story(self.type)

    @property
    def is_folder(self) -> bool:
        return is_folder(self.type)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def _read_item(buf: bytes, offset: int) -> tuple[dict, int]:
    """Parse one item starting at offset. Lenient on length overflow: if a
    previous version of the writer produced a uuid or title block longer than
    nominal (because the title exceeded TITLE_MAX_BYTES), this reader still
    realigns correctly on the next item.
    """
    def u16(o):
        return int.from_bytes(buf[o : o + 2], "little")

    def u32(o):
        return int.from_bytes(buf[o : o + 4], "little")

    item = {
        "id": u16(offset),
        "parent_id": u16(offset + 2),
        "order": u16(offset + 4),
        "nb_children": u16(offset + 6),
        "fav_order": u16(offset + 8),
        "type": u16(offset + 10),
        "limit_time": u32(offset + 12),
        "add_time": u32(offset + 16),
    }
    o = offset + 20
    uuid_len = buf[o]
    item["uuid"] = buf[o + 1 : o + 1 + uuid_len].decode("utf-8", errors="replace")
    o += 1 + max(UUID_MAX_BYTES, uuid_len)

    title_len = buf[o]
    item["title"] = buf[o + 1 : o + 1 + title_len].decode("utf-8", errors="replace")
    o += 1 + max(TITLE_MAX_BYTES, title_len)
    return item, o


def _write_item(item: dict) -> bytes:
    out = bytearray()
    out += item["id"].to_bytes(2, "little")
    out += item["parent_id"].to_bytes(2, "little")
    out += item["order"].to_bytes(2, "little")
    out += item["nb_children"].to_bytes(2, "little")
    out += item["fav_order"].to_bytes(2, "little")
    out += item["type"].to_bytes(2, "little")
    out += item["limit_time"].to_bytes(4, "little")
    out += item["add_time"].to_bytes(4, "little")

    uuid_str = _truncate_utf8(item["uuid"], UUID_MAX_BYTES)
    u = uuid_str.encode("utf-8")
    out += len(u).to_bytes(1, "little")
    out += u
    out += b"\x00" * (UUID_MAX_BYTES - len(u))

    title_str = _truncate_utf8(item["title"], TITLE_MAX_BYTES)
    t = title_str.encode("utf-8")
    out += len(t).to_bytes(1, "little")
    out += t
    out += b"\x00" * (TITLE_MAX_BYTES - len(t))
    return bytes(out)


def load_playlist(playlist_bin: Path) -> Node:
    """Parse playlist.bin and resolve media paths from the same directory."""
    playlist_bin = Path(playlist_bin)
    data = playlist_bin.read_bytes()
    media_dir = playlist_bin.parent

    raw_items: list[dict] = []
    offset = 0
    # An item is at minimum ITEM_SIZE bytes, but can be larger if a previous
    # version of the writer overflowed the title block. Stop when there's not
    # enough room for even a minimal item.
    while offset + ITEM_SIZE <= len(data):
        item, offset = _read_item(data, offset)
        raw_items.append(item)

    nodes_by_id: dict[int, Node] = {}
    for it in raw_items:
        node = Node(
            uuid=it["uuid"],
            title=it["title"],
            type=it["type"],
            fav_order=it["fav_order"],
            limit_time=it["limit_time"],
            add_time=it["add_time"],
        )
        if it["type"] != TYPE_ROOT:
            jpg = media_dir / f"{it['uuid']}.jpg"
            if jpg.exists():
                node.image_path = jpg
        if is_story(it["type"]):
            mp3 = media_dir / f"{it['uuid']}.mp3"
            if mp3.exists():
                node.audio_path = mp3
        nodes_by_id[it["id"]] = node

    root: Node | None = None
    for it in raw_items:
        node = nodes_by_id[it["id"]]
        if it["parent_id"] == 0:
            root = node
        else:
            parent = nodes_by_id.get(it["parent_id"])
            if parent is not None:
                parent.children.append(node)
                node.parent = parent

    if root is None:
        raise ValueError(f"No root node found in {playlist_bin}")

    for parent in nodes_by_id.values():
        parent.children.sort(key=lambda n: _original_order(n, raw_items, nodes_by_id))

    return root


def _original_order(node: Node, raw_items: list[dict], nodes_by_id: dict[int, Node]) -> int:
    for it in raw_items:
        if nodes_by_id.get(it["id"]) is node:
            return it["order"]
    return 0


def new_folder(title: str) -> Node:
    return Node(
        uuid=str(uuid_lib.uuid4()),
        title=title,
        type=TYPE_FAVORITES if title == FAVORITES_TITLE else TYPE_FOLDER,
        add_time=int(time.time()),
    )


def new_story(title: str, audio_path: Path | None = None, image_path: Path | None = None) -> Node:
    return Node(
        uuid=str(uuid_lib.uuid4()),
        title=title,
        type=TYPE_STORY,
        audio_path=audio_path,
        image_path=image_path,
        add_time=int(time.time()),
    )


ProgressCb = Callable[[int, int, str], None]


def save_playlist(
    root: Node,
    target_dir: Path,
    progress: ProgressCb | None = None,
) -> None:
    """Serialize the tree to playlist.bin + copy media files into target_dir.

    Files at target_dir/<uuid>.jpg|.mp3 are overwritten when a node's
    current image_path/audio_path points elsewhere. Orphaned <uuid>.jpg|.mp3
    files (no longer referenced by any node) are removed.

    If ``progress`` is given, it is called as ``progress(done, total, label)``
    before each file copy and final cleanup step.
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    flat: list[tuple[Node, int, int, int]] = []  # (node, id, parent_id, order)
    _flatten(root, parent_id=0, counter=[0], out=flat)

    # Count copy operations up front so the caller can show a real progress bar.
    copy_ops: list[tuple[Path, Path]] = []
    referenced_uuids: set[str] = set()
    raw_items: list[dict] = []
    for node, node_id, parent_id, order in flat:
        nb_children = len(node.children) if not node.is_story else 0
        raw_items.append(
            {
                "id": node_id,
                "parent_id": parent_id,
                "order": order,
                "nb_children": nb_children,
                "fav_order": node.fav_order,
                "type": node.type,
                "limit_time": node.limit_time,
                "add_time": node.add_time or int(time.time()),
                "uuid": node.uuid,
                "title": node.title,
            }
        )
        if node.type == TYPE_ROOT:
            continue
        referenced_uuids.add(node.uuid)
        if node.image_path is not None:
            copy_ops.append((node.image_path, target_dir / f"{node.uuid}.jpg"))
        if node.is_story and node.audio_path is not None:
            copy_ops.append((node.audio_path, target_dir / f"{node.uuid}.mp3"))

    total_steps = len(copy_ops) + 1  # +1 for the playlist.bin write

    for i, (src, dst) in enumerate(copy_ops):
        if progress is not None:
            progress(i, total_steps, dst.name)
        _copy_if_different(src, dst)

    if progress is not None:
        progress(len(copy_ops), total_steps, "playlist.bin")

    for existing in target_dir.glob("*"):
        if not existing.is_file():
            continue
        stem, suffix = existing.stem, existing.suffix.lower()
        if suffix in {".jpg", ".mp3"} and stem not in referenced_uuids:
            existing.unlink()

    playlist_bin = target_dir / "playlist.bin"
    with playlist_bin.open("wb") as f:
        for it in raw_items:
            f.write(_write_item(it))

    if progress is not None:
        progress(total_steps, total_steps, "Done")


def _flatten(node: Node, parent_id: int, counter: list[int], out: list) -> None:
    if node.type == TYPE_ROOT:
        node_id = 1
        counter[0] = 1
    else:
        counter[0] += 1
        node_id = counter[0]

    order = node.parent.children.index(node) if node.parent is not None else 0
    out.append((node, node_id, parent_id, order))

    for child in node.children:
        _flatten(child, parent_id=node_id, counter=counter, out=out)


def _copy_if_different(src: Path, dst: Path) -> None:
    src = Path(src)
    dst = Path(dst)
    try:
        if src.resolve() == dst.resolve():
            return
    except FileNotFoundError:
        pass
    shutil.copyfile(src, dst)

"""Main window for the Merlin GUI editor."""

from __future__ import annotations

import tempfile
import uuid as uuid_lib
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, QUrl
from PySide6.QtGui import QAction, QPainter, QPainterPath, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QToolButton,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .converters import (
    ConversionError,
    FFmpegMissing,
    extract_embedded_cover,
    ffmpeg_available,
    is_audio,
    is_image,
    to_merlin_audio,
    to_merlin_image,
)
from .playlist import (
    Node,
    TYPE_ROOT,
    load_playlist,
    new_folder,
    new_story,
    save_playlist,
)
from .styles import detail_bg_color
from .tree import NODE_ROLE, MerlinTree

IMAGE_PREVIEW_SIZE = 220


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Merlin Editor")
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.resize(1100, 720)

        self.root: Node | None = None
        self.source_dir: Path | None = None
        self._tmp = tempfile.TemporaryDirectory(prefix="merlin-gui-")
        self.tmp_dir = Path(self._tmp.name)

        self._player = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)

        self._build_toolbar()
        self._build_ui()
        self._refresh_actions_enabled()
        self._show_empty_state()

    # ----------------------------------------------------------- UI building

    def _build_toolbar(self) -> None:
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        self.open_action = QAction("Open…", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self._on_open)
        toolbar.addAction(self.open_action)

        # SD card dropdown
        self.sd_button = QToolButton()
        self.sd_button.setText("SD card  ▾")
        self.sd_button.setPopupMode(QToolButton.InstantPopup)
        self.sd_menu = QMenu(self.sd_button)
        self.sd_menu.aboutToShow.connect(self._refresh_sd_menu)
        self.sd_button.setMenu(self.sd_menu)
        toolbar.addWidget(self.sd_button)

        toolbar.addSeparator()

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self._on_save)
        toolbar.addAction(self.save_action)

        self.save_as_action = QAction("Save As…", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self._on_save_as)
        toolbar.addAction(self.save_as_action)

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_detail())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 800])

        self.setCentralWidget(splitter)

        status = QStatusBar()
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFrameShape(QFrame.NoFrame)
        sidebar.setMinimumWidth(240)
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.tree = MerlinTree()
        self.tree.setFrameShape(QFrame.NoFrame)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        self.tree.files_dropped.connect(self._on_files_dropped)
        self.tree.node_moved.connect(self._on_node_moved)
        v.addWidget(self.tree, 1)

        bottom = QFrame()
        bottom.setObjectName("sidebarBottomBar")
        bottom.setFrameShape(QFrame.NoFrame)
        bh = QHBoxLayout(bottom)
        bh.setContentsMargins(8, 4, 8, 4)
        bh.setSpacing(2)

        self.add_story_btn = QPushButton("＋")
        self.add_story_btn.setToolTip("Add story")
        self.add_story_btn.clicked.connect(self._on_add_story)

        self.add_folder_btn = QPushButton("⊕")
        self.add_folder_btn.setToolTip("Add folder")
        self.add_folder_btn.clicked.connect(self._on_add_folder)

        self.delete_btn = QPushButton("−")
        self.delete_btn.setToolTip("Delete selection")
        self.delete_btn.clicked.connect(self._on_delete)

        self.up_btn = QPushButton("↑")
        self.up_btn.setToolTip("Move up")
        self.up_btn.clicked.connect(lambda: self._move_selected(-1))

        self.down_btn = QPushButton("↓")
        self.down_btn.setToolTip("Move down")
        self.down_btn.clicked.connect(lambda: self._move_selected(+1))

        bh.addWidget(self.add_story_btn)
        bh.addWidget(self.add_folder_btn)
        bh.addWidget(self.delete_btn)
        bh.addStretch(1)
        bh.addWidget(self.up_btn)
        bh.addWidget(self.down_btn)

        v.addWidget(bottom)
        return sidebar

    def _build_detail(self) -> QWidget:
        self._detail_bg = detail_bg_color()
        self.detail_stack = QStackedWidget()
        self.detail_stack.setObjectName("detail")

        # Empty state
        empty = QFrame()
        empty.setObjectName("detailEmpty")
        empty.setFrameShape(QFrame.NoFrame)
        empty.setStyleSheet(f"QFrame#detailEmpty {{ background: {self._detail_bg}; }}")
        ev = QVBoxLayout(empty)
        ev.addStretch(1)
        title = QLabel("No playlist open")
        title.setObjectName("emptyState")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Open a playlist.bin from your Merlin SD card to begin.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #8E8E93;")
        open_btn = QPushButton("Open…")
        open_btn.setObjectName("primary")
        open_btn.setFixedWidth(140)
        open_btn.clicked.connect(self._on_open)
        ev.addWidget(title)
        ev.addSpacing(6)
        ev.addWidget(subtitle)
        ev.addSpacing(16)
        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(open_btn)
        wrap.addStretch(1)
        ev.addLayout(wrap)
        ev.addStretch(2)
        self.detail_stack.addWidget(empty)

        # Editor
        editor = QFrame()
        editor.setObjectName("detailEditor")
        editor.setFrameShape(QFrame.NoFrame)
        editor.setStyleSheet(f"QFrame#detailEditor {{ background: {self._detail_bg}; }}")
        e = QVBoxLayout(editor)
        e.setContentsMargins(40, 32, 40, 24)
        e.setSpacing(18)

        # Image preview
        image_wrap = QHBoxLayout()
        image_wrap.addStretch(1)
        self.image_frame = QLabel()
        self.image_frame.setObjectName("imageFrame")
        self.image_frame.setFixedSize(IMAGE_PREVIEW_SIZE, IMAGE_PREVIEW_SIZE)
        self.image_frame.setAlignment(Qt.AlignCenter)
        self.image_frame.setText("No image")
        self.image_frame.setStyleSheet(self.image_frame.styleSheet() + " color:#8E8E93;")
        image_wrap.addWidget(self.image_frame)
        image_wrap.addStretch(1)
        e.addLayout(image_wrap)

        replace_img_wrap = QHBoxLayout()
        replace_img_wrap.addStretch(1)
        self.replace_image_btn = QPushButton("Replace image…")
        self.replace_image_btn.setObjectName("linkButton")
        self.replace_image_btn.clicked.connect(self._on_replace_image)
        replace_img_wrap.addWidget(self.replace_image_btn)
        replace_img_wrap.addStretch(1)
        e.addLayout(replace_img_wrap)

        # Title section
        title_section = self._section_header("TITLE")
        e.addWidget(title_section)
        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("titleEdit")
        self.title_edit.editingFinished.connect(self._on_title_edited)
        e.addWidget(self.title_edit)

        # Audio section
        self.audio_section_header = self._section_header("AUDIO")
        e.addWidget(self.audio_section_header)

        audio_row = QWidget()
        audio_row.setObjectName("audioRow")
        ar = QHBoxLayout(audio_row)
        ar.setContentsMargins(12, 10, 14, 10)
        ar.setSpacing(12)

        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("playButton")
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.setCheckable(True)
        self.play_btn.clicked.connect(self._on_play_toggle)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setSingleStep(1000)
        self.position_slider.setPageStep(5000)
        self.position_slider.sliderMoved.connect(self._on_slider_moved)
        self.position_slider.sliderPressed.connect(self._on_slider_pressed)
        self.position_slider.sliderReleased.connect(self._on_slider_released)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setFixedWidth(90)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        ar.addWidget(self.play_btn)
        ar.addWidget(self.position_slider, 1)
        ar.addWidget(self.time_label)
        e.addWidget(audio_row)
        self.audio_row = audio_row

        self.audio_caption = QLabel("No audio")
        self.audio_caption.setStyleSheet("color:#8E8E93;")
        self.audio_caption.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        e.addWidget(self.audio_caption)

        self._slider_dragging = False
        self._player.positionChanged.connect(self._on_player_position_changed)
        self._player.durationChanged.connect(self._on_player_duration_changed)
        self._player.playbackStateChanged.connect(self._on_player_state_changed)

        replace_audio_wrap = QHBoxLayout()
        self.replace_audio_btn = QPushButton("Replace audio…")
        self.replace_audio_btn.setObjectName("linkButton")
        self.replace_audio_btn.clicked.connect(self._on_replace_audio)
        replace_audio_wrap.addWidget(self.replace_audio_btn)
        replace_audio_wrap.addStretch(1)
        e.addLayout(replace_audio_wrap)

        e.addStretch(1)
        self.detail_stack.addWidget(editor)

        return self.detail_stack

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionHeader")
        return lbl

    def _show_empty_state(self) -> None:
        self.detail_stack.setCurrentIndex(0)

    def _show_editor(self) -> None:
        self.detail_stack.setCurrentIndex(1)

    # ----------------------------------------------------------- File ops

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open playlist.bin", "", "Merlin playlist (playlist.bin)"
        )
        if path:
            self._open_playlist(Path(path))

    def _on_save(self) -> None:
        if self.source_dir is None:
            self._on_save_as()
            return
        self._save_to(self.source_dir)

    def _on_save_as(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Save to directory (SD card root)")
        if not path:
            return
        self._save_to(Path(path))

    def _save_to(self, target: Path) -> None:
        if self.root is None:
            return

        progress = QProgressDialog("Saving…", None, 0, 1, self)
        progress.setWindowTitle("Save")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(200)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setCancelButton(None)  # save shouldn't be cancellable mid-write
        progress.setValue(0)

        def report(done: int, total: int, label: str) -> None:
            progress.setMaximum(total)
            progress.setValue(done)
            progress.setLabelText(f"Saving {label}  ({done}/{total})")
            QApplication.processEvents()

        try:
            save_playlist(self.root, target, progress=report)
        except Exception as e:
            progress.cancel()
            QMessageBox.critical(self, "Save failed", str(e))
            return
        finally:
            progress.close()

        self.source_dir = target
        self.setWindowTitle(f"Merlin Editor — {target.name}")
        self.statusBar().showMessage(f"Saved to {target}", 5000)

    # ----------------------------------------------------------- Tree

    def _refresh_tree(self) -> None:
        self.tree.clear()
        if self.root is None:
            return
        for child in self.root.children:
            top = self._make_item(child)
            self.tree.addTopLevelItem(top)
            self._populate_children(top, child)
            top.setExpanded(True)

    def _populate_children(self, parent_item: QTreeWidgetItem, parent_node: Node) -> None:
        for child in parent_node.children:
            item = self._make_item(child)
            parent_item.addChild(item)
            self._populate_children(item, child)

    def _make_item(self, node: Node) -> QTreeWidgetItem:
        prefix = "📁  " if node.is_folder else "🎵  "
        item = QTreeWidgetItem([f"{prefix}{node.title or '(untitled)'}"])
        item.setData(0, NODE_ROLE, node)
        return item

    def _selected_node(self) -> Node | None:
        item = self.tree.currentItem()
        return item.data(0, NODE_ROLE) if item else None

    def _on_selection_changed(self, current, _previous):
        node = current.data(0, NODE_ROLE) if current else None
        self._update_editor(node)
        self._refresh_actions_enabled()

    def _update_editor(self, node: Node | None) -> None:
        self._player.stop()
        if node is None or node.type == TYPE_ROOT:
            self._show_empty_state()
            return

        self._show_editor()
        self.title_edit.setText(node.title)

        # Image
        if node.image_path and node.image_path.exists():
            pix = QPixmap(str(node.image_path))
            if not pix.isNull():
                self.image_frame.setPixmap(_rounded_pixmap(pix, IMAGE_PREVIEW_SIZE, radius=14))
            else:
                self.image_frame.clear()
                self.image_frame.setText("Image error")
        else:
            self.image_frame.clear()
            self.image_frame.setText("No image")

        # Audio section visibility
        is_story = node.is_story
        self.audio_section_header.setVisible(is_story)
        self.audio_row.setVisible(is_story)
        self.audio_caption.setVisible(is_story)
        self.replace_audio_btn.setVisible(is_story)

        if is_story:
            has_audio = node.audio_path is not None and node.audio_path.exists()
            self.play_btn.setEnabled(has_audio)
            self.position_slider.setEnabled(has_audio)
            if has_audio:
                size_kb = node.audio_path.stat().st_size // 1024
                size_str = (
                    f"{size_kb / 1024:.1f} MB" if size_kb >= 1024 else f"{size_kb} KB"
                )
                self.audio_caption.setText(f"MP3 stereo · {size_str}")
            else:
                self.audio_caption.setText("No audio")
                self.position_slider.setRange(0, 0)
                self.time_label.setText("0:00 / 0:00")

    def _on_title_edited(self) -> None:
        node = self._selected_node()
        if node is None or node.type == TYPE_ROOT:
            return
        new_title = self.title_edit.text().strip()
        if not new_title or new_title == node.title:
            return
        node.title = new_title
        item = self.tree.currentItem()
        prefix = "📁  " if node.is_folder else "🎵  "
        item.setText(0, f"{prefix}{new_title}")

    def _on_play_toggle(self) -> None:
        node = self._selected_node()
        if node is None or not node.is_story or not node.audio_path or not node.audio_path.exists():
            self.play_btn.setChecked(False)
            return
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
            return
        current_src = self._player.source().toLocalFile() if self._player.source().isValid() else ""
        if current_src != str(node.audio_path):
            self._player.setSource(QUrl.fromLocalFile(str(node.audio_path)))
        self._player.play()

    def _on_slider_pressed(self) -> None:
        self._slider_dragging = True

    def _on_slider_released(self) -> None:
        self._slider_dragging = False
        self._player.setPosition(self.position_slider.value())

    def _on_slider_moved(self, value: int) -> None:
        self.time_label.setText(f"{_fmt_ms(value)} / {_fmt_ms(self._player.duration())}")

    def _on_player_position_changed(self, ms: int) -> None:
        if not self._slider_dragging:
            self.position_slider.setValue(ms)
            self.time_label.setText(f"{_fmt_ms(ms)} / {_fmt_ms(self._player.duration())}")

    def _on_player_duration_changed(self, ms: int) -> None:
        self.position_slider.setRange(0, ms)
        self.time_label.setText(f"{_fmt_ms(self._player.position())} / {_fmt_ms(ms)}")

    def _on_player_state_changed(self, state) -> None:
        playing = state == QMediaPlayer.PlayingState
        self.play_btn.setChecked(playing)
        self.play_btn.setText("⏸" if playing else "▶")

    # ----------------------------------------------------------- Edit ops

    def _selected_folder_for_insert(self) -> Node | None:
        node = self._selected_node()
        if node is None:
            return self.root
        if node.is_folder:
            return node
        return node.parent

    def _on_add_folder(self) -> None:
        if self.root is None:
            self._notice("Open a playlist first.")
            return
        parent = self._selected_folder_for_insert() or self.root
        title, ok = QInputDialog.getText(self, "New folder", "Folder name:")
        if not ok or not title.strip():
            return
        node = new_folder(title.strip())
        node.parent = parent
        parent.children.append(node)
        self._refresh_tree()
        self._select_node(node)

    def _on_add_story(self) -> None:
        if self.root is None:
            self._notice("Open a playlist first.")
            return
        if not ffmpeg_available():
            QMessageBox.critical(
                self,
                "ffmpeg required",
                "ffmpeg is needed to convert audio.\nInstall with: brew install ffmpeg",
            )
            return

        sources, _ = QFileDialog.getOpenFileNames(
            self,
            "Pick audio files",
            "",
            "Audio (*.mp3 *.m4a *.aac *.wav *.flac *.ogg *.opus *.aiff *.aif *.wma)",
        )
        if not sources:
            return

        parent = self._selected_folder_for_insert() or self.root
        paths = [Path(s) for s in sources]

        # Single file → let user rename. Multiple → use the filename as title.
        if len(paths) == 1:
            title, ok = QInputDialog.getText(
                self, "Story title", "Title:", text=paths[0].stem
            )
            if not ok or not title.strip():
                return
            tasks = [(paths[0], None, title.strip())]
        else:
            tasks = [(p, None, p.stem) for p in paths]

        created = self._batch_convert_and_add(parent, tasks)
        if created:
            self._refresh_tree()
            self._select_node(created[-1])
            msg = f"Added “{created[0].title}”" if len(created) == 1 else f"Added {len(created)} stories"
            self.statusBar().showMessage(msg, 5000)

    def _on_replace_audio(self) -> None:
        node = self._selected_node()
        if node is None or not node.is_story:
            return
        if not ffmpeg_available():
            QMessageBox.critical(self, "ffmpeg required", "Install with: brew install ffmpeg")
            return
        src, _ = QFileDialog.getOpenFileName(self, "Pick audio", "", "Audio (*.*)")
        if not src:
            return
        dst = self.tmp_dir / f"{node.uuid}.mp3"
        try:
            to_merlin_audio(Path(src), dst)
        except (FFmpegMissing, ConversionError) as e:
            QMessageBox.critical(self, "Conversion failed", str(e))
            return
        node.audio_path = dst
        self._update_editor(node)

    def _on_replace_image(self) -> None:
        node = self._selected_node()
        if node is None or node.type == TYPE_ROOT:
            return
        src, _ = QFileDialog.getOpenFileName(self, "Pick image", "", "Images (*.*)")
        if not src:
            return
        dst = self.tmp_dir / f"{node.uuid}.jpg"
        try:
            to_merlin_image(Path(src), dst)
        except Exception as e:
            QMessageBox.critical(self, "Conversion failed", str(e))
            return
        node.image_path = dst
        self._update_editor(node)

    def _on_delete(self) -> None:
        node = self._selected_node()
        if node is None or node.type == TYPE_ROOT or node.parent is None:
            return
        suffix = " (and its content)" if node.children else ""
        if QMessageBox.question(self, "Delete", f"Delete “{node.title}”?{suffix}") != QMessageBox.Yes:
            return
        node.parent.children.remove(node)
        self._refresh_tree()
        self._show_empty_state()
        self._refresh_actions_enabled()

    def _move_selected(self, delta: int) -> None:
        node = self._selected_node()
        if node is None or node.parent is None:
            return
        siblings = node.parent.children
        idx = siblings.index(node)
        new_idx = idx + delta
        if not (0 <= new_idx < len(siblings)):
            return
        siblings[idx], siblings[new_idx] = siblings[new_idx], siblings[idx]
        self._refresh_tree()
        self._select_node(node)

    def _on_node_moved(self, node: Node) -> None:
        self._refresh_tree()
        self._select_node(node)

    def _on_files_dropped(self, paths: list, target_item) -> None:
        target_node: Node | None = (
            target_item.data(0, NODE_ROLE) if target_item is not None else self.root
        )
        if target_node is None:
            return

        audios = [p for p in paths if is_audio(p)]
        images = [p for p in paths if is_image(p)]
        other = [p for p in paths if not is_audio(p) and not is_image(p)]
        if other:
            self.statusBar().showMessage(
                f"Ignored {len(other)} unsupported file(s)", 4000
            )

        # Single image on a story → replace its image
        if (
            not audios
            and len(images) == 1
            and target_node.is_story
        ):
            self._replace_node_image(target_node, images[0])
            return

        # Audio drops → create stories under the right folder
        folder = target_node if target_node.is_folder else target_node.parent
        if folder is None:
            return

        if not ffmpeg_available() and audios:
            QMessageBox.critical(
                self,
                "ffmpeg required",
                "ffmpeg is needed to convert audio.\nInstall with: brew install ffmpeg",
            )
            return

        # Pair audios with images by basename (same stem)
        images_by_stem = {p.stem.lower(): p for p in images}
        tasks = [
            (audio, images_by_stem.get(audio.stem.lower()), audio.stem)
            for audio in audios
        ]
        created = self._batch_convert_and_add(folder, tasks)

        # Orphan images (no paired audio) on a folder: ignored silently here.
        if created:
            self._refresh_tree()
            self._select_node(created[-1])
            msg = (
                f"Added “{created[0].title}”"
                if len(created) == 1
                else f"Added {len(created)} stories"
            )
            self.statusBar().showMessage(msg, 5000)

    def _replace_node_image(self, node: Node, src: Path) -> None:
        dst = self.tmp_dir / f"{node.uuid}.jpg"
        try:
            to_merlin_image(src, dst)
        except Exception as e:
            QMessageBox.critical(self, "Conversion failed", str(e))
            return
        node.image_path = dst
        self._update_editor(node)
        self.statusBar().showMessage(f"Replaced image for “{node.title}”", 4000)

    def _batch_convert_and_add(
        self,
        folder: Node,
        tasks: list[tuple[Path, Path | None, str]],
    ) -> list[Node]:
        """Convert+add a list of (audio, image_or_None, title) under folder, with
        a modal progress dialog and Cancel support."""
        if not tasks:
            return []

        progress = QProgressDialog(
            "Preparing…", "Cancel", 0, len(tasks), self
        )
        progress.setWindowTitle("Converting")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(200)  # don't flash for fast single conversions
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.setValue(0)

        created: list[Node] = []
        for i, (audio_src, image_src, title) in enumerate(tasks):
            if progress.wasCanceled():
                break
            progress.setLabelText(f"Converting {audio_src.name} ({i + 1}/{len(tasks)})…")
            progress.setValue(i)
            QApplication.processEvents()

            story = self._convert_and_add_story(folder, audio_src, image_src, title)
            if story:
                created.append(story)

        progress.setValue(len(tasks))
        return created

    def _convert_and_add_story(
        self,
        folder: Node,
        audio_src: Path,
        image_src: Path | None,
        suggested_title: str,
    ) -> Node | None:
        new_uuid = str(uuid_lib.uuid4())
        audio_dst = self.tmp_dir / f"{new_uuid}.mp3"
        image_dst = self.tmp_dir / f"{new_uuid}.jpg"
        self.statusBar().showMessage(f"Converting {audio_src.name}…")
        try:
            to_merlin_audio(audio_src, audio_dst)
        except (FFmpegMissing, ConversionError) as e:
            QMessageBox.critical(self, "Conversion failed", str(e))
            return None

        final_image: Path | None = None
        if image_src is not None:
            try:
                to_merlin_image(image_src, image_dst)
                final_image = image_dst
            except Exception as e:
                QMessageBox.critical(self, "Image conversion failed", str(e))
                return None
        else:
            # Try to pull the cover art embedded in the audio file.
            cover_raw = self.tmp_dir / f"{new_uuid}.cover.jpg"
            if extract_embedded_cover(audio_src, cover_raw):
                try:
                    to_merlin_image(cover_raw, image_dst)
                    final_image = image_dst
                except Exception:
                    final_image = None
                cover_raw.unlink(missing_ok=True)

        story = new_story(suggested_title, audio_path=audio_dst, image_path=final_image)
        story.uuid = new_uuid
        story.parent = folder
        folder.children.append(story)
        return story

    def _select_node(self, target: Node) -> None:
        def walk(item: QTreeWidgetItem):
            if item.data(0, NODE_ROLE) is target:
                self.tree.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                if walk(item.child(i)):
                    item.setExpanded(True)
                    return True
            return False

        for i in range(self.tree.topLevelItemCount()):
            if walk(self.tree.topLevelItem(i)):
                return

    # ----------------------------------------------------------- Helpers

    def _refresh_sd_menu(self) -> None:
        self.sd_menu.clear()
        found = _scan_for_playlists()
        if not found:
            act = QAction("No SD card with a playlist found", self.sd_menu)
            act.setEnabled(False)
            self.sd_menu.addAction(act)
            return
        for playlist_path in found:
            label = f"{playlist_path.parent.name}  —  {playlist_path.parent}"
            act = QAction(label, self.sd_menu)
            act.triggered.connect(lambda checked=False, p=playlist_path: self._open_playlist(p))
            self.sd_menu.addAction(act)

    def _open_playlist(self, path: Path) -> None:
        try:
            self.root = load_playlist(path)
        except Exception as e:
            QMessageBox.critical(self, "Open failed", str(e))
            return
        self.source_dir = path.parent
        self.setWindowTitle(f"Merlin Editor — {self.source_dir.name}")
        self.tree.set_root(self.root)
        self._refresh_tree()
        self._show_editor()
        self._refresh_actions_enabled()
        self.statusBar().showMessage(f"Loaded {path}", 5000)

    def _refresh_actions_enabled(self) -> None:
        has_playlist = self.root is not None
        self.save_action.setEnabled(has_playlist)
        self.save_as_action.setEnabled(has_playlist)
        self.add_story_btn.setEnabled(has_playlist)
        self.add_folder_btn.setEnabled(has_playlist)
        node = self._selected_node()
        can_edit = node is not None and node.type != TYPE_ROOT and node.parent is not None
        self.delete_btn.setEnabled(can_edit)
        self.up_btn.setEnabled(can_edit)
        self.down_btn.setEnabled(can_edit)

    def _notice(self, msg: str) -> None:
        QMessageBox.information(self, "Merlin Editor", msg)

    def closeEvent(self, event):
        self._player.stop()
        self._tmp.cleanup()
        super().closeEvent(event)


def _scan_for_playlists() -> list[Path]:
    """Find playlist.bin candidates on mounted volumes."""
    candidates: list[Path] = []
    mount_roots = [Path("/Volumes")]  # macOS
    if Path("/media").exists():
        mount_roots.append(Path("/media"))
    if Path("/run/media").exists():
        mount_roots.append(Path("/run/media"))

    for root in mount_roots:
        if not root.is_dir():
            continue
        try:
            entries = list(root.iterdir())
        except PermissionError:
            continue
        for entry in entries:
            if not entry.is_dir():
                continue
            # macOS internal volumes — skip "Macintosh HD" and the system /
            if entry.name in {"Macintosh HD", "Preboot", "Recovery", "VM", "Update"}:
                continue
            # Try the volume root, then one subfolder deep
            for path in (entry / "playlist.bin", *(entry.glob("*/playlist.bin"))):
                if path.is_file():
                    candidates.append(path)
    return sorted(set(candidates))


def _fmt_ms(ms: int) -> str:
    if ms <= 0:
        return "0:00"
    seconds = ms // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def _rounded_pixmap(src: QPixmap, target_size: int, radius: int) -> QPixmap:
    side = target_size - 4
    scaled = src.scaled(side, side, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x = (scaled.width() - side) // 2
    y = (scaled.height() - side) // 2
    cropped = scaled.copy(x, y, side, side)

    out = QPixmap(side, side)
    out.fill(Qt.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, side, side), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return out

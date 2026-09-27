#!/usr/bin/env python3
"""Create a KDE Plasma light/dark dynamic wallpaper package from two images."""

import json
import re
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

WALLPAPERS_DIR = Path.home() / ".local/share/wallpapers"
IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.avif *.jxl)"
PREVIEW_SIZE = (240, 135)


class ImagePicker(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.path: Path | None = None
        self.title = title

        self.setAcceptDrops(True)

        self.preview = QLabel("Drop an image here")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(*PREVIEW_SIZE)
        self.set_highlighted(False)

        self.info = QLabel()
        self.info.setAlignment(Qt.AlignCenter)

        button = QPushButton(f"Choose {title.lower()} image…")
        button.clicked.connect(self.choose)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>{title}</b>"), alignment=Qt.AlignCenter)
        layout.addWidget(self.preview)
        layout.addWidget(self.info)
        layout.addWidget(button)

    def choose(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, f"Choose {self.title.lower()} image", str(Path.home()), IMAGE_FILTER
        )
        if filename:
            self.load(filename)

    def load(self, filename: str):
        size = QImageReader(filename).size()
        if not size.isValid():
            QMessageBox.warning(self, "Invalid image", f"Could not read {filename}.")
            return
        self.path = Path(filename)
        pixmap = QPixmap(filename).scaled(
            *PREVIEW_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview.setPixmap(pixmap)
        self.info.setText(f"{self.path.name}\n{size.width()}×{size.height()}")

    def set_highlighted(self, highlighted: bool):
        border = "2px solid palette(highlight)" if highlighted else "1px dashed palette(mid)"
        self.preview.setStyleSheet(f"QLabel {{ border: {border}; }}")

    @staticmethod
    def dropped_file(event) -> str | None:
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile():
            return urls[0].toLocalFile()
        return None

    def dragEnterEvent(self, event):
        if self.dropped_file(event):
            event.acceptProposedAction()
            self.set_highlighted(True)

    def dragLeaveEvent(self, event):
        self.set_highlighted(False)

    def dropEvent(self, event):
        self.set_highlighted(False)
        if filename := self.dropped_file(event):
            event.acceptProposedAction()
            self.load(filename)


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.") or "wallpaper"


def copy_image(src: Path, dest_dir: Path):
    size = QImageReader(str(src)).size()
    dest_dir.mkdir(parents=True)
    shutil.copy2(src, dest_dir / f"{size.width()}x{size.height()}{src.suffix.lower()}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Wallpaper Creator")

        self.name = QLineEdit()
        self.name.setPlaceholderText("My Wallpaper")
        self.author = QLineEdit()
        self.author.setPlaceholderText("Optional")

        form = QFormLayout()
        form.addRow("Name:", self.name)
        form.addRow("Author:", self.author)

        self.light = ImagePicker("Light")
        self.dark = ImagePicker("Dark")
        pickers = QHBoxLayout()
        pickers.addWidget(self.light)
        pickers.addWidget(self.dark)

        create = QPushButton("Create wallpaper")
        create.setDefault(True)
        create.clicked.connect(self.create)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(pickers)
        layout.addWidget(create)

    def create(self):
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a wallpaper name.")
            return
        if not (self.light.path and self.dark.path):
            QMessageBox.warning(self, "Missing image", "Please choose both images.")
            return

        plugin_id = slugify(name)
        target = WALLPAPERS_DIR / plugin_id
        if target.exists():
            answer = QMessageBox.question(
                self, "Wallpaper exists", f"{target} already exists. Replace it?"
            )
            if answer != QMessageBox.Yes:
                return
            shutil.rmtree(target)

        metadata = {"KPlugin": {"Id": plugin_id, "Name": name}}
        if author := self.author.text().strip():
            metadata["KPlugin"]["Authors"] = [{"Name": author}]

        try:
            copy_image(self.light.path, target / "contents/images")
            copy_image(self.dark.path, target / "contents/images_dark")
            (target / "metadata.json").write_text(json.dumps(metadata, indent=4) + "\n")
        except OSError as e:
            shutil.rmtree(target, ignore_errors=True)
            QMessageBox.critical(self, "Error", f"Failed to create wallpaper:\n{e}")
            return

        QMessageBox.information(
            self,
            "Done",
            f"Created “{name}” in {target}.\n\n"
            "It should now appear in the wallpaper settings.",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

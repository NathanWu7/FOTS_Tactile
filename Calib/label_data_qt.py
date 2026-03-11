"""
球心/半径标注 GUI（PyQt5）。左键圆心、再左键圆周一点得半径。输出 CSV：img_names, center_x, center_y, radius。
"""
import argparse
import csv
import math
import os
import sys

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QSplitter, QStatusBar, QMessageBox,
)

CALIB_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(CALIB_DIR, "data")
base_path = DATA_DIR


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #222;")
        self._pixmap = self._center = self._radius = self._circum = None

    def set_image(self, qimg):
        if qimg is None:
            self._pixmap = None
            self.clear()
            return
        self._pixmap = QPixmap.fromImage(qimg)
        self._center = self._radius = self._circum = None
        self._draw()

    def set_center_radius(self, center, radius):
        self._center, self._radius, self._circum = center, radius, None
        self._draw()

    def clear_label(self):
        self._center = self._radius = self._circum = None
        self._draw()

    def get_center_radius(self):
        return self._center, self._radius

    def _draw(self):
        if self._pixmap is None:
            return
        pix = self._pixmap.copy()
        painter = QPainter(pix)
        if self._center is not None:
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.drawEllipse(QPoint(*self._center), 4, 4)
            if self._radius is not None and self._radius > 0:
                painter.setPen(QPen(QColor(0, 200, 255), 1))
                painter.drawEllipse(QPoint(*self._center), self._radius, self._radius)
        painter.end()
        self.setPixmap(pix.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._draw()

    def mousePressEvent(self, event):
        if self._pixmap is None or event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        px, py = event.pos().x(), event.pos().y()
        w, h = self.width(), self.height()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        scale = min(w / pw, h / ph)
        x = int(round((px - (w - pw * scale) / 2) / scale))
        y = int(round((py - (h - ph * scale) / 2) / scale))
        if self._center is None:
            self._center, self._radius, self._circum = (x, y), None, None
        else:
            dx, dy = x - self._center[0], y - self._center[1]
            self._radius = int(round(math.sqrt(dx * dx + dy * dy)))
            self._circum = (x, y)
        self._draw()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, img_folder=None, csv_path=None):
        super().__init__()
        self.setWindowTitle("球心/半径标注 (PyQt5)")
        self.img_folder = img_folder or os.path.join(DATA_DIR, "imgs")
        self.csv_path = csv_path or os.path.join(DATA_DIR, "csv", "annotate.csv")
        self.labels = {}
        self._load_csv()
        self._image_files = []
        self._current_index = -1
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        splitter = QSplitter(Qt.Horizontal)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_list_row)
        splitter.addWidget(self.list_widget)
        right = QWidget()
        rlayout = QVBoxLayout(right)
        self.image_label = ImageLabel()
        rlayout.addWidget(self.image_label)
        btn_layout = QHBoxLayout()
        for lbl, slot in [("上一张", self._prev), ("下一张", self._next), ("清除当前", self._clear_current)]:
            b = QPushButton(lbl)
            b.clicked.connect(slot)
            btn_layout.addWidget(b)
        rlayout.addLayout(btn_layout)
        splitter.addWidget(right)
        splitter.setSizes([180, 600])
        layout.addWidget(splitter)
        toolbar = self.addToolBar("File")
        toolbar.addAction("打开文件夹").triggered.connect(self._open_folder)
        toolbar.addAction("保存 CSV").triggered.connect(self._save_csv)
        self.statusBar().showMessage("请通过「打开文件夹」选择图像目录")
        if os.path.isdir(self.img_folder):
            self._set_folder(self.img_folder)

    def _load_csv(self):
        if not os.path.isfile(self.csv_path):
            return
        self.labels = {}
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = (row.get("img_names") or "").strip()
                if not name:
                    continue
                name = os.path.basename(name)
                try:
                    self.labels[name] = (int(row["center_x"]), int(row["center_y"]), int(row["radius"]))
                except (KeyError, ValueError):
                    pass

    def _set_folder(self, folder):
        import glob
        self.img_folder = folder
        self._image_files = []
        for e in ("*.png", "*.jpg", "*.jpeg", "*.bmp"):
            self._image_files.extend(glob.glob(os.path.join(folder, e)))
        self._image_files = sorted(self._image_files)
        self.list_widget.clear()
        for p in self._image_files:
            self.list_widget.addItem(QListWidgetItem(os.path.basename(p)))
        self.statusBar().showMessage(f"已加载 {len(self._image_files)} 张: {folder}")
        if self._image_files:
            self._current_index = 0
            self._show_index(0)

    def _open_folder(self):
        d = QFileDialog.getExistingDirectory(self, "选择图像目录", self.img_folder)
        if d:
            self._set_folder(d)
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

    def _on_list_row(self, row):
        if row >= 0 and row != self._current_index:
            self._show_index(row)

    def _show_index(self, index):
        if index < 0 or index >= len(self._image_files):
            return
        self._current_index = index
        path = self._image_files[index]
        fname = os.path.basename(path)
        self.list_widget.setCurrentRow(index)
        try:
            import cv2
            img = cv2.imread(path)
            if img is None:
                self.image_label.set_image(None)
                self.statusBar().showMessage(f"无法读取: {path}")
                return
            h, w, c = img.shape
            qimg = QImage(img.data, w, h, w * 3, QImage.Format_BGR888) if c == 3 else QImage(img.data, w, h, w, QImage.Format_Grayscale8)
            self.image_label.set_image(qimg)
            if fname in self.labels:
                cx, cy, r = self.labels[fname]
                self.image_label.set_center_radius((cx, cy), r)
            else:
                self.image_label.clear_label()
            self.statusBar().showMessage(f"{index + 1} / {len(self._image_files)}: {fname}")
        except Exception as e:
            self.image_label.set_image(None)
            self.statusBar().showMessage(str(e))

    def _prev(self):
        if self._image_files and self._current_index > 0:
            self._save_current_label()
            self._show_index(self._current_index - 1)

    def _next(self):
        if self._image_files and self._current_index < len(self._image_files) - 1:
            self._save_current_label()
            self._show_index(self._current_index + 1)

    def _save_current_label(self):
        if not self._image_files or self._current_index < 0:
            return
        fname = os.path.basename(self._image_files[self._current_index])
        center, radius = self.image_label.get_center_radius()
        if center is not None and radius is not None and radius > 0:
            self.labels[fname] = (center[0], center[1], radius)

    def _clear_current(self):
        if not self._image_files or self._current_index < 0:
            return
        self.labels.pop(os.path.basename(self._image_files[self._current_index]), None)
        self.image_label.clear_label()

    def _save_csv(self):
        self._save_current_label()
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["img_names", "center_x", "center_y", "radius"])
            for fname in sorted(self.labels.keys()):
                cx, cy, r = self.labels[fname]
                w.writerow([fname, cx, cy, r])
        self.statusBar().showMessage(f"已保存: {self.csv_path}")
        QMessageBox.information(self, "保存", f"已保存到 {self.csv_path}")


def main():
    ap = argparse.ArgumentParser(description="PyQt5 球心/半径标注.")
    ap.add_argument("--folder", type=str, default="", help="图像目录")
    ap.add_argument("--csv", type=str, default="", help="输出 CSV 路径")
    args = ap.parse_args()
    folder = args.folder or os.path.join(DATA_DIR, "imgs")
    csv_path = args.csv or os.path.join(DATA_DIR, "csv", "annotate.csv")
    app = QApplication(sys.argv)
    win = MainWindow(img_folder=folder, csv_path=csv_path)
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

from __future__ import annotations

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap, QImage
from ryven.gui_env import *


class ImageNodeGuiBase(NodeMainWidget, QWidget):
    """Standardized GUI base that shows a live image preview in a QLabel.

    Subclasses may add controls (sliders, buttons) by appending to the layout.
    """

    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(160)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.preview, 1)
        self.setLayout(v)

        try:
            cached = getattr(self.node, 'get_last_processed', lambda: None)()
            if cached is not None:
                w, h = cached.size
                rgba = cached.convert('RGBA').tobytes('raw', 'RGBA')
                qimg = QImage(rgba, w, h, 4 * w, QImage.Format_RGBA8888)
                self.show_qimage(qimg)
            else:
                self.node.update()
        except Exception:
            try:
                self.node.update()
            except Exception:
                pass

    def show_qimage(self, qimage):
        if qimage is None:
            self.preview.setPixmap(QPixmap())
            return
        pix = QPixmap.fromImage(qimage)
        if pix.isNull():
            self.preview.setPixmap(QPixmap())
            return
        scaled = pix.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1)
        self.preview.setPixmap(scaled)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        p = self.preview.pixmap()
        if p is not None and not p.isNull():
            self.preview.setPixmap(p.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1))



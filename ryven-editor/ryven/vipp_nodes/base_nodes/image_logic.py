from __future__ import annotations

from typing import Optional

from ryven.node_env import *


class ImageNodeBase(Node):
    """Standardized image-processing Node with preview signal and IO contracts.

    Subclasses should override `process(self, img)` and optionally add setters
    that call `self.update()`.
    """

    tags = ['image', 'generated']
    init_inputs = [NodeInputType('image')]
    init_outputs = [NodeOutputType('image')]

    def __init__(self, params):
        super().__init__(params)
        self._last = None
        self._gui_connected = False
        if self.session.gui:
            from qtpy.QtCore import QObject, Signal

            class Signals(QObject):
                new_qimage = Signal(object)

            self.SIGNALS = Signals()

    def input_image(self) -> Optional['Image.Image']:
        payload = None if self.input(0) is None else self.input(0).payload
        obj = payload.payload if hasattr(payload, 'payload') else payload
        if obj is None:
            return None
        from PIL import Image
        if hasattr(obj, 'size') and hasattr(obj, 'mode'):
            return obj.convert('RGBA')
        if isinstance(obj, str):
            try:
                return Image.open(obj).convert('RGBA')
            except Exception:
                return None
        return None

    def emit_preview(self, img):
        if not self.session.gui:
            return
        try:
            from qtpy.QtGui import QImage
            w, h = img.size
            rgba = img.tobytes('raw', 'RGBA')
            qimg = QImage(rgba, w, h, 4 * w, QImage.Format_RGBA8888)
            self.SIGNALS.new_qimage.emit(qimg.copy())
        except Exception:
            try:
                self.SIGNALS.new_qimage.emit(None)
            except Exception:
                pass

    def set_image_output(self, img):
        self.set_output_val(0, Data(img) if img is not None else None)

    def view_place_event(self):
        if self.session.gui:
            try:
                self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
                self._gui_connected = True
            except Exception:
                self._gui_connected = False
            self.update()

    def _ensure_gui_connection(self):
        if self.session.gui and not self._gui_connected and hasattr(self, 'gui') and self.gui:
            try:
                self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
                self._gui_connected = True
            except Exception:
                pass

    def process(self, img):
        return img

    def update_event(self, inp=-1):
        img = self.input_image()
        if img is None:
            self._last = None
            self.set_image_output(None)
            if self.session.gui:
                try:
                    self.SIGNALS.new_qimage.emit(None)
                except Exception:
                    pass
            return
        try:
            out = self.process(img)
        except Exception:
            out = None
        self._last = out
        self.set_image_output(out)
        if self.session.gui and out is not None:
            self._ensure_gui_connection()
            self.emit_preview(out)

    def get_last_processed(self):
        return self._last



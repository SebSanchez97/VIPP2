from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QComboBox, QMessageBox
from qtpy.QtCore import Qt
from ryven.gui_env import *
from . import nodes
from qtpy.QtGui import QPixmap
from qtpy.QtGui import QImage

### VIPP NODES ###

class ImageNodeGuiBase(NodeMainWidget, QWidget):
    """Preview at top + free controls area below.
    Subclasses may add any widgets to `self.controls` and wire them to node setters.
    """

    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(160)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.controls = QVBoxLayout()
        self.controls.setContentsMargins(0, 0, 0, 0)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.preview, 1)
        v.addLayout(self.controls, 0)
        self.setLayout(v)

        # Kickstart preview: show cached image if available, else trigger update
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

    # ---- helpers (optional) ----
    def add_slider(self, minimum: int, maximum: int, value: int, on_change=None, orientation=Qt.Horizontal):
        s = QSlider(orientation, self)
        s.setRange(minimum, maximum)
        s.setValue(value)
        if on_change is not None:
            s.valueChanged.connect(on_change)
        self.controls.addWidget(s, 0)
        return s

    def add_checkbox(self, text: str, checked: bool, on_change=None):
        cb = QPushButton(text, self)
        cb.setCheckable(True)
        cb.setChecked(checked)
        if on_change is not None:
            cb.toggled.connect(on_change)
        self.controls.addWidget(cb, 0)
        return cb

    def add_combo(self, items: list, current_index: int, on_change=None):
        box = QComboBox(self)
        for it in items:
            box.addItem(str(it))
        if 0 <= current_index < box.count():
            box.setCurrentIndex(current_index)
        if on_change is not None:
            box.currentIndexChanged.connect(on_change)
        self.controls.addWidget(box, 0)
        return box

    # ---- preview plumbing (fixed) ----
    def show_qimage(self, qimage):
        if qimage is None:
            self.preview.setPixmap(QPixmap())
            return
        pix = QPixmap.fromImage(qimage)
        if pix.isNull():
            self.preview.setPixmap(QPixmap())
            return
        self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        p = self.preview.pixmap()
        if p is not None and not p.isNull():
            self.preview.setPixmap(p.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1))

class ImageLoaderNode_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.import_btn = QPushButton('Import Image', self)
        self.import_btn.clicked.connect(self.on_import)

        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(160)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setText('No image')

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.import_btn, 0)
        v.addWidget(self.preview, 1)
        self.setLayout(v)

        try:
            self._refresh_preview(self.node.path())
        except Exception:
            pass

    def on_import(self):
        try:
            from qtpy.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(
                self,
                'Select Image',
                '',
                'Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)'
            )
            if path:
                self.node.set_path(path)
                self._refresh_preview(path)
        except Exception:
            pass

    def _refresh_preview(self, path: str):
        try:
            from qtpy.QtGui import QPixmap
            if not path:
                self.preview.setText('No image')
                self.preview.setPixmap(QPixmap())
                return
            pix = QPixmap(path)
            if pix.isNull():
                self.preview.setText('Failed to load image')
                self.preview.setPixmap(QPixmap())
                return
            scaled = pix.scaled(
                self.preview.size(),
                Qt.KeepAspectRatio,
                transformMode=1  # Qt.SmoothTransformation
            )
            self.preview.setPixmap(scaled)
            self.preview.setText('')
        except Exception:
            self.preview.setText('Error')

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._refresh_preview(self.node.path())

@node_gui(nodes.ImageLoaderNode)
class ImageLoaderNodeGui(NodeGUI):
    main_widget_class = ImageLoaderNode_MainWidget
    main_widget_pos = 'between ports'
    color = '#d0aa4f'

### VIPP NODES END ###






### USER GUIS BEGIN ###







### USER GUIS END ###
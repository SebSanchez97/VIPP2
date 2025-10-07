from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QComboBox, QMessageBox
from qtpy.QtCore import Qt
from ryven.gui_env import *
from . import nodes
from qtpy.QtGui import QPixmap
### USER GUIS BEGIN ###

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

class BrightnessNode_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(160)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setText('No image')

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(300)
        self.slider.setSingleStep(1)
        self.slider.setValue(int(self.node.brightness() * 100))
        self.slider.valueChanged.connect(self.on_slider_changed)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.preview, 1)
        v.addWidget(self.slider, 0)
        self.setLayout(v)

        # Try to fetch cached adjusted image for immediate display
        try:
            cached = getattr(self.node, 'get_last_adjusted', lambda: None)()
            if cached is not None:
                from qtpy.QtGui import QImage
                w, h = cached.size
                rgba = cached.convert('RGBA').tobytes('raw', 'RGBA')
                qimg = QImage(rgba, w, h, 4*w, QImage.Format_RGBA8888)
                self.show_qimage(qimg)
            else:
                self.node.update()
        except Exception:
            try:
                self.node.update()
            except Exception:
                pass

    def on_slider_changed(self, val: int):
        try:
            self.node.set_brightness(val / 100.0)
        except Exception:
            pass

    def show_qimage(self, qimage):
        try:
            print('[BrightnessNode GUI] show_qimage called')
            if qimage is None:
                self.preview.setText('No image')
                self.preview.setPixmap(QPixmap())
                return
            pix = QPixmap.fromImage(qimage)
            if pix.isNull():
                self.preview.setText('Failed to display image')
                self.preview.setPixmap(QPixmap())
                return
            scaled = pix.scaled(
                self.preview.size(),
                Qt.KeepAspectRatio,
                transformMode=1
            )
            self.preview.setPixmap(scaled)
            self.preview.setText('')
        except Exception:
            self.preview.setText('Error')

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # Re-scale current pixmap on resize
        try:
            current = self.preview.pixmap()
            if current is not None and not current.isNull():
                scaled = current.scaled(
                    self.preview.size(),
                    Qt.KeepAspectRatio,
                    transformMode=1
                )
                self.preview.setPixmap(scaled)
        except Exception:
            pass

@node_gui(nodes.BrightnessNode)
class BrightnessNodeGui(NodeGUI):
    main_widget_class = BrightnessNode_MainWidget
    main_widget_pos = 'between ports'
    color = '#5fb36b'


### USER GUIS END ###

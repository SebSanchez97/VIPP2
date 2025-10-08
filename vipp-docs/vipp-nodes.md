## Pattern: Image-processing node with live GUI preview and controls

This guide shows how to build nodes that:
- accept images from upstream nodes
- process them (brightness/contrast/filters)
- display a live-updating preview in the node GUI
- emit processed images to downstream nodes

### 1) Data contract: wrap images in Data(PIL.Image)
- Always output `Data(pil_image)` to satisfy ryvencore and enable chaining.
- Example (loader node): open path with Pillow, convert to RGBA, set `Data(img)`.

```python
from ryven.node_env import *
from PIL import Image

class ImageLoaderNode(Node):
    init_inputs = []
    init_outputs = [NodeOutputType('image')]

    def __init__(self, params):
        super().__init__(params)
        self._path = ''

    def set_path(self, path: str):
        self._path = str(path or '')
        self.update()

    def update_event(self, inp=-1):
        if not self._path:
            self.set_output_val(0, None)
            return
        img = Image.open(self._path).convert('RGBA')
        self.set_output_val(0, Data(img))
```

### 2) Processing node logic: unwrap, process, emit
- Unwrap `Data` into the underlying `PIL.Image` (accept str path as fallback if desired).
- Ensure RGBA mode for predictable conversion.
- Apply the transform (e.g., brightness), cache the latest result, and output `Data(processed)`.
- For preview, convert `PIL.Image` → `QImage` via raw RGBA bytes and emit a signal to the GUI.

```python
from ryven.node_env import *
from PIL import Image, ImageEnhance

class MyFilterNode(Node):
    init_inputs = [NodeInputType('image')]
    init_outputs = [NodeOutputType('image')]

    def __init__(self, params):
        super().__init__(params)
        self._factor = 1.0
        self._last_processed = None
        if self.session.gui:
            from qtpy.QtCore import QObject, Signal
            class Signals(QObject):
                new_qimage = Signal(object)
            self.SIGNALS = Signals()

    def set_factor(self, factor: float):
        self._factor = max(0.0, min(3.0, float(factor)))
        self.update()

    def view_place_event(self):
        if self.session.gui:
            # connect node signal to GUI slot using self.gui.main_widget()
            self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
            self.update()  # trigger initial render

    def update_event(self, inp=-1):
        payload = None if self.input(0) is None else self.input(0).payload
        obj = payload.payload if hasattr(payload, 'payload') else payload
        if obj is None:
            self._last_processed = None
            self.set_output_val(0, None)
            if self.session.gui:
                self.SIGNALS.new_qimage.emit(None)
            return

        # process image
        base = obj.convert('RGBA')
        processed = ImageEnhance.Brightness(base).enhance(self._factor)
        self._last_processed = processed

        # preview: PIL → QImage via raw RGBA bytes
        if self.session.gui:
            from qtpy.QtGui import QImage
            w, h = processed.size
            rgba = processed.tobytes('raw', 'RGBA')
            qimg = QImage(rgba, w, h, 4*w, QImage.Format_RGBA8888)
            self.SIGNALS.new_qimage.emit(qimg.copy())

        # downstream output
        self.set_output_val(0, Data(processed))

    # optional for GUI to fetch cached preview on init
    def get_last_processed(self):
        return self._last_processed
```

### 3) GUI: preview + controls
- Build a `NodeMainWidget` with a `QLabel` preview and controls (e.g., `QSlider`).
- The slider drives a node setter and calls `node.update()`.
- On init, try to render the cached image for immediate feedback.

```python
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QSizePolicy
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap, QImage
from ryven.gui_env import *

class MyFilterNode_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(160)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 300)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(lambda v: self.node.set_factor(v/100.0))

        v = QVBoxLayout(); v.setContentsMargins(0,0,0,0)
        v.addWidget(self.preview, 1)
        v.addWidget(self.slider, 0)
        self.setLayout(v)

        # show cached image if available; otherwise request an update
        cached = getattr(self.node, 'get_last_processed', lambda: None)()
        if cached is not None:
            w, h = cached.size
            rgba = cached.convert('RGBA').tobytes('raw', 'RGBA')
            qimg = QImage(rgba, w, h, 4*w, QImage.Format_RGBA8888)
            self.show_qimage(qimg)
        else:
            self.node.update()

    def show_qimage(self, qimage):
        if qimage is None:
            self.preview.setPixmap(QPixmap())
            return
        pix = QPixmap.fromImage(qimage)
        scaled = pix.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1)
        self.preview.setPixmap(scaled)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        p = self.preview.pixmap()
        if p is not None and not p.isNull():
            self.preview.setPixmap(p.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1))
```

Register the GUI with the node:
```python
@node_gui(nodes.MyFilterNode)
class MyFilterNodeGui(NodeGUI):
    main_widget_class = MyFilterNode_MainWidget
    main_widget_pos = 'between ports'
    color = '#5fb36b'
```

### 4) Key notes
- Always wrap outputs as `Data(pil_image)`; unwrap defensively on input.
- Connect signals using `self.gui.main_widget().<slot>` in the node.
- Avoid `PIL.ImageQt` mismatch by converting to `QImage` using raw RGBA bytes.
- Scale preview on resize; reprocess on parameter changes via `node.update()`.
- Use light try/except around I/O, Pillow, Qt conversion, and signal wiring.

### 5) Minimal checklist
- Node:
  - Input: `NodeInputType('image')`; Output: `NodeOutputType('image')`
  - Unwrap `Data`, process image, emit `Data(processed)`
  - Emit preview via `self.SIGNALS.new_qimage.emit(qimg)` and connect in `view_place_event`
- GUI:
  - `QLabel` preview with aspect-preserving scaling
  - Controls (e.g., `QSlider`) bound to node setters
  - Optional: show cached image on init

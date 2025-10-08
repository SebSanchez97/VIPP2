from ryven.node_env import *
import inspect
import time

### VIPP NODES ###

class ImageNodeBase(Node):
    """Standardized image node base:
    - IO: one image in, one image out (Data(PIL.Image.Image, RGBA))
    - GUI preview is emitted by this base
    - Subclasses implement logic via `transform(self, img)`; legacy `process` supported
    """

    tags = ['image', 'generated']
    init_inputs = [NodeInputType('image')]
    init_outputs = [NodeOutputType('image')]

    def __init__(self, params):
        """Initialize cache, GUI-connection state, and preview throttling.
        Creates a Qt signal emitter when a GUI session is active so that
        processed previews can be forwarded to the node GUI widget.
        """
        super().__init__(params)
        self._last = None
        self._last_in_sig = None
        self._last_param_sig = None
        self._gui_connected = False
        self._preview_min_interval = 0.03  # ~33 FPS
        self._last_emit_t = 0.0

        if self.session.gui:
            from qtpy.QtCore import QObject, Signal

            class Signals(QObject):
                new_qimage = Signal(object)

            self.SIGNALS = Signals()

    # ---------- Subclass API ----------

    def transform(self, img):
        """Subclass hook: implement image processing here.
        Must return a PIL.Image.Image in RGBA mode. If not overridden,
        the image is passed through unchanged.
        """
        return img


    def params_signature(self):
        """Return a small, hashable summary of parameters.
        Default: tuple of private primitives (ints/floats/bools/str/tuple) excluding internals.
        """
        ignore = {
            '_last', '_last_in_sig', '_last_param_sig', '_gui_connected',
            'SIGNALS', '_preview_min_interval', '_last_emit_t'
        }
        items = []
        for k, v in sorted(self.__dict__.items()):
            if k in ignore or not k.startswith('_'):
                continue
            if isinstance(v, (int, float, bool, str, tuple)):
                s = str(v)
                if len(s) <= 256:
                    items.append((k, v))
        return tuple(items)

    # ---------- Helpers ----------

    def input_image(self):
        """Read input 0 and normalize it to a PIL RGBA image.
        Accepts either a Data-wrapped PIL image, a bare PIL image, or a
        filesystem path string to an image. Returns None if unavailable.
        """
        payload = None if self.input(0) is None else self.input(0).payload
        obj = payload.payload if hasattr(payload, 'payload') else payload
        if obj is None:
            return None
        try:
            from PIL import Image
        except Exception:
            return None
        if hasattr(obj, 'size') and hasattr(obj, 'mode'):
            return obj.convert('RGBA')
        if isinstance(obj, str):
            try:
                return Image.open(obj).convert('RGBA')
            except Exception:
                return None
        return None

    def ensure_rgba(self, img):
        """Best-effort conversion to RGBA; returns input unchanged on failure."""
        try:
            return img.convert('RGBA')
        except Exception:
            return img

    def clamp(self, v, lo, hi):
        """Clamp numeric value v to the inclusive range [lo, hi]."""
        try:
            v = float(v)
        except Exception:
            return lo
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    def _to_qimage(self, img):
        """Convert a PIL RGBA image to a Qt QImage (deep-copied)."""
        try:
            from qtpy.QtGui import QImage
            w, h = img.size
            rgba = img.tobytes('raw', 'RGBA')
            return QImage(rgba, w, h, 4 * w, QImage.Format_RGBA8888).copy()
        except Exception:
            return None

    def _emit_preview(self, img_or_none):
        """Emit a GUI preview via Qt signal, throttled to ~33 FPS.
        If no GUI session exists, this is a no-op. Emits None to clear the
        preview when no image is available.
        """
        if not self.session.gui:
            return
        now = time.monotonic()
        if now - self._last_emit_t < self._preview_min_interval:
            return
        self._last_emit_t = now
        try:
            if img_or_none is None:
                self.SIGNALS.new_qimage.emit(None)
            else:
                self.SIGNALS.new_qimage.emit(self._to_qimage(img_or_none))
        except Exception:
            pass


    def set_image_output(self, img):
        """Set output 0 to a Data-wrapped PIL image (or None)."""
        self.set_output_val(0, Data(img) if img is not None else None)

    # ---------- Lifecycle ----------

    def view_place_event(self):
        """Called when the node is placed in the view.
        Connects the preview signal to the GUI widget and triggers an update.
        """
        if not self.session.gui:
            return
        try:
            self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
            self._gui_connected = True
        except Exception:
            self._gui_connected = False
        self.update()

    def _ensure_gui_connection(self):
        """Ensure the preview signal is connected to the GUI widget."""
        if self.session.gui and not self._gui_connected and hasattr(self, 'gui') and self.gui:
            try:
                self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
                self._gui_connected = True
            except Exception:
                pass

    def update_event(self, inp=-1):
        """Main compute step: read input, apply transform/process, cache, output, preview.
        Skips recomputation when both input and parameter signatures match the
        previous run. Always keeps outputs in RGBA mode for consistency.
        """
        img = self.input_image()
        if img is None:
            # No input: clear caches, output None, and clear the preview
            self._last = None
            self.set_image_output(None)
            if self.session.gui:
                self._ensure_gui_connection()
            self._emit_preview(None)
            return

        # cache signatures
        # input signature captures identity and basic image shape/format
        in_sig = (id(img), getattr(img, 'size', None), getattr(img, 'mode', None))
        # parameter signature captures relevant private primitives
        param_sig = self.params_signature()

        if self._last is not None and in_sig == self._last_in_sig and param_sig == self._last_param_sig:
            # Nothing changed: reuse cached result and re-emit preview
            self.set_image_output(self._last)
            if self.session.gui:
                self._ensure_gui_connection()
            self._emit_preview(self._last)
            return

        try:
            base = self.ensure_rgba(img)
            out = self.transform(base)
            if out is None:
                out = base
            out = self.ensure_rgba(out)
        except Exception:
            out = None

        # Update caches and propagate outputs/preview
        self._last = out
        self._last_in_sig = in_sig
        self._last_param_sig = param_sig
        self.set_image_output(out)
        if self.session.gui:
            self._ensure_gui_connection()
        self._emit_preview(out)

    def get_last_processed(self):
        """Return the last processed PIL image (or None)."""
        return self._last

class ImageLoaderNode(Node):
    title = 'Image Loader'
    tags = ['image', 'io', 'import']
    init_inputs = []
    init_outputs = [NodeOutputType('image')]

    def __init__(self, params):
        super().__init__(params)
        self._path = ''

    def set_path(self, path: str):
        self._path = str(path or '')
        try:
            print(f"[ImageLoaderNode] set_path -> '{self._path}'")
        except Exception:
            pass
        self.update()

    def path(self) -> str:
        return self._path

    def update_event(self, inp=-1):
        if not self._path:
            try:
                print('[ImageLoaderNode] update_event: no path set -> output None')
            except Exception:
                pass
            self.set_output_val(0, None)
            return
        try:
            from PIL import Image
            img = Image.open(self._path).convert('RGBA')
            try:
                print(f"[ImageLoaderNode] update_event: loaded PIL.Image size={img.size} mode={img.mode}")
            except Exception:
                pass
            self.set_output_val(0, Data(img))
        except Exception as e:
            try:
                print(f"[ImageLoaderNode] error loading image: {e}")
            except Exception:
                pass
            self.set_output_val(0, None)

### VIPP NODES END ###





















### USER NODES BEGIN ###

### USER NODES END ###




















# auto-discover Node subclasses (so appended classes are exported too)
_node_types = []
# Iterates through the global variables and checks if the object is a class 
# and a subclass of Node and not the Node class itself
for _name, _obj in list(globals().items()):
    try:
        if inspect.isclass(_obj) and issubclass(_obj, Node) and _obj not in (Node, ImageNodeBase):
            _node_types.append(_obj)
    except Exception:
        pass

export_nodes(_node_types)

@on_gui_load
def load_gui():
    from . import gui

from ryven.node_env import *
import inspect

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


### USER NODES BEGIN ###

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

class BrightnessNode(Node):
    title = 'Brightness Adjust'
    tags = ['image', 'brightness', 'filter']
    init_inputs = [NodeInputType('image')]
    init_outputs = [NodeOutputType('image')]

    def __init__(self, params):
        super().__init__(params)
        self._brightness = 1.0  # 1.0 means no change
        self._gui_connected = False
        self._last_adjusted = None

        if self.session.gui:
            # Defer Qt import to GUI mode only
            from qtpy.QtCore import QObject, Signal

            class Signals(QObject):
                new_qimage = Signal(object)

            self.SIGNALS = Signals()

    # Exposed for GUI widget to adjust
    def set_brightness(self, factor: float):
        try:
            f = float(factor)
        except Exception:
            return
        if f < 0.0:
            f = 0.0
        if f > 3.0:
            f = 3.0
        if abs(self._brightness - f) < 1e-6:
            return
        self._brightness = f
        self.update()

    def brightness(self) -> float:
        return self._brightness

    def view_place_event(self):
        # Connect signal to GUI preview method when widget is ready
        try:
            if self.session.gui:
                print('[BrightnessNode] view_place_event: GUI present, checking gui/main_widget availability')
                print(f"[BrightnessNode] view_place_event: has gui? {hasattr(self, 'gui')} value={getattr(self, 'gui', None)}")
                try:
                    print(f"[BrightnessNode] view_place_event: has gui.main_widget()? {hasattr(self.gui, 'main_widget')}")
                except Exception:
                    pass
                self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
                print('[BrightnessNode] view_place_event: connection established via self.gui.main_widget()')
                self._gui_connected = True
                try:
                    print('[BrightnessNode] view_place_event: triggering update to render current state')
                except Exception:
                    pass
                try:
                    self.update()
                except Exception:
                    pass
            else:
                print('[BrightnessNode] view_place_event: no GUI session')
        except Exception:
            pass

    def update_event(self, inp=-1):
        input_payload = None
        try:
            if self.input(0) is not None:
                input_payload = self.input(0).payload
        except Exception:
            input_payload = None

        try:
            print(f"[BrightnessNode] update_event: inp={inp}, input0_type={type(input_payload)}, brightness={self._brightness}")
            if hasattr(input_payload, 'payload'):
                print(f"[BrightnessNode] update_event: Data wrapper payload_type={type(getattr(input_payload, 'payload', None))}")
        except Exception:
            pass

        if not input_payload:
            self._last_adjusted = None
            self.set_output_val(0, None)
            # also notify GUI to clear
            try:
                if self.session.gui:
                    self.SIGNALS.new_qimage.emit(None)
            except Exception:
                pass
            return

        # Process brightness using Pillow
        qimage_obj = None
        output_payload = None
        try:
            from PIL import Image, ImageEnhance

            # Unwrap Data payloads
            payload_obj = input_payload.payload if hasattr(input_payload, 'payload') else input_payload
            try:
                print(f"[BrightnessNode] unwrap: payload_obj_type={type(payload_obj)}")
            except Exception:
                pass

            if hasattr(payload_obj, 'size') and hasattr(payload_obj, 'mode'):
                # Likely a PIL.Image.Image
                img = payload_obj
            elif isinstance(payload_obj, str):
                # Backward-compat: load from path
                img = Image.open(payload_obj).convert('RGBA')
            else:
                img = None

            if img is None:
                raise Exception('Unsupported input payload for BrightnessNode')
            else:
                try:
                    print(f"[BrightnessNode] got PIL image: size={getattr(img,'size',None)} mode={getattr(img,'mode',None)}")
                except Exception:
                    pass

            # Ensure RGBA for consistent downstream handling
            base = img.convert('RGBA')
            enhancer = ImageEnhance.Brightness(base)
            adjusted = enhancer.enhance(self._brightness)
            try:
                print(f"[BrightnessNode] adjusted image: size={adjusted.size} mode={adjusted.mode}")
            except Exception:
                pass
            self._last_adjusted = adjusted

            # Build QImage without Pillow ImageQt to avoid version issues
            if self.session.gui:
                try:
                    from qtpy.QtGui import QImage
                    w, h = adjusted.size
                    rgba = adjusted.tobytes('raw', 'RGBA')
                    print(f"[BrightnessNode] QImage conversion: w={w} h={h} bytes={len(rgba)}")
                    qimg = QImage(rgba, w, h, 4*w, QImage.Format_RGBA8888)
                    print(f"[BrightnessNode] QImage created: w={qimg.width()} h={qimg.height()} format={qimg.format()}")
                    qimage_obj = qimg.copy()  # detach from buffer
                except Exception as conv_e:
                    try:
                        print(f"[BrightnessNode] QImage conversion error: {conv_e}")
                    except Exception:
                        pass

            # For output, return the adjusted PIL Image wrapped in Data
            output_payload = Data(adjusted)
        except Exception as e:
            try:
                print(f"[BrightnessNode] processing error: {e}")
            except Exception:
                pass
            output_payload = None

        # Emit for GUI
        try:
            if self.session.gui:
                if not getattr(self, '_gui_connected', False):
                    try:
                        print('[BrightnessNode] update_event: attempting lazy GUI connection')
                        if hasattr(self, 'gui') and getattr(self, 'gui') is not None:
                            self.SIGNALS.new_qimage.connect(self.gui.main_widget().show_qimage)
                            self._gui_connected = True
                            print('[BrightnessNode] update_event: lazy connection established via self.gui.main_widget()')
                        else:
                            raise AttributeError('gui not available yet')
                    except Exception as lazy_e:
                        try:
                            print(f"[BrightnessNode] update_event: lazy connection failed: {lazy_e}")
                        except Exception:
                            pass
                print(f"[BrightnessNode] emit new_qimage: has_image={qimage_obj is not None}")
                self.SIGNALS.new_qimage.emit(qimage_obj)
            else:
                print('[BrightnessNode] emit skipped: no GUI session')
        except Exception:
            pass

        try:
            base_type = type(output_payload)
            inner_type = type(getattr(output_payload, 'payload', None)) if hasattr(output_payload, 'payload') else None
            print(f"[BrightnessNode] set_output_val: type={base_type}, inner={inner_type}")
        except Exception:
            pass
        self.set_output_val(0, output_payload)

    # Exposed for GUI to fetch last adjusted image on init
    def get_last_adjusted(self):
        return self._last_adjusted

### USER NODES END ###

# auto-discover Node subclasses (so appended classes are exported too)
_node_types = []
# Iterates through the global variables and checks if the object is a class 
# and a subclass of Node and not the Node class itself
for _name, _obj in list(globals().items()):
    try:
        if inspect.isclass(_obj) and issubclass(_obj, Node) and _obj is not Node:
            _node_types.append(_obj)
    except Exception:
        pass

export_nodes(_node_types)

@on_gui_load
def load_gui():
    from . import gui

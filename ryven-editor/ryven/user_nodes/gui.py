from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QComboBox, QMessageBox
from qtpy.QtCore import Qt
from ryven.gui_env import *
from . import nodes
from qtpy.QtGui import QPixmap
from qtpy.QtGui import QImage

### VIPP NODES ###

class ImageNodeGuiBase(NodeMainWidget, QWidget):
    """
    Base class for image processing node GUI widgets.
    
    This class provides a standardized layout with:
    - Image preview area at the top (60% of height)
    - Controls area at the bottom (40% of height)
    - Automatic preview management and caching
    - Helper methods for common control types
    
    Subclasses should:
    1. Call super().__init__(params) first
    2. Add custom controls to self.controls layout
    3. Wire controls to node parameter setters
    4. Optionally override helper methods for custom behavior
    """

    def __init__(self, params):
        """
        Initialize the GUI widget with preview and controls layout.
        
        Args:
            params: Node parameters passed from Ryven framework
        """
        # Initialize parent classes (NodeMainWidget provides Ryven integration, QWidget provides Qt functionality)
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        # Create preview label for displaying processed images
        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)  # Center the image in the label
        self.preview.setMinimumHeight(300)  # Ensure larger minimum preview size
        # Make preview expand to fill available space
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create vertical layout for custom controls (sliders, buttons, etc.)
        self.controls = QVBoxLayout()
        self.controls.setContentsMargins(0, 0, 0, 0)  # Remove default margins

        # Create main vertical layout to organize preview and controls
        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)  # Remove default margins
        v.addWidget(self.preview, 1)      # Preview takes 1 unit of space (expands)
        v.addLayout(self.controls, 0)     # Controls take 0 units (fixed size)
        self.setLayout(v)

        # Initialize preview with cached image if available, otherwise trigger node update
        try:
            # Try to get the last processed image from the node
            cached = getattr(self.node, 'get_last_processed', lambda: None)()
            if cached is not None:
                # Convert PIL image to QImage for display
                w, h = cached.size
                rgba = cached.convert('RGBA').tobytes('raw', 'RGBA')
                qimg = QImage(rgba, w, h, 4 * w, QImage.Format_RGBA8888)
                self.show_qimage(qimg)
            else:
                # No cached image, trigger node processing
                self.node.update()
        except Exception:
            # Fallback: try to trigger node update
            try:
                self.node.update()
            except Exception:
                pass

    def sizeHint(self):
        # Provide a larger default size so nodes appear bigger by default
        try:
            from qtpy.QtCore import QSize
            return QSize(380, 460)
        except Exception:
            return super().sizeHint()

    # ========== HELPER METHODS FOR COMMON CONTROLS ==========
    # These methods provide convenient ways to add standard controls to the GUI

    def add_slider(self, minimum: int, maximum: int, value: int, on_change=None, orientation=Qt.Horizontal):
        """
        Add a slider control to the controls area.
        
        Args:
            minimum: Minimum slider value
            maximum: Maximum slider value  
            value: Initial slider value
            on_change: Callback function called when slider value changes (optional)
            orientation: Slider orientation (Qt.Horizontal or Qt.Vertical)
            
        Returns:
            QSlider: The created slider widget for further customization
        """
        s = QSlider(orientation, self)
        s.setRange(minimum, maximum)
        s.setValue(value)
        if on_change is not None:
            s.valueChanged.connect(on_change)
        self.controls.addWidget(s, 0)  # Add to controls layout with 0 stretch
        return s

    def add_checkbox(self, text: str, checked: bool, on_change=None):
        """
        Add a checkbox control to the controls area.
        
        Note: This uses QPushButton with checkable=True instead of QCheckBox
        for consistency with the existing codebase.
        
        Args:
            text: Text label for the checkbox
            checked: Initial checked state
            on_change: Callback function called when checkbox state changes (optional)
            
        Returns:
            QPushButton: The created checkbox widget for further customization
        """
        cb = QPushButton(text, self)
        cb.setCheckable(True)  # Make button behave like a checkbox
        cb.setChecked(checked)
        if on_change is not None:
            cb.toggled.connect(on_change)
        self.controls.addWidget(cb, 0)  # Add to controls layout with 0 stretch
        return cb

    def add_combo(self, items: list, current_index: int, on_change=None):
        """
        Add a dropdown/combo box control to the controls area.
        
        Args:
            items: List of items to display in the dropdown
            current_index: Index of initially selected item
            on_change: Callback function called when selection changes (optional)
            
        Returns:
            QComboBox: The created combo box widget for further customization
        """
        box = QComboBox(self)
        for it in items:
            box.addItem(str(it))  # Convert items to strings for display
        if 0 <= current_index < box.count():
            box.setCurrentIndex(current_index)
        if on_change is not None:
            box.currentIndexChanged.connect(on_change)
        self.controls.addWidget(box, 0)  # Add to controls layout with 0 stretch
        return box

    # ========== PREVIEW MANAGEMENT METHODS ==========
    # These methods handle image display and preview updates

    def show_qimage(self, qimage):
        """
        Display a QImage in the preview area.
        
        This method handles:
        - Converting QImage to QPixmap for display
        - Scaling the image to fit the preview area while maintaining aspect ratio
        - Clearing the preview if no valid image is provided
        
        Args:
            qimage: QImage object to display, or None to clear the preview
        """
        if qimage is None:
            # Clear the preview by setting an empty pixmap
            self.preview.setPixmap(QPixmap())
            return
        # Convert QImage to QPixmap for display
        pix = QPixmap.fromImage(qimage)
        if pix.isNull():
            # Invalid image, clear the preview
            self.preview.setPixmap(QPixmap())
            return
        # Scale the pixmap to fit the preview area while maintaining aspect ratio
        # transformMode=1 corresponds to Qt.SmoothTransformation for better quality
        self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1))

    def resizeEvent(self, e):
        """
        Handle widget resize events to maintain proper image scaling.
        
        This method is called automatically by Qt when the widget is resized.
        It ensures that the preview image is properly scaled to fit the new size
        while maintaining its aspect ratio.
        
        Args:
            e: QResizeEvent object containing resize information
        """
        # Call parent class resize handling first
        super().resizeEvent(e)
        # Get the current pixmap from the preview label
        p = self.preview.pixmap()
        if p is not None and not p.isNull():
            # Re-scale the pixmap to fit the new preview size
            self.preview.setPixmap(p.scaled(self.preview.size(), Qt.KeepAspectRatio, transformMode=1))

class ImageLoaderNode_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.import_btn = QPushButton('Import Image', self)
        self.import_btn.clicked.connect(self.on_import)

        self.preview = QLabel(self)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(300)
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

    def sizeHint(self):
        try:
            from qtpy.QtCore import QSize
            return QSize(380, 460)
        except Exception:
            return super().sizeHint()

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
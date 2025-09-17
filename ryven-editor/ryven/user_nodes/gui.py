from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout
from qtpy.QtCore import Qt
from ryven.gui_env import *
from . import nodes

class RandSliderWidget(NodeInputWidget, QSlider):
    def __init__(self, params):
        NodeInputWidget.__init__(self, params)
        QSlider.__init__(self)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(100)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(50)
        self.valueChanged.connect(self.value_changed)
    
    def value_changed(self, val):
        # triggers update of the node input this widget is attached to
        self.update_node_input(Data(val))
    
    def get_state(self) -> dict:
        return {'value': self.value()}
    
    def set_state(self, state: dict):
        self.setValue(state['value'])

@node_gui(nodes.RandNode)
class RandNodeGui(NodeGUI):
    color = '#fcba03'
    input_widget_classes = { 'slider': RandSliderWidget }
    init_input_widgets = { 0: {'name': 'slider', 'pos': 'below'} }


class TextInput_MainWidget(NodeMainWidget, QLineEdit):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLineEdit.__init__(self)

        self.setPlaceholderText('Type here...')
        self.textChanged.connect(self.text_changed)

    def text_changed(self, text: str):
        self.node.set_text(text)

    def get_state(self) -> dict:
        return {'text': self.text()}

    def set_state(self, state: dict):
        self.setText(state.get('text', ''))

@node_gui(nodes.TextInputNode)
class TextInputNodeGui(NodeGUI):
    main_widget_class = TextInput_MainWidget
    main_widget_pos = 'between ports'
    color = '#88c0d0'

class NodeGenerator_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText('Paste your Node subclass code here...')
        self.submit_btn = QPushButton('Submit', self)
        self.submit_btn.clicked.connect(self.on_submit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        layout.addWidget(self.submit_btn)
        self.setLayout(layout)

    def on_submit(self):
        user_input_code = self.editor.toPlainText()
        try:
            self.node.append_user_code(user_input_code)
        except Exception as e:
            print(e)

@node_gui(nodes.NodeGeneratorNode)
class NodeGeneratorNodeGui(NodeGUI):
    main_widget_class = NodeGenerator_MainWidget
    main_widget_pos = 'between ports'
    color = '#a3be8c'
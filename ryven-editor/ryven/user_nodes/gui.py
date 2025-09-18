from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy
from qtpy.QtCore import Qt
from ryven.gui_env import *
from . import nodes

class NodeGenerator_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText('Paste your Node subclass code here...')
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor.setMinimumHeight(200)
        self.gui_editor = QTextEdit(self)
        self.gui_editor.setPlaceholderText('Paste your Node GUI code here (NodeGUI, NodeMainWidget, @node_gui, etc.)...')
        self.gui_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.gui_editor.setMinimumHeight(200)
        self.submit_btn = QPushButton('Submit', self)
        self.submit_btn.clicked.connect(self.on_submit)

        # left panel (logic)
        left_group = QGroupBox('Logic', self)
        left_v = QVBoxLayout()
        left_v.setContentsMargins(6, 6, 6, 6)
        left_v.addWidget(self.editor)
        left_group.setLayout(left_v)

        # right panel (GUI)
        right_group = QGroupBox('GUI', self)
        right_v = QVBoxLayout()
        right_v.setContentsMargins(6, 6, 6, 6)
        right_v.addWidget(self.gui_editor)
        right_group.setLayout(right_v)

        # main horizontal layout
        main_h = QHBoxLayout()
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.addWidget(left_group, 1)
        main_h.addWidget(right_group, 1)

        # root vertical layout to include button below
        root_v = QVBoxLayout()
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.addLayout(main_h)
        root_v.addWidget(self.submit_btn)
        self.setLayout(root_v)

    def on_submit(self):
        user_input_code = self.editor.toPlainText()
        user_gui_code = self.gui_editor.toPlainText()
        try:
            self.node.append_user_code(user_input_code, user_gui_code)
        except Exception as e:
            print(e)

@node_gui(nodes.NodeGeneratorNode)
class NodeGeneratorNodeGui(NodeGUI):
    main_widget_class = NodeGenerator_MainWidget
    main_widget_pos = 'between ports'
    color = '#a3be8c'

### USER GUIS BEGIN ###

class MultiplyText_MainWidget(NodeMainWidget, QLineEdit):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QLineEdit.__init__(self)
        self.setPlaceholderText('Factor (e.g., 2.5)')
        self.setText('1.0')
        self.textChanged.connect(self.on_text)

    def on_text(self, text: str):
        self.node.set_factor(text)

    def get_state(self) -> dict:
        return {'text': self.text()}

    def set_state(self, state: dict):
        self.setText(state.get('text', '1.0'))

@node_gui(nodes.MultiplyTextNode)
class MultiplyTextNodeGui(NodeGUI):
    main_widget_class = MultiplyText_MainWidget
    main_widget_pos = 'between ports'
    color = '#a3be8c'

### USER GUIS END ###
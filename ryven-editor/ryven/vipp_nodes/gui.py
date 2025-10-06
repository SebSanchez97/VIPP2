from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QComboBox, QMessageBox
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

class NodeDeletor_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        self.combo = QComboBox(self)
        self.combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.refresh_btn = QPushButton('Refresh', self)
        self.refresh_btn.clicked.connect(self.populate_nodes)

        self.delete_btn = QPushButton('Delete Node', self)
        self.delete_btn.clicked.connect(self.on_delete)

        top_h = QHBoxLayout()
        top_h.setContentsMargins(0, 0, 0, 0)
        top_h.addWidget(QLabel('Select node to delete:', self))
        top_h.addStretch(1)

        controls_h = QHBoxLayout()
        controls_h.setContentsMargins(0, 0, 0, 0)
        controls_h.addWidget(self.combo, 1)
        controls_h.addWidget(self.refresh_btn, 0)
        controls_h.addWidget(self.delete_btn, 0)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.addLayout(top_h)
        v.addLayout(controls_h)
        self.setLayout(v)

        self.populate_nodes()

    def populate_nodes(self):
        try:
            items = self.node.list_user_nodes()
        except Exception as e:
            print(e)
            items = []

        current = self.combo.currentData() if self.combo.count() > 0 else None
        self.combo.clear()
        for it in items:
            cls_name = it.get('class')
            title = it.get('title') or ''
            label = f"{title} — {cls_name}" if title else cls_name
            self.combo.addItem(label, cls_name)

        # Restore selection if possible
        if current is not None:
            idx = self.combo.findData(current)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)

    def on_delete(self):
        if self.combo.count() == 0:
            return
        cls_name = self.combo.currentData()
        label = self.combo.currentText()

        # confirm
        msg = QMessageBox(
            QMessageBox.Warning,
            'Delete node?',
            f'You are about to delete:\n{label}\n\nThis will remove its code from user_nodes. Continue?',
            QMessageBox.Cancel | QMessageBox.Yes,
            self,
        )
        msg.setDefaultButton(QMessageBox.Cancel)
        if msg.exec_() != QMessageBox.Yes:
            return

        try:
            # use class name for exact match
            self.node.delete_user_node(cls_name)
        except Exception as e:
            print(e)
        self.populate_nodes()

@node_gui(nodes.NodeDeletorNode)
class NodeDeletorNodeGui(NodeGUI):
    main_widget_class = NodeDeletor_MainWidget
    main_widget_pos = 'between ports'
    color = '#bf616a'

class PromptGenerator_MainWidget(NodeMainWidget, QWidget):
    def __init__(self, params):
        NodeMainWidget.__init__(self, params)
        QWidget.__init__(self)

        # Top: node name textbox
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText('Name your node')
        self.name_edit.textChanged.connect(self.on_name_changed)

        # Left: prompt editor + Generate button
        self.prompt_edit = QTextEdit(self)
        self.prompt_edit.setPlaceholderText('Write your prompt here...')
        self.prompt_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.generate_btn = QPushButton('Generate', self)
        self.generate_btn.clicked.connect(self.on_generate)

        left_v = QVBoxLayout()
        left_v.setContentsMargins(6, 6, 6, 6)
        left_v.addWidget(self.prompt_edit, 1)
        left_v.addWidget(self.generate_btn, 0)

        left_group = QGroupBox('Prompt', self)
        left_group.setLayout(left_v)

        # Center: logic code + Create button
        self.logic_edit = QTextEdit(self)
        self.logic_edit.setPlaceholderText('Generated logic code (nodes.py)')
        self.logic_edit.setReadOnly(True)
        self.logic_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.create_logic_btn = QPushButton('Create', self)

        center_v = QVBoxLayout()
        center_v.setContentsMargins(6, 6, 6, 6)
        center_v.addWidget(self.logic_edit, 1)
        center_v.addWidget(self.create_logic_btn, 0)

        center_group = QGroupBox('Logic (nodes.py)', self)
        center_group.setLayout(center_v)

        # Right: GUI code + Create button
        self.gui_edit = QTextEdit(self)
        self.gui_edit.setPlaceholderText('Generated GUI code (gui.py)')
        self.gui_edit.setReadOnly(True)
        self.gui_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.create_gui_btn = QPushButton('Create', self)

        right_v = QVBoxLayout()
        right_v.setContentsMargins(6, 6, 6, 6)
        right_v.addWidget(self.gui_edit, 1)
        right_v.addWidget(self.create_gui_btn, 0)

        right_group = QGroupBox('GUI (gui.py)', self)
        right_group.setLayout(right_v)

        # Row with three panels
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(left_group, 1)
        row.addWidget(center_group, 1)
        row.addWidget(right_group, 1)

        # Root layout
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.name_edit)
        root.addLayout(row)
        self.setLayout(root)

    def on_name_changed(self, text: str):
        # Update node title display live (non-persistent)
        try:
            self.node.title = text or 'Prompt Generator'
            self.update_node()
        except Exception:
            pass

    def on_generate(self):
        try:
            # Resolve template path adjacent to this module
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(base_dir, 'promt_template.txt')

            # Read template
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
            except Exception as e:
                print(f'Failed to read template: {e}')
                return

            node_name = (self.name_edit.text() or 'Prompt Generator').strip()
            user_prompt = self.prompt_edit.toPlainText().strip()

            # Fill placeholders
            filled = (
                template
                .replace('{{NODE_NAME}}', node_name)
                .replace('{{CLASS_NAME}}', ''.join(ch for ch in node_name.title() if ch.isalnum()) + 'Node')
                .replace('{{USER_PROMPT}}', user_prompt)
            )

            # Print to console for inspection
            print('\n=== Composed LLM Prompt Start ===\n')
            print(filled)
            print('\n=== Composed LLM Prompt End ===\n')
        except Exception as e:
            print(e)

@node_gui(nodes.PromptGeneratorNode)
class PromptGeneratorGui(NodeGUI):
    main_widget_class = PromptGenerator_MainWidget
    main_widget_pos = 'between ports'
    color = '#6a9bd8'

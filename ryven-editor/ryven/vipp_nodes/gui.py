from qtpy.QtWidgets import QSlider, QLineEdit, QTextEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QComboBox, QMessageBox
from qtpy.QtCore import Qt, QThread, Signal
from ryven.gui_env import *
from . import nodes
from .openai_worker import OpenAIWorker
from .code_injection import insert_user_node_code, insert_user_gui_code
import os
import json
import re
import urllib.request
import urllib.error


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
        self.create_logic_btn.clicked.connect(self.on_create_logic)

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
        self.create_gui_btn.clicked.connect(self.on_create_gui)

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

            # Print composed prompt for verification
            print('\n=== Composed LLM Prompt Start ===\n')
            print(filled)
            print('\n=== Composed LLM Prompt End ===\n')

            api_key = self._get_openai_api_key()
            if not api_key:
                print('Missing OPENAI_API_KEY (environment or .env).')
                return

            # Launch background worker to call OpenAI API
            self.generate_btn.setEnabled(False)
            self.generate_btn.setText('Generating...')
            self._worker = OpenAIWorker(prompt=filled, api_key=api_key, model='gpt-4o', temperature=0.2)
            self._worker.finished.connect(self.on_llm_finished)
            self._worker.errored.connect(self.on_llm_error)
            self._worker.start()
        except Exception as e:
            print(e)

    def on_llm_finished(self, content: str):
        # Log raw LLM output for inspection
        try:
            print('\n=== LLM Raw Output Start ===\n')
            print(content)
            print('\n=== LLM Raw Output End ===\n')
        except Exception:
            pass
        # Parse returned content into logic and gui code if possible
        logic, gui = self._parse_generated(content)
        self.logic_edit.setPlainText(logic.strip())
        self.gui_edit.setPlainText(gui.strip())
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText('Generate')

    def on_llm_error(self, err: str):
        print(f'OpenAI error: {err}')
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText('Generate')

    def _parse_generated(self, text: str) -> tuple[str, str]:
        # Prefer template example tags if present
        try:
            nodes_match = re.search(r'^\[nodes\.py\]\s*$([\s\S]*?)(?=^\[gui\.py\]\s*$)', text, re.MULTILINE)
            gui_match = re.search(r'^\[gui\.py\]\s*$([\s\S]*)\Z', text, re.MULTILINE)
            if nodes_match and gui_match:
                return nodes_match.group(1).strip(), gui_match.group(1).strip()
        except Exception:
            pass

        # Heuristic split:
        # - Identify class definitions and GUI-oriented imports/decorators
        lines = text.splitlines(True)
        class_idxs = [i for i, ln in enumerate(lines) if re.match(r'^\s*class\s+\w+', ln)]
        gui_imp_idx = None
        for i, ln in enumerate(lines):
            if re.match(r'^\s*from\s+ryven\.gui_env\s+import\s+\*', ln):
                gui_imp_idx = i
                break
            if re.match(r'^\s*from\s+qtpy\.', ln):
                gui_imp_idx = i
                break
            if re.match(r'^\s*from\s+\.\s+import\s+nodes', ln):
                gui_imp_idx = i
                break
            if re.match(r'^\s*@node_gui\(', ln):
                gui_imp_idx = i
                break

        if class_idxs:
            if len(class_idxs) >= 2:
                # If we have a GUI import before the second class, prefer to split there
                if gui_imp_idx is not None and gui_imp_idx > class_idxs[0] and gui_imp_idx < class_idxs[1]:
                    split_at = gui_imp_idx
                else:
                    split_at = class_idxs[1]
                return ''.join(lines[:split_at]).strip(), ''.join(lines[split_at:]).strip()
            else:
                # Single class but GUI imports found later
                if gui_imp_idx is not None and gui_imp_idx > class_idxs[0]:
                    split_at = gui_imp_idx
                    return ''.join(lines[:split_at]).strip(), ''.join(lines[split_at:]).strip()

        # Fallback: naive split if a strong separator pattern exists
        parts = re.split(r'\n{3,}', text)
        if len(parts) >= 2:
            return parts[0], '\n\n'.join(parts[1:])
        return text, ''

    def _get_openai_api_key(self) -> str:
        key = os.environ.get('OPENAI_API_KEY')
        if key:
            return key
        # Fallback: try to read from a .env file upwards from this directory
        try:
            dir_path = os.path.dirname(os.path.abspath(__file__))
            for _ in range(6):
                env_path = os.path.join(dir_path, '.env')
                if os.path.isfile(env_path):
                    try:
                        with open(env_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith('#'):
                                    continue
                                if '=' in line:
                                    k, v = line.split('=', 1)
                                    k = k.strip()
                                    v = v.strip().strip('"\'')
                                    if k == 'OPENAI_API_KEY' and v:
                                        return v
                    except Exception:
                        pass
                parent = os.path.dirname(dir_path)
                if parent == dir_path:
                    break
                dir_path = parent
        except Exception:
            pass
        return ''

    def on_create_logic(self):
        try:
            code = self.logic_edit.toPlainText()
            if not code.strip():
                print('No logic code to create.')
                return
            err = insert_user_node_code(__file__, code)
            if err:
                print(err)
                return
            print('Logic code inserted into user_nodes/nodes.py')
        except Exception as e:
            print(e)

    def on_create_gui(self):
        try:
            code = self.gui_edit.toPlainText()
            if not code.strip():
                print('No GUI code to create.')
                return
            err = insert_user_gui_code(__file__, code)
            if err:
                print(err)
                return
            print('GUI code inserted into user_nodes/gui.py')
        except Exception as e:
            print(e)

@node_gui(nodes.PromptGeneratorNode)
class PromptGeneratorGui(NodeGUI):
    main_widget_class = PromptGenerator_MainWidget
    main_widget_pos = 'between ports'
    color = '#6a9bd8'

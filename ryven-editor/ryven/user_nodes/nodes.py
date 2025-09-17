from ryven.node_env import *
from random import random
import inspect

class RandNode(Node):
    title = 'Rand'
    tags = ['random', 'numbers']
    init_inputs = [NodeInputType()]
    init_outputs = [NodeOutputType()]

    # sets the node's output port value
    def update_event(self, inp=-1):
        self.set_output_val(0, Data(random() * self.input(0).payload))

class TextInputNode(Node):
    title = 'textInput'
    tags = ['text', 'input']
    init_outputs = [NodeOutputType()]

    def __init__(self, params):
        super().__init__(params)
        self.text = ''

    def set_text(self, value: str):
        self.text = value
        self.update()

    def update_event(self, inp=-1):
        self.set_output_val(0, Data(self.text))

# --- VIPP AUTO EXPORT MARKER ---

class CodePasteNode(Node):
    title = 'CodePaste'
    tags = ['dev', 'generator']
    init_outputs = []

    def __init__(self, params):
        super().__init__(params)

    def append_user_code(self, code_str: str):
        import os, ast
        if not code_str or not code_str.strip():
            return
        try:
            ast.parse(code_str)
        except Exception as e:
            print(f'Invalid user code: {e}')
            return
        file_path = os.path.abspath(__file__)
        marker = '# --- VIPP AUTO EXPORT MARKER ---'
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        insert_block = '\n\n# --- BEGIN USER NODE ---\n' + code_str + ('' if code_str.endswith('\n') else '\n') + '# --- END USER NODE ---\n'
        if marker in content:
            idx = content.find(marker)
            new_content = content[:idx] + insert_block + content[idx:]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(insert_block)

# auto-discover Node subclasses (so appended classes are exported too)
_node_types = []
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
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


### USER NODES BEGIN ###

class ConcatNode(Node):
    title = 'Concat'
    tags = ['text']
    init_inputs = [NodeInputType(), NodeInputType()]
    init_outputs = [NodeOutputType()]

    def update_event(self, inp=-1):
        a = self.input(0)
        b = self.input(1)
        a_val = '' if a is None or a.payload is None else a.payload
        b_val = '' if b is None or b.payload is None else b.payload
        self.set_output_val(0, Data(str(a_val) + str(b_val)))

### USER NODES END ###

class NodeGeneratorNode(Node):
    title = 'Node Generator'
    tags = ['dev', 'generator']
    init_outputs = []

    def __init__(self, params):
        super().__init__(params)

    def append_user_code(self, user_input_code: str):
        import os, ast

        # Checks if the user input code is valid else returns nothing
        if not user_input_code or not user_input_code.strip():
            return
        try:
            # Parses the user input code to check for valid python syntax
            ast.parse(user_input_code)
        except Exception as e:
            print(f'Invalid user code: {e}')
            return
        
        # Gets the file path of the current file
        file_path = os.path.abspath(__file__)

        # Gets the marker of the auto export marker to insert the user code at the correct position
        marker = '### USER NODES END ###'

        # Reads the content of the current file and stores it in file_contents
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
        
        # Creates the insert block of the user code
        user_node_code = user_input_code + ('' if user_input_code.endswith('\n') else '\n') + '\n'
        
        # Checks if the marker is in the file contents and inserts the user code at the correct position
        if marker in file_contents:
            idx = file_contents.find(marker)
            new_content = file_contents[:idx] + user_node_code + file_contents[idx:]

            # Writes the new content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            # Writes the user code to the file
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(user_node_code)

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
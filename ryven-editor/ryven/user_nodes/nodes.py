from ryven.node_env import *
import inspect

### USER NODES BEGIN ###

class MultiplyTextNode(Node):
    title = 'Multiply (Text)'
    tags = ['math']
    init_inputs = [NodeInputType()]
    init_outputs = [NodeOutputType()]

    def __init__(self, params):
        super().__init__(params)
        self.factor = 1.0

    def set_factor(self, text: str):
        try:
            self.factor = float(text)
        except Exception:
            pass
        self.update()

    def update_event(self, inp=-1):
        x_data = self.input(0)
        x = 0.0 if x_data is None or x_data.payload is None else float(x_data.payload)
        self.set_output_val(0, Data(self.factor * x))

### USER NODES END ###

class NodeGeneratorNode(Node):
    title = 'Node Generator'
    tags = ['dev', 'generator']
    init_outputs = []

    def __init__(self, params):
        super().__init__(params)

    def append_user_code(self, user_input_code: str, user_gui_code: str = ''):
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

        # Gets the marker to insert the user code at the correct position
        marker = '### USER NODES END ###'

        # Reads the content of the current file and stores it in file_contents
        with open(file_path, 'r', encoding='utf-8') as f:
            file_contents = f.read()
        
        # Creates the insert block of the user code
        user_node_code = user_input_code + ('' if user_input_code.endswith('\n') else '\n') + '\n'
        
        # Checks if the marker is in the file contents and inserts the user code at the correct position
        if marker in file_contents:
            idx = file_contents.find(marker)

            # Inserts the user code at the correct position
            new_content = file_contents[:idx] + user_node_code + file_contents[idx:]

            # Writes the new content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            # Writes the user code to the file
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(user_node_code)

        # Checks if the user GUI code is valid else returns nothing
        if user_gui_code and user_gui_code.strip():
            try:
                ast.parse(user_gui_code)
            except Exception as e:
                print(f'Invalid GUI code: {e}')
                return
            
            # Gets the file path of the GUI file
            gui_path = os.path.join(os.path.dirname(file_path), 'gui.py')
            gui_marker = '### USER GUIS END ###'

            # Reads the content of the GUI file and stores it in gui_contents
            try:
                with open(gui_path, 'r', encoding='utf-8') as gf:
                    gui_contents = gf.read()
            except FileNotFoundError:
                gui_contents = ''

            # Creates the insert block of the user GUI code
            gui_insert = user_gui_code + ('' if user_gui_code.endswith('\n') else '\n') + '\n'
            if gui_marker in gui_contents:
                idx = gui_contents.find(gui_marker)
                new_gui = gui_contents[:idx] + gui_insert + gui_contents[idx:]
                with open(gui_path, 'w', encoding='utf-8') as gf:
                    gf.write(new_gui)
            else:
                with open(gui_path, 'a', encoding='utf-8') as gf:
                    gf.write(gui_insert)

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
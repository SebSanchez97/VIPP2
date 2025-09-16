from ryven.node_env import *
from random import random

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

export_nodes([
    RandNode,
    TextInputNode
])

@on_gui_load
def load_gui():
    from . import gui
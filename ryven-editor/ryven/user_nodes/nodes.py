from ryven.node_env import *
from random import random

class RandNode(Node):
    title = 'Rand'
    tags = ['random', 'numbers']
    init_inputs = [NodeInputType()]
    init_outputs = [NodeOutputType()]

    def update_event(self, inp=-1):
        self.set_output_val(0, Data(random() * self.input(0).payload))

class PrintNode(Node):
    title = 'Print'
    init_inputs = [NodeInputType()]

    def update_event(self, inp=-1):
        print(self.input(0))

export_nodes([
    RandNode,
    PrintNode
])

@on_gui_load
def load_gui():
    from . import gui
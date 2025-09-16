from qtpy.QtWidgets import QSlider
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
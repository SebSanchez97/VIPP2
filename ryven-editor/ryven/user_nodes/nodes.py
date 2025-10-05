from ryven.node_env import *
import inspect

### USER NODES BEGIN ###
### USER NODES END ###

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

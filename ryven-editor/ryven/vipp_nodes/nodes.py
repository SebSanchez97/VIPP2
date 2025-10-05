from ryven.node_env import *
import inspect
import os

BACKUP_ON_DELETE = False


def _user_nodes_paths():
    # Resolve sibling package paths for user_nodes
    ryven_dir = os.path.dirname(os.path.dirname(__file__))
    user_pkg_dir = os.path.join(ryven_dir, 'user_nodes')
    nodes_path = os.path.join(user_pkg_dir, 'nodes.py')
    gui_path = os.path.join(user_pkg_dir, 'gui.py')
    return nodes_path, gui_path, user_pkg_dir


class NodeGeneratorNode(Node):
    title = 'Node Generator'
    tags = ['dev', 'generator']
    init_outputs = []

    def __init__(self, params):
        super().__init__(params)

    def append_user_code(self, user_input_code: str, user_gui_code: str = ''):
        import ast

        # Checks if the user input code is valid else returns
        if not user_input_code or not user_input_code.strip():
            return
        try:
            ast.parse(user_input_code)
        except Exception as e:
            print(f'Invalid user code: {e}')
            return

        # Paths into user_nodes package
        nodes_path, gui_path, _ = _user_nodes_paths()

        # Gets the marker to insert the user code at the correct position
        marker = '### USER NODES END ###'

        # Read nodes.py
        try:
            with open(nodes_path, 'r', encoding='utf-8') as f:
                file_contents = f.read()
        except FileNotFoundError:
            file_contents = ''

        # Creates the insert block of the user code
        user_node_code = user_input_code + ('' if user_input_code.endswith('\n') else '\n') + '\n'

        # Insert before marker when present, otherwise append
        if marker in file_contents:
            idx = file_contents.find(marker)
            new_content = file_contents[:idx] + user_node_code + file_contents[idx:]
            with open(nodes_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            with open(nodes_path, 'a', encoding='utf-8') as f:
                f.write(user_node_code)

        # Optional GUI code handling
        if user_gui_code and user_gui_code.strip():
            try:
                ast.parse(user_gui_code)
            except Exception as e:
                print(f'Invalid GUI code: {e}')
                return

            gui_marker = '### USER GUIS END ###'

            # Read gui.py
            try:
                with open(gui_path, 'r', encoding='utf-8') as gf:
                    gui_contents = gf.read()
            except FileNotFoundError:
                gui_contents = ''

            gui_insert = user_gui_code + ('' if user_gui_code.endswith('\n') else '\n') + '\n'
            if gui_marker in gui_contents:
                idx = gui_contents.find(gui_marker)
                new_gui = gui_contents[:idx] + gui_insert + gui_contents[idx:]
                with open(gui_path, 'w', encoding='utf-8') as gf:
                    gf.write(new_gui)
            else:
                with open(gui_path, 'a', encoding='utf-8') as gf:
                    gf.write(gui_insert)


class NodeDeletorNode(Node):
    title = 'Node Deletor'
    tags = ['dev', 'tools']
    init_outputs = []

    def __init__(self, params):
        super().__init__(params)

    def list_user_nodes(self):
        import ast

        nodes_path, _, _ = _user_nodes_paths()
        try:
            with open(nodes_path, 'r', encoding='utf-8') as f:
                src = f.read()
        except Exception:
            return []

        try:
            tree = ast.parse(src)
        except Exception:
            return []

        items = []
        protected = {'NodeGeneratorNode', 'NodeDeletorNode'}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # must look like a Node subclass by base name
                is_node_sub = any(
                    (isinstance(b, ast.Name) and b.id == 'Node') or
                    (isinstance(b, ast.Attribute) and b.attr == 'Node')
                    for b in node.bases
                )
                if not is_node_sub:
                    continue
                cls_name = node.name
                if cls_name in protected:
                    continue
                title_val = None
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for tgt in stmt.targets:
                            if isinstance(tgt, ast.Name) and tgt.id == 'title':
                                v = getattr(stmt, 'value', None)
                                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    title_val = v.value
                items.append({'class': cls_name, 'title': title_val})
        return items

    def delete_user_node(self, node_identifier: str):
        import ast, datetime, re

        protected = {'NodeGeneratorNode', 'NodeDeletorNode'}
        if not node_identifier or not node_identifier.strip():
            return
        target_name = node_identifier.strip()
        if target_name in protected:
            print(f'Cannot delete protected node: {target_name}')
            return

        # Paths
        nodes_path, gui_path, pkg_dir = _user_nodes_paths()

        # Backup (reads always; writes only if enabled)
        try:
            backups_dir = os.path.join(pkg_dir, '.backups')
            os.makedirs(backups_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(nodes_path, 'r', encoding='utf-8') as f:
                nodes_src = f.read()
            if BACKUP_ON_DELETE:
                with open(os.path.join(backups_dir, f'nodes.py.{ts}'), 'w', encoding='utf-8') as bf:
                    bf.write(nodes_src)
            try:
                with open(gui_path, 'r', encoding='utf-8') as gf:
                    gui_src = gf.read()
                if BACKUP_ON_DELETE:
                    with open(os.path.join(backups_dir, f'gui.py.{ts}'), 'w', encoding='utf-8') as gbf:
                        gbf.write(gui_src)
            except FileNotFoundError:
                gui_src = ''
        except Exception as e:
            print(f'Backup failed: {e}')
            return

        # Parse nodes.py and find class by class name or title
        try:
            nodes_tree = ast.parse(nodes_src)
        except Exception as e:
            print(f'Invalid nodes.py: {e}')
            return

        # Determine class names to delete
        class_defs = [n for n in nodes_tree.body if isinstance(n, ast.ClassDef)]
        target_classes = set()

        # 1) by class name
        for cls in class_defs:
            if cls.name == target_name:
                target_classes.add(cls.name)

        # 2) by title match if not found by class name
        if not target_classes:
            for cls in class_defs:
                for stmt in cls.body:
                    if isinstance(stmt, ast.Assign):
                        for tgt in stmt.targets:
                            if isinstance(tgt, ast.Name) and tgt.id == 'title':
                                v = getattr(stmt, 'value', None)
                                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                                    if v.value.strip() == target_name:
                                        target_classes.add(cls.name)

        if not target_classes:
            print(f'Node not found: {target_name}')
            return

        # Build deletion spans in nodes.py
        spans = []
        for cls in class_defs:
            if cls.name in target_classes and hasattr(cls, 'lineno') and hasattr(cls, 'end_lineno'):
                spans.append((cls.lineno, cls.end_lineno))

        if not spans:
            print('Could not compute deletion span(s) for nodes.py')
            return

        nodes_lines = nodes_src.splitlines()
        for start, end in sorted(spans, reverse=True):
            del nodes_lines[start - 1:end]
        try:
            with open(nodes_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(nodes_lines) + '\n')
        except Exception as e:
            print(f'Failed to write nodes.py: {e}')
            return

        # Remove associated GUI decorations/classes
        try:
            gui_tree = ast.parse(gui_src) if gui_src else None
        except Exception as e:
            print(f'Invalid gui.py: {e}')
            gui_tree = None

        if gui_tree is not None:
            gui_spans = []
            widget_class_names = set()

            for n in gui_tree.body:
                if isinstance(n, ast.ClassDef):
                    decorated_for_target = False
                    for dec in n.decorator_list:
                        if isinstance(dec, ast.Call):
                            func = dec.func
                            if isinstance(func, ast.Name) and func.id == 'node_gui' and len(dec.args) >= 1:
                                arg0 = dec.args[0]
                                if isinstance(arg0, ast.Attribute) and isinstance(arg0.value, ast.Name) and arg0.value.id == 'nodes':
                                    if arg0.attr in target_classes:
                                        decorated_for_target = True
                    if decorated_for_target and hasattr(n, 'lineno') and hasattr(n, 'end_lineno'):
                        gui_spans.append((n.lineno, n.end_lineno))
                        for stmt in n.body:
                            if isinstance(stmt, ast.Assign):
                                for tgt in stmt.targets:
                                    if isinstance(tgt, ast.Name) and tgt.id == 'main_widget_class':
                                        val = getattr(stmt, 'value', None)
                                        if isinstance(val, ast.Name):
                                            widget_class_names.add(val.id)

            # also remove widget classes
            for n in gui_tree.body:
                if isinstance(n, ast.ClassDef) and n.name in widget_class_names and hasattr(n, 'lineno') and hasattr(n, 'end_lineno'):
                    gui_spans.append((n.lineno, n.end_lineno))

            # Work on a single lines buffer and track changes
            gui_lines = gui_src.splitlines()
            changed = False

            # Remove class spans first
            if gui_spans:
                for start, end in sorted(gui_spans, reverse=True):
                    del gui_lines[start - 1:end]
                changed = True

            # Remove orphan decorator lines like: @node_gui(nodes.<ClassName>)
            # Build regexes for each target class
            if target_classes:
                patterns = [re.compile(r'^\s*@node_gui\(nodes\.' + re.escape(cls) + r'\)\s*$') for cls in target_classes]
                idxs_to_delete = []
                for i, line in enumerate(gui_lines):
                    if any(pat.match(line) for pat in patterns):
                        idxs_to_delete.append(i)
                        # also remove immediate following blank line for neatness
                        if i + 1 < len(gui_lines) and gui_lines[i + 1].strip() == '':
                            idxs_to_delete.append(i + 1)
                if idxs_to_delete:
                    for i in sorted(set(idxs_to_delete), reverse=True):
                        del gui_lines[i]
                    changed = True

            if changed:
                try:
                    with open(gui_path, 'w', encoding='utf-8') as gf:
                        gf.write('\n'.join(gui_lines) + '\n')
                except Exception as e:
                    print(f'Failed to write gui.py: {e}')
                    return


# Export nodes from this module for completeness
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



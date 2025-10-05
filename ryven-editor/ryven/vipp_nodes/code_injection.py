from __future__ import annotations

import ast
import os
from typing import Optional, Tuple


NODES_MARKER = '### USER NODES END ###'
GUIS_MARKER = '### USER GUIS END ###'


def get_user_nodes_paths(base_file: str) -> Tuple[str, str, str]:
    """Resolve paths for the `user_nodes` package relative to this package."""
    ryven_dir = os.path.dirname(os.path.dirname(base_file))
    user_pkg_dir = os.path.join(ryven_dir, 'user_nodes')
    return (
        os.path.join(user_pkg_dir, 'nodes.py'),
        os.path.join(user_pkg_dir, 'gui.py'),
        user_pkg_dir,
    )


def validate_python(code: str) -> Optional[str]:
    """Return None if valid python, otherwise an error string."""
    if not code or not code.strip():
        return "Empty code"
    try:
        ast.parse(code)
        return None
    except Exception as e:
        return f"{e}"


def prepare_block(code: str) -> str:
    """Ensure a trailing newline and an extra separator line for cleanliness."""
    return code + ('' if code.endswith('\n') else '\n') + '\n'


def read_text(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def write_text(path: str, content: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def append_text(path: str, content: str) -> None:
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content)


def insert_before_marker(path: str, marker: str, block: str) -> None:
    contents = read_text(path)
    if marker in contents:
        idx = contents.find(marker)
        write_text(path, contents[:idx] + block + contents[idx:])
    else:
        append_text(path, block)


def insert_user_node_code(base_file: str, code: str) -> Optional[str]:
    err = validate_python(code)
    if err:
        return f"Invalid user code: {err}"
    nodes_path, _, _ = get_user_nodes_paths(base_file)
    insert_before_marker(nodes_path, NODES_MARKER, prepare_block(code))
    return None


def insert_user_gui_code(base_file: str, code: str) -> Optional[str]:
    err = validate_python(code)
    if err:
        return f"Invalid GUI code: {err}"
    _, gui_path, _ = get_user_nodes_paths(base_file)
    insert_before_marker(gui_path, GUIS_MARKER, prepare_block(code))
    return None

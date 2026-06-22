# Shared dogtail / AT-SPI helpers for GUI tests across the suite.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Extracted from Tables' working test_tables.py and Decks' test_decks.py.
# All actions use AT-SPI (doActionNamed); no X mouse synthesis — so they
# work headlessly on Wayland.  See TESTING-SPEC.md §4 for rationale and
# hard limits.

import time

import pyatspi   # noqa: E402
from dogtail import tree  # noqa: E402


# ── Node-level actions ────────────────────────────────────────────────

def click(node):
    """Activate a node via its AT-SPI action (no X mouse synthesis)."""
    for action in ('click', 'activate', 'press'):
        try:
            node.doActionNamed(action)
            return
        except Exception:
            continue
    raise AssertionError(f'no clickable action on {node}')


def pressed(node):
    """Check whether a GTK4 toggle button is currently pressed.

    GTK4 toggles expose STATE_PRESSED, *not* the older STATE_CHECKED.
    """
    return pyatspi.STATE_PRESSED in node.getState().getStates()


# ── Application helpers ────────────────────────────────────────────────

def find_app(name, settle_s=8.0):
    """Resolve an AT-SPI application node, waiting for the a11y tree to
    populate (the GTK4 a11y tree appears lazily once an AT client connects).

    Args:
        name:    Flatpak app-id fragment (e.g. 'tables', 'decks').
        settle_s: Seconds to wait for the a11y tree to settle.

    Returns:
        dogtail.tree.Node for the application root.
    """
    time.sleep(settle_s)
    return tree.root.application(name)


# ── Tree inspection ────────────────────────────────────────────────────

def count_nodes(root):
    """Count total descendants of an AT-SPI node (recursive)."""
    total = 1
    try:
        for child in root.children:
            total += count_nodes(child)
    except Exception:
        pass
    return total


# ── Widget discovery ───────────────────────────────────────────────────

def find_widget(root, name=None, role=None, showing_only=True):
    """Recursively search for a widget by accessible name and/or AT-SPI role.

    Unlike dogtail's ``child()``, this traverses the full subtree, which is
    necessary when widgets are nested inside AdwToolbarView top-bar boxes
    that dogtail may not search deeply enough to reach.

    Args:
        root:        Starting node (application or window).
        name:        Accessible name to match (None = any name).
        role:        AT-SPI role name to match (None = any role).
        showing_only: If True, skip invisible nodes.

    Returns:
        The first matching node, or None.
    """
    try:
        if showing_only and not root.getState().contains(pyatspi.STATE_SHOWING):
            return None
        name_ok = name is None or root.name == name
        role_ok = role is None or root.getRoleName() == role
        if name_ok and role_ok:
            return root
        for child in root.children:
            found = find_widget(child, name, role, showing_only)
            if found is not None:
                return found
    except Exception:
        pass
    return None


def dump_tree(root, indent=0, max_depth=4):
    """Print the accessible tree for debugging (role + name)."""
    if indent > max_depth:
        return
    try:
        role = root.getRoleName()
        name = root.name
        print(f'{"  " * indent}[{role}] {name}')
        for child in root.children:
            dump_tree(child, indent + 1, max_depth)
    except Exception:
        pass


# ── Assertion helpers ──────────────────────────────────────────────────

def toggle_and_assert(node):
    """Click a toggle button and assert its state flips from unpressed
    to pressed."""
    assert not pressed(node), f'{node.name} should start unpressed'
    click(node)
    time.sleep(0.6)
    assert pressed(node), f'{node.name} should be pressed after AT-SPI click'

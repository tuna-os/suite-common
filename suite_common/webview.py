# webview.py — shared WebKit canvas + Python<->JS bridge for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Ported from Letters' window.py (new_webview ~L287, run_js ~L376): an offline,
# sandboxed WebKit.WebView whose JS engine talks to Python over a
# UserContentManager script-message channel. See SPEC.md.

import gi
import json

gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, WebKit, GLib  # noqa: E402


class SuiteWebView(WebKit.WebView):
    """A WebView wired for two-way messaging with its JS engine.

    - JS -> Python: ``window.webkit.messageHandlers.<channel>.postMessage(obj)``
      arrives at ``on_message(payload_dict)``.
    - Python -> JS: ``send(name, data)`` calls ``window.bridgeReceive(name, data)``.
    - JS ``console.log`` is forwarded to stdout so headless builds can be verified.
    """

    def __init__(self, on_message=None, channel='bridge'):
        super().__init__()
        self._on_message = on_message
        self._channel = channel

        settings = self.get_settings()
        settings.set_enable_developer_extras(True)
        # Forward JS console to stdout — lets `flatpak run` logs prove the engine
        # loaded (and surface JS errors) without a visible window.
        try:
            settings.set_enable_write_console_messages_to_stdout(True)
        except Exception:
            pass

        ucm = self.get_user_content_manager()
        ucm.register_script_message_handler(channel)
        ucm.connect(f'script-message-received::{channel}', self._on_script_message)

    def _on_script_message(self, ucm, value):
        try:
            payload = json.loads(value.to_json(0))
        except Exception:
            payload = {'type': 'raw', 'value': value.to_string()}
        if self._on_message is not None:
            self._on_message(payload)

    def run_js(self, code):
        self.evaluate_javascript(code, -1, None, None, None, None, None)

    def send(self, name, data):
        """Invoke window.bridgeReceive(name, data) in the page."""
        payload = json.dumps(data)
        self.run_js(f'window.bridgeReceive && window.bridgeReceive({json.dumps(name)}, {payload});')

    def load_app(self, html):
        """Load a self-contained HTML document (CSS/JS already inlined)."""
        self.load_html(html, None)


def build_document(vendor_dir, assets, body, head_extra=''):
    """Assemble a self-contained HTML doc by inlining vendored CSS/JS.

    ``assets`` is an ordered list of (kind, filename) where kind is 'css' or 'js';
    files are read from ``vendor_dir`` (the installed pkgdatadir/vendor). Inlining
    keeps the webview fully offline with no resource-URI plumbing.
    """
    import os

    parts = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
             '<style>html,body{margin:0;padding:0;height:100%;'
             'font-family:system-ui,sans-serif;}</style>']
    for kind, name in assets:
        path = os.path.join(vendor_dir, name)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
        except OSError as exc:
            parts.append(f'<!-- missing {kind} {name}: {exc} -->')
            continue
        if kind == 'css':
            parts.append(f'<style>{content}</style>')
        else:
            parts.append(f'<script>{content}</script>')
    parts.append(head_extra)
    parts.append('</head><body>')
    parts.append(body)
    parts.append('</body></html>')
    return ''.join(parts)

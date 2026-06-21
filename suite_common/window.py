# window.py — shared Adw.ApplicationWindow base for the suite.
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw  # noqa: E402


class SuiteWindow(Adw.ApplicationWindow):
    """Shared window shell: ToolbarView + HeaderBar + TabView.

    Mirrors Letters' window architecture (Adw.ApplicationWindow + Adw.ToolbarView
    + Adw.HeaderBar + Adw.TabView). Apps subclass and fill tabs with their engine
    webview. The WebKit bridge lands in suite-common #2.
    """

    def __init__(self, app_name='App', **kwargs):
        super().__init__(**kwargs)
        self.set_title(app_name)
        self.set_default_size(1000, 700)

        self.toolbar_view = Adw.ToolbarView()

        self.header_bar = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header_bar)

        # Primary menu (about / quit) — shared chrome.
        menu_button = Gtk.MenuButton(icon_name='open-menu-symbolic',
                                     menu_model=self._build_menu())
        self.header_bar.pack_end(menu_button)

        self.tab_view = Adw.TabView()
        self.tab_bar = Adw.TabBar(view=self.tab_view)
        self.toolbar_view.add_top_bar(self.tab_bar)
        self.toolbar_view.set_content(self.tab_view)

        self.set_content(self.toolbar_view)

    def _build_menu(self):
        menu = Gio.Menu()
        menu.append('About', 'app.about')
        menu.append('Quit', 'app.quit')
        return menu

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

    def __init__(self, app_name='App', use_tabs=True, **kwargs):
        super().__init__(**kwargs)
        self.set_title(app_name)
        self.set_default_size(1000, 700)

        self.toolbar_view = Adw.ToolbarView()

        self.header_bar = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header_bar)

        # Primary menu (about / quit) — shared chrome.
        menu_button = Gtk.MenuButton(icon_name='open-menu-symbolic',
                                     menu_model=self._build_menu())
        menu_button.set_tooltip_text('Main Menu')
        menu_button.update_property([Gtk.AccessibleProperty.LABEL], ['Main Menu'])
        self.header_bar.pack_end(menu_button)

        # Apps that want a document-per-tab UI (Tables, Letters) get a TabView;
        # apps with a custom layout (Decks' slide sidebar) pass use_tabs=False
        # and call set_main_content().
        if use_tabs:
            self.tab_view = Adw.TabView()
            self.tab_bar = Adw.TabBar(view=self.tab_view)
            self.toolbar_view.add_top_bar(self.tab_bar)
            self.toolbar_view.set_content(self.tab_view)

        # Toast overlay wraps everything so any app can surface transient messages.
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.toolbar_view)
        self.set_content(self.toast_overlay)

    def set_main_content(self, widget):
        self.toolbar_view.set_content(widget)

    def toast(self, text, timeout=3):
        """Show a transient libadwaita toast."""
        self.toast_overlay.add_toast(Adw.Toast(title=text, timeout=timeout))

    def _build_menu(self):
        menu = Gio.Menu()
        menu.append('Preferences', 'app.preferences')
        menu.append('Keyboard Shortcuts', 'app.shortcuts')
        menu.append('About', 'app.about')
        menu.append('Quit', 'app.quit')
        return menu

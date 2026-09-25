# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys
import unittest
import tempfile
import json

from suite_common import shortcuts_presets, fileio_base


class TestShortcutsPresets(unittest.TestCase):
    def test_presets_structure(self):
        self.assertIn('google-docs', shortcuts_presets.PRESETS)
        self.assertIn('microsoft-word', shortcuts_presets.PRESETS)
        self.assertIn('macos', shortcuts_presets.PRESETS)
        self.assertIn('libreoffice', shortcuts_presets.PRESETS)

        for key, labels in shortcuts_presets.PRESET_LABELS.items():
            self.assertIn(key, shortcuts_presets.PRESETS)

    def test_build_shortcuts_display(self):
        display_default = shortcuts_presets.build_shortcuts_display()
        self.assertIn('File', display_default)
        self.assertIn('Edit', display_default)
        self.assertIn('View', display_default)

        display_word = shortcuts_presets.build_shortcuts_display('microsoft-word')
        file_items = display_word['File']
        save_as_accel = next(accel for accel, label in file_items if label == 'Save As')
        self.assertEqual(save_as_accel, 'F12')

        display_unknown = shortcuts_presets.build_shortcuts_display('unknown-preset')
        self.assertEqual(display_unknown, display_default)

    def test_load_and_save_preset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_base = shortcuts_presets._CONFIG_BASE
            shortcuts_presets._CONFIG_BASE = tmpdir
            try:
                app_id = 'test-app'
                self.assertEqual(shortcuts_presets.load_preset(app_id), shortcuts_presets.DEFAULT_PRESET)

                shortcuts_presets.save_preset(app_id, 'microsoft-word')
                self.assertEqual(shortcuts_presets.load_preset(app_id), 'microsoft-word')

                # Test corrupt file fallback
                path = shortcuts_presets._config_path(app_id)
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write("invalid json")
                self.assertEqual(shortcuts_presets.load_preset(app_id), shortcuts_presets.DEFAULT_PRESET)
            finally:
                shortcuts_presets._CONFIG_BASE = orig_base


class TestFileIOBase(unittest.TestCase):
    def test_format_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test.txt')
            fileio_base.write(filepath, ['line1', 'line2'])
            content = fileio_base.read(filepath)
            self.assertEqual(content, ['line1', 'line2'])

            patterns = fileio_base.patterns()
            self.assertIn('*.txt', patterns)

    def test_unregistered_extension(self):
        with self.assertRaises(ValueError):
            fileio_base.read('unknown.xyz')

        with self.assertRaises(ValueError):
            fileio_base.write('unknown.xyz', [])


if __name__ == '__main__':
    unittest.main()

project('suite-common',
  version: '0.1.0',
  meson_version: '>= 1.0.0',
)

# suite-common is consumed as a meson subproject. It exposes the list of shared
# Python source files; the parent app installs them into its module path so they
# import as the `suite_common` package. See SPEC.md.
suite_common_sources = files(
  'suite_common/__init__.py',
  'suite_common/application.py',
  'suite_common/window.py',
  'suite_common/webview.py',
  'suite_common/dialogs.py',
)

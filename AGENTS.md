# AGENTS.md — agent guide for tuna-os/suite-common

A shared **Python/GTK4 scaffold** — `SuiteApplication`, `SuiteWindow`, a WebKit
bridge, file-I/O base classes, dogtail helpers and LibreOffice oracle wrappers
— designed to be consumed as a [meson
subproject](https://mesonbuild.com/Subprojects.html).

Human docs: [`README.md`](README.md), [`SPEC.md`](SPEC.md) (architecture
rationale), [`TESTING-SPEC.md`](TESTING-SPEC.md), [`HANDOFF.md`](HANDOFF.md).

## Read this before doing any work here

**Nothing in the org currently consumes this library.** README names Letters,
Tables and Decks; `ci.yml` records that Tables and Decks "have since been
folded into `tuna-os/gtk-office-suite` as workspace members", and that repo is
a **Rust** workspace with its own, unrelated `suite-common/` and
`suite-common-core/` crates — it has no `subprojects/` directory and no meson
build at all. Its README even warns about the three-way name collision.

So a change here does not reach any shipping app today, and the README's
consumer table describes an arrangement that no longer exists. Before
investing effort, get the maintainer's decision on whether this repo is being
revived, re-pointed at a new consumer, or archived (the same question applies
to `tuna-os/suite-common-rust`). Do not "fix" the README's links to make them
resolve — that would document a dependency that isn't there.

## The exported source list is narrower than the README

`meson.build` exposes exactly five files to consumers:

```python
suite_common_sources = files(
  'suite_common/__init__.py', 'suite_common/application.py',
  'suite_common/window.py',   'suite_common/webview.py',
  'suite_common/dialogs.py',
)
```

`fileio_base.py`, `test_helpers.py` and `oracles.py` are **not** in it, even
though the README's module table lists all eight. A consumer installing
`suite_common_sources` and then importing `suite_common.fileio_base` gets an
ImportError. If that omission is deliberate — test helpers and oracles are
plausibly test-only — `fileio_base` still looks like an oversight, since it is
production scaffolding with its own test. Either way, `meson.build` is the
contract and the README is the description; they disagree.

## "Lint" does not lint

```bash
just check    # python3 -m compileall suite_common
just lint     # python3 -m compileall -q suite_common  — the same thing
python3 tests/test_fileio.py
```

`just lint` is byte-compilation with `-q`. There is no linter configured — no
ruff, no flake8, no pyproject.toml — so "lint passes" means only "it parses".
CI runs the same two commands and nothing else, and `tests/` contains exactly
one test file. Treat a green tick here as a syntax check.

## Fixtures are MPL-2.0

`tests/fixtures/` comes from LibreOffice's `qa/` suite under MPL-2.0, while
this repo is GPL-3.0-or-later. `tests/fixtures/PROVENANCE.md` records where
each file came from — keep it accurate when adding fixtures, and do not
relicense them.

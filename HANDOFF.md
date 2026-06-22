# Handoff — GNOME Office Suite (Letters / Tables / Decks)

_Last updated: 2026-06-22. Maintainer agent: Claude (Opus 4.8)._

## Goal
A FOSS GNOME/libadwaita office suite completing Letters (word processor) with **Tables**
(spreadsheet, Excel-equivalent) and **Decks** (presentation, PowerPoint-equivalent).
Pattern (from Letters): pure libadwaita chrome wrapping a `WebKit.WebView` engine, with
in-process Python libs for file I/O. Best-of-breed engines per app. Shared code in
`suite-common` (meson subproject). Letters migrates onto suite-common too.

## Repos (all under github.com/hanthor)
- **suite-common** — shared scaffold. Has SPEC.md + (this session) minimal `suite_common`
  Python package (`SuiteApplication`, `SuiteWindow`). 5 issues.
- **tables** — spreadsheet. SPEC.md + (this session) buildable blank-window scaffold +
  justfile + Flatpak manifest. 10 issues. Engines: Jspreadsheet CE (MIT) + HyperFormula
  (GPLv3); I/O: openpyxl/python-calamine/odfpy.
- **decks** — presentation. SPEC.md only so far. 11 issues. Engines: Fabric.js + Reveal.js
  (MIT); I/O: python-pptx/odfpy.
- **letters** — existing fork (upstream codeberg.org/eyekay/letters). 5 migration issues
  to adopt suite-common. Local checkout: /home/james/dev/letters.

## Engine/license decisions (locked with user)
- Best-of-breed per app (NOT unified Univer). Two separate apps sharing suite-common.
- File I/O = in-process Python libs (the pypandoc model), no server.
- HyperFormula GPLv3 is fine (Letters/suite are GPL-3.0-or-later). Others MIT.
- App IDs: `io.github.hanthor.tables`, `io.github.hanthor.decks` (Flathub GitHub convention).

## Build infra
- Build host: SSH `himachal` (x86_64, tuna-os workstation). 533G free at ~.
- Toolchain there: `just`, `flatpak`, `git`, GNOME Platform/Sdk **50**, **org.flatpak.Builder**
  (flatpak). NO system flatpak-builder — use `flatpak run org.flatpak.Builder`.
- GitHub push works from himachal as hanthor (SSH).
- Pattern: `just setup` (clone suite-common into subprojects/), `just build` (org.flatpak.Builder
  --user --install), `just run` / `just smoke`. Build artifacts kept in ~/.cache/tables-flatpak
  so the manifest's `type: dir` source only copies sources.

## ⚠️ Environment gotchas
- **Local dev box (rpi) root disk is 100% FULL** — cannot write app trees locally except
  /tmp (tmpfs). All scaffold files staged in /tmp/work, pushed via git from himachal.
- /tmp files have vanished once unexpectedly — verify after writing.
- Running GUI flatpak over SSH needs the session's WAYLAND_DISPLAY/XDG_RUNTIME_DIR.

## First tracer bullet (this session)
Tables = blank libadwaita window (ToolbarView + HeaderBar + TabView + StatusPage),
pure-Python UI (no Blueprint/gresource yet) consuming `suite_common`. Goal: prove the
himachal flatpak build+run pipeline. UI built in code to minimize first-build risk.

## Status / next steps
- [x] Push suite-common code → hanthor/suite-common
- [x] Push tables code → hanthor/tables
- [x] `just build` tables on himachal — **GREEN** (installs app/io.github.hanthor.tables/x86_64/master)
- [x] `just run`/smoke on himachal Wayland (wayland-0) — **app presents window, no errors** (tables #1 done)
- [ ] tables #2 (embed Jspreadsheet CE webview) — first WebKit slice
- [ ] decks scaffold mirroring tables
- [ ] suite-common #2 WebKit bridge (port from Letters window.py new_webview/run_js)

### Issue progress (goal: implement+build+test all open issues)
- CLOSED (verified on himachal): suite-common #1-#5 (all); tables #1-#6, #8, #9, #10;
  decks #1-#11 (all).  (25 issues)
- Test recipes per repo: tables `just verify|csvtest|fmttest|multitest`;
  decks `just verify|slidetest|presenttest|decktest|pdftest`; letters `just verify`.
- REMAINING: tables #7 (cell formatting round-trip — Jspreadsheet getData doesn't expose
  styles; needs getStyle+openpyxl style mapping); letters #1 epic, #3 (bridge), #4 (chrome),
  #5 (file-IO) — deeper behaviour-preserving refactors of Letters' integrated editor.
- letters #2 (subproject): DONE — suite-common is a meson subproject, importable, Letters
  builds + launches on himachal. Bonus: fixed 3 pre-existing Letters build/runtime bugs
  (stale weasyprint wheel 404 → network pip; window.blp breakpoint `setters:` + `styles[];`
  syntax drift; WebKit 6.0 `set_enable_spell_checking` removed → guarded).

### Hard-won gotchas (all in justfiles now)
- App is single-instance (Gio.Application): `flatpak kill <id>` before each headless run,
  else a stale instance is just *activated* and your --env (selftest) is ignored → empty log.
- Need the session display: `XDG_RUNTIME_DIR=/run/user/$(id -u) WAYLAND_DISPLAY=wayland-0`.
- Python stdout is buffered → use `--env=PYTHONUNBUFFERED=1` and `flush=True` for bridge asserts.
- INCREMENTAL RSYNC BUG: `rsync src/x himachal:.../app/` flattens to `app/x`. ALWAYS
  `rsync -az --delete /tmp/work/ himachal:~/dev/suite-work/` (whole tree) then `cp -a .../src/. src/`.
- pip libs in flatpak: python3-deps module with `build-options.build-args:["--share=network"]`
  (himachal pipeline). For Flathub → vendored wheels.

### Verified build recipe (himachal)
- Project MUST live under `$HOME` (flatpaks get a private /tmp). Working copy: `~/dev/tables`.
- `just build` = `flatpak run --cwd="$PWD" --filesystem=host org.flatpak.Builder --force-clean
  --user --install --install-deps-from=flathub --state-dir=... --repo=... <build> <manifest>`.
- Run over SSH: `XDG_RUNTIME_DIR=/run/user/$(id -u) WAYLAND_DISPLAY=wayland-0 flatpak run io.github.hanthor.tables`.
- Manifest source is `type: dir path: .`; build artifacts kept in `~/.cache/tables-flatpak` so
  only sources get copied. suite-common comes in via `just setup` (git clone into subprojects/).

## Key source refs
- Letters meson/launcher pattern: /home/james/dev/letters/src/{meson.build,letters.in,main.py,window.py}
- Letters WebKit bridge to port: src/window.py ~L287 new_webview(), ~L376 run_js(), ~L316 pypandoc.
- Plan file: /home/james/.claude/plans/partitioned-meandering-raven.md

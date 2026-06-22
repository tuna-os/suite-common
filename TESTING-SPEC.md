# Comprehensive Test Suite — Specification

Status: proposed. Applies to the suite (suite-common, Tables, Decks; Letters where it
consumes suite-common). Build/run host: `himachal` (Flatpak via org.flatpak.Builder).

## 0. The question this answers

> "A known file as input, do specified actions through the GUI, then read the output with
> an independent library so we know we're editing correctly. Does that make sense? Is that
> the point of weakness, or should we test something else?"

**Yes — it makes sense, and it targets the right weakness.** But it should be the *top*
layer of a pyramid, not the whole suite, because GUI tests are slow and flaky.

### Where the bugs actually live (the stack, by risk)
| Layer | Tech | Who wrote it | Bug risk |
|---|---|---|---|
| Chrome | GTK4 / libadwaita | us (thin) | low |
| **Editing surface** | Jspreadsheet / Fabric (JS) | third-party | low–med (our *integration* is the risk) |
| **Python↔JS bridge** | custom JSON over script-message | **us** | **high** — untyped, easy to drift |
| **Format adapters** | CSS↔openpyxl, EMU↔canvas, etc. | **us** | **high** — fiddly conversions |
| File libs | openpyxl/calamine/odfpy/python-pptx | third-party | low — assume correct |

**The weak points are the bridge and the format-mapping code — not the file libraries.**
So: don't spend tests re-proving openpyxl works; spend them proving *our glue* turns a user
action into the correct bytes on disk. The proposed input→GUI→output test exercises the
whole glue chain at once, which is exactly why it's valuable.

## 1. Test pyramid

### Layer 1 — Adapter round-trips (many, fast, no display)
Pure-Python tests of `fileio` / `fileio_base`: write with one library, read back with a
**different** library, assert equality. Independence matters (don't verify with the writer).
- Tables: csv↔xlsx↔ods values; cell styles (bold/italic/underline/align) via openpyxl write
  → calamine/openpyxl read; multi-sheet.
- Decks: pptx/odp text + image + slide-count via python-pptx/odfpy.
- *Already implemented* as the `*test` self-test hooks; promote to standalone pytest modules.

### Layer 2 — Bridge round-trips (some, headless Flatpak)
Inject a model → JS engine → extract model, asserting the bridge + engine preserve it.
- Tables: load rows+styles → `getData` → identical; `=SUM` recalcs.
- Decks: load slide JSON → `getSlide` → identical; render-all returns N images.
- *Already implemented* via `TABLES_SELFTEST`/`DECKS_*` env hooks.

### Layer 3 — Golden-file end-to-end (few, real session, dogtail) — **the proposed suite**
Known fixture → drive the real GUI → save → verify with an **independent oracle**.
This is the only layer that proves "clicking Bold actually bolds the cell in the file."

## 2. The independent oracle

For office formats the gold standard is **LibreOffice headless** — a different codebase and
the de-facto reference implementation:
```
soffice --headless --convert-to csv  out.xlsx     # → out.csv, assert values
soffice --headless --convert-to fodp out.pptx     # → flat XML, grep for text
```
Cross-check styles/structure with a second reader (openpyxl / python-pptx) for richer
assertions (bold flags, shape positions) that csv can't express. Using LibreOffice avoids
the trap of "verifying our openpyxl output with openpyxl."

## 3. Golden-file E2E cases (initial set)

Fixtures live in `tests/fixtures/`. Each case: **load fixture → GUI action(s) → save → oracle assert.**

**Tables**
1. `numbers.xlsx` → select A1 → click **Bold** → save → openpyxl: `A1.font.bold is True`;
   LibreOffice→csv: values unchanged.
2. `numbers.xlsx` → click **Align Center** on B2 → save → openpyxl: `B2.alignment.horizontal=='center'`.
3. `two-sheets.xlsx` → switch sheet via the **sheet dropdown** → edit → save → both sheets present (openpyxl).
4. `data.csv` → save as `.xlsx` → LibreOffice→csv round-trips the values.

**Decks**
1. `one-slide.pptx` → click **Add Text Box** → save → python-pptx: a text frame exists;
   LibreOffice→fodp: contains the text.
2. `deck.pptx` → **Add slide** (sidebar) → save → python-pptx: slide count +1.
3. `deck.pptx` → **Export to PDF** → assert valid `%PDF`, page count == slide count.

## 4. Driving the GUI (dogtail) — patterns & hard limits

**Patterns (proven on himachal):**
- Use **AT-SPI actions** (`node.doActionNamed('click')`), never mouse synthesis — there is no
  X display on Wayland (`.click()` → "Bad display name").
- GTK4 toggle buttons expose **`STATE_PRESSED`**, not `STATE_CHECKED` — assert with pyatspi.
- Allow **~8s settle**; the GTK4 a11y tree populates lazily once an AT client connects.
- Give every interactive widget an explicit `Gtk.AccessibleProperty.LABEL` (done across the suite).

**Hard limits / design implications:**
- **Responsive breakpoints drop collapsed subtrees from the a11y tree.** Widgets in the
  `extended` box vanish when narrow. Either drive the window wide first, or target
  always-visible widgets, or assert via the `more` menu.
- **AdwHeaderBar plain buttons don't always surface** to AT-SPI; the action-toolbar and menu
  buttons do. Prefer those for assertions, or add explicit labels and verify per-widget.
- **Editing *inside* the WebKit canvas is not directly drivable.** Cells/objects are bridged
  read-only-ish (the grid exposes 500+ nodes, but typing into cell B2 via AT-SPI EditableText
  is unreliable, and keyboard synthesis is limited on Wayland). **Implication:** drive *value*
  setup through a fixture/load (or a thin test hook), and drive the *chrome editing actions*
  (Bold, align, add-slide, add-shape, sheet-switch) through the real GUI — those are the
  weak-point wiring. Don't try to type cell contents through dogtail.
- **File dialogs are flaky to drive.** For save/open paths, prefer a test-mode hook
  (`TABLES_SELFTEST=in:out`, etc.) over driving `GtkFileDialog`. The action under test is the
  edit, not the dialog.

## 4b. Reuse existing corpora & validators ("pro-level" without authoring everything)

Don't hand-author thousands of fixtures — borrow battle-tested ones and standards validators:

- **LibreOffice `qa/` test documents** (MPL-2.0): the LibreOffice tree ships large corpora of
  real-world round-trip test files — `sc/qa/unit/data/{xlsx,ods,…}` (spreadsheets),
  `sd/qa/unit/data/{pptx,odp,…}` (presentations). Vendor a *curated subset* as `tests/fixtures/`
  (keep the MPL-2.0 notice). Many come with LibreOffice's own expected values in its C++ tests,
  which we can translate into oracle assertions.
- **LibreOffice headless** as the conversion oracle (§2) — the reference implementation.
- **openxml-audit** (PyPI, pure Python): validates OOXML (xlsx/pptx/docx) *and* ODF with staged
  conformance levels — a second, independent structural validator to run on our output.
- **Office-o-tron**: the OOXML/ODF schema validator LibreOffice itself uses for conformance.
- **ODF OpenFormula test suite** (ODF 1.2 spreadsheet-formula conformance): a standards-based
  corpus to validate the formula engine (HyperFormula / Jspreadsheet) against expected results.
- **Upstream library fixtures**: python-pptx and openpyxl ship sample documents and known-good
  expectations we can import directly.

This yields three independent oracles (LibreOffice conversion, openxml-audit/Office-o-tron
validation, and standards formula vectors) over real documents — which is what makes the suite
"pro-level" rather than a few toy fixtures.

## 5. What NOT to test (low ROI)
- Third-party libraries (openpyxl, LibreOffice, Jspreadsheet, Fabric) — assume correct.
- Pixel/visual rendering of cells/slides — brittle; only add targeted image-diffs if a
  rendering regression is actually reported.
- Every format permutation through the GUI — exhaustively cover formats at Layer 1; the GUI
  layer needs only a few representative flows.

## 6. Execution & CI
- **Layer 1**: plain `pytest`, no display — runs in GitHub Actions today (suite-common CI model).
- **Layer 2**: headless Flatpak; needs a nested compositor (`weston --headless` / `mutter
  --headless`) + at-spi in CI, or runs on himachal.
- **Layer 3 (dogtail)**: real session — `just guitest` on himachal now; schedule nightly.
  Mitigate flakiness with generous waits, AT-SPI actions, retries, and a fresh `flatpak kill`
  before each run (the app is single-instance).

## 7. Layout
```
tests/
  fixtures/        known input files (numbers.xlsx, deck.pptx, …)
  unit/            Layer 1 — adapter round-trips (pytest)
  integration/    Layer 2 — bridge self-tests
  gui/             Layer 3 — dogtail golden-file E2E (test_tables.py, test_decks.py)
```

## 8. Recommendation
Build it — but as the **thin top** of the pyramid. Concentrate assertions on the **bridge and
format adapters** (where our bugs are), use **LibreOffice headless as the independent oracle**,
drive **chrome editing actions** through dogtail while loading data via fixtures/hooks, and
keep Layer-1 round-trips as the fast safety net. The current `just guitest` (Tables/Decks) and
the `*test` self-test recipes are the first concrete pieces of Layers 3 and 1–2.

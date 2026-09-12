# EVE wormhole bookmark helper

Planning baseline: 2026-09-12. The initial Python application, parser, formatter,
and automated checks are implemented. Native Wayland startup has been verified;
the EVE clipboard round trip still needs an in-game check. See the
[README](../README.md) for current startup instructions and verification status.

## Goal and chosen stack

Build a small, standalone Linux application that turns pasted EVE Online wormhole
information into a bookmark name. The user copies information in EVE, moves to the
floating helper, pastes, and receives a formatted name on the clipboard to paste
back into the game.

Use Python with PySide6 and Qt Widgets. This keeps text parsing, ordinary desktop
controls, and clipboard access in one process. Godot with GDScript remains a viable
alternative, but the first version will use Python throughout.

- Use **uv** to manage the Python interpreter, environment, dependencies, and lockfile.
- Use **Ruff** for linting, import sorting, and formatting.
- Use **pytest** for parser, formatter, and application-state tests.
- Keep the first version local and offline during normal use.

Qt provides the normal copy/paste clipboard through
[`QClipboard`](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html).
No separate clipboard package is needed.

## Intended workflow

1. Open the helper beside or over EVE.
2. Copy the wormhole's information in EVE.
3. Move to the helper and paste into its large input area.
4. The app extracts available fields and shows what is still missing.
5. Paste a scan signature or fill in the remaining fields for this wormhole.
6. Once the record is complete, the app automatically copies the bookmark name and
   shows `Copied` beside the preview.
7. Return to EVE and paste the name into the bookmark dialog.
8. Use `New hole` before starting another wormhole.

Hover-to-paste requires the helper to have keyboard focus. The development session
reports Hyprland on Wayland. Hyprland controls focus follows mouse and floating
window behavior; the app should focus its paste field when activated without
taking focus back while the user works in EVE. A click-to-focus path must also work.
See [Hyprland focus settings](https://wiki.hypr.land/Configuring/Basics/Variables/)
and [window rules](https://wiki.hypr.land/configuring/core/rules/window-rules/).

The first desktop experiment must verify this workflow with the actual EVE client,
including its fullscreen or windowed mode. An always-on-top request alone does
not establish that the helper stays visible on Wayland. Provide optional Hyprland
configuration instructions once tested.

## Bookmark convention

The supplied screenshot defines this structure:

```text
[Sort][Signature] [Space Type][Direction][Size] [Destination] [Flags]
```

There is no space between the sort prefix and signature, or between the three
parts of the destination class. Separate the remaining fields with one space.
Omit the flags field and its preceding space when no flags apply. Clipboard output
is one line of plain text with no trailing newline.

| Component | Rule |
| --- | --- |
| Sort | `--` for a wormhole leading home; `-` for other wormholes |
| Signature | First three letters of the scan signature: `YRU-123` becomes `YRU` |
| Space type | `HS`, `LS`, `NS`, `C1` through `C6`, `C13`, `DR`, `PV`, or `Thera` |
| Direction | `i` incoming, `o` outgoing, `r` random, `s` static |
| Size | `S` small, `M` medium, `L` large, `XL` extra large |
| Destination | User-supplied system name or destination label |
| Flags | Applicable lifetime and mass indicators |

Use `C13` for the screenshot's shattered-wormhole category, `DR` for Drifter space,
and `PV` for Pochven. Preserve the screenshot's spelling and capitalization.

Although the screenshot calls Sort a single character, its home prefix and
examples use two hyphens. Follow the explicit examples: `--` for home.

| Condition | Flag |
| --- | --- |
| Less than 4 hours remaining | `EOL` |
| Less than 1 hour remaining | `VEOL` |
| Less than 50% mass remaining | `DSTB` |
| Less than 10% mass remaining | `CRIT` |

Proposed flag behavior: emit only the strongest flag in each category. `VEOL`
replaces `EOL`; `CRIT` replaces `DSTB`. If both categories apply, emit lifetime
first, then mass, for example `EOL DSTB`. Unknown status is distinct from a known
status that needs no flag.

Home is a manual toggle. Default direction to `o` when unsure, as the screenshot
specifies, and make the default visible and editable. Recognizing `K162` sets `i`
unless the user has explicitly overridden it. Static and random classifications
remain manual in the first version.

## What the sample can tell us

Preserve this description as a parser fixture:

```text
An unstable wormhole, deep in space. Wormholes of this kind usually collapse after a few days, and can lead to anywhere.

Destination: Class 1-3 wormhole systems
Maximum Ship Size: Large

Reliable Lifetime: Less than 4 hours remaining
Mass Stability: More than 50% remaining
```

The user also supplied `Wormhole K162` as the object's name. The parser should
accept that name within the paste or as a separate paste into the current record.

| Field | Result |
| --- | --- |
| Wormhole type, if the name is supplied | `K162` |
| Direction inferred from that type | `i` |
| Destination candidates | `C1`, `C2`, or `C3`; exact class unresolved |
| Size | `L` |
| Lifetime | `EOL` |
| Mass | Known to have more than 50% remaining; no mass flag |
| Scan signature | Missing |
| Destination name or label | Missing |

A wormhole type such as `K162` and a scan signature such as `YRU-123` are separate
identifiers. K162 identifies the return side and cannot determine the exact class
or system name. Other wormhole types may support a later local lookup table.
See [EVE University wormhole attributes](https://wiki.eveuniversity.org/Wormhole_Types).

Never convert `Class 1-3` into `C13`: a class range and the shattered-wormhole code
have different meanings. Keep candidate classes as structured data until resolved.
The parser must not arbitrarily choose C1, C2, or C3.

With an additional signature `YRU-123`, a manually confirmed class `C2`, and a
destination label `533`, the result is:

```text
-YRU C2iL 533 EOL
```

With the home toggle enabled:

```text
--YRU C2iL 533 EOL
```

The meaning of short labels such as `533` is still unconfirmed. Initially accept
an explicit destination label unchanged apart from whitespace cleanup. Do not
automatically shorten J-numbers until that convention is settled.

## First interface

Keep one compact, resizable window with these controls:

- A large paste area that accepts a description, an object name, or a signature.
- Editable fields for signature, wormhole type, exact space type, direction, size,
  and destination.
- A `Leads home` toggle and lifetime/mass selectors showing parsed values.
- A bookmark preview, with optional colors matching the reference screenshot.
- A short status such as `Needs signature and destination`, `Choose C1, C2, or C3`,
  `Ready`, or `Copied`.
- `New hole`, `Copy`, and an enabled-by-default `Auto-copy` toggle.

Use the preview colors only for display; EVE receives ordinary text. Missing and
conflicting fields need text labels as well as color.

Each paste is an input event for the current record, not text that must be appended
to every earlier paste. Retain the latest source text for inspection. Prefer a
single large paste target over requiring the user to aim at several tiny fields.

## Parsing, record updates, and copying

Use deterministic parsing with regular expressions and explicit mappings. No AI
service is needed to interpret these structured labels.

1. Normalize line endings, tabs, non-breaking spaces, and surrounding whitespace.
2. Match known labels case-insensitively and normalize recognized codes.
3. Extract a partial result, including class candidates and any unrecognized values.
4. Merge that result into the active record without silently replacing manual edits.
5. Validate the record and produce either a finished name or a list of missing or
   conflicting fields.
6. Copy only a valid name after a paste or a user edit, including typing in the
   final field. Do this while the helper still has focus; do not wait for Tab,
   Enter, or focus loss. Programmatic UI refreshes do not copy.

Treat the description's labeled lifetime as authoritative over its generic opening
sentence about collapsing after a few days. Match size labels completely so that
`Extra Large` cannot accidentally become `L`.

Require signature, exact space type, direction, size, destination, and resolved
lifetime/mass states before automatic copying. A recognized healthy status is a
resolved state with no flag. A user can explicitly set a state through the controls
when the pasted description does not supply it.

Preserve previously supplied fields during complementary pastes for the same hole.
A new recognized description replaces the previous parsed description fields,
including clearing old flags when newer information indicates a healthy state.
Manual values that conflict with new evidence must be highlighted and resolved
before copying. Multiple signatures or descriptions in one paste need an explicit
selection or a clear validation message; do not silently choose the first.

If a pasted signature differs from the current signature, require `New hole` before
applying it. `New hole` clears all wormhole-specific data, home state, overrides,
flags, and copy status. Resetting or rejecting a paste leaves the system clipboard
alone. Keep ordinary UI preferences, such as auto-copy, separate from the record.

Process explicit pastes only in the first version. Copying output must not trigger
another parse. Use Qt's normal clipboard mode for Ctrl+V; do not confuse it with
Linux's primary selection used by middle-click. Keep the Qt event loop running to
serve clipboard requests, including after the helper loses focus.
See [Qt's clipboard modes and platform notes](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html).

Enabling auto-copy copies an already complete record. Do not rewrite the clipboard
on focus changes or because an older record is complete.
Clear the `Copied` indicator when edits make the preview differ from the copied
value, or when another application replaces the clipboard contents.

## Proposed code layout

Keep parsing and formatting independent of Qt so the main behavior can be tested
without opening a window. Start with a few modules and split further only when
their responsibilities grow.

```text
docs/
  idea.md
src/
  eve_wormhole/
    __init__.py
    app.py          # Qt startup and application entry point
    models.py       # Partial records, resolved values, validation results
    parser.py       # Pasted text to partial record
    formatter.py    # Validated record to bookmark name
    state.py        # Merge rules, overrides, reset, copy eligibility
    window.py       # Widgets, paste events, clipboard access
tests/
  fixtures/
  test_parser.py
  test_formatter.py
  test_state.py
pyproject.toml
uv.lock
.python-version
README.md
```

## Development setup

Initialize a packaged application with a `src` layout and a console entry point
named `eve-wormhole`. Select a current stable CPython release with compatible
PySide6 Linux wheels during bootstrap, record its minimum in `requires-python`,
and pin the development interpreter in `.python-version`. Add PySide6 as a runtime
dependency and Ruff/pytest to the development dependency group. Commit `uv.lock`
for repeatable installs. See [uv project creation](https://docs.astral.sh/uv/concepts/projects/init/)
and [dependency management](https://docs.astral.sh/uv/concepts/projects/dependencies/).

As of 2026-09-12, the latest stable Ruff release is **0.16.7**, published
2026-09-10. Recheck at bootstrap and resolve the newest stable release rather than
using an older global installation. The lockfile will record the exact version.
Source: [Ruff on PyPI](https://pypi.org/project/ruff/).

Planned bootstrap commands, to run when implementation begins:

```bash
uv init --package --name eve-wormhole
uv add pyside6
uv add --dev "ruff>=0.16.7" pytest
uv run ruff --version
```

Keep Ruff's stable default rules and add import sorting. Use an 88-character line
length and let Ruff infer its Python target from `requires-python`. Keep pytest
configuration in the same `pyproject.toml`, with tests outside the package:

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
extend-select = ["I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--import-mode=importlib", "-ra"]
```

The formatter does not sort imports itself; use the lint rule for that.
See [Ruff configuration](https://docs.astral.sh/ruff/configuration/),
[Ruff formatting](https://docs.astral.sh/ruff/formatter/), and
[pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html).

Routine validation after code changes:

```bash
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

For deliberate Ruff upgrades, use `uv lock --upgrade-package ruff`, verify the
resolved version, and rerun the checks. This respects the dependency constraint;
keep it compatible with the requirement to use the latest stable Ruff. See
[uv lockfile upgrades](https://docs.astral.sh/uv/concepts/projects/sync/#upgrading-locked-package-versions).

## Verification

Use parametrized pytest cases and captured paste fixtures to cover behavior that
can produce an incorrect bookmark:

- The supplied sample remains incomplete until signature, class, and destination
  are provided; the completed example matches the expected name exactly.
- Every space type, direction, size, and home prefix formats correctly.
- `K162` is a wormhole type, never a three-letter scan signature.
- Class ranges stay unresolved and cannot collide with `C13`.
- Lifetime and mass flags have the intended precedence and ordering; a newer
  healthy description removes stale flags.
- Whitespace variations, CRLF input, unknown labels, malformed values, and multiple
  candidate signatures produce predictable results.
- Conflicting pastes, manual overrides, incomplete records, and resets cannot
  silently combine data from different wormholes or copy an invalid name.

Exercise paste-to-preview-to-copy behavior through a small GUI integration test
when the window exists. Keep automated clipboard tests isolated from the user's
live clipboard. Headless tests do not establish that EVE clipboard interoperability
works; manually verify the real application round trip on Hyprland, including
focus changes, game display mode, repeated pastes, reset, and auto-copy disabled.
Record tested conditions and remaining limitations in the README.

## Implementation milestones

1. **Bootstrap and clipboard experiment.** Create the uv project, configure Ruff
   and pytest, and open a minimal PySide6 window that accepts a paste and copies a
   visible test result. Verify the actual EVE clipboard round trip and window focus.
2. **Parser and formatter.** Implement the record model, explicit mappings,
   validation, and sample-based tests. Keep ambiguous values unresolved.
3. **Complete bookmark workflow.** Add editable fields, complementary pastes,
   conflict handling, automatic copying, and `New hole`. Verify state transitions.
4. **Desktop usability.** Refine sizing, colors, keyboard navigation, and optional
   Hyprland rules. Add a desktop launcher and document startup and checks.

The first usable version is complete when the user can paste real EVE information,
fill only the missing fields, obtain the correct clipboard text, and start the
next wormhole without stale data. Ruff and pytest must pass, and the desktop round
trip must have been verified under documented conditions.

## Open choices and later ideas

- Confirm whether numeric destinations such as `533` are shortened J-numbers or
  custom map labels. Until then, accept an explicit label without shortening it.
- Confirm whether scouting needs an explicit option to copy incomplete names.
  The initial default requires a complete bookmark.
- Collect real scan-result and object-name pastes to establish their exact formats.
  Support the supplied English description first and extend from verified samples.
- Add a local wormhole-type table and system lookup if they reduce manual entry.
  Keep lookup provenance and updates separate from parsing pasted status.
- Consider recent-bookmark history, saved naming profiles, a tray icon, and a
  desktop shortcut to show the helper after the core workflow works.
- Consider optional clipboard monitoring later, with pause controls and detection
  of the app's own output. Explicit paste remains the first implementation.
- Revisit portable packaging after the uv-launched application works reliably.

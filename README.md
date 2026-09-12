# Wormhole bookmarks

A Linux desktop helper that turns pasted EVE Online wormhole information into a
bookmark name. Built with Python, PySide6, and uv.

## Run

From the project directory:

```bash
uv sync --locked
uv run --locked eve-wormhole
```

The development interpreter is pinned to Python 3.13. The package supports Python
3.13 and 3.14. Dependencies are recorded in `uv.lock`, including PySide6 6.11.2,
Ruff 0.16.7, pytest 9.1.1, and pytest-qt 4.5.0.

## Make a bookmark

1. Paste the description from EVE into the large input area. Size, lifetime, mass,
   and destination class candidates appear below it.
2. Paste the wormhole type, such as `Wormhole K162`, and scan signature, such as
   `YRU-123`, into the same area. Each paste updates the current record.
3. Choose an exact destination class and enter a destination name or label. A
   standalone J-number can also be pasted into the large area.
4. A complete record is copied automatically when you paste, choose an option, or
   edit a field. You do not need to press Tab or Enter: the clipboard follows valid
   edits while the helper has focus. Return to EVE and paste it.
5. Click **New hole**, or press **Ctrl+N**, before starting the next wormhole.

Use **Copy bookmark** to copy again, or turn off **Auto-copy** to copy manually.
Turning **Auto-copy** back on also copies an already complete record. If the status
starts with **Not copied**, fill in the fields it lists. The description alone
usually cannot supply the signature, exact class, and destination name.
If you edit the source text directly, click **Parse edited text** to apply it.
Unknown values and conflicting pastes block copying until you choose a value or
explicitly keep your manual choices. Resetting and rejected pastes do not write to
the clipboard. The app does not monitor the clipboard for new input.

With the sample in [tests/fixtures/k162.txt](tests/fixtures/k162.txt), type `K162`,
signature `YRU-123`, class `C2`, and destination label `533`, the result is:

```text
-YRU C2iL 533 EOL
```

Enable **Leads home** for `--YRU C2iL 533 EOL`. Destination labels are preserved;
the app does not shorten J-numbers automatically. `Class 1-3` requires an exact
class selection and is never interpreted as `C13`.

The parser currently accepts the English labeled descriptions in the planning
document. It recognizes full `ABC-123` signatures in scan-result rows, wormhole
types, and standalone J-numbers. It does not infer a destination system from K162
or look up other wormhole types yet. Use the controls for information not supplied
by the paste. The outgoing/unsure direction defaults to `o`; K162 supplies `i`.

## Hyprland and Wayland

The helper opens as a native Wayland window with app ID `eve-wormhole`. Keeping it
floating, positioning it, and focusing it when the mouse enters are compositor
settings. The app requests always-on-top behavior, but Wayland does not guarantee
that this request will take effect.

[docs/hyprland.conf](docs/hyprland.conf) contains an optional floating rule. To use
it with the hyprlang configuration format, add this line to your Hyprland config,
adjusting the path if the repository is elsewhere, then reopen the helper:

```ini
source = /home/j/eve_worm_hole/docs/hyprland.conf
```

The optional `pin` rule in that file keeps the helper on all workspaces. Mouse-over
Ctrl+V requires Hyprland to give it keyboard focus; clicking the input area also
works. No changes to your desktop configuration are made by the application.
For other Hyprland versions or Lua configuration, translate the app ID rule using
the [Hyprland window rule documentation](https://wiki.hypr.land/configuring/core/rules/window-rules/).

Keep the helper running while pasting its output. Check its visibility and focus
behavior with EVE's actual display mode; fullscreen behavior may differ from a
windowed game. The helper focuses its paste area when activated and does not try
to take focus while you are working in EVE.

## Desktop launcher

After `uv sync --locked`, [packaging/eve-wormhole.desktop.in](packaging/eve-wormhole.desktop.in)
can be used as a launcher template. Replace `@PROJECT_DIR@` with the absolute
project directory and save it as
`~/.local/share/applications/eve-wormhole.desktop`. The launcher runs this
project's environment directly. Update it if you move the repository.

## Checks

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest
```

Tests force Qt's `offscreen` platform. GUI clipboard tests are isolated from the
desktop clipboard, so running pytest cannot overwrite something you copied in EVE.
Core parser, formatter, and state modules do not import Qt.

To upgrade Ruff deliberately:

```bash
uv lock --upgrade-package ruff
uv run --locked ruff --version
```

Then rerun the checks and review the lockfile changes. The project was bootstrapped
with the newest stable Ruff release available on PyPI, 0.16.7, verified on
2026-09-12. See the [Ruff package](https://pypi.org/project/ruff/).

## Verification status

- Parser, formatting, record updates, and GUI clipboard behavior are covered by
  automated tests.
- The initial and completed windows were rendered and visually inspected offscreen.
- Native startup was verified with Qt 6.11.2 on Wayland and Hyprland 0.56.2, using
  the development machine's Python 3.13.11.
- The remaining manual check is the real EVE round trip: copy a description and
  signature, complete the record, paste the result into a bookmark, then create
  a second bookmark with `New hole`. Also check hover focus and visibility in the
  game's chosen fullscreen or windowed mode.

Naming conventions, design decisions, and future work are in
[docs/idea.md](docs/idea.md).

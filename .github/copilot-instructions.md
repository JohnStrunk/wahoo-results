
# Copilot Coding Agent Instructions for Wahoo! Results

## Project Overview

Wahoo! Results is a Windows-focused Python application for displaying swimming
meet results on Chromecast devices. It integrates with meet management software
(Hy-Tek Meet Manager, SwimTopia Meet Maestro) and Colorado Dolphin timing
systems. The scoreboard is rendered as images and broadcast to Chromecasts via
an embedded web server.

## Architecture & Key Components

- **MVC-inspired structure**: The codebase separates UI (`main_window.py`,
  `scoreboard_window.py`), data model (`model.py`), and logic. The `Model`
  class holds application state and configuration.
- **Scoreboard rendering**: `scoreboard.py` generates scoreboard images from
  race data and user preferences.
- **Chromecast integration**: `imagecast.py` manages device discovery and image
  casting. The scoreboard is sent as a PNG via a local web server.
- **Data ingestion**: The `raceinfo/` package abstracts reading/writing start
  lists and result files (CTS, Dolphin, Generic formats). `DolphinDo4` and
  related classes parse timing data.
- **GUI**: Built with Tkinter, using custom widgets (`widgets.py`). The main
  window has tabs for configuration, directories, and live results.
- **Testing**: `autotest.py` provides end-to-end and randomized test harnesses.
  Unit tests use `pytest`.

## Developer Workflows

- **Environment**: Use [uv](https://docs.astral.sh/uv/) for all dependency
  management (`uv add`, `uv remove`). Do not use pip directly.
- **Run for development**: `uv run wahoo_results.py`
- **Build executable**: `uv run python build.py` (requires UPX, see
  `Contributing.md`)
- **Testing**:
  - Unit tests: `uv run pytest`
  - End-to-end:
    `wahoo-results.exe --loglevel=debug --logfile=debug.log --test=scripted:<duration_secs>`
  - Randomized:
    `wahoo-results.exe --loglevel=debug --logfile=debug.log --test=random:<delay>:<runtime>:<max_ops>`
- **Linting & style**: `uv run pyright` and `pre-commit run -a` (pre-commit
  hooks recommended)
- **Docs**: Written in Markdown, built with MkDocs. Build with
  `uv run mkdocs build --strict` after changes to `docs/`.

**IMPORTANT**: After making changes, unit tests and style/lint MUST PASS. When
you make changes, run the tests, fix any issues, then re-run the tests.
Continue to iterate until everything passes.

At the end of your work, evaluate your instructions, feedback, and this file.
If the instructions in this file were incorrect or omitted important
information, suggest improvements to make it more accurate and complete.

## Project-Specific Conventions

- **Docstrings**: Use reStructuredText (reST) style. All functions/methods
  require type annotations and docstrings. Do not repeat parameter types in
  docstrings.
- **Windows-first**: Target Windows for development/testing.
- **Configuration**: User settings are stored in `wahoo-results.ini` in the
  executable's directory.
- **Image assets**: Scoreboard backgrounds should be 1280x720 PNGs.
- **Chromecast quirks**: Chromecast with Google TV requires special settings
  (see `docs/cc-compat.md`).

## Integration Points & External Dependencies

- **Chromecast**: Uses `pychromecast` for device discovery and control.
- **Image processing**: Uses `Pillow` for image generation.
- **Crash reporting**: Integrates with Sentry via `sentry-sdk`.
- **Analytics**: Optional analytics via `segment-analytics-python`.
- **File watching**: Uses `watchdog` to monitor result/start list directories.

## Example Patterns

- **Adding a new timing system**: Implement a subclass of `TimingSystem` in
  `raceinfo/`, and update the UI to allow selection.
- **Scoreboard updates**: When new result files are detected, the model is
  updated, triggering a re-render and broadcast to Chromecasts.
- **UI extension**: Add new tabs or dialogs by extending `main_window.py` and
  using the `widgets.py` helpers.

## Key Files & Directories

- `wahoo_results.py`: Main entry point
- `main_window.py`, `scoreboard_window.py`: UI
- `model.py`: Application state/config
- `scoreboard.py`: Scoreboard rendering
- `imagecast.py`: Chromecast integration
- `raceinfo/`: Data file parsing/abstraction
- `autotest.py`: Test harness
- `docs/`: User/developer documentation

---
For more, see `README.md`, `Contributing.md`, and `docs/` for user/developer
docs. When in doubt, follow the patterns in the files above.

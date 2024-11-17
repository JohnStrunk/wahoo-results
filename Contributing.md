# Contributing to Wahoo! Results

Thank you for taking the time to consider contributing to the project. Use the
information in this document to get started.

## Bugs and feature requests

Even if you don't want to contribute code, you can still contribute to the
project by providing feedback. Here are some ways you can do that:

- Did you find a problem? Please [open an
  issue](https://github.com/JohnStrunk/wahoo-results/issues/new?labels=bug) for
  it!
- Do you have an idea for a new feature? Great! [Start a
  discussion](https://github.com/JohnStrunk/wahoo-results/discussions/new?category=ideas-feature-requests)
  about it.

## Developing & building from source

**Note:** Wahoo! Results, while it is written in Python, is primarily targeted
at Windows. As such, it is recommended to use Windows for development and
testing.

### Environment setup

- Install Python 3
  Chocolatey is a good way to install Python on Windows:
  `choco install python3`
  The version of Python currently being used can be found in the
  [.python-version](.python-version) file.
- Install dependencies:
  - Install [uv](https://docs.astral.sh/uv/): `pip install --user --upgrade uv`
- (Optional) Install [pre-commit](https://pre-commit.com) to verify code style
  before committing
  - Install pre-commit: `pip install --user --upgrade pre-commit`
  - Install pre-commit hooks: `pre-commit install`

### Building & running

- To run the app (for development): `uv run wahoo_results.py`
- To build the executable version:
  - Install UPX: `choco install upx --version 4.2.4`
  - Run the build script: `uv run python build.py`

### Testing

- The unit tests can be run via: `uv run pytest`
- There are also end-to-end tests that are build into the program. To run them,
  pass command-line options when running either the `.py` or `.exe` versions.
  - Specific scenario tests: `wahoo-results.exe --loglevel=debug
    --logfile=debug.log --test=scripted:<duration_secs>`
  - Randomized testing: `wahoo-results.exe --loglevel=debug --logfile=debug.log
    --test=random:<operation_delay_secs>:<runtime_secs>:<max_num_operations>`

## Release procedure

- Update release notes in [Changelog.md](Changelog.md)
- Update download link in documentation (docs/download.rst)
- Commit above items: "Updates for vX.Y.Z release"
- Tag the repo with the appropriate version tag (e.g. `vX.Y.Z`)
- Push the tag to GitHub, and the automation will create a draft release
- Edit the draft release to add the release notes
- Publish the release

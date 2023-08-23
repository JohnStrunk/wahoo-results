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
  Chocolatey is a good way to install Python on Windows: `choco install python3`  
  The version of Python currently being used can be found at the botton of the
  [Pipfile](Pipfile).
- Install dependencies:
  - Install [pipenv](https://pipenv.pypa.io): `pip install --user --upgrade
    pipenv==2023.8.23`
  - Install project dependencies: `pipenv sync --dev`
- (Optional) Install [pre-commit](https://pre-commit.com) to verify code style
  before committing
  - Install pre-commit: `pip install --user --upgrade pre-commit`
  - Install pre-commit hooks: `pre-commit install`

### Building & running

- To run the app (for development): `pipenv run python wahoo_results.py`
- To build the executable version:
  - Install UPX: `choco install upx --version 4.1.0`
  - Run the build script: `pipenv run python build.py`

### Testing

- The unit tests can be run via: `pipenv run pytest`
- There are also end-to-end tests that are build into the program. To run them,
  pass command-line options when running either the `.py` or `.exe` versions.
  - Specific scenario tests: `wahoo-results.exe --loglevel=debug
    --logfile=debug.log --test=scripted:<duration_secs>`
  - Randomized testing: `wahoo-results.exe --loglevel=debug --logfile=debug.log
    --test=random:<operation_delay_secs>,<runtime_secs>,<max_num_operations>`

## Release procedure

- Update release notes in [Changelog.md](Changelog.md)
- Tag the repo with the appropriate version tag (e.g. `vX.Y.Z`)
- Push the tag to GitHub, and the automation will create a draft release
- Edit the draft release to add the release notes
- Publish the release

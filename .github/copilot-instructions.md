# Coding instructions for GitHub Copilot

## Code documentation style

- All functions and methods must have type annotations.
- All functions and methods must have docstrings.
- The first line of a docstring must be a short summary of the function's
  purpose in the imperative mood.
- Docstrings must describe the function's purpose, parameters, and return
  values.
- Use reStructuredText (reST) style for docstrings in Python files.
  - DO NOT repeat the parameter types in the docstring
  - Example:

    ```python
    def add(a: int, b: int) -> int:
        """
        Add two integers.

        :param a: The first integer.
        :param b: The second integer.
        :return: The sum of the two integers.
        """
        return a + b
    ```

## Development environment

- The Python environment must be managed using uv.
- DO NOT use pip directly; always use uv to manage dependencies via `uv add`
  or `uv remove`.

## Testing

- After making ANY changes to files in the repository:
  - Run the test suite using `uv run pytest` to ensure that all tests pass.
  - Run `uv run pyright` to check for code style and linting issues.
  - Run `pre-commit run -a` to ensure all pre-commit hooks pass.
  - If any of these checks fail, fix the issues and re-run the checks until
    they all pass.

## Documentation

- Documentation is written in Markdown (.md) files, and it is built using
  MkDocs.
- After making ANY changes to files in the `docs` directory:
  - Run `uv run mkdocs build --strict` to ensure that the documentation builds
    without errors.
  - If the build fails, fix the issues and re-run the build until it succeeds.

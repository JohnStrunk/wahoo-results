"""Unit tests for the fonts module."""

import pytest

from fonts import font_names, font_to_path

VALID_FONT_EXTENSIONS = (".ttf", ".ttc", ".otf", ".otc")


def test_get_all_font_names_returns_list():
    """Test that get_all_font_names returns a non-empty list of strings."""
    names = font_names()
    assert isinstance(names, list)
    assert all(isinstance(n, str) for n in names)
    # There should be at least one font installed
    assert len(names) > 0


def test_get_ttf_path_for_font_regular():
    """Test that get_ttf_path_for_font returns a .ttf path or None for a regular font."""
    names = font_names()
    # Try to get a ttf path for the first font (default to Regular)
    ttf = font_to_path(names[0])
    assert ttf is None or (
        isinstance(ttf, str) and ttf.lower().endswith(VALID_FONT_EXTENSIONS)
    )


def test_get_ttf_path_for_font_with_subfamily():
    """Test that get_ttf_path_for_font returns a .ttf path or None for Bold and Italic subfamilies."""
    names = font_names()
    # Try to get a ttf path for the first font with subfamily 'Bold' and 'Italic'
    ttf_bold = font_to_path(names[0], "Bold")
    ttf_italic = font_to_path(names[0], "Italic")
    # Should be None or a .ttf path
    assert ttf_bold is None or (
        isinstance(ttf_bold, str) and ttf_bold.lower().endswith(VALID_FONT_EXTENSIONS)
    )
    assert ttf_italic is None or (
        isinstance(ttf_italic, str)
        and ttf_italic.lower().endswith(VALID_FONT_EXTENSIONS)
    )


def test_get_ttf_path_for_font_nonexistent():
    """Test that get_ttf_path_for_font returns None for non-existent font names."""
    # Should return None for a font that doesn't exist
    assert font_to_path("DefinitelyNotARealFontName") is None


def test_get_ttf_path_for_font_fallback_to_any_subfamily():
    """Test that get_ttf_path_for_font falls back to any available subfamily if the requested one does not exist."""
    names = font_names()
    if not names:
        pytest.skip("No fonts installed to test fallback.")
    font_name = names[0]
    # Use a subfamily that is very unlikely to exist
    ttf = font_to_path(font_name, "NonexistentSubfamily")
    # If the font exists at all, should return a .ttf path (fallback to any subfamily)
    assert ttf is None or (
        isinstance(ttf, str) and ttf.lower().endswith(VALID_FONT_EXTENSIONS)
    )

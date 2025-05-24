"""Font management utilities for installed system fonts using fontTools."""

import os
import sys
import threading
from dataclasses import dataclass

from fontTools.ttLib import TTFont  # type: ignore


@dataclass(frozen=True)
class FontInfo:
    """Information about an installed font."""

    name: str
    ttf_path: str


# Internal cache and lock for thread safety
_fonts_cache: dict[tuple[str, str], FontInfo] | None = None
_cache_lock = threading.Lock()

if sys.platform == "win32":
    _FONT_DIRS = [os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")]
elif sys.platform == "darwin":
    _FONT_DIRS = [
        "/System/Library/Fonts",
        "/Library/Fonts",
        os.path.expanduser("~/Library/Fonts"),
    ]
else:
    _FONT_DIRS = [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        os.path.expanduser("~/.fonts"),
    ]


def _scan_fonts() -> dict[tuple[str, str], FontInfo]:
    fonts: dict[tuple[str, str], FontInfo] = {}
    for font_dir in _FONT_DIRS:
        if not os.path.isdir(font_dir):
            continue
        for file in os.listdir(font_dir):
            if file.lower().endswith(".ttf"):
                path = os.path.join(font_dir, file)
                try:
                    font = TTFont(path, fontNumber=0)
                    name_table = font["name"]  # type: ignore
                    family = None
                    subfamily = None
                    for record in name_table.names:  # type: ignore
                        # Record 1 is the Font Family name
                        if getattr(record, "nameID", None) == 1:  # type: ignore
                            try:
                                family = record.string.decode(  # type: ignore
                                    record.getEncoding(),  # type: ignore
                                    errors="ignore",
                                )
                            except Exception:
                                continue
                        elif (
                            # Record 2 is the Font Subfamily name
                            getattr(record, "nameID", None) == 2  # type: ignore  # noqa: PLR2004
                        ):  # Font Subfamily name
                            try:
                                subfamily = record.string.decode(  # type: ignore
                                    record.getEncoding(),  # type: ignore
                                    errors="ignore",
                                )
                            except Exception:
                                continue
                    if family:
                        key = (family, subfamily or "Regular")  # type: ignore
                        if key not in fonts:
                            fonts[key] = FontInfo(name=family, ttf_path=path)  # type: ignore
                except Exception:
                    continue
    return fonts


def _ensure_cache() -> None:
    global _fonts_cache  # noqa: PLW0603
    if _fonts_cache is None:
        with _cache_lock:
            if _fonts_cache is None:
                _fonts_cache = _scan_fonts()


def font_names() -> list[str]:
    """
    Get all installed font family names.

    :returns: Sorted list of unique font family names (no subfamilies).
    """
    _ensure_cache()
    if _fonts_cache is None:
        return []
    return sorted(set(family for (family, _) in _fonts_cache.keys()))


def font_to_path(font_name: str, subfamily: str | None = None) -> str | None:
    """
    Get the TTF file path for a given font name and optional subfamily.

    :param font_name: The font family name to search for.
    :param subfamily: The font subfamily (e.g., 'Bold', 'Italic', 'Bold Italic'). If not provided, defaults to 'Regular'.
    :returns: The path to the TTF file, or None if not found.
    """
    _ensure_cache()
    if _fonts_cache is None:
        return None
    # Normalize subfamily
    subfamily = (subfamily or "Regular").strip().lower()
    # Try exact match
    for (family, subfam), info in _fonts_cache.items():
        if family == font_name and subfam.strip().lower() == subfamily:
            return info.ttf_path
    # Fallbacks: try to match common subfamily synonyms
    fallback_map = {
        "bold": ["bold", "boldmt"],
        "italic": ["italic", "oblique"],
        "bold italic": ["bold italic", "bolditalic", "bold oblique", "boldoblique"],
        "regular": ["regular", "roman", "normal", "plain", "book"],
    }
    for _, synonyms in fallback_map.items():
        if subfamily in synonyms:
            for (family, subfam), info in _fonts_cache.items():
                if family == font_name and subfam.strip().lower() in synonyms:
                    return info.ttf_path
    # Fallback to any subfamily for the family
    for (family, subfam), info in _fonts_cache.items():
        if family == font_name:
            return info.ttf_path
    return None


def main() -> None:
    """Print all font names, subfamilies, and their corresponding ttf file paths."""
    _ensure_cache()
    if _fonts_cache is None:
        return
    for (family, subfamily), info in sorted(_fonts_cache.items()):
        print(f"{family} ({subfamily}) => {info.ttf_path}")


if __name__ == "__main__":
    main()

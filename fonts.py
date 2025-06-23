"""Font management utilities for installed system fonts using fontTools."""

import logging
import os
import sys
import threading
from dataclasses import dataclass

from fontTools.ttLib import TTCollection, TTFont  # type: ignore

logger = logging.getLogger(__name__)


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


def _scan_fonts() -> dict[tuple[str, str], FontInfo]:  # noqa: PLR0912
    fonts: dict[tuple[str, str], FontInfo] = {}
    for font_dir in _FONT_DIRS:
        if not os.path.isdir(font_dir):
            continue
        for file in os.listdir(font_dir):
            if file.lower().endswith((".ttf", ".ttc", ".otf", ".otc")):
                path = os.path.join(font_dir, file)
                fonts_to_process = []
                collection = None  # To ensure TTCollection is closed

                try:
                    if file.lower().endswith((".ttc", ".otc")):
                        # It's a font collection, use TTCollection
                        collection = TTCollection(path)
                        fonts_to_process.extend(collection.fonts)  # type: ignore
                    else:
                        # It's a single font file
                        fonts_to_process.append(TTFont(path))  # type: ignore

                    for font in fonts_to_process:  # type: ignore
                        try:
                            name_table = font["name"]  # type: ignore
                            family = None
                            subfamily = None

                            for record in name_table.names:  # type: ignore
                                # nameID 1: Font Family name
                                if record.nameID == 1:  # type: ignore
                                    family = record.string.decode(  # type: ignore
                                        record.getEncoding(),  # type: ignore
                                        errors="ignore",
                                    )
                                # nameID 2: Font Subfamily name
                                elif record.nameID == 2:  # type: ignore  # noqa: PLR2004
                                    subfamily = record.string.decode(  # type: ignore
                                        record.getEncoding(),  # type: ignore
                                        errors="ignore",
                                    )

                            if family:
                                key = (family, subfamily or "Regular")  # type: ignore
                                if key not in fonts:
                                    fonts[key] = FontInfo(name=family, ttf_path=path)  # type: ignore
                        except Exception as inner_e:
                            logger.debug(
                                "Failed to process font info for %s (from %s): %s",
                                font,  # type: ignore
                                path,
                                inner_e,
                            )
                        finally:
                            font.close()  # Ensure each font object is closed # type: ignore
                except Exception as e:
                    logger.debug("Failed to process font file %s: %s", path, e)
                    continue
                finally:
                    if collection:
                        collection.close()  # Ensure TTCollection is closed
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

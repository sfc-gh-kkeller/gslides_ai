"""Styling utilities for Google Slides presentations."""

from typing import Any


# Snowflake 2026 brand colors (from official template)
COLORS = {
    # Primary brand colors
    "snowflake_blue": {"red": 0.161, "green": 0.710, "blue": 0.906},  # #29B5E7
    "snowflake_dark_blue": {"red": 0.067, "green": 0.333, "blue": 0.498},  # #11557F
    "snowflake_medium_blue": {"red": 0.106, "green": 0.365, "blue": 0.745},  # #1B5DBE
    
    # Neutral colors
    "white": {"red": 1.0, "green": 1.0, "blue": 1.0},
    "black": {"red": 0.0, "green": 0.0, "blue": 0.0},
    "dark_gray": {"red": 0.133, "green": 0.133, "blue": 0.133},  # #222222
    "medium_gray": {"red": 0.357, "green": 0.357, "blue": 0.357},  # #5B5B5B
    "light_gray": {"red": 0.953, "green": 0.953, "blue": 0.953},  # #F3F3F3
    "off_white": {"red": 0.906, "green": 0.941, "blue": 0.992},  # #E7F0FD
    
    # Accent colors
    "accent_pink": {"red": 0.831, "green": 0.357, "blue": 0.565},  # #D45B90
    "accent_red": {"red": 0.635, "green": 0.0, "blue": 0.0},  # #A20000
    
    # Legacy aliases for compatibility
    "snowflake_dark": {"red": 0.067, "green": 0.333, "blue": 0.498},  # #11557F
    "snowflake_light_blue": {"red": 0.906, "green": 0.941, "blue": 0.992},  # #E7F0FD
}


def rgb(hex_color: str) -> dict[str, float]:
    """Convert hex color to RGB dict."""
    hex_color = hex_color.lstrip("#")
    return {
        "red": int(hex_color[0:2], 16) / 255,
        "green": int(hex_color[2:4], 16) / 255,
        "blue": int(hex_color[4:6], 16) / 255,
    }


def get_color(color: str | dict) -> dict[str, float]:
    """Get color dict from name or hex."""
    if isinstance(color, dict):
        return color
    if color.startswith("#"):
        return rgb(color)
    return COLORS.get(color, COLORS["black"])


def text_style_request(
    object_id: str,
    bold: bool = False,
    italic: bool = False,
    font_size: int | None = None,
    font_family: str | None = None,
    color: str | dict | None = None,
    start_index: int = 0,
    end_index: int | None = None,
) -> dict[str, Any]:
    """Create a text style update request."""
    style = {}
    fields = []
    
    if bold:
        style["bold"] = True
        fields.append("bold")
    if italic:
        style["italic"] = True
        fields.append("italic")
    if font_size:
        style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
        fields.append("fontSize")
    if font_family:
        style["fontFamily"] = font_family
        fields.append("fontFamily")
    if color:
        style["foregroundColor"] = {"opaqueColor": {"rgbColor": get_color(color)}}
        fields.append("foregroundColor")
    
    request = {
        "updateTextStyle": {
            "objectId": object_id,
            "style": style,
            "fields": ",".join(fields),
        }
    }
    
    if end_index:
        request["updateTextStyle"]["textRange"] = {
            "type": "FIXED_RANGE",
            "startIndex": start_index,
            "endIndex": end_index,
        }
    else:
        request["updateTextStyle"]["textRange"] = {"type": "ALL"}
    
    return request


def paragraph_style_request(
    object_id: str,
    alignment: str = "START",  # START, CENTER, END, JUSTIFIED
) -> dict[str, Any]:
    """Create a paragraph style update request."""
    return {
        "updateParagraphStyle": {
            "objectId": object_id,
            "style": {"alignment": alignment},
            "fields": "alignment",
            "textRange": {"type": "ALL"},
        }
    }


def shape_background_request(
    object_id: str,
    color: str | dict,
) -> dict[str, Any]:
    """Create a shape background color request."""
    return {
        "updateShapeProperties": {
            "objectId": object_id,
            "shapeProperties": {
                "shapeBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": get_color(color)}}
                }
            },
            "fields": "shapeBackgroundFill.solidFill.color",
        }
    }


def shape_outline_request(
    object_id: str,
    color: str | dict | None = None,
    weight: float = 1.0,
    dash_style: str = "SOLID",  # SOLID, DOT, DASH, etc.
) -> dict[str, Any]:
    """Create a shape outline style request."""
    outline = {"weight": {"magnitude": weight, "unit": "PT"}, "dashStyle": dash_style}
    
    if color:
        outline["outlineFill"] = {
            "solidFill": {"color": {"rgbColor": get_color(color)}}
        }
    
    return {
        "updateShapeProperties": {
            "objectId": object_id,
            "shapeProperties": {"outline": outline},
            "fields": "outline",
        }
    }


def slide_background_request(
    slide_id: str,
    color: str | dict,
) -> dict[str, Any]:
    """Create a slide background color request."""
    return {
        "updatePageProperties": {
            "objectId": slide_id,
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": get_color(color)}}
                }
            },
            "fields": "pageBackgroundFill.solidFill.color",
        }
    }

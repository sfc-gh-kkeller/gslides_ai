"""Google Slides API wrapper for presentation manipulation."""

from typing import Any
import uuid

from googleapiclient.discovery import build, Resource

from .auth import get_credentials


def get_slides_service() -> Resource:
    """Get authenticated Slides API service."""
    creds = get_credentials()
    return build("slides", "v1", credentials=creds)


def get_drive_service() -> Resource:
    """Get authenticated Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def generate_id() -> str:
    """Generate a unique object ID."""
    return f"obj_{uuid.uuid4().hex[:12]}"


# Presentation operations

def create_presentation(title: str) -> dict[str, Any]:
    """Create a new presentation.
    
    Args:
        title: Title of the presentation.
        
    Returns:
        Presentation metadata including presentationId.
    """
    service = get_slides_service()
    body = {"title": title}
    return service.presentations().create(body=body).execute()


def get_presentation(presentation_id: str) -> dict[str, Any]:
    """Get presentation metadata.
    
    Args:
        presentation_id: The presentation ID.
        
    Returns:
        Full presentation object with slides and metadata.
    """
    service = get_slides_service()
    return service.presentations().get(presentationId=presentation_id).execute()


def list_slides(presentation_id: str) -> list[dict[str, Any]]:
    """List all slides in a presentation.
    
    Args:
        presentation_id: The presentation ID.
        
    Returns:
        List of slide objects.
    """
    presentation = get_presentation(presentation_id)
    return presentation.get("slides", [])


# Slide operations

LAYOUTS = {
    "blank": "BLANK",
    "title": "TITLE",
    "title_body": "TITLE_AND_BODY",
    "title_two_columns": "TITLE_AND_TWO_COLUMNS",
    "title_only": "TITLE_ONLY",
    "section": "SECTION_HEADER",
    "section_title": "SECTION_TITLE_AND_DESCRIPTION",
    "one_column": "ONE_COLUMN_TEXT",
    "main_point": "MAIN_POINT",
    "big_number": "BIG_NUMBER",
}


def add_slide(
    presentation_id: str,
    layout: str = "blank",
    insertion_index: int | None = None,
) -> dict[str, Any]:
    """Add a new slide to the presentation.
    
    Args:
        presentation_id: The presentation ID.
        layout: Layout type (blank, title, title_body, etc.).
        insertion_index: Where to insert (None = end).
        
    Returns:
        Response with created slide info.
    """
    service = get_slides_service()
    slide_id = generate_id()
    
    request = {
        "createSlide": {
            "objectId": slide_id,
            "slideLayoutReference": {
                "predefinedLayout": LAYOUTS.get(layout, "BLANK")
            },
        }
    }
    
    if insertion_index is not None:
        request["createSlide"]["insertionIndex"] = insertion_index
    
    response = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [request]}
    ).execute()
    
    return {"slideId": slide_id, "response": response}


def delete_slide(presentation_id: str, slide_id: str) -> dict[str, Any]:
    """Delete a slide from the presentation.
    
    Args:
        presentation_id: The presentation ID.
        slide_id: The slide object ID to delete.
        
    Returns:
        API response.
    """
    service = get_slides_service()
    request = {"deleteObject": {"objectId": slide_id}}
    
    return service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [request]}
    ).execute()


# Element operations

def add_text_box(
    presentation_id: str,
    slide_id: str,
    text: str,
    x: float = 100,
    y: float = 100,
    width: float = 400,
    height: float = 50,
) -> dict[str, Any]:
    """Add a text box to a slide.
    
    Args:
        presentation_id: The presentation ID.
        slide_id: The slide to add text to.
        text: The text content.
        x, y: Position in points from top-left.
        width, height: Size in points.
        
    Returns:
        Response with created text box info.
    """
    service = get_slides_service()
    text_box_id = generate_id()
    
    requests = [
        {
            "createShape": {
                "objectId": text_box_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": height, "unit": "PT"},
                        "width": {"magnitude": width, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        },
        {
            "insertText": {
                "objectId": text_box_id,
                "insertionIndex": 0,
                "text": text,
            }
        },
    ]
    
    response = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()
    
    return {"textBoxId": text_box_id, "response": response}


def add_image(
    presentation_id: str,
    slide_id: str,
    image_url: str,
    x: float = 100,
    y: float = 100,
    width: float = 300,
    height: float = 200,
) -> dict[str, Any]:
    """Add an image to a slide.
    
    Args:
        presentation_id: The presentation ID.
        slide_id: The slide to add image to.
        image_url: URL of the image (must be publicly accessible).
        x, y: Position in points from top-left.
        width, height: Size in points.
        
    Returns:
        Response with created image info.
    """
    service = get_slides_service()
    image_id = generate_id()
    
    request = {
        "createImage": {
            "objectId": image_id,
            "url": image_url,
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {
                    "height": {"magnitude": height, "unit": "PT"},
                    "width": {"magnitude": width, "unit": "PT"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": x,
                    "translateY": y,
                    "unit": "PT",
                },
            },
        }
    }
    
    response = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [request]}
    ).execute()
    
    return {"imageId": image_id, "response": response}


SHAPE_TYPES = {
    "rectangle": "RECTANGLE",
    "ellipse": "ELLIPSE",
    "round_rectangle": "ROUND_RECTANGLE",
    "triangle": "TRIANGLE",
    "arrow_right": "RIGHT_ARROW",
    "arrow_left": "LEFT_ARROW",
    "arrow_up": "UP_ARROW",
    "arrow_down": "DOWN_ARROW",
    "diamond": "DIAMOND",
    "pentagon": "PENTAGON",
    "hexagon": "HEXAGON",
    "star": "STAR_5",
    "cloud": "CLOUD",
    "heart": "HEART",
}


def add_shape(
    presentation_id: str,
    slide_id: str,
    shape_type: str = "rectangle",
    x: float = 100,
    y: float = 100,
    width: float = 100,
    height: float = 100,
) -> dict[str, Any]:
    """Add a shape to a slide.
    
    Args:
        presentation_id: The presentation ID.
        slide_id: The slide to add shape to.
        shape_type: Shape type (rectangle, ellipse, triangle, etc.).
        x, y: Position in points from top-left.
        width, height: Size in points.
        
    Returns:
        Response with created shape info.
    """
    service = get_slides_service()
    shape_id = generate_id()
    
    request = {
        "createShape": {
            "objectId": shape_id,
            "shapeType": SHAPE_TYPES.get(shape_type, "RECTANGLE"),
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {
                    "height": {"magnitude": height, "unit": "PT"},
                    "width": {"magnitude": width, "unit": "PT"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": x,
                    "translateY": y,
                    "unit": "PT",
                },
            },
        }
    }
    
    response = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [request]}
    ).execute()
    
    return {"shapeId": shape_id, "response": response}


def add_table(
    presentation_id: str,
    slide_id: str,
    rows: int = 3,
    columns: int = 3,
    x: float = 100,
    y: float = 100,
    width: float = 400,
    height: float = 200,
) -> dict[str, Any]:
    """Add a table to a slide.
    
    Args:
        presentation_id: The presentation ID.
        slide_id: The slide to add table to.
        rows: Number of rows.
        columns: Number of columns.
        x, y: Position in points from top-left.
        width, height: Size in points.
        
    Returns:
        Response with created table info.
    """
    service = get_slides_service()
    table_id = generate_id()
    
    request = {
        "createTable": {
            "objectId": table_id,
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {
                    "height": {"magnitude": height, "unit": "PT"},
                    "width": {"magnitude": width, "unit": "PT"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": x,
                    "translateY": y,
                    "unit": "PT",
                },
            },
            "rows": rows,
            "columns": columns,
        }
    }
    
    response = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [request]}
    ).execute()
    
    return {"tableId": table_id, "response": response}


def update_table_cell(
    presentation_id: str,
    table_id: str,
    row: int,
    column: int,
    text: str,
) -> dict[str, Any]:
    """Update text in a table cell.
    
    Args:
        presentation_id: The presentation ID.
        table_id: The table object ID.
        row: Row index (0-based).
        column: Column index (0-based).
        text: Text to insert.
        
    Returns:
        API response.
    """
    service = get_slides_service()
    
    request = {
        "insertText": {
            "objectId": table_id,
            "cellLocation": {
                "rowIndex": row,
                "columnIndex": column,
            },
            "text": text,
            "insertionIndex": 0,
        }
    }
    
    return service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": [request]}
    ).execute()


def get_presentation_url(presentation_id: str) -> str:
    """Get the URL to open a presentation in Google Slides."""
    return f"https://docs.google.com/presentation/d/{presentation_id}/edit"

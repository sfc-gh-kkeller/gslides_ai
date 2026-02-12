#!/usr/bin/env python3
"""Add Snowflake Architecture slide to existing presentation."""

import sys
sys.path.insert(0, "/Users/kevin/DevWork/gslides_ai/src")

from gslides_ai.slides import (
    get_slides_service,
    get_presentation,
    generate_id,
    add_slide,
)
from gslides_ai.styling import (
    get_color,
    text_style_request,
    paragraph_style_request,
    shape_background_request,
    shape_outline_request,
    slide_background_request,
)

PRESENTATION_ID = "17F6drLMbF3LD6Tp23CdTKOoog940ZBV4pXmcIBxg9UU"

# Theme colors
SNOWFLAKE_BLUE = "snowflake_blue"
SNOWFLAKE_DARK_BLUE = "snowflake_dark_blue"
WHITE = "white"
DARK_GRAY = "dark_gray"
LIGHT_GRAY = "light_gray"

def add_architecture_slide():
    """Add a Snowflake architecture diagram slide."""
    service = get_slides_service()
    
    # Get current presentation to find number of slides
    pres = get_presentation(PRESENTATION_ID)
    num_slides = len(pres.get("slides", []))
    
    # Create new slide at the end
    slide_id = generate_id()
    
    requests = [
        # Create the slide
        {
            "createSlide": {
                "objectId": slide_id,
                "insertionIndex": num_slides,
            }
        }
    ]
    
    service.presentations().batchUpdate(
        presentationId=PRESENTATION_ID,
        body={"requests": requests}
    ).execute()
    
    # Set white background
    requests = [slide_background_request(slide_id, WHITE)]
    service.presentations().batchUpdate(
        presentationId=PRESENTATION_ID,
        body={"requests": requests}
    ).execute()
    
    # Now add content elements
    elements = []
    
    # === Title ===
    title_id = generate_id()
    elements.append({
        "type": "title",
        "id": title_id,
        "text": "Separation of Storage and Compute",
        "x": 40, "y": 20, "width": 640, "height": 45,
        "font_size": 28, "color": SNOWFLAKE_BLUE, "bold": True, "alignment": "START"
    })
    
    # === Subtitle ===
    subtitle_id = generate_id()
    elements.append({
        "type": "text",
        "id": subtitle_id,
        "text": "Scale Each Layer Independently",
        "x": 40, "y": 60, "width": 640, "height": 25,
        "font_size": 14, "color": DARK_GRAY, "bold": False, "alignment": "START"
    })
    
    # === Architecture Diagram - Three Layers ===
    
    # Layer 1: Cloud Services Layer (Top)
    cloud_services_box_id = generate_id()
    elements.append({
        "type": "box",
        "id": cloud_services_box_id,
        "x": 60, "y": 95, "width": 280, "height": 60,
        "fill_color": SNOWFLAKE_DARK_BLUE, "outline_color": SNOWFLAKE_DARK_BLUE
    })
    
    cloud_services_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": cloud_services_text_id,
        "text": "Cloud Services Layer",
        "x": 60, "y": 105, "width": 280, "height": 40,
        "font_size": 16, "color": WHITE, "bold": True, "alignment": "CENTER"
    })
    
    cloud_desc_id = generate_id()
    elements.append({
        "type": "text",
        "id": cloud_desc_id,
        "text": "• Query optimization\n• Security & access control\n• Metadata management",
        "x": 355, "y": 95, "width": 310, "height": 60,
        "font_size": 11, "color": DARK_GRAY, "bold": False, "alignment": "START"
    })
    
    # Layer 2: Compute Layer (Virtual Warehouses) - Middle
    compute_box_id = generate_id()
    elements.append({
        "type": "box",
        "id": compute_box_id,
        "x": 60, "y": 170, "width": 280, "height": 90,
        "fill_color": SNOWFLAKE_BLUE, "outline_color": SNOWFLAKE_BLUE
    })
    
    compute_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": compute_text_id,
        "text": "Compute Layer\n(Virtual Warehouses)",
        "x": 60, "y": 185, "width": 280, "height": 50,
        "font_size": 16, "color": WHITE, "bold": True, "alignment": "CENTER"
    })
    
    # Mini warehouse icons inside compute layer
    wh1_id = generate_id()
    elements.append({
        "type": "box",
        "id": wh1_id,
        "x": 80, "y": 230, "width": 55, "height": 22,
        "fill_color": WHITE, "outline_color": SNOWFLAKE_DARK_BLUE
    })
    wh1_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": wh1_text_id,
        "text": "WH-1",
        "x": 80, "y": 232, "width": 55, "height": 18,
        "font_size": 9, "color": SNOWFLAKE_DARK_BLUE, "bold": True, "alignment": "CENTER"
    })
    
    wh2_id = generate_id()
    elements.append({
        "type": "box",
        "id": wh2_id,
        "x": 145, "y": 230, "width": 55, "height": 22,
        "fill_color": WHITE, "outline_color": SNOWFLAKE_DARK_BLUE
    })
    wh2_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": wh2_text_id,
        "text": "WH-2",
        "x": 145, "y": 232, "width": 55, "height": 18,
        "font_size": 9, "color": SNOWFLAKE_DARK_BLUE, "bold": True, "alignment": "CENTER"
    })
    
    wh3_id = generate_id()
    elements.append({
        "type": "box",
        "id": wh3_id,
        "x": 210, "y": 230, "width": 55, "height": 22,
        "fill_color": WHITE, "outline_color": SNOWFLAKE_DARK_BLUE
    })
    wh3_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": wh3_text_id,
        "text": "WH-3",
        "x": 210, "y": 232, "width": 55, "height": 18,
        "font_size": 9, "color": SNOWFLAKE_DARK_BLUE, "bold": True, "alignment": "CENTER"
    })
    
    wh4_id = generate_id()
    elements.append({
        "type": "box",
        "id": wh4_id,
        "x": 275, "y": 230, "width": 55, "height": 22,
        "fill_color": WHITE, "outline_color": SNOWFLAKE_DARK_BLUE
    })
    wh4_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": wh4_text_id,
        "text": "WH-N",
        "x": 275, "y": 232, "width": 55, "height": 18,
        "font_size": 9, "color": SNOWFLAKE_DARK_BLUE, "bold": True, "alignment": "CENTER"
    })
    
    compute_desc_id = generate_id()
    elements.append({
        "type": "text",
        "id": compute_desc_id,
        "text": "• MPP query execution\n• Spin up/down instantly\n• Multiple isolated warehouses\n• Pay per-second usage",
        "x": 355, "y": 170, "width": 310, "height": 90,
        "font_size": 11, "color": DARK_GRAY, "bold": False, "alignment": "START"
    })
    
    # Layer 3: Storage Layer (Bottom)
    storage_box_id = generate_id()
    elements.append({
        "type": "box",
        "id": storage_box_id,
        "x": 60, "y": 275, "width": 280, "height": 60,
        "fill_color": "#1B5DBE", "outline_color": "#1B5DBE"
    })
    
    storage_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": storage_text_id,
        "text": "Storage Layer",
        "x": 60, "y": 285, "width": 280, "height": 40,
        "font_size": 16, "color": WHITE, "bold": True, "alignment": "CENTER"
    })
    
    storage_desc_id = generate_id()
    elements.append({
        "type": "text",
        "id": storage_desc_id,
        "text": "• Cloud object storage (S3/Azure/GCS)\n• Compressed columnar format\n• Auto micro-partitioning",
        "x": 355, "y": 275, "width": 310, "height": 60,
        "font_size": 11, "color": DARK_GRAY, "bold": False, "alignment": "START"
    })
    
    # === Key Benefits Section ===
    benefits_header_id = generate_id()
    elements.append({
        "type": "text",
        "id": benefits_header_id,
        "text": "Key Benefits:",
        "x": 60, "y": 350, "width": 150, "height": 22,
        "font_size": 12, "color": SNOWFLAKE_DARK_BLUE, "bold": True, "alignment": "START"
    })
    
    benefits_text_id = generate_id()
    elements.append({
        "type": "text",
        "id": benefits_text_id,
        "text": "• Scale compute without affecting storage  • No resource contention between workloads  • True pay-for-what-you-use pricing",
        "x": 60, "y": 370, "width": 620, "height": 30,
        "font_size": 11, "color": DARK_GRAY, "bold": False, "alignment": "START"
    })
    
    # Create all shapes and text boxes
    create_requests = []
    text_elements = []
    
    for elem in elements:
        if elem["type"] == "box":
            create_requests.append({
                "createShape": {
                    "objectId": elem["id"],
                    "shapeType": "ROUND_RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": elem["height"], "unit": "PT"},
                            "width": {"magnitude": elem["width"], "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": elem["x"],
                            "translateY": elem["y"],
                            "unit": "PT",
                        },
                    },
                }
            })
        else:
            # Text box
            create_requests.append({
                "createShape": {
                    "objectId": elem["id"],
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": elem["height"], "unit": "PT"},
                            "width": {"magnitude": elem["width"], "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": elem["x"],
                            "translateY": elem["y"],
                            "unit": "PT",
                        },
                    },
                }
            })
            create_requests.append({
                "insertText": {
                    "objectId": elem["id"],
                    "insertionIndex": 0,
                    "text": elem["text"],
                }
            })
            text_elements.append(elem)
    
    # Execute shape/textbox creation
    service.presentations().batchUpdate(
        presentationId=PRESENTATION_ID,
        body={"requests": create_requests}
    ).execute()
    
    # Apply styling to boxes
    style_requests = []
    for elem in elements:
        if elem["type"] == "box":
            style_requests.append(shape_background_request(elem["id"], elem["fill_color"]))
            style_requests.append(shape_outline_request(elem["id"], elem["outline_color"], weight=1.5))
    
    if style_requests:
        service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body={"requests": style_requests}
        ).execute()
    
    # Apply text styling
    text_style_requests = []
    for elem in text_elements:
        text_style_requests.append(text_style_request(
            elem["id"],
            bold=elem.get("bold", False),
            font_size=elem["font_size"],
            font_family="Open Sans" if not elem.get("bold") else "Montserrat",
            color=elem["color"],
        ))
        text_style_requests.append(paragraph_style_request(elem["id"], elem["alignment"]))
    
    if text_style_requests:
        service.presentations().batchUpdate(
            presentationId=PRESENTATION_ID,
            body={"requests": text_style_requests}
        ).execute()
    
    print(f"Added architecture slide to presentation!")
    print(f"URL: https://docs.google.com/presentation/d/{PRESENTATION_ID}/edit")

if __name__ == "__main__":
    add_architecture_slide()

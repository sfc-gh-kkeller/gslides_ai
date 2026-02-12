"""High-level deck builder for creating professional presentations."""

from dataclasses import dataclass, field
from typing import Any

from .slides import (
    get_slides_service,
    create_presentation,
    get_presentation,
    get_presentation_url,
    generate_id,
)
from .styling import (
    COLORS,
    get_color,
    text_style_request,
    paragraph_style_request,
    shape_background_request,
    shape_outline_request,
    slide_background_request,
)


# Slide dimensions (standard 16:9)
SLIDE_WIDTH = 720  # points
SLIDE_HEIGHT = 405  # points


@dataclass
class Theme:
    """Presentation theme with colors and fonts."""
    
    name: str = "snowflake"
    # Cover/title slide background
    primary_color: str = "snowflake_blue"
    # Divider/section slide background  
    secondary_color: str = "snowflake_dark_blue"
    # Accent for highlights
    accent_color: str = "snowflake_medium_blue"
    # Content slide background
    background_color: str = "white"
    # Main text color
    text_color: str = "dark_gray"
    # Fonts (matching Snowflake 2026 template)
    title_font: str = "Montserrat"
    body_font: str = "Open Sans"
    # Font sizes
    title_size: int = 40
    subtitle_size: int = 20
    heading_size: int = 28
    body_size: int = 16
    

THEMES = {
    "snowflake": Theme(),
    "snowflake_dark": Theme(
        name="snowflake_dark",
        background_color="snowflake_dark_blue",
        text_color="white",
        primary_color="snowflake_blue",
        secondary_color="snowflake_dark_blue",
    ),
    "minimal": Theme(
        name="minimal",
        primary_color="dark_gray",
        secondary_color="dark_gray",
        accent_color="snowflake_blue",
        title_font="Helvetica Neue",
        body_font="Helvetica Neue",
    ),
}


@dataclass
class TextElement:
    """A text element on a slide."""
    
    text: str
    x: float
    y: float
    width: float
    height: float
    font_size: int = 18
    font_family: str | None = None
    color: str | None = None
    bold: bool = False
    italic: bool = False
    alignment: str = "START"  # START, CENTER, END


@dataclass
class SlideContent:
    """Content for a single slide."""
    
    layout: str = "blank"
    background_color: str | None = None
    elements: list[TextElement] = field(default_factory=list)
    

class DeckBuilder:
    """Build professional presentations with a fluent API."""
    
    def __init__(self, title: str, theme: str | Theme = "snowflake"):
        self.title = title
        self.theme = THEMES.get(theme, theme) if isinstance(theme, str) else theme
        self.slides: list[SlideContent] = []
        self.presentation_id: str | None = None
        
    def add_title_slide(
        self,
        title: str,
        subtitle: str = "",
    ) -> "DeckBuilder":
        """Add a title slide."""
        slide = SlideContent(
            layout="blank",
            background_color=self.theme.primary_color,
            elements=[
                TextElement(
                    text=title,
                    x=50,
                    y=140,
                    width=620,
                    height=80,
                    font_size=self.theme.title_size,
                    font_family=self.theme.title_font,
                    color="white",
                    bold=True,
                    alignment="CENTER",
                ),
            ],
        )
        if subtitle:
            slide.elements.append(
                TextElement(
                    text=subtitle,
                    x=50,
                    y=230,
                    width=620,
                    height=50,
                    font_size=self.theme.subtitle_size,
                    font_family=self.theme.body_font,
                    color="white",
                    alignment="CENTER",
                )
            )
        self.slides.append(slide)
        return self
    
    def add_section_slide(
        self,
        title: str,
        subtitle: str = "",
    ) -> "DeckBuilder":
        """Add a section divider slide."""
        slide = SlideContent(
            layout="blank",
            background_color=self.theme.secondary_color,
            elements=[
                TextElement(
                    text=title,
                    x=50,
                    y=160,
                    width=620,
                    height=60,
                    font_size=self.theme.heading_size + 4,
                    font_family=self.theme.title_font,
                    color="white",
                    bold=True,
                    alignment="CENTER",
                ),
            ],
        )
        if subtitle:
            slide.elements.append(
                TextElement(
                    text=subtitle,
                    x=50,
                    y=230,
                    width=620,
                    height=40,
                    font_size=self.theme.body_size,
                    font_family=self.theme.body_font,
                    color="snowflake_blue",
                    alignment="CENTER",
                )
            )
        self.slides.append(slide)
        return self
    
    def add_content_slide(
        self,
        title: str,
        bullets: list[str],
        subtitle: str = "",
    ) -> "DeckBuilder":
        """Add a content slide with title and bullet points."""
        # Format bullets with bullet character
        bullet_text = "\n".join(f"•  {b}" for b in bullets)
        
        slide = SlideContent(
            layout="blank",
            background_color=self.theme.background_color,
            elements=[
                # Title bar background
                TextElement(
                    text=title,
                    x=40,
                    y=30,
                    width=640,
                    height=50,
                    font_size=self.theme.heading_size,
                    font_family=self.theme.title_font,
                    color=self.theme.primary_color,
                    bold=True,
                    alignment="START",
                ),
                # Bullet content
                TextElement(
                    text=bullet_text,
                    x=50,
                    y=100,
                    width=620,
                    height=280,
                    font_size=self.theme.body_size,
                    font_family=self.theme.body_font,
                    color=self.theme.text_color,
                    alignment="START",
                ),
            ],
        )
        if subtitle:
            slide.elements.insert(
                1,
                TextElement(
                    text=subtitle,
                    x=40,
                    y=75,
                    width=640,
                    height=25,
                    font_size=self.theme.body_size - 2,
                    font_family=self.theme.body_font,
                    color=self.theme.accent_color,
                    alignment="START",
                )
            )
        self.slides.append(slide)
        return self
    
    def add_two_column_slide(
        self,
        title: str,
        left_title: str,
        left_bullets: list[str],
        right_title: str,
        right_bullets: list[str],
    ) -> "DeckBuilder":
        """Add a two-column comparison slide."""
        left_text = "\n".join(f"•  {b}" for b in left_bullets)
        right_text = "\n".join(f"•  {b}" for b in right_bullets)
        
        slide = SlideContent(
            layout="blank",
            background_color=self.theme.background_color,
            elements=[
                # Main title
                TextElement(
                    text=title,
                    x=40,
                    y=25,
                    width=640,
                    height=45,
                    font_size=self.theme.heading_size,
                    font_family=self.theme.title_font,
                    color=self.theme.primary_color,
                    bold=True,
                    alignment="START",
                ),
                # Left column title
                TextElement(
                    text=left_title,
                    x=40,
                    y=85,
                    width=300,
                    height=30,
                    font_size=self.theme.body_size + 2,
                    font_family=self.theme.title_font,
                    color=self.theme.secondary_color,
                    bold=True,
                    alignment="START",
                ),
                # Left column content
                TextElement(
                    text=left_text,
                    x=40,
                    y=120,
                    width=300,
                    height=250,
                    font_size=self.theme.body_size - 2,
                    font_family=self.theme.body_font,
                    color=self.theme.text_color,
                    alignment="START",
                ),
                # Right column title
                TextElement(
                    text=right_title,
                    x=380,
                    y=85,
                    width=300,
                    height=30,
                    font_size=self.theme.body_size + 2,
                    font_family=self.theme.title_font,
                    color=self.theme.secondary_color,
                    bold=True,
                    alignment="START",
                ),
                # Right column content
                TextElement(
                    text=right_text,
                    x=380,
                    y=120,
                    width=300,
                    height=250,
                    font_size=self.theme.body_size - 2,
                    font_family=self.theme.body_font,
                    color=self.theme.text_color,
                    alignment="START",
                ),
            ],
        )
        self.slides.append(slide)
        return self
    
    def add_quote_slide(
        self,
        quote: str,
        attribution: str = "",
    ) -> "DeckBuilder":
        """Add a quote/callout slide."""
        slide = SlideContent(
            layout="blank",
            background_color=self.theme.primary_color,
            elements=[
                TextElement(
                    text=f'"{quote}"',
                    x=60,
                    y=120,
                    width=600,
                    height=150,
                    font_size=self.theme.subtitle_size,
                    font_family=self.theme.title_font,
                    color="white",
                    italic=True,
                    alignment="CENTER",
                ),
            ],
        )
        if attribution:
            slide.elements.append(
                TextElement(
                    text=f"— {attribution}",
                    x=60,
                    y=280,
                    width=600,
                    height=30,
                    font_size=self.theme.body_size,
                    font_family=self.theme.body_font,
                    color="white",
                    alignment="CENTER",
                )
            )
        self.slides.append(slide)
        return self
    
    def add_closing_slide(
        self,
        title: str = "Thank You",
        contact: str = "",
    ) -> "DeckBuilder":
        """Add a closing slide."""
        slide = SlideContent(
            layout="blank",
            background_color=self.theme.secondary_color,
            elements=[
                TextElement(
                    text=title,
                    x=50,
                    y=150,
                    width=620,
                    height=70,
                    font_size=self.theme.title_size,
                    font_family=self.theme.title_font,
                    color="white",
                    bold=True,
                    alignment="CENTER",
                ),
            ],
        )
        if contact:
            slide.elements.append(
                TextElement(
                    text=contact,
                    x=50,
                    y=240,
                    width=620,
                    height=40,
                    font_size=self.theme.body_size,
                    font_family=self.theme.body_font,
                    color="snowflake_blue",
                    alignment="CENTER",
                )
            )
        self.slides.append(slide)
        return self
    
    def build(self) -> str:
        """Build the presentation and return its ID."""
        service = get_slides_service()
        
        # Create the presentation
        result = create_presentation(self.title)
        self.presentation_id = result["presentationId"]
        
        # Get the default slide to delete later
        pres = get_presentation(self.presentation_id)
        default_slide_id = pres["slides"][0]["objectId"]
        
        # Build all slides
        all_requests = []
        slide_ids = []
        
        for i, slide_content in enumerate(self.slides):
            slide_id = generate_id()
            slide_ids.append(slide_id)
            
            # Create the slide
            all_requests.append({
                "createSlide": {
                    "objectId": slide_id,
                    "insertionIndex": i + 1,  # After default slide
                }
            })
        
        # Execute slide creation
        if all_requests:
            service.presentations().batchUpdate(
                presentationId=self.presentation_id,
                body={"requests": all_requests}
            ).execute()
        
        # Now add content to each slide
        for slide_id, slide_content in zip(slide_ids, self.slides):
            self._populate_slide(service, slide_id, slide_content)
        
        # Delete the default slide
        service.presentations().batchUpdate(
            presentationId=self.presentation_id,
            body={"requests": [{"deleteObject": {"objectId": default_slide_id}}]}
        ).execute()
        
        return self.presentation_id
    
    def _populate_slide(
        self,
        service,
        slide_id: str,
        content: SlideContent,
    ) -> None:
        """Populate a slide with content."""
        requests = []
        element_ids = []
        
        # Set background color
        if content.background_color:
            requests.append(slide_background_request(slide_id, content.background_color))
        
        # Create text elements
        for elem in content.elements:
            elem_id = generate_id()
            element_ids.append((elem_id, elem))
            
            # Create text box
            requests.append({
                "createShape": {
                    "objectId": elem_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "height": {"magnitude": elem.height, "unit": "PT"},
                            "width": {"magnitude": elem.width, "unit": "PT"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": elem.x,
                            "translateY": elem.y,
                            "unit": "PT",
                        },
                    },
                }
            })
            
            # Insert text
            requests.append({
                "insertText": {
                    "objectId": elem_id,
                    "insertionIndex": 0,
                    "text": elem.text,
                }
            })
        
        # Execute shape creation and text insertion
        if requests:
            service.presentations().batchUpdate(
                presentationId=self.presentation_id,
                body={"requests": requests}
            ).execute()
        
        # Apply text styling (separate batch for reliability)
        style_requests = []
        for elem_id, elem in element_ids:
            # Text style
            style_requests.append(text_style_request(
                elem_id,
                bold=elem.bold,
                italic=elem.italic,
                font_size=elem.font_size,
                font_family=elem.font_family or self.theme.body_font,
                color=elem.color or self.theme.text_color,
            ))
            
            # Paragraph alignment
            style_requests.append(paragraph_style_request(elem_id, elem.alignment))
        
        if style_requests:
            service.presentations().batchUpdate(
                presentationId=self.presentation_id,
                body={"requests": style_requests}
            ).execute()
    
    def get_url(self) -> str:
        """Get the presentation URL."""
        if not self.presentation_id:
            raise ValueError("Presentation not built yet. Call build() first.")
        return get_presentation_url(self.presentation_id)

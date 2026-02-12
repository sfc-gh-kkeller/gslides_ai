"""CLI interface for Google Slides generation."""

import json
import webbrowser

import click
from rich.console import Console
from rich.table import Table

from . import auth, slides

console = Console()


@click.group()
@click.version_option()
def cli():
    """Google Slides CLI - Generate presentations programmatically."""
    pass


# Authentication commands

@cli.command()
@click.option(
    "--oauth", is_flag=True,
    help="Use OAuth with credentials.json file instead of gcloud.",
)
@click.option(
    "--credentials", "-c",
    type=click.Path(exists=True),
    help="Path to OAuth credentials.json file (only with --oauth).",
)
def auth_cmd(oauth, credentials):
    """Authenticate with Google.
    
    By default, uses gcloud CLI which opens a browser for SSO login.
    Use --oauth to authenticate with a credentials.json file instead.
    """
    try:
        if oauth:
            from pathlib import Path
            creds_path = Path(credentials) if credentials else None
            auth.authenticate_with_oauth(creds_path)
            console.print("[green]✓[/green] Successfully authenticated via OAuth!")
            console.print(f"Token saved to: {auth.get_token_path()}")
        else:
            console.print("Opening browser for Google SSO login...")
            auth.authenticate_with_gcloud()
            console.print("[green]✓[/green] Successfully authenticated via gcloud!")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        raise SystemExit(1)


# Register with proper name
cli.add_command(auth_cmd, name="auth")


@cli.command()
def status():
    """Check authentication status."""
    if auth.is_authenticated():
        method = auth.get_auth_method()
        console.print("[green]✓[/green] Authenticated")
        if method == "gcloud":
            console.print("Method: gcloud Application Default Credentials")
        elif method == "oauth":
            console.print(f"Method: OAuth token at {auth.get_token_path()}")
    else:
        console.print("[yellow]![/yellow] Not authenticated")
        console.print("Run 'gslides auth' to authenticate via browser SSO.")


# Presentation commands

@cli.command()
@click.argument("title")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def create(title, json_output):
    """Create a new presentation."""
    try:
        result = slides.create_presentation(title)
        presentation_id = result["presentationId"]
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[green]✓[/green] Created presentation: {title}")
            console.print(f"ID: {presentation_id}")
            console.print(f"URL: {slides.get_presentation_url(presentation_id)}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("presentation_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def get(presentation_id, json_output):
    """Get presentation metadata."""
    try:
        result = slides.get_presentation(presentation_id)
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[bold]Title:[/bold] {result.get('title', 'Untitled')}")
            console.print(f"[bold]ID:[/bold] {result['presentationId']}")
            console.print(f"[bold]Slides:[/bold] {len(result.get('slides', []))}")
            console.print(f"[bold]URL:[/bold] {slides.get_presentation_url(presentation_id)}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command("list-slides")
@click.argument("presentation_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def list_slides_cmd(presentation_id, json_output):
    """List all slides in a presentation."""
    try:
        slide_list = slides.list_slides(presentation_id)
        
        if json_output:
            click.echo(json.dumps(slide_list, indent=2))
        else:
            table = Table(title="Slides")
            table.add_column("Index", style="cyan")
            table.add_column("Slide ID", style="green")
            table.add_column("Elements", style="yellow")
            
            for i, slide in enumerate(slide_list):
                elements = len(slide.get("pageElements", []))
                table.add_row(str(i), slide["objectId"], str(elements))
            
            console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command()
@click.argument("presentation_id")
def open_cmd(presentation_id):
    """Open presentation in browser."""
    url = slides.get_presentation_url(presentation_id)
    webbrowser.open(url)
    console.print(f"[green]✓[/green] Opened: {url}")


cli.add_command(open_cmd, name="open")


# Slide commands

@cli.command("add-slide")
@click.argument("presentation_id")
@click.option(
    "--layout", "-l",
    default="blank",
    type=click.Choice(list(slides.LAYOUTS.keys())),
    help="Slide layout.",
)
@click.option("--index", "-i", type=int, help="Insertion index.")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def add_slide_cmd(presentation_id, layout, index, json_output):
    """Add a new slide to the presentation."""
    try:
        result = slides.add_slide(presentation_id, layout, index)
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[green]✓[/green] Added slide: {result['slideId']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command("delete-slide")
@click.argument("presentation_id")
@click.argument("slide_id")
def delete_slide_cmd(presentation_id, slide_id):
    """Delete a slide from the presentation."""
    try:
        slides.delete_slide(presentation_id, slide_id)
        console.print(f"[green]✓[/green] Deleted slide: {slide_id}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


# Element commands

@cli.command("add-text")
@click.argument("presentation_id")
@click.argument("slide_id")
@click.argument("text")
@click.option("--x", default=100.0, help="X position in points.")
@click.option("--y", default=100.0, help="Y position in points.")
@click.option("--width", "-w", default=400.0, help="Width in points.")
@click.option("--height", "-h", default=50.0, help="Height in points.")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def add_text_cmd(presentation_id, slide_id, text, x, y, width, height, json_output):
    """Add a text box to a slide."""
    try:
        result = slides.add_text_box(
            presentation_id, slide_id, text, x, y, width, height
        )
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[green]✓[/green] Added text box: {result['textBoxId']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command("add-image")
@click.argument("presentation_id")
@click.argument("slide_id")
@click.argument("image_url")
@click.option("--x", default=100.0, help="X position in points.")
@click.option("--y", default=100.0, help="Y position in points.")
@click.option("--width", "-w", default=300.0, help="Width in points.")
@click.option("--height", "-h", default=200.0, help="Height in points.")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def add_image_cmd(presentation_id, slide_id, image_url, x, y, width, height, json_output):
    """Add an image to a slide (URL must be publicly accessible)."""
    try:
        result = slides.add_image(
            presentation_id, slide_id, image_url, x, y, width, height
        )
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[green]✓[/green] Added image: {result['imageId']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command("add-shape")
@click.argument("presentation_id")
@click.argument("slide_id")
@click.option(
    "--type", "-t", "shape_type",
    default="rectangle",
    type=click.Choice(list(slides.SHAPE_TYPES.keys())),
    help="Shape type.",
)
@click.option("--x", default=100.0, help="X position in points.")
@click.option("--y", default=100.0, help="Y position in points.")
@click.option("--width", "-w", default=100.0, help="Width in points.")
@click.option("--height", "-h", default=100.0, help="Height in points.")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def add_shape_cmd(presentation_id, slide_id, shape_type, x, y, width, height, json_output):
    """Add a shape to a slide."""
    try:
        result = slides.add_shape(
            presentation_id, slide_id, shape_type, x, y, width, height
        )
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[green]✓[/green] Added shape: {result['shapeId']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command("add-table")
@click.argument("presentation_id")
@click.argument("slide_id")
@click.option("--rows", "-r", default=3, help="Number of rows.")
@click.option("--cols", "-c", default=3, help="Number of columns.")
@click.option("--x", default=100.0, help="X position in points.")
@click.option("--y", default=100.0, help="Y position in points.")
@click.option("--width", "-w", default=400.0, help="Width in points.")
@click.option("--height", "-h", default=200.0, help="Height in points.")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
def add_table_cmd(presentation_id, slide_id, rows, cols, x, y, width, height, json_output):
    """Add a table to a slide."""
    try:
        result = slides.add_table(
            presentation_id, slide_id, rows, cols, x, y, width, height
        )
        
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            console.print(f"[green]✓[/green] Added table: {result['tableId']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@cli.command("set-cell")
@click.argument("presentation_id")
@click.argument("table_id")
@click.argument("row", type=int)
@click.argument("column", type=int)
@click.argument("text")
def set_cell_cmd(presentation_id, table_id, row, column, text):
    """Set text in a table cell."""
    try:
        slides.update_table_cell(presentation_id, table_id, row, column, text)
        console.print(f"[green]✓[/green] Updated cell ({row}, {column})")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


# Utility commands

@cli.command()
def layouts():
    """List available slide layouts."""
    table = Table(title="Available Layouts")
    table.add_column("Name", style="cyan")
    table.add_column("API Value", style="green")
    
    for name, value in slides.LAYOUTS.items():
        table.add_row(name, value)
    
    console.print(table)


@cli.command()
def shapes():
    """List available shape types."""
    table = Table(title="Available Shapes")
    table.add_column("Name", style="cyan")
    table.add_column("API Value", style="green")
    
    for name, value in slides.SHAPE_TYPES.items():
        table.add_row(name, value)
    
    console.print(table)


if __name__ == "__main__":
    cli()

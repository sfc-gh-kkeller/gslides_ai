"""GSlides AI Desktop App - Chat interface with Cortex Code integration."""

import flet as ft
import sqlite3
import json
import os
import subprocess
import sys
import threading
import queue
import webbrowser
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

# App version - update this for each release
APP_VERSION = "1.0.0"
GITHUB_REPO = "sfc-gh-kkeller/gslides_ai"

# Snowflake brand colors
SNOWFLAKE_BLUE = "#29B5E7"
SNOWFLAKE_DARK_BLUE = "#11567F"
SNOWFLAKE_MEDIUM_BLUE = "#1B5DBE"
DARK_GRAY = "#222222"
LIGHT_GRAY = "#F5F5F5"
SIDEBAR_BG = "#1a1a2e"
SIDEBAR_HOVER = "#16213e"

# App data directory
APP_DATA_DIR = Path.home() / ".gslides_ai"
DB_PATH = APP_DATA_DIR / "data.db"
THEMES_DIR = APP_DATA_DIR / "themes"


class Database:
    """SQLite database for chat history and projects."""
    
    def __init__(self):
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        THEMES_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self):
        cursor = self.conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                project_id TEXT,
                presentation_url TEXT,
                theme TEXT DEFAULT 'snowflake_2026',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                content TEXT NOT NULL,
                is_user BOOLEAN NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.conn.commit()
    
    # Project methods
    def create_project(self, name: str) -> str:
        id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (id, name))
        self.conn.commit()
        return id
    
    def get_projects(self) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM projects ORDER BY name")
        return [{"id": r[0], "name": r[1], "created_at": r[2]} for r in cursor.fetchall()]
    
    def rename_project(self, id: str, name: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE projects SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (name, id))
        self.conn.commit()
    
    def delete_project(self, id: str):
        cursor = self.conn.cursor()
        # Move chats out of project first
        cursor.execute("UPDATE chats SET project_id = NULL WHERE project_id = ?", (id,))
        cursor.execute("DELETE FROM projects WHERE id = ?", (id,))
        self.conn.commit()
    
    # Chat methods
    def create_chat(self, title: str = "New Chat", project_id: str = None) -> str:
        id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO chats (id, title, project_id) VALUES (?, ?, ?)",
            (id, title, project_id)
        )
        self.conn.commit()
        return id
    
    def get_recent_chats(self, limit: int = 20) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, project_id, presentation_url, theme, created_at, updated_at
            FROM chats ORDER BY updated_at DESC LIMIT ?
        """, (limit,))
        return [{"id": r[0], "title": r[1], "project_id": r[2], "presentation_url": r[3], 
                 "theme": r[4], "created_at": r[5], "updated_at": r[6]} for r in cursor.fetchall()]
    
    def get_project_chats(self, project_id: str) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, project_id, presentation_url, theme, created_at, updated_at
            FROM chats WHERE project_id = ? ORDER BY updated_at DESC
        """, (project_id,))
        return [{"id": r[0], "title": r[1], "project_id": r[2], "presentation_url": r[3],
                 "theme": r[4], "created_at": r[5], "updated_at": r[6]} for r in cursor.fetchall()]
    
    def get_chat(self, id: str) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, project_id, presentation_url, theme FROM chats WHERE id = ?", (id,))
        r = cursor.fetchone()
        if r:
            return {"id": r[0], "title": r[1], "project_id": r[2], "presentation_url": r[3], "theme": r[4]}
        return None
    
    def update_chat(self, id: str, title: str = None, project_id: str = None, presentation_url: str = None):
        cursor = self.conn.cursor()
        updates = ["updated_at = CURRENT_TIMESTAMP"]
        params = []
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if project_id is not None:
            updates.append("project_id = ?")
            params.append(project_id if project_id != "" else None)
        if presentation_url is not None:
            updates.append("presentation_url = ?")
            params.append(presentation_url)
        params.append(id)
        cursor.execute(f"UPDATE chats SET {', '.join(updates)} WHERE id = ?", params)
        self.conn.commit()
    
    def move_chat_to_project(self, chat_id: str, project_id: Optional[str]):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE chats SET project_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                       (project_id, chat_id))
        self.conn.commit()
    
    def delete_chat(self, id: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (id,))
        cursor.execute("DELETE FROM chats WHERE id = ?", (id,))
        self.conn.commit()
    
    # Message methods
    def add_message(self, chat_id: str, content: str, is_user: bool) -> str:
        id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO messages (id, chat_id, content, is_user) VALUES (?, ?, ?, ?)",
            (id, chat_id, content, is_user)
        )
        cursor.execute("UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (chat_id,))
        self.conn.commit()
        return id
    
    def get_messages(self, chat_id: str) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, content, is_user, created_at FROM messages WHERE chat_id = ? ORDER BY created_at",
            (chat_id,)
        )
        return [{"id": r[0], "content": r[1], "is_user": r[2], "created_at": r[3]} for r in cursor.fetchall()]
    
    # Settings
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        r = cursor.fetchone()
        return r[0] if r else default
    
    def set_setting(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()


class ChatMessage(ft.Container):
    """A chat message bubble."""
    
    def __init__(self, text: str, is_user: bool = True, is_thinking: bool = False, page: ft.Page = None):
        if is_thinking:
            content = ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=SNOWFLAKE_BLUE),
                ft.Text("Thinking...", size=14, color="#666666", italic=True),
            ], spacing=10)
            bgcolor = "#F8F8F8"
        else:
            content = ft.Markdown(
                text,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme=ft.MarkdownCodeTheme.GITHUB,
                on_tap_link=lambda e: webbrowser.open(e.data),
            )
            bgcolor = SNOWFLAKE_BLUE if is_user else "#F0F0F0"
        
        super().__init__(
            content=ft.Container(
                content=content,
                padding=ft.Padding(left=15, right=15, top=10, bottom=10),
                bgcolor=bgcolor,
                border_radius=15,
            ),
            alignment=ft.Alignment(1, 0) if is_user else ft.Alignment(-1, 0),
            margin=ft.Margin(left=50 if is_user else 10, right=10 if is_user else 50, top=5, bottom=5),
        )


class StreamingChatMessage(ft.Container):
    """A chat message that streams content in real-time."""
    
    def __init__(self):
        self.status_text = ft.Text("Starting...", size=12, color="#666666", italic=True)
        self.output_markdown = ft.Markdown(
            "",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.GITHUB,
            on_tap_link=lambda e: webbrowser.open(e.data),
        )
        self.progress = ft.ProgressRing(width=14, height=14, stroke_width=2, color=SNOWFLAKE_BLUE)
        self.tool_chips = ft.Row(wrap=True, spacing=5)
        
        self._content_column = ft.Column([
            ft.Row([self.progress, self.status_text], spacing=8),
            self.tool_chips,
            self.output_markdown,
        ], spacing=8, tight=True)
        
        super().__init__(
            content=ft.Container(
                content=self._content_column,
                padding=ft.Padding(left=15, right=15, top=10, bottom=10),
                bgcolor="#F8F8F8",
                border_radius=15,
            ),
            alignment=ft.Alignment(-1, 0),
            margin=ft.Margin(left=10, right=50, top=5, bottom=5),
        )
        self._tools_seen = set()
        self._full_output = []
    
    def update_status(self, status: str):
        """Update the status text."""
        self.status_text.value = status
    
    def add_tool(self, tool_name: str):
        """Add a tool chip."""
        if tool_name not in self._tools_seen:
            self._tools_seen.add(tool_name)
            chip = ft.Container(
                content=ft.Text(tool_name, size=10, color="#FFFFFF"),
                bgcolor=SNOWFLAKE_DARK_BLUE,
                padding=ft.Padding(left=8, right=8, top=3, bottom=3),
                border_radius=10,
            )
            self.tool_chips.controls.append(chip)
    
    def append_line(self, line: str):
        """Append a line to output."""
        self._full_output.append(line)
        # Show last 15 lines during streaming
        recent = self._full_output[-15:] if len(self._full_output) > 15 else self._full_output
        self.output_markdown.value = '\n'.join(recent)
    
    def set_output(self, text: str):
        """Set the output text."""
        self.output_markdown.value = text
    
    def finish(self, final_text: str = None):
        """Mark as finished and set final markdown content."""
        self.progress.visible = False
        self.status_text.value = "Complete"
        self.status_text.color = "#28a745"
        if final_text:
            self.output_markdown.value = final_text


class GSlidesChatApp:
    """Main application with sidebar navigation."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "GSlides AI for Snowflake (powered by CoCo)"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.bgcolor = "#FFFFFF"
        
        # Database
        self.db = Database()
        
        # State
        self.current_chat_id: Optional[str] = None
        self.current_view = "chats"  # chats, projects, settings
        self.output_queue = queue.Queue()
        self.is_processing = False
        self.active_process = None  # Track running cortex process
        self.active_streaming_msg = None  # Track streaming message widget
        self.processing_chat_id = None  # Which chat is being processed
        self.processing_chat_name = None  # Name of chat being processed
        
        # Check Google auth status
        self.is_authenticated = self._check_google_auth()
        
        # Check cortex
        self.cortex_available = self._check_cortex()
        
        self._build_ui()
    
    def _check_google_auth(self) -> bool:
        """Check if user is authenticated with Google (quick check)."""
        try:
            # Quick check - just look for token file existence
            from pathlib import Path
            token_path = Path.home() / ".config" / "gslides_ai" / "token.json"
            adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
            return token_path.exists() or adc_path.exists()
        except:
            return False
    
    def _check_cortex(self) -> bool:
        """Check if cortex CLI is available."""
        try:
            result = subprocess.run(["which", "cortex"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_for_updates(self):
        """Check GitHub for available updates (runs in background)."""
        def check():
            try:
                url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("tag_name", "").lstrip("v")
                    
                    if latest_version and self._is_newer_version(latest_version, APP_VERSION):
                        # Find download URL for current architecture
                        download_url = None
                        import platform
                        arch = platform.machine()
                        
                        for asset in data.get("assets", []):
                            name = asset.get("name", "").lower()
                            if arch == "arm64" and "arm" in name:
                                download_url = asset.get("browser_download_url")
                                break
                            elif arch == "x86_64" and "intel" in name:
                                download_url = asset.get("browser_download_url")
                                break
                        
                        # Fallback to first zip if no arch-specific found
                        if not download_url:
                            for asset in data.get("assets", []):
                                if asset.get("name", "").endswith(".zip"):
                                    download_url = asset.get("browser_download_url")
                                    break
                        
                        if download_url:
                            self.page.run_thread(
                                lambda: self._show_update_dialog(latest_version, download_url, data.get("body", ""))
                            )
            except Exception as e:
                print(f"Update check failed: {e}")
        
        threading.Thread(target=check, daemon=True).start()
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (e.g., '1.2.0' > '1.1.0')."""
        try:
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]
            return latest_parts > current_parts
        except:
            return False
    
    def _show_update_dialog(self, version: str, download_url: str, changelog: str):
        """Show dialog when update is available."""
        def do_update(e):
            dialog.open = False
            self.page.update()
            self._launch_updater(download_url)
        
        def dismiss(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SYSTEM_UPDATE, color=SNOWFLAKE_BLUE, size=28),
                ft.Text("Update Available", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Column([
                ft.Text(f"Version {version} is available!", size=14),
                ft.Text(f"You have version {APP_VERSION}", size=12, color="#666666"),
                ft.Container(height=10),
                ft.Text("What's New:", size=12, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=ft.Markdown(
                        changelog[:500] + ("..." if len(changelog) > 500 else ""),
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    ),
                    height=150,
                    border=ft.border.all(1, "#E0E0E0"),
                    border_radius=8,
                    padding=10,
                ),
            ], tight=True, spacing=5, width=400),
            actions=[
                ft.TextButton("Later", on_click=dismiss),
                ft.ElevatedButton(
                    "Update Now",
                    icon=ft.Icons.DOWNLOAD,
                    bgcolor=SNOWFLAKE_BLUE,
                    color="#FFFFFF",
                    on_click=do_update,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _launch_updater(self, download_url: str):
        """Launch the updater and quit the app."""
        # Get path to updater script
        updater_path = Path(__file__).parent / "updater.py"
        
        # Get path to current app bundle (if running as .app)
        # When running as .app, sys.executable points to the Python inside the bundle
        app_path = None
        if ".app" in sys.executable:
            # Extract .app path from executable path
            parts = sys.executable.split(".app")
            app_path = parts[0] + ".app"
        else:
            # Running in development mode - use a placeholder
            app_path = str(Path.home() / "Applications" / "GSlides AI.app")
        
        # Launch updater
        pid = os.getpid()
        subprocess.Popen([
            sys.executable,
            str(updater_path),
            download_url,
            app_path,
            "--main-pid", str(pid),
        ])
        
        # Give updater time to start, then quit
        import time
        time.sleep(0.5)
        self.page.window.close()
    
    def _build_ui(self):
        """Build the main UI with sidebar."""
        # Sidebar
        self.sidebar = self._build_sidebar()
        
        # Main content area
        self.content_area = ft.Container(expand=True, bgcolor="#FFFFFF")
        
        # Layout
        self.page.add(
            ft.Row([
                self.sidebar,
                ft.VerticalDivider(width=1, color="#E0E0E0"),
                self.content_area,
            ], spacing=0, expand=True)
        )
        
        # Show chats view by default
        self._show_chats_view()
        
        # Check for updates in background
        self._check_for_updates()
    
    def _build_sidebar(self) -> ft.Container:
        """Build the sidebar navigation."""
        # Logo/header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color=SNOWFLAKE_BLUE, size=24),
                ft.Text("GSlides AI", size=18, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ], spacing=10),
            padding=ft.Padding(left=15, right=15, top=20, bottom=15),
        )
        
        # New chat button
        new_chat_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, color="#FFFFFF", size=18),
                ft.Text("New Chat", color="#FFFFFF", size=14),
            ], spacing=10),
            padding=ft.Padding(left=15, right=15, top=10, bottom=10),
            border_radius=8,
            bgcolor=SNOWFLAKE_BLUE,
            on_click=lambda e: self._new_chat(),
            ink=True,
        )
        
        # Navigation items
        def nav_item(icon, label, view_name):
            is_active = self.current_view == view_name
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=SNOWFLAKE_BLUE if is_active else "#888888", size=20),
                    ft.Text(label, color="#FFFFFF" if is_active else "#AAAAAA", size=14),
                ], spacing=12),
                padding=ft.Padding(left=15, right=15, top=12, bottom=12),
                bgcolor=SIDEBAR_HOVER if is_active else None,
                border_radius=8,
                on_click=lambda e, v=view_name: self._switch_view(v),
            )
        
        self.nav_chats = nav_item(ft.Icons.CHAT_BUBBLE_OUTLINE, "Chats", "chats")
        self.nav_projects = nav_item(ft.Icons.FOLDER_OUTLINED, "Projects", "projects")
        self.nav_themes = nav_item(ft.Icons.PALETTE_OUTLINED, "Themes", "themes")
        self.nav_settings = nav_item(ft.Icons.SETTINGS_OUTLINED, "Settings", "settings")
        
        # Auth status - clicking goes to settings
        auth_status = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if self.is_authenticated else ft.Icons.WARNING,
                    color="#4CAF50" if self.is_authenticated else "#FF9800",
                    size=16,
                ),
                ft.Text(
                    "Google Connected" if self.is_authenticated else "Not Signed In",
                    color="#AAAAAA",
                    size=12,
                ),
            ], spacing=8),
            padding=ft.Padding(left=15, right=15, top=10, bottom=10),
            on_click=lambda e: self._switch_view("settings"),
        )
        
        # Global processing indicator
        self.processing_indicator = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=14, height=14, stroke_width=2, color=SNOWFLAKE_BLUE),
                ft.Column([
                    ft.Text("Processing...", size=11, color="#FFFFFF", weight=ft.FontWeight.W_500),
                    ft.Text("", size=10, color="#AAAAAA"),  # Chat name placeholder
                ], spacing=1, tight=True),
            ], spacing=8),
            padding=ft.Padding(left=15, right=15, top=8, bottom=8),
            bgcolor="#2A2A3A",
            border_radius=8,
            visible=False,
            on_click=lambda e: self._go_to_processing_chat(),
        )
        
        # About button (opens dialog, not a view)
        about_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#888888", size=20),
                ft.Text("About", color="#AAAAAA", size=14),
            ], spacing=12),
            padding=ft.Padding(left=15, right=15, top=12, bottom=12),
            border_radius=8,
            on_click=lambda e: self._show_about_dialog(),
        )
        
        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=new_chat_btn,
                    padding=ft.Padding(left=10, right=10, top=0, bottom=15),
                ),
                ft.Divider(height=1, color="#333344"),
                self.nav_chats,
                self.nav_projects,
                self.nav_themes,
                ft.Container(expand=True),
                self.processing_indicator,  # Global processing status
                ft.Divider(height=1, color="#333344"),
                self.nav_settings,
                about_btn,
                auth_status,
            ], spacing=2),
            width=220,
            bgcolor=SIDEBAR_BG,
        )
    
    def _switch_view(self, view_name: str):
        """Switch the main content view."""
        self.current_view = view_name
        
        # Rebuild sidebar to update active state
        # Indices: 0=header, 1=new_chat_btn, 2=divider, 3=chats, 4=projects, 5=themes, 
        #          6=expand, 7=processing_indicator, 8=divider, 9=settings, 10=about, 11=auth
        self.sidebar.content.controls[3] = self._build_nav_item(ft.Icons.CHAT_BUBBLE_OUTLINE, "Chats", "chats")
        self.sidebar.content.controls[4] = self._build_nav_item(ft.Icons.FOLDER_OUTLINED, "Projects", "projects")
        self.sidebar.content.controls[5] = self._build_nav_item(ft.Icons.PALETTE_OUTLINED, "Themes", "themes")
        self.sidebar.content.controls[9] = self._build_nav_item(ft.Icons.SETTINGS_OUTLINED, "Settings", "settings")
        
        if view_name == "chats":
            self._show_chats_view()
        elif view_name == "projects":
            self._show_projects_view()
        elif view_name == "themes":
            self._show_themes_view()
        elif view_name == "settings":
            self._show_settings_view()
        
        self.page.update()
    
    def _build_nav_item(self, icon, label, view_name):
        is_active = self.current_view == view_name
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=SNOWFLAKE_BLUE if is_active else "#888888", size=20),
                ft.Text(label, color="#FFFFFF" if is_active else "#AAAAAA", size=14),
            ], spacing=12),
            padding=ft.Padding(left=15, right=15, top=12, bottom=12),
            bgcolor=SIDEBAR_HOVER if is_active else None,
            border_radius=8,
            on_click=lambda e, v=view_name: self._switch_view(v),
        )
    
    def _show_chats_view(self):
        """Show the chats list view."""
        chats = self.db.get_recent_chats()
        
        chat_items = []
        for chat in chats:
            chat_items.append(self._build_chat_list_item(chat))
        
        if not chat_items:
            chat_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=48, color="#CCCCCC"),
                        ft.Text("No chats yet", size=16, color="#999999"),
                        ft.Text("Click 'New Chat' to get started", size=13, color="#BBBBBB"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=50,
                    alignment=ft.Alignment(0, 0),
                )
            )
        
        self.content_area.content = ft.Column([
            ft.Container(
                content=ft.Text("Recent Chats", size=20, weight=ft.FontWeight.BOLD),
                padding=ft.Padding(left=20, right=20, top=20, bottom=10),
            ),
            ft.ListView(
                controls=chat_items,
                spacing=5,
                padding=ft.Padding(left=15, right=15, top=5, bottom=15),
                expand=True,
            ),
        ], spacing=0, expand=True)
        self.page.update()
    
    def _build_chat_list_item(self, chat: dict) -> ft.Container:
        """Build a chat list item."""
        row_controls = [
            ft.Icon(ft.Icons.CHAT, color=SNOWFLAKE_BLUE, size=20),
            ft.Column([
                ft.Text(chat["title"], size=14, weight=ft.FontWeight.W_500),
                ft.Text(chat["updated_at"][:16] if chat["updated_at"] else "", size=11, color="#999999"),
            ], spacing=2, expand=True),
        ]
        
        # Add presentation link if exists
        if chat.get("presentation_url"):
            row_controls.append(
                ft.IconButton(
                    ft.Icons.OPEN_IN_NEW,
                    icon_color=SNOWFLAKE_BLUE,
                    icon_size=18,
                    tooltip="Open Presentation",
                    on_click=lambda e, url=chat["presentation_url"]: webbrowser.open(url),
                )
            )
        
        row_controls.append(
            ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                icon_size=18,
                items=[
                    ft.PopupMenuItem(content="Move to Project", on_click=lambda e, c=chat: self._show_move_dialog(c)),
                    ft.PopupMenuItem(content="Rename", on_click=lambda e, c=chat: self._show_rename_dialog(c)),
                    ft.PopupMenuItem(content="Delete", on_click=lambda e, c=chat: self._delete_chat(c["id"])),
                ],
            )
        )
        
        return ft.Container(
            content=ft.Row(row_controls, spacing=12),
            padding=ft.Padding(left=15, right=10, top=12, bottom=12),
            border_radius=8,
            bgcolor="#F8F8F8",
            on_click=lambda e, c=chat: self._open_chat(c["id"]),
            ink=True,
        )
    
    def _show_projects_view(self):
        """Show projects management view."""
        projects = self.db.get_projects()
        
        project_items = []
        for project in projects:
            chats = self.db.get_project_chats(project["id"])
            project_items.append(self._build_project_item(project, len(chats)))
        
        # Add new project button
        new_project_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, color=SNOWFLAKE_BLUE, size=20),
                ft.Text("New Project", color=SNOWFLAKE_BLUE, size=14),
            ], spacing=10),
            padding=ft.Padding(left=15, right=15, top=12, bottom=12),
            border_radius=8,
            border=ft.Border.all(1, SNOWFLAKE_BLUE),
            on_click=lambda e: self._show_new_project_dialog(),
            ink=True,
        )
        
        self.content_area.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Projects", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    new_project_btn,
                ]),
                padding=ft.Padding(left=20, right=20, top=20, bottom=10),
            ),
            ft.ListView(
                controls=project_items if project_items else [
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.FOLDER_OUTLINED, size=48, color="#CCCCCC"),
                            ft.Text("No projects yet", size=16, color="#999999"),
                            ft.Text("Create a project to organize your chats", size=13, color="#BBBBBB"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        padding=50,
                    )
                ],
                spacing=5,
                padding=ft.Padding(left=15, right=15, top=5, bottom=15),
                expand=True,
            ),
        ], spacing=0, expand=True)
        self.page.update()
    
    def _build_project_item(self, project: dict, chat_count: int) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER, color=SNOWFLAKE_DARK_BLUE, size=24),
                ft.Column([
                    ft.Text(project["name"], size=14, weight=ft.FontWeight.W_500),
                    ft.Text(f"{chat_count} chat{'s' if chat_count != 1 else ''}", size=11, color="#999999"),
                ], spacing=2, expand=True),
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    icon_size=18,
                    items=[
                        ft.PopupMenuItem(content="Rename", on_click=lambda e, p=project: self._rename_project(p)),
                        ft.PopupMenuItem(content="Delete", on_click=lambda e, p=project: self._delete_project(p["id"])),
                    ],
                ),
            ], spacing=12),
            padding=ft.Padding(left=15, right=10, top=15, bottom=15),
            border_radius=8,
            bgcolor="#F8F8F8",
            on_click=lambda e, p=project: self._show_project_chats(p),
            ink=True,
        )
    
    def _show_themes_view(self):
        """Show themes management view."""
        themes = [
            {"id": "snowflake_2026", "name": "Snowflake 2026", "desc": "Official Snowflake brand theme", "builtin": True},
            {"id": "snowflake_dark", "name": "Snowflake Dark", "desc": "Dark mode variant", "builtin": True},
            {"id": "minimal", "name": "Minimal", "desc": "Clean, simple design", "builtin": True},
        ]
        
        # Check for custom themes
        if THEMES_DIR.exists():
            for f in THEMES_DIR.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                    themes.append({"id": f.stem, "name": data.get("name", f.stem), "desc": data.get("description", "Custom theme"), "builtin": False})
                except:
                    pass
        
        theme_items = [self._build_theme_item(t) for t in themes]
        
        self.content_area.content = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Themes", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Manage presentation templates", size=13, color="#666666"),
                ], spacing=5),
                padding=ft.Padding(left=20, right=20, top=20, bottom=10),
            ),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINE, color="#666666", size=16),
                    ft.Text(f"Drop .json theme files into: {THEMES_DIR}", size=12, color="#666666"),
                ], spacing=8),
                padding=ft.Padding(left=20, right=20, top=5, bottom=10),
                bgcolor="#F5F5F5",
                border_radius=5,
                margin=ft.Margin(left=15, right=15, top=0, bottom=0),
            ),
            ft.ListView(
                controls=theme_items,
                spacing=5,
                padding=ft.Padding(left=15, right=15, top=10, bottom=15),
                expand=True,
            ),
        ], spacing=0, expand=True)
        self.page.update()
    
    def _build_theme_item(self, theme: dict) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.PALETTE, color="#FFFFFF", size=20),
                    width=40,
                    height=40,
                    bgcolor=SNOWFLAKE_BLUE if theme["builtin"] else SNOWFLAKE_DARK_BLUE,
                    border_radius=8,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(theme["name"], size=14, weight=ft.FontWeight.W_500),
                        ft.Container(
                            content=ft.Text("Built-in" if theme["builtin"] else "Custom", size=10, color="#666666"),
                            bgcolor="#E0E0E0",
                            border_radius=3,
                            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
                        ) if theme["builtin"] else None,
                    ], spacing=8),
                    ft.Text(theme["desc"], size=12, color="#666666"),
                ], spacing=3, expand=True),
            ], spacing=15),
            padding=ft.Padding(left=15, right=15, top=12, bottom=12),
            border_radius=8,
            bgcolor="#F8F8F8",
        )
    
    def _show_settings_view(self):
        """Show settings view."""
        self.content_area.content = ft.Column([
            ft.Container(
                content=ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
                padding=ft.Padding(left=20, right=20, top=20, bottom=15),
            ),
            ft.Container(
                content=ft.Column([
                    # Google Auth section
                    ft.Text("Google Account", size=16, weight=ft.FontWeight.W_500),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if self.is_authenticated else ft.Icons.ACCOUNT_CIRCLE,
                                color="#4CAF50" if self.is_authenticated else "#999999",
                                size=40,
                            ),
                            ft.Column([
                                ft.Text("Google Drive" if self.is_authenticated else "Not connected", size=14),
                                ft.Text("Connected" if self.is_authenticated else "Sign in to create presentations", size=12, color="#666666"),
                            ], spacing=3, expand=True),
                            ft.Button(
                                "Sign Out" if self.is_authenticated else "Sign In",
                                on_click=lambda e: self._handle_auth(),
                            ),
                        ], spacing=15),
                        padding=15,
                        bgcolor="#F8F8F8",
                        border_radius=8,
                    ),
                    
                    ft.Container(height=25),
                    
                    # Cortex CLI section
                    ft.Text("Cortex Code CLI", size=16, weight=ft.FontWeight.W_500),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.TERMINAL if self.cortex_available else ft.Icons.WARNING,
                                color="#4CAF50" if self.cortex_available else "#FF9800",
                                size=40,
                            ),
                            ft.Column([
                                ft.Text("Cortex CLI", size=14),
                                ft.Text("Available" if self.cortex_available else "Not found in PATH", size=12, color="#666666"),
                            ], spacing=3, expand=True),
                        ], spacing=15),
                        padding=15,
                        bgcolor="#F8F8F8",
                        border_radius=8,
                    ),
                ], spacing=2),
                padding=ft.Padding(left=20, right=20, top=0, bottom=20),
            ),
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.page.update()
    
    def _show_about_dialog(self):
        """Show the About dialog with app info and contact details."""
        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color=SNOWFLAKE_BLUE, size=28),
                ft.Text("GSlides AI", size=20, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Column([
                ft.Text(f"Version {APP_VERSION}", size=14, color="#666666"),
                ft.Container(height=15),
                
                ft.Text("Created by", size=12, color="#999999"),
                ft.Text("Kevin Keller", size=16, weight=ft.FontWeight.W_500),
                ft.Container(height=15),
                
                ft.Divider(height=1, color="#E0E0E0"),
                ft.Container(height=15),
                
                ft.Text("Questions or Suggestions?", size=14, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHAT, color=SNOWFLAKE_BLUE, size=20),
                        ft.Text("Connect on Slack", size=13, color=SNOWFLAKE_BLUE),
                    ], spacing=10),
                    on_click=lambda e: webbrowser.open("https://snowflake.enterprise.slack.com/team/U02B75K719B"),
                    ink=True,
                    padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                    border_radius=5,
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EMAIL, color=SNOWFLAKE_BLUE, size=20),
                        ft.Text("kevin.keller@snowflake.com", size=13, color=SNOWFLAKE_BLUE),
                    ], spacing=10),
                    on_click=lambda e: webbrowser.open("mailto:kevin.keller@snowflake.com"),
                    ink=True,
                    padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                    border_radius=5,
                ),
                
                ft.Container(height=15),
                ft.Divider(height=1, color="#E0E0E0"),
                ft.Container(height=10),
                
                ft.Text("© 2026 Snowflake Inc.", size=12, color="#999999"),
            ], tight=True, spacing=2),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _new_chat(self):
        """Create a new chat and open it."""
        chat_id = self.db.create_chat()
        self._open_chat(chat_id)
    
    def _open_chat(self, chat_id: str):
        """Open a chat conversation."""
        self.current_chat_id = chat_id
        chat = self.db.get_chat(chat_id)
        messages = self.db.get_messages(chat_id)
        
        # Build chat UI
        self.chat_list = ft.ListView(controls=[], spacing=0, auto_scroll=True, expand=True,
                                     padding=ft.Padding(left=10, right=10, top=10, bottom=10))
        
        # Add existing messages
        for msg in messages:
            self.chat_list.controls.append(ChatMessage(msg["content"], is_user=msg["is_user"]))
        
        # Welcome message for new chats
        if not messages:
            welcome = """**Welcome!** I'll help you create presentations using AI.

Try: *"Create a 5-slide presentation about cloud computing"*"""
            self.chat_list.controls.append(ChatMessage(welcome, is_user=False))
        
        # Input field
        self.input_field = ft.TextField(
            hint_text="Describe the presentation you want...",
            border_color=SNOWFLAKE_BLUE,
            focused_border_color=SNOWFLAKE_DARK_BLUE,
            border_radius=25,
            content_padding=ft.Padding(left=20, right=20, top=12, bottom=12),
            expand=True,
            on_submit=self._send_message,
        )
        
        input_row = ft.Container(
            content=ft.Row([
                self.input_field,
                ft.IconButton(ft.Icons.SEND, icon_color="#FFFFFF", bgcolor=SNOWFLAKE_BLUE, on_click=self._send_message),
            ], spacing=10),
            padding=ft.Padding(left=15, right=15, top=10, bottom=15),
            bgcolor="#FFFFFF",
            border=ft.Border(top=ft.BorderSide(1, "#E0E0E0")),
        )
        
        # Header with optional presentation link
        header_controls = [
            ft.IconButton(ft.Icons.ARROW_BACK, icon_color="#666666", on_click=lambda e: self._show_chats_view()),
            ft.Text(chat["title"] if chat else "Chat", size=16, weight=ft.FontWeight.W_500, expand=True),
        ]
        
        if chat and chat.get("presentation_url"):
            header_controls.append(
                ft.TextButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SLIDESHOW, size=18, color=SNOWFLAKE_BLUE),
                        ft.Text("Open Slides", color=SNOWFLAKE_BLUE, size=13),
                    ], spacing=5),
                    on_click=lambda e, url=chat["presentation_url"]: self._open_url(url),
                )
            )
        
        header = ft.Container(
            content=ft.Row(header_controls),
            padding=ft.Padding(left=5, right=15, top=10, bottom=10),
            border=ft.Border(bottom=ft.BorderSide(1, "#E0E0E0")),
        )
        
        self.content_area.content = ft.Column([
            header,
            ft.Container(content=self.chat_list, expand=True, bgcolor="#FFFFFF"),
            input_row,
        ], spacing=0, expand=True)
        self.page.update()
    
    def _send_message(self, e):
        """Send a message in the current chat."""
        if not self.current_chat_id or self.is_processing:
            return
        
        user_input = self.input_field.value.strip()
        if not user_input:
            return
        
        # Clear input, reset styling, and add message
        self.input_field.value = ""
        self._reset_input_field()
        self.db.add_message(self.current_chat_id, user_input, is_user=True)
        self.chat_list.controls.append(ChatMessage(user_input, is_user=True))
        
        # Update chat title if first message
        chat = self.db.get_chat(self.current_chat_id)
        if chat and chat["title"] == "New Chat":
            title = user_input[:50] + ("..." if len(user_input) > 50 else "")
            self.db.update_chat(self.current_chat_id, title=title)
        
        self.page.update()
        
        # Process with cortex
        if self.cortex_available:
            self._process_with_cortex(user_input)
        else:
            response = "⚠️ Cortex CLI not found. Please install it to generate presentations."
            self.db.add_message(self.current_chat_id, response, is_user=False)
            self.chat_list.controls.append(ChatMessage(response, is_user=False))
            self.page.update()
    
    def _process_with_cortex(self, user_input: str):
        """Process user input with Cortex CLI with streaming output."""
        import re
        
        self.is_processing = True
        self.processing_chat_id = self.current_chat_id
        
        # Get chat info including existing presentation and theme
        chat = self.db.get_chat(self.current_chat_id)
        self.processing_chat_name = chat["title"] if chat else "Chat"
        existing_presentation_url = chat.get("presentation_url") if chat else None
        selected_theme = chat.get("theme") if chat else None
        
        # Get default theme from settings if not set on chat
        if not selected_theme:
            selected_theme = self.db.get_setting("default_theme", "Snowflake 2026")
        
        # Update processing indicator
        self._update_processing_indicator(True, self.processing_chat_name)
        
        streaming_msg = StreamingChatMessage()
        self.chat_list.controls.append(streaming_msg)
        self.active_streaming_msg = streaming_msg
        self.page.update()
        
        # Build context from chat history
        messages = self.db.get_messages(self.current_chat_id)
        context_parts = []
        # Include last 10 messages for context (5 exchanges)
        for msg in messages[-10:]:
            role = "User" if msg["is_user"] else "Assistant"
            # Truncate long messages
            content = msg["content"][:500] + "..." if len(msg["content"]) > 500 else msg["content"]
            context_parts.append(f"{role}: {content}")
        
        context_str = "\n".join(context_parts) if context_parts else ""
        
        # Theme instructions
        theme_context = f"""
THEME/TEMPLATE: Use the "{selected_theme}" theme/template for styling.
- Primary color: #29B5E7 (Snowflake Blue)
- Secondary color: #11567F (Snowflake Dark Blue)
- Clean, professional, modern design
- Use these colors for headings, accents, and highlights
"""
        
        # Build the full prompt with context and existing presentation
        if existing_presentation_url:
            presentation_context = f"""
IMPORTANT: This chat is linked to an existing Google Slides presentation:
{existing_presentation_url}

You must UPDATE this existing presentation, do NOT create a new one.
Use the Google Slides API to modify the slides in this presentation.
{theme_context}"""
        else:
            presentation_context = f"""
This is a new presentation request. Create a new Google Slides presentation.
After creating it, provide the presentation URL.
{theme_context}"""
        
        if context_str:
            full_prompt = f"""Previous conversation context:
{context_str}
{presentation_context}
Current request: {user_input}"""
        else:
            full_prompt = f"""{presentation_context}
Current request: Help me create a Google Slides presentation: {user_input}"""
        
        chat_id = self.current_chat_id  # Capture for thread
        
        def run_cortex():
            full_output = []
            detected_url = None
            
            try:
                process = subprocess.Popen(
                    ["cortex", "-p", full_prompt],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                self.active_process = process
                
                streaming_msg.update_status("Processing...")
                self._safe_update()
                
                # Pattern to detect Google Slides URLs
                slides_url_pattern = re.compile(
                    r'https://docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)'
                )
                
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    full_output.append(line)
                    
                    # Stream line to UI
                    streaming_msg.append_line(line)
                    
                    # Check for Google Slides URL
                    url_match = slides_url_pattern.search(line)
                    if url_match and not detected_url:
                        detected_url = url_match.group(0)
                        streaming_msg.update_status("Presentation found!")
                    
                    # Parse for tool calls (Cortex outputs tool names)
                    if "tool" in line.lower() or "calling" in line.lower():
                        for tool in ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task", "snowflake_sql"]:
                            if tool.lower() in line.lower():
                                streaming_msg.add_tool(tool)
                                break
                    
                    # Update status based on output
                    if "thinking" in line.lower():
                        streaming_msg.update_status("Thinking...")
                    elif "writing" in line.lower():
                        streaming_msg.update_status("Writing...")
                    elif "creating" in line.lower():
                        streaming_msg.update_status("Creating slides...")
                    elif "updating" in line.lower():
                        streaming_msg.update_status("Updating slides...")
                    
                    self._safe_update()
                
                process.wait()
                
                # Save detected presentation URL to chat
                if detected_url and not existing_presentation_url:
                    self.db.update_chat(chat_id, presentation_url=detected_url)
                
                # Check if cortex is asking a question (needs user input)
                final_response = '\n'.join(full_output) if full_output else "Completed (no output)"
                needs_input = self._detect_question(final_response)
                
                if needs_input:
                    streaming_msg.finish(final_response)
                    streaming_msg.status_text.value = "⏳ Waiting for your response..."
                    streaming_msg.status_text.color = "#FF9800"
                    # Focus input field
                    try:
                        self.input_field.focus()
                        self.input_field.hint_text = "Cortex is waiting for your response..."
                        self.input_field.border_color = "#FF9800"
                    except:
                        pass
                else:
                    streaming_msg.finish(final_response)
                
                self.db.add_message(chat_id, final_response, is_user=False)
                
            except Exception as ex:
                streaming_msg.finish(f"Error: {str(ex)}")
                self.db.add_message(chat_id, f"Error: {str(ex)}", is_user=False)
            finally:
                self.is_processing = False
                self.active_process = None
                self.active_streaming_msg = None
                self.processing_chat_id = None
                self.processing_chat_name = None
                self._update_processing_indicator(False)
                self._safe_update()
        
        threading.Thread(target=run_cortex, daemon=True).start()
    
    def _update_processing_indicator(self, visible: bool, chat_name: str = ""):
        """Update the global processing indicator in sidebar."""
        try:
            self.processing_indicator.visible = visible
            if visible and chat_name:
                # Update the chat name text
                col = self.processing_indicator.content.controls[1]  # The Column
                col.controls[1].value = chat_name[:20] + "..." if len(chat_name) > 20 else chat_name
            self._safe_update()
        except Exception:
            pass
    
    def _detect_question(self, text: str) -> bool:
        """Detect if the output contains a question needing user input."""
        # Check last portion of text for question indicators
        last_lines = '\n'.join(text.split('\n')[-5:]).lower()
        
        question_patterns = [
            '?',
            'please provide',
            'please specify',
            'what would you like',
            'which option',
            'would you prefer',
            'can you clarify',
            'could you provide',
            'let me know',
            'please confirm',
            'do you want',
            'should i',
        ]
        
        for pattern in question_patterns:
            if pattern in last_lines:
                return True
        return False
    
    def _reset_input_field(self):
        """Reset input field to default state."""
        try:
            self.input_field.hint_text = "Describe the presentation you want..."
            self.input_field.border_color = SNOWFLAKE_BLUE
        except:
            pass
    
    def _go_to_processing_chat(self):
        """Navigate to the chat that is currently processing."""
        if self.processing_chat_id:
            self._open_chat(self.processing_chat_id)
    
    def _safe_update(self):
        """Safely update the page from a background thread."""
        try:
            self.page.update()
        except Exception:
            pass  # Page might not be ready
    
    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        try:
            webbrowser.open(url)
        except Exception as ex:
            print(f"Failed to open URL: {ex}")
    
    def _handle_auth(self):
        """Handle Google auth."""
        if self.is_authenticated:
            # Sign out - clear credentials
            try:
                from .auth import clear_credentials
                clear_credentials()
                self.is_authenticated = False
            except:
                pass
        else:
            self._show_auth_dialog()
        self._show_settings_view()
    
    def _show_auth_dialog(self):
        """Show Google authentication dialog."""
        def do_auth(e):
            dialog.open = False
            self.page.update()
            try:
                from .auth import authenticate_with_gcloud
                authenticate_with_gcloud()
                self.is_authenticated = True
            except Exception as ex:
                self._show_error(f"Auth failed: {str(ex)}")
            self._show_settings_view()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Sign in with Google"),
            content=ft.Column([
                ft.Text("This will open a browser window for Google authentication."),
                ft.Text("You'll need to grant access to Google Slides.", size=12, color="#666666"),
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.Button("Sign In", on_click=do_auth),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_new_project_dialog(self):
        """Show dialog to create new project."""
        name_field = ft.TextField(label="Project Name", autofocus=True)
        
        def create(e):
            if name_field.value.strip():
                self.db.create_project(name_field.value.strip())
                dialog.open = False
                self.page.update()
                self._show_projects_view()
        
        dialog = ft.AlertDialog(
            title=ft.Text("New Project"),
            content=name_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.Button("Create", on_click=create),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_move_dialog(self, chat: dict):
        """Show dialog to move chat to project."""
        projects = self.db.get_projects()
        
        options = [ft.dropdown.Option("", "No Project")]
        for p in projects:
            options.append(ft.dropdown.Option(p["id"], p["name"]))
        
        dropdown = ft.Dropdown(label="Select Project", options=options, value=chat.get("project_id") or "")
        
        def move(e):
            self.db.move_chat_to_project(chat["id"], dropdown.value if dropdown.value else None)
            dialog.open = False
            self.page.update()
            self._show_chats_view()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Move to Project"),
            content=dropdown,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.Button("Move", on_click=move),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_rename_dialog(self, chat: dict):
        """Show dialog to rename chat."""
        name_field = ft.TextField(label="Chat Title", value=chat["title"], autofocus=True)
        
        def rename(e):
            if name_field.value.strip():
                self.db.update_chat(chat["id"], title=name_field.value.strip())
                dialog.open = False
                self.page.update()
                self._show_chats_view()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Rename Chat"),
            content=name_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.Button("Rename", on_click=rename),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _delete_chat(self, chat_id: str):
        """Delete a chat."""
        self.db.delete_chat(chat_id)
        self._show_chats_view()
    
    def _delete_project(self, project_id: str):
        """Delete a project."""
        self.db.delete_project(project_id)
        self._show_projects_view()
    
    def _rename_project(self, project: dict):
        """Show dialog to rename project."""
        name_field = ft.TextField(label="Project Name", value=project["name"], autofocus=True)
        
        def rename(e):
            if name_field.value.strip():
                self.db.rename_project(project["id"], name_field.value.strip())
                dialog.open = False
                self.page.update()
                self._show_projects_view()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Rename Project"),
            content=name_field,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(dialog)),
                ft.Button("Rename", on_click=rename),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_project_chats(self, project: dict):
        """Show chats in a project."""
        chats = self.db.get_project_chats(project["id"])
        
        chat_items = [self._build_chat_list_item(c) for c in chats]
        
        if not chat_items:
            chat_items.append(
                ft.Container(
                    content=ft.Text("No chats in this project yet", color="#999999"),
                    padding=30,
                )
            )
        
        self.content_area.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self._show_projects_view()),
                    ft.Text(project["name"], size=18, weight=ft.FontWeight.BOLD),
                ]),
                padding=ft.Padding(left=10, right=20, top=15, bottom=10),
            ),
            ft.ListView(controls=chat_items, spacing=5, padding=ft.Padding(left=15, right=15, top=5, bottom=15), expand=True),
        ], spacing=0, expand=True)
        self.page.update()
    
    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
    
    def _show_error(self, message: str):
        dialog = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text(message))
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


def main(page: ft.Page):
    """Main entry point."""
    page.window.width = 900
    page.window.height = 650
    page.window.min_width = 700
    page.window.min_height = 500
    GSlidesChatApp(page)

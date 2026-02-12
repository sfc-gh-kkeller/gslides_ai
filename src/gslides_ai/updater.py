#!/usr/bin/env python3
"""
GSlides AI Updater - Standalone updater application.

This script is launched by the main app when an update is available.
It downloads the new version, replaces the app bundle, and relaunches.

Usage:
    python updater.py <download_url> <app_path> [--main-pid <pid>]
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path


def wait_for_process_exit(pid: int, timeout: int = 30) -> bool:
    """Wait for a process to exit."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            # Check if process exists
            os.kill(pid, 0)
            time.sleep(0.5)
        except OSError:
            # Process doesn't exist, it has exited
            return True
    return False


def download_file(url: str, dest: Path, progress_callback=None) -> bool:
    """Download a file from URL to destination."""
    try:
        def reporthook(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                progress_callback(percent)
        
        urllib.request.urlretrieve(url, dest, reporthook)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def extract_app(zip_path: Path, extract_to: Path) -> Path:
    """Extract the app bundle from a zip file."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)
    
    # Find the .app bundle in extracted contents
    for item in extract_to.iterdir():
        if item.suffix == '.app':
            return item
    
    # Check if it's nested in a folder
    for item in extract_to.iterdir():
        if item.is_dir():
            for subitem in item.iterdir():
                if subitem.suffix == '.app':
                    return subitem
    
    raise FileNotFoundError("No .app bundle found in zip file")


def replace_app(new_app: Path, old_app: Path) -> bool:
    """Replace the old app bundle with the new one."""
    backup_path = old_app.with_suffix('.app.backup')
    
    try:
        # Remove old backup if exists
        if backup_path.exists():
            shutil.rmtree(backup_path)
        
        # Backup current app
        if old_app.exists():
            shutil.move(str(old_app), str(backup_path))
        
        # Move new app into place
        shutil.move(str(new_app), str(old_app))
        
        # Remove backup on success
        if backup_path.exists():
            shutil.rmtree(backup_path)
        
        return True
    except Exception as e:
        print(f"Replace failed: {e}")
        # Try to restore backup
        if backup_path.exists() and not old_app.exists():
            shutil.move(str(backup_path), str(old_app))
        return False


def launch_app(app_path: Path):
    """Launch the app bundle."""
    subprocess.Popen(['open', str(app_path)])


def run_gui_updater(download_url: str, app_path: str, main_pid: int = None):
    """Run the updater with a simple GUI progress window."""
    try:
        import flet as ft
    except ImportError:
        # Fall back to CLI mode if Flet not available
        run_cli_updater(download_url, app_path, main_pid)
        return
    
    def main(page: ft.Page):
        page.title = "GSlides AI Updater"
        page.window.width = 400
        page.window.height = 200
        page.window.center()
        page.padding = 30
        
        status_text = ft.Text("Preparing update...", size=14)
        progress_bar = ft.ProgressBar(width=340, value=0)
        progress_percent = ft.Text("0%", size=12, color="#666666")
        
        page.add(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SYSTEM_UPDATE, color="#29B5E7", size=32),
                    ft.Text("Updating GSlides AI", size=18, weight=ft.FontWeight.BOLD),
                ], spacing=10),
                ft.Container(height=20),
                status_text,
                ft.Container(height=10),
                progress_bar,
                progress_percent,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
        def update_progress(percent: float, status: str = None):
            progress_bar.value = percent / 100
            progress_percent.value = f"{int(percent)}%"
            if status:
                status_text.value = status
            page.update()
        
        def do_update():
            import threading
            
            def update_thread():
                try:
                    # Wait for main app to exit
                    if main_pid:
                        update_progress(5, "Waiting for app to close...")
                        if not wait_for_process_exit(main_pid, timeout=30):
                            update_progress(0, "Error: Main app didn't close")
                            time.sleep(3)
                            page.window.close()
                            return
                    
                    # Download
                    update_progress(10, "Downloading update...")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        zip_path = temp_path / "update.zip"
                        
                        def on_progress(percent):
                            # Map download progress to 10-70%
                            update_progress(10 + (percent * 0.6), "Downloading update...")
                        
                        if not download_file(download_url, zip_path, on_progress):
                            update_progress(0, "Error: Download failed")
                            time.sleep(3)
                            page.window.close()
                            return
                        
                        # Extract
                        update_progress(75, "Extracting...")
                        extract_path = temp_path / "extracted"
                        extract_path.mkdir()
                        
                        try:
                            new_app = extract_app(zip_path, extract_path)
                        except FileNotFoundError as e:
                            update_progress(0, f"Error: {e}")
                            time.sleep(3)
                            page.window.close()
                            return
                        
                        # Replace
                        update_progress(85, "Installing...")
                        app_bundle = Path(app_path)
                        
                        if not replace_app(new_app, app_bundle):
                            update_progress(0, "Error: Installation failed")
                            time.sleep(3)
                            page.window.close()
                            return
                        
                        # Launch
                        update_progress(95, "Launching...")
                        launch_app(app_bundle)
                        
                        update_progress(100, "Update complete!")
                        time.sleep(1)
                        page.window.close()
                        
                except Exception as e:
                    update_progress(0, f"Error: {e}")
                    time.sleep(5)
                    page.window.close()
            
            threading.Thread(target=update_thread, daemon=True).start()
        
        # Start update after UI is ready
        page.on_idle = lambda: do_update()
    
    ft.run(main)


def run_cli_updater(download_url: str, app_path: str, main_pid: int = None):
    """Run the updater in CLI mode (no GUI)."""
    print("GSlides AI Updater")
    print("=" * 40)
    
    # Wait for main app to exit
    if main_pid:
        print("Waiting for app to close...")
        if not wait_for_process_exit(main_pid, timeout=30):
            print("Error: Main app didn't close in time")
            sys.exit(1)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "update.zip"
        
        # Download
        print(f"Downloading update...")
        
        def show_progress(percent):
            bar_length = 30
            filled = int(bar_length * percent / 100)
            bar = '=' * filled + '-' * (bar_length - filled)
            print(f"\r[{bar}] {percent:.0f}%", end='', flush=True)
        
        if not download_file(download_url, zip_path, show_progress):
            print("\nError: Download failed")
            sys.exit(1)
        print()  # Newline after progress bar
        
        # Extract
        print("Extracting...")
        extract_path = temp_path / "extracted"
        extract_path.mkdir()
        
        try:
            new_app = extract_app(zip_path, extract_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        
        # Replace
        print("Installing...")
        app_bundle = Path(app_path)
        
        if not replace_app(new_app, app_bundle):
            print("Error: Installation failed")
            sys.exit(1)
        
        # Launch
        print("Launching updated app...")
        launch_app(app_bundle)
        
        print("Update complete!")


def main():
    parser = argparse.ArgumentParser(description="GSlides AI Updater")
    parser.add_argument("download_url", help="URL to download the update from")
    parser.add_argument("app_path", help="Path to the app bundle to update")
    parser.add_argument("--main-pid", type=int, help="PID of main app to wait for")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    
    args = parser.parse_args()
    
    if args.cli:
        run_cli_updater(args.download_url, args.app_path, args.main_pid)
    else:
        run_gui_updater(args.download_url, args.app_path, args.main_pid)


if __name__ == "__main__":
    main()

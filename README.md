# GSlides AI for Snowflake

A macOS desktop application for generating Google Slides presentations using natural language, powered by [Cortex Code (CoCo)](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code).

![Snowflake](https://img.shields.io/badge/Powered%20by-Snowflake-29B5E7)
![Platform](https://img.shields.io/badge/Platform-macOS-000000)
![Python](https://img.shields.io/badge/Python-3.11+-blue)

## Overview

GSlides AI provides a chat-based interface where you can describe the presentation you want, and it uses Snowflake's Cortex Code CLI to generate and modify Google Slides presentations. The app streams responses in real-time, showing you exactly what's happening as your presentation is being created.

### Key Features

- **Natural Language to Slides**: Describe your presentation in plain English and watch it come to life
- **Real-time Streaming**: See Cortex Code's progress as it works, including tool calls and status updates
- **Chat History**: All conversations are saved and organized for easy reference
- **Projects**: Group related chats together for better organization
- **Theme Templates**: Pre-configured Snowflake 2026 branded themes for consistent styling
- **Presentation Linking**: Chats automatically link to the presentations they create or modify
- **Google Drive Integration**: Seamless authentication with your Google account

## Prerequisites

1. **macOS** (Intel or Apple Silicon)
2. **Python 3.11+**
3. **[Pixi](https://pixi.sh)** package manager
4. **[Cortex Code CLI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code)** installed and configured
5. **Google Cloud Project** with Google Slides API and Google Drive API enabled

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/gslides_ai.git
cd gslides_ai
```

### 2. Install dependencies with Pixi

```bash
pixi install
```

### 3. Set up Google Cloud credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Slides API** and **Google Drive API**
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download the credentials JSON file
6. Place it at `~/.gslides_ai/credentials.json`

### 4. Verify Cortex Code is installed

```bash
cortex --version
```

If not installed, follow the [Cortex Code installation guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code).

## Usage

### Running the App

```bash
pixi run python main.py
```

Or use the Pixi task:

```bash
pixi run app
```

### First Launch

1. Click **"Connect Google Drive"** in the sidebar to authenticate
2. A browser window will open for Google OAuth
3. Grant the requested permissions
4. Return to the app - you're ready to create presentations!

### Creating a Presentation

1. Click **"New Chat"** in the sidebar
2. Type a description of the presentation you want, for example:
   ```
   Create a 5-slide presentation about Snowflake's data cloud platform.
   Include an overview, key features, architecture diagram placeholder,
   use cases, and a conclusion slide. Use the Snowflake 2026 theme.
   ```
3. Press Enter or click Send
4. Watch as Cortex Code creates your presentation in real-time
5. Click the presentation link when it appears to view in Google Slides

### Tips for Best Results

- **Be specific**: Include the number of slides, topics to cover, and style preferences
- **Reference themes**: Mention "Snowflake 2026 theme" to use branded styling
- **Iterate**: Use follow-up messages to refine and improve your presentation
- **Context is preserved**: The app sends your last 10 messages for context, so Cortex understands what you're working on

## Building for Distribution

### Build macOS App Bundle

```bash
# For Apple Silicon (M1/M2/M3)
pixi run build-macos-arm

# For Intel Macs
pixi run build-macos-intel

# Universal binary (both architectures)
pixi run build-macos
```

The built app will be in the `build/` directory.

## Project Structure

```
gslides_ai/
├── main.py                 # Application entry point
├── pyproject.toml          # Project configuration and dependencies
├── pixi.lock              # Locked dependencies
├── src/
│   └── gslides_ai/
│       ├── app.py         # Main Flet application (~1400 lines)
│       ├── cli.py         # CLI commands (auth, etc.)
│       └── database.py    # SQLite database for persistence
├── assets/
│   └── icon.png           # App icon
├── examples/              # Example scripts
└── scripts/               # Build and utility scripts
```

## Configuration

App data is stored in `~/.gslides_ai/`:

- `credentials.json` - Google OAuth credentials (you provide this)
- `token.json` - Google OAuth token (auto-generated)
- `gslides_ai.db` - SQLite database for chats, projects, and settings

## Troubleshooting

### "Cortex CLI not found"

Ensure Cortex Code is installed and in your PATH:
```bash
which cortex
```

### Google authentication fails

1. Verify `credentials.json` is in `~/.gslides_ai/`
2. Delete `~/.gslides_ai/token.json` and re-authenticate
3. Check that Slides API and Drive API are enabled in your Google Cloud project

### App won't launch

Check for errors:
```bash
pixi run python main.py
```

## Contact

**Created by Kevin Keller**

- Slack: [Connect on Slack](https://snowflake.enterprise.slack.com/team/U02B75K719B)
- Email: kevin.keller@snowflake.com

## License

Copyright 2026 Snowflake Inc. All rights reserved.

---

*GSlides AI is powered by [Cortex Code](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code), Snowflake's AI-powered coding assistant.*

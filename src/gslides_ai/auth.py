"""Authentication for Google Slides API.

Supports multiple authentication methods:
1. Application Default Credentials (ADC) via gcloud CLI - recommended
2. OAuth 2.0 with credentials.json file
"""

import os
import subprocess
from pathlib import Path

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]

DEFAULT_CREDENTIALS_PATH = Path("credentials.json")
DEFAULT_TOKEN_PATH = Path("token.json")


def get_credentials_dir() -> Path:
    """Get the directory for storing credentials."""
    config_dir = Path.home() / ".config" / "gslides_ai"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_token_path() -> Path:
    """Get the path to the token file."""
    return get_credentials_dir() / "token.json"


def get_credentials_path() -> Path:
    """Get the path to the OAuth credentials file.
    
    Checks in order:
    1. GSLIDES_CREDENTIALS environment variable
    2. credentials.json in current directory
    3. ~/.config/gslides_ai/credentials.json
    """
    if env_path := os.environ.get("GSLIDES_CREDENTIALS"):
        return Path(env_path)
    
    if DEFAULT_CREDENTIALS_PATH.exists():
        return DEFAULT_CREDENTIALS_PATH
    
    config_path = get_credentials_dir() / "credentials.json"
    if config_path.exists():
        return config_path
    
    return DEFAULT_CREDENTIALS_PATH


def authenticate_with_gcloud() -> bool:
    """Authenticate using gcloud CLI (opens browser for SSO).
    
    Returns:
        True if authentication succeeded.
        
    Raises:
        RuntimeError: If gcloud is not installed or auth fails.
    """
    scopes_str = ",".join(SCOPES)
    
    try:
        result = subprocess.run(
            [
                "gcloud", "auth", "application-default", "login",
                f"--scopes={scopes_str},https://www.googleapis.com/auth/cloud-platform",
            ],
            check=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        raise RuntimeError(
            "gcloud CLI not found. Install it from: "
            "https://cloud.google.com/sdk/docs/install"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"gcloud authentication failed: {e}")


def authenticate_with_oauth(credentials_path: Path | None = None) -> Credentials:
    """Run OAuth flow using credentials.json file.
    
    Args:
        credentials_path: Path to OAuth credentials.json file.
        
    Returns:
        Authenticated credentials.
        
    Raises:
        FileNotFoundError: If credentials.json is not found.
    """
    creds_path = credentials_path or get_credentials_path()
    token_path = get_token_path()
    
    if not creds_path.exists():
        raise FileNotFoundError(
            f"OAuth credentials not found at {creds_path}. "
            "Download credentials.json from Google Cloud Console, "
            "or use 'gslides auth --gcloud' for SSO authentication."
        )
    
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)
    
    token_path.write_text(creds.to_json())
    return creds


def get_credentials():
    """Get valid credentials, trying multiple methods.
    
    Order of precedence:
    1. Saved OAuth token (from previous 'gslides auth --oauth')
    2. Application Default Credentials (from 'gslides auth' or 'gcloud auth')
    
    Returns:
        Valid credentials for API calls.
        
    Raises:
        Exception: If no valid credentials found.
    """
    token_path = get_token_path()
    
    # First, try saved OAuth token
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json())
            if creds.valid:
                return creds
        except Exception:
            pass  # Fall through to ADC
    
    # Try Application Default Credentials (gcloud)
    try:
        creds, project = google.auth.default(scopes=SCOPES)
        if hasattr(creds, 'refresh') and hasattr(creds, 'expired'):
            if creds.expired:
                creds.refresh(Request())
        return creds
    except google.auth.exceptions.DefaultCredentialsError:
        pass
    
    raise RuntimeError(
        "Not authenticated. Run one of:\n"
        "  gslides auth          # Browser SSO via gcloud (recommended)\n"
        "  gslides auth --oauth  # OAuth with credentials.json file"
    )


def is_authenticated() -> bool:
    """Check if valid credentials exist."""
    try:
        get_credentials()
        return True
    except Exception:
        return False


def get_auth_method() -> str | None:
    """Determine which auth method is currently active."""
    token_path = get_token_path()
    
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds.valid or creds.refresh_token:
                return "oauth"
        except Exception:
            pass
    
    try:
        creds, _ = google.auth.default(scopes=SCOPES)
        if creds:
            return "gcloud"
    except Exception:
        pass
    
    return None


def clear_credentials():
    """Clear saved OAuth credentials."""
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()
    return True

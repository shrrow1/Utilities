import pathlib
import yaml
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tidalapi
from typing import List, Dict, Tuple, Optional
from pathlib import Path

TIDAL_SESSION_FILE = Path(".tidalLogin.json")


def load_config(config_path: Path = Path("config.yml")) -> Dict:
    """
    Loads credentials from an external YAML configuration file.
    Handles file discovery and basic validation.
    """
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
            if not config or "spotify" not in config:
                raise ValueError("Configuration file is invalid or missing 'spotify' section.")
            return config
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

def get_tidal_session() -> tidalapi.Session:
    """
    Authenticates and returns a Tidal session.
    Handles the first-time login via OAuth and persists the session to a file.
    """
    session = tidalapi.Session()

    # Try to load existing session
    if TIDAL_SESSION_FILE.exists():
        try:
            session.login_session_file(TIDAL_SESSION_FILE, do_pkce=True)
            if session.check_login():
                print("Successfully logged into Tidal using existing session.")
                return session
        except Exception:
            print("Existing Tidal session is invalid or expired.")

    # Fallback to interactive OAuth login
    print("No valid Tidal session found. Starting login flow...")
    session.login_oauth_simple()

    if session.check_login():
        # Save session data for next time
        TIDAL_SESSION_FILE.write_text(session.session_id) # Some versions use .session_id or specific serializing
        # Note: tidalapi's login_session_file handles standard JSON formatting
        # If the specific version requires manual save, ensure logic matches lib version:
        # with open(TIDAL_SESSION_FILE, 'w') as f: json.dump(session.get_params(), f)

        # Re-verify and inform user
        print(f"Successfully logged into Tidal. Session saved to {TIDAL_SESSION_FILE}")
        return session
    else:
        raise Exception("Failed to login to Tidal via OAuth.")

def main():
    tidal_session = get_tidal_session()

    playlist_to_keep=tidal_session.playlist(playlist_id='79b47e85-1fe4-4ff3-98d8-cab3cb01896c')
    current_ids = set([x.id for x in playlist_to_keep.items()])

    playlist_from=tidal_session.playlist(playlist_id='a8d88f6b-6bcf-4262-892e-ada4c6d94fce')
    new_ids = set([x.id for x in playlist_from.items()])

    to_add = list(new_ids - current_ids)
    print(f'Before Merge: {len(playlist_to_keep.items())}')
    playlist_to_keep.add(to_add, allow_duplicates=False)
    print(f'After Merge: {len(playlist_to_keep.items())}')

if __name__ == "__main__":
    main()
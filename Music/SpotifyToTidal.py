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

def get_spotify_client(config: Dict) -> spotipy.Spotify:
    """
    Authenticates and returns a Spotify client using OAuth to access private playlists.
    """
    scope = "playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=config["spotify"]["client_id"],
        client_secret=config["spotify"]["client_secret"],
        redirect_uri=config["spotify"]["redirect_uri"],
        scope=scope
    ))

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

def fetch_playlist_data(sp: spotipy.Spotify, playlist_id: str) -> Tuple[str, List[Dict]]:
    """
    Fetches both the playlist name and the track list with pagination.
    """
    print(f"Connecting to Spotify to fetch playlist: {playlist_id}...")

    playlist_meta = sp.playlist(playlist_id, fields="name")
    playlist_name = playlist_meta.get("name", "Unknown Playlist")

    results = sp.playlist_items(playlist_id)
    tracks = []

    while results:
        for item in results.get("items", []):
            track = item.get("track")
            if track and "artists" in track:
                tracks.append({
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"]
                })

        if results["next"]:
            results = sp.next(results)
        else:
            results = None

    return playlist_name, tracks

def get_or_create_tidal_playlist(session: tidalapi.Session, name: str) -> Optional[tidalapi.Playlist]:
    """
    Checks if a playlist exists. If so, asks to overwrite.
    Otherwise, creates a new one.
    """
    user = session.user
    existing_playlists = user.playlists()
    target_playlist = next((p for p in existing_playlists if p.name == name), None)

    if target_playlist:
        print(f"\nA playlist named '{name}' already exists on Tidal.")
        choice = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if choice == "y":
            print(f"Overwriting '{name}' (re-creating for clean slate)...")
            target_playlist.delete()
            return user.create_playlist(name, "Migrated from Spotify")
        else:
            print("Creation cancelled by user.")
            return None

    print(f"Creating new Tidal playlist: {name}")
    return user.create_playlist(name, "Migrated from Spotify")

def inject_tracks_to_tidal(session: tidalapi.Session, playlist: tidalapi.Playlist, tracks: List[Dict]):
    """
    Searches for Spotify tracks on Tidal and adds matches to the playlist.
    """
    print(f"\nStarting track injection for '{playlist.name}'...")
    added_count = 0
    failed_count = 0

    for i, track_info in enumerate(tracks, 1):
        search_query = f"{track_info['name']} {track_info['artist']}"
        search_results = session.search(search_query, models=[tidalapi.Track], limit=1)

        tidal_tracks = search_results.get("tracks", [])
        if tidal_tracks:
            target_track = tidal_tracks[0]
            playlist.add([target_track.id])
            added_count += 1
            print(f"[{i}/{len(tracks)}] Added: {track_info['name']} - {track_info['artist']}")
        else:
            failed_count += 1
            print(f"[{i}/{len(tracks)}] Not found: {track_info['name']} - {track_info['artist']}")

    print(f"\nInjection Complete!")
    print(f"Successfully added: {added_count}")
    print(f"Failed to find: {failed_count}")

def get_spotify_playlists(sp: spotipy.Spotify) -> List[Tuple[str, str]]:
    """
    Lists the current user's Spotify playlists and returns a list of (id, name).
    """
    return_playlists = []
    print("\n--- Your Spotify Playlists ---")
    playlists = sp.current_user_playlists(limit=50)

    while playlists:
        for i, playlist in enumerate(playlists["items"]):
            index = i + 1 + playlists["offset"]
            print(f"{index:4d} | {playlist['name']} (ID: {playlist['id']})")
            return_playlists.append((playlist["id"], playlist["name"]))

        if playlists["next"]:
            playlists = sp.next(playlists)
        else:
            playlists = None

    return return_playlists

def main():
    config = load_config()

    try:
        # 1. Authenticate
        sp = get_spotify_client(config)
        tidal_session = get_tidal_session()

        # 2. Show User's Playlists
        spotify_playlists = get_spotify_playlists(sp)

        # 3. User Input
        playlist_input = input("\nEnter the Spotify Playlist ID or URL to migrate: ").strip()
        if not playlist_input:
            print("Error: No playlist ID or URL provided.")
            return

        # 4. Extract Data from Spotify
        playlist_name, tracks = fetch_playlist_data(sp, playlist_input)

        if not tracks:
            print("No tracks found on Spotify.")
            return

        print(f"\nFound '{playlist_name}' with {len(tracks)} tracks.")

        # 5. Handle Tidal Playlist Creation/Check
        tidal_playlist = get_or_create_tidal_playlist(tidal_session, playlist_name)

        if tidal_playlist:
            # 6. Inject tracks
            inject_tracks_to_tidal(tidal_session, tidal_playlist, tracks)
        else:
            print("No changes made to Tidal.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
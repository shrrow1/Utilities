import yaml
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict

def load_config(config_path: str = 'config.yml'):
    """
    Loads credentials from an external YAML configuration file.
    Handles file discovery and basic validation.
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            if not config:
                raise ValueError("Configuration file is empty.")
            return config
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        exit(1)

def get_spotify_client(config):
    """Authenticates and returns a Spotify client."""
    # Using 'playlist-read-private' to allow access to your own private playlists
    scope = "playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=config['spotify']['redirect_uri'],
        scope=scope
    ))

def fetch_spotify_tracks(sp, playlist_id: str) -> List[Dict]:
    """Retrieves all tracks from a specific Spotify playlist."""
    print(f"Fetching tracks for playlist ID: {playlist_id}...")

    results = sp.playlist_items(playlist_id)
    tracks = []

    while results:
        for item in results['items']:
            track = item['track']
            if track: # Ensure it's not a null track or podcast episode
                tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'spotify_id': track['id']
                })

        # Handle pagination if the playlist is longer than 100 tracks
        if results['next']:
            results = sp.next(results)
        else:
            results = None

    print(f"Successfully fetched {len(tracks)} tracks from Spotify.")
    return tracks

def main():
    # 1. Setup and Config Loading
    config = load_config()

    playlist_id = input("Enter the Spotify Playlist ID: ")

    try:
        # 2. Authenticate with Spotify
        sp = get_spotify_client(config)

        # 3. Extract Playlist Data
        tracks = fetch_spotify_tracks(sp, playlist_id)

        # 4. Display Results (Preview of first 5)
        print("\n--- Extracted Track List (First 5) ---")
        for track in tracks[:5]:
            print(f"- {track['name']} by {track['artist']} (Album: {track['album']})")

        if len(tracks) > 5:
            print(f"... and {len(tracks) - 5} more tracks.")

    except Exception as e:
        print(f"An error occurred during extraction: {e}")

if __name__ == "__main__":
    main()
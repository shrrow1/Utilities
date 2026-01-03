import sys
from datetime import datetime
import tidalapi
from MusicUtilities import TidalManager
from TextualUi import PlaylistSelector

DATE_FORMAT = '%Y-%m-%d-%H:%M:%S'

def get_tracks(playlist: tidalapi.Playlist) -> set[str]:
    """Retrieves all track IDs from a playlist as a set."""
    pl_items = playlist.tracks()
    return {str(x.id) for x in pl_items}

def backup_playlist(session: tidalapi.Session, playlist: tidalapi.Playlist, folder: tidalapi.playlist.Folder) -> None:
    """Creates a copy of a playlist inside a specific folder."""
    new_playlist = session.user.create_playlist(
        title=f"Backup - {playlist.name}",
        description=playlist.description,
        parent_id=folder.id
    )

    tracks = list(get_tracks(playlist))
    if tracks:
        new_playlist.add(tracks)

def main():
    tidal_mgr = TidalManager()
    log = tidal_mgr.logger

    try:
        tidal_session = tidal_mgr.get_session()

        # Load all user playlists

        # TODO: not usre this will work if ther are more than 50 playlists
            # user_playlists = tidal_session.user.playlists()
            # user_playlists = tidal_session.user.favorites.playlists()
            # Filter for only root playlists (parent_id is None)
            # root_playlists = [p for p in user_playlists if p.parent_id is None]

        # Use the selector to get source and target from the root list
        # log.info("Select the SOURCE playlist (the one to copy FROM):")
        # source_id = PlaylistSelector([(x.name, x.id) for x in user_playlists]).run()

        # log.info("Select the TARGET playlist (the one to copy TO):")
        # target_id = PlaylistSelector([(x.name, x.id) for x in user_playlists]).run()

        source_id = '499ad7c1-0681-4d27-bd63-b5701299f039'
        target_id = 'b7828b75-778a-42a4-96a4-9eea50cd8fef'

        if not source_id or not target_id:

            log.warning("Selection cancelled.")
            return

        log.info(f"Syncing playlists: {source_id} -> {target_id}")

        target_playlist = tidal_session.playlist(target_id)
        current_ids = get_tracks(target_playlist)

        source_playlist = tidal_session.playlist(source_id)
        new_ids = get_tracks(source_playlist)

        source_track_count = source_playlist.get_tracks_count()
        target_track_count = target_playlist.get_tracks_count()
        log.info(f'Current status: Source={source_track_count} Target={target_track_count}')

        # Create a backup folder for safety before modification
        folder_name = f'PlaylistBackup-{datetime.now().strftime(DATE_FORMAT)}'
        backup_folder = tidal_session.user.create_folder(folder_name)
        log.info(f"Created backup folder: {folder_name}")

        for pl in [source_playlist, target_playlist]:
            backup_playlist(tidal_session, pl, backup_folder)

        # Identify tracks in source not in target
        to_add = list(new_ids - current_ids)

        if not to_add:
            log.info("Playlist is already up to date. No tracks to add.")
            return

        num_to_add = len(to_add)
        log.info(f"Adding {num_to_add} unique tracks to target...")

        # Perform merge
        target_playlist.add(to_add, allow_duplicates=False)

        # Verification Logic
        new_target_track_count = target_playlist.get_tracks_count()
        expected_count = target_track_count + num_to_add

        if new_target_track_count != expected_count:
            msg = f'Sync verification failed: Expected {expected_count} tracks, but found {new_target_track_count}'
            log.error(msg)
            raise ValueError(msg)

        log.info(f"Merge completed successfully. New target total: {new_target_track_count}")

    except Exception as e:
        log.exception(f"Fatal error during playlist sync: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
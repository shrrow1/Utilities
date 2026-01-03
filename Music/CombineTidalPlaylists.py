import sys
from datetime import datetime

import tidalapi

from MusicUtilities import TidalManager

DATE_FORMAT = '%Y%-m-%d-%H:%M:%S'


def get_tracks(playlist: tidalapi.Playlist) -> set[str]:
    pl_items = playlist.tracks()
    # pl_items = playlist.items()

    return {str(x.id) for x in pl_items}


def backup_playlist(session: tidalapi.Session, playlist: tidalapi.Playlist, folder: tidalapi.playlist.Folder) -> None:
    new_playlist = session.user.create_playlist(title=playlist.name, description=playlist.description,
        parent_id=folder.id)

    tracks = get_tracks(playlist)
    if tracks:
        new_playlist.add(list(tracks))


def main():

    tidal_mgr = TidalManager()
    log = tidal_mgr.logger

    try:
        tidal_session = tidal_mgr.get_session()

        target_id = '031de0f8-a240-4aaa-bb43-770c852c4646'
        source_id = '088b1b48-a6ae-48da-8c2a-fdde75f3acf9'

        # TODO: list playlists
        # users_playlist = =tidal_session.user.playlists()

        log.info(f"Syncing playlists: {source_id} -> {target_id}")

        target_playlist = tidal_session.playlist(target_id)
        current_ids = get_tracks(target_playlist)

        source_playlist = tidal_session.playlist(source_id)
        new_ids = get_tracks(source_playlist)

        backup_folder = tidal_session.user.create_folder(f'PlaylistBackup-{datetime.now().strftime(DATE_FORMAT)}')

        for pl in source_playlist, target_playlist:
            backup_playlist(tidal_session, pl, backup_folder)

        to_add = list(new_ids - current_ids)
        if not to_add:
            log.info("Playlist is already up to date.")
            return

        log.info(f"Adding {len(to_add)} tracks.")
        target_playlist.add(to_add, allow_duplicates=False)
        log.info("Merge completed successfully.")

    except Exception as e:
        log.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

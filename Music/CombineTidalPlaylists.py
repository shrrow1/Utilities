from MusicUtilities import _load_config, TidalManager
import sys

def main():
    # tidal_session = get_tidal_session()
    tidal_mgr = TidalManager()
    log = tidal_mgr.logger
    # config = load_config(Path("config.yml"), logger=log)
    try:
        tidal_session = tidal_mgr.get_session()

        target_id = 'e9171f7a-f154-4274-afe4-429e91c634c4'
        source_id = '3b47b891-6d62-4a92-8a96-37f498a69aa7'

        log.info(f"Syncing playlists: {source_id} -> {target_id}")

        playlist_to_keep = tidal_session.playlist(target_id)
        current_ids = {str(x.id) for x in playlist_to_keep.items()}

        playlist_from = tidal_session.playlist(source_id)
        new_ids = {str(x.id) for x in playlist_from.items()}

        to_add = list(new_ids - current_ids)


        if not to_add:
            log.info("Playlist is already up to date.")
            return

        log.info(f"Adding {len(to_add)} tracks.")
        playlist_to_keep.add(to_add, allow_duplicates=False)
        log.info("Merge completed successfully.")

    except Exception as e:
        log.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
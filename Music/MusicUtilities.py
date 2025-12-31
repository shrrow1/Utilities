import yaml
import tidalapi
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional

def _load_config(config_path: Path = Path("config.yml"), logger: Optional[logging.Logger] = None) -> Dict:
    """
    Standalone utility to load YAML configuration.
    Can be used by Tidal, Spotify, or any other client.
    """
    if logger:
        logger.info(f"Loading configuration from {config_path}")

    try:
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file {config_path} missing.")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError("Configuration file is empty.")

        return config
    except Exception as e:
        if logger:
            logger.error(f"Failed to load config: {e}")
        raise

class TidalManager:
    """
    A reusable manager for Tidal API operations, including
    logging and session persistence using the standard tidalapi methods.
    """

    def __init__(
            self,
            session_path: str = ".tidal_session.json",
            log_file: str = "tidal_app.log"
    ):
        self.session_path = Path(session_path)
        self.log_file = log_file

        # Initialize internal state
        self.session: Optional[tidalapi.Session] = None

        # Setup Logger
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configures a logger with both console and file handlers."""
        logger = logging.getLogger("MusicSyncManager")
        logger.setLevel(logging.INFO)

        if logger.hasHandlers():
            logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = RotatingFileHandler(self.log_file, maxBytes=5*1024*1024, backupCount=3)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def get_session(self) -> tidalapi.Session:
        """
        Authenticates and returns a Tidal session.
        Handles the first-time login via OAuth and persists the session to a file.
        Reverted to original login logic.
        """
        self.session = tidalapi.Session()

        # Try to load existing session
        if self.session_path.exists():
            try:
                self.logger.info("Attempting to login using existing session file...")
                self.session.login_session_file(self.session_path, do_pkce=True)
                if self.session.check_login():
                    self.logger.info("Successfully logged into Tidal using existing session.")
                    return self.session
            except Exception as e:
                self.logger.warning(f"Existing Tidal session is invalid or expired: {e}")

        # Fallback to interactive OAuth login
        self.logger.info("No valid Tidal session found. Starting login flow...")
        try:
            self.session.login_oauth_simple()

            if self.session.check_login():
                # Save session data for next time
                self.session_path.write_text(self.session.session_id)
                self.logger.info(f"Successfully logged into Tidal. Session saved to {self.session_path}")
                return self.session
            else:
                raise Exception("Failed to login to Tidal via OAuth.")
        except Exception as e:
            self.logger.critical(f"Tidal Authentication failed: {e}")
            raise
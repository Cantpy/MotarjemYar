import configparser
import traceback
from shared.utils.path_utils import get_resource_path


class ConfigManager:
    def __init__(self, filepath=get_resource_path('config', 'config.ini')):
        self.config = configparser.ConfigParser()
        # read() returns the list of files successfully read. If empty, the file was not found.
        if not self.config.read(filepath):
            raise FileNotFoundError(f"Configuration file not found at: {filepath}")

    def get_broker_host(self) -> str:
        """Returns the broker's IP address or hostname."""
        return self.config.get('Network', 'broker_host', fallback='127.0.0.1')

    def get_broker_port(self) -> int:
        """Returns the broker's port."""
        return self.config.getint('Network', 'broker_port', fallback=8888)

    # You can add other getters for database paths, etc.

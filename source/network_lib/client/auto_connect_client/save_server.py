import json
import os


class save_server:
    def __init__(self, file_path: str):
        """
        Simple JSON storage handler for server info.
        JSON structure:
        {
            "hash": "<sha256>",
            "ipv4": "<ip address>"
        }
        """
        self.file_path = file_path

    def ensure_file(self, initial_hash: str = "0", initial_ipv4: str = "127.0.0.1") -> bool:
        """
        Checks if the server.json file exists.
        If not, creates it with an initial hash and ipv4.
        Returns True if file exists or created successfully.
        """
        if not os.path.exists(self.file_path):
            data = {"hash": initial_hash, "ipv4": initial_ipv4, "port": 1797}
            return self.save(data)
        return True

    def load(self) -> dict:
        """
        Loads and returns server.json content.
        Returns {} if file missing or invalid.
        """
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                return data
        except (json.JSONDecodeError, IOError):
            return {}

    def save(self, data: dict) -> bool:
        """
        Saves the given dict to server.json.
        """
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception:
            return False

    def get_hash(self) -> str | None:
        """
        Returns the stored hash, or None if missing.
        """
        data = self.load()
        return data.get("hash")

    def get_ipv4(self) -> str | None:
        """
        Returns the stored IPv4, or None if missing.
        """
        data = self.load()
        return data.get("ipv4")
    def get_port(self) -> int | None:
        """
        Returns the stored port, or None if missing.
        """
        data = self.load()
        return data.get("port")
    def update(self, data) -> bool:
        """
        Updates hash and/or IPv4 in server.json.
        """
        return self.save(data)

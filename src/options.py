from __future__ import annotations

class Options:
    def __init__(self) -> None:
        self.profile_path: str = None
        self.driver_path: str = None
        self.download_path: str = None
        self.verbose: bool = False

    def setProfilePath(self, profile_path: str) -> Options:
        self.profile_path = profile_path
        return self

    def setDriverPath(self, driver_path: str) -> Options:
        self.driver_path = driver_path
        return self

    def setDownloadPath(self, download_path: str) -> Options:
        self.download_path = download_path
        return self

    def setVerbose(self) -> Options:
        self.verbose = True
        return self
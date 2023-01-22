from __future__ import annotations

class Options:
    """Represents the options to configure the scrapper.

    Attributes:
        profile_path (str):
            The path to the Firefox profile to use.
        driver_path (str):
            The path to the geckodriver executable.
        download_path (str):
            The path to the directory where the PDFs will be downloaded.
        verbose (bool):
            Whether to print the progress of the scrapper or not.
    """

    def __init__(self) -> None:
        """Initializes the options with default values."""
        self.profile_path: str = None
        self.driver_path: str = None
        self.download_path: str = None
        self.verbose: bool = False

    def setProfilePath(self, profile_path: str) -> Options:
        """Sets the path to the Firefox profile to use.

        Args:
            profile_path (str): The path to the Firefox profile.

        Returns:
            The options object"""
        self.profile_path = profile_path
        return self

    def setDriverPath(self, driver_path: str) -> Options:
        """Sets the path to the geckodriver executable.

        Args:
            driver_path (str): The path to the geckodriver executable.

        Returns:
            The options object"""
        self.driver_path = driver_path
        return self

    def setDownloadPath(self, download_path: str) -> Options:
        """Sets the path to the directory where the PDFs will be downloaded.

        Args:
            download_path (str): The path to the store the downloaded PDFs.

        Returns:
            The options object"""
        self.download_path = download_path
        return self

    def setVerbose(self) -> Options:
        """Sets the verbose mode.

        Returns:
            The options object"""
        self.verbose = True
        return self
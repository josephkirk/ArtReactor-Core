from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class SourceControlProvider(ABC):
    """
    Abstract base class for Source Control Providers (Git, FileSystem, Zip).
    """

    @abstractmethod
    async def download(self, path: str, version: str, dest: str) -> bool:
        """
        Downloads the plugin from the source path/url to the destination directory.

        Args:
            path: The source URL or path.
            version: The version identifier (commit hash, tag, or suffix).
            dest: The destination directory path.

        Returns:
            bool: True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def get_version(self, path: str) -> str:
        """
        Gets the current version from the remote source.
        """
        pass


class SourceControlManager:
    def __init__(self):
        self.providers: Dict[str, SourceControlProvider] = {}

    def register_provider(self, name: str, provider: SourceControlProvider):
        """Registers a new Source Control Provider."""
        if name in self.providers:
            logger.warning(f"Overwriting existing provider for {name}")
        self.providers[name] = provider
        logger.info(f"Registered Source Control Provider: {name}")

    def get_provider(self, name: str) -> Optional[SourceControlProvider]:
        return self.providers.get(name)

    async def download_plugin(
        self, provider_name: str, path: str, version: str, dest: str
    ) -> bool:
        """
        Downloads a plugin using the specified provider.
        """
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"No provider registered for {provider_name}")
            return False

        try:
            # Ensure dest exists or clean it?
            # Usually we want to clean it if it exists to ensure clean install
            dest_path = Path(dest)
            if dest_path.exists():
                logger.info(f"Cleaning existing directory {dest}")
                shutil.rmtree(dest_path)

            return await provider.download(path, version, dest)
        except Exception as e:
            logger.error(f"Failed to download plugin: {e}")
            return False

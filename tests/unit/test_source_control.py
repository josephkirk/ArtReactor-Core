import pytest
from unittest.mock import AsyncMock
from artreactor.core.managers.source_control import (
    SourceControlManager,
    SourceControlProvider,
)


class MockProvider(SourceControlProvider):
    async def download(self, path: str, version: str, dest: str) -> bool:
        return True

    async def get_version(self, path: str) -> str:
        return "1.0.0"


@pytest.mark.asyncio
async def test_register_provider():
    manager = SourceControlManager()
    provider = MockProvider()

    manager.register_provider("git", provider)
    assert manager.get_provider("git") == provider


@pytest.mark.asyncio
async def test_download_plugin_success():
    manager = SourceControlManager()
    provider = MockProvider()
    provider.download = AsyncMock(return_value=True)
    manager.register_provider("git", provider)

    result = await manager.download_plugin("git", "url", "ver", "dest")
    assert result is True
    provider.download.assert_called_once_with("url", "ver", "dest")


@pytest.mark.asyncio
async def test_download_plugin_no_provider():
    manager = SourceControlManager()
    result = await manager.download_plugin("git", "url", "ver", "dest")
    assert result is False

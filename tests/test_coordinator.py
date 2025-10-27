"""Tests for MeteoLux coordinator."""
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meteolux.coordinator import MeteoLuxDataUpdateCoordinator


async def test_coordinator_success(hass: HomeAssistant, mock_meteolux_api):
    """Test successful data fetch."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_meteolux_api)

        # Create async context manager mock
        mock_get_result = MagicMock()
        mock_get_result.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_result.__aexit__ = AsyncMock(return_value=None)

        # get() should return the context manager (not a coroutine)
        mock_session.get = MagicMock(return_value=mock_get_result)
        mock_session_class.return_value = mock_session

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
            city_id=490,
        )

        result = await coordinator._async_update_data()

        assert result == mock_meteolux_api
        mock_session.get.assert_called_once()


async def test_coordinator_with_coordinates(hass: HomeAssistant, mock_meteolux_api):
    """Test coordinator with lat/lon instead of city_id."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_meteolux_api)

        # Create async context manager mock
        mock_get_result = MagicMock()
        mock_get_result.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_result.__aexit__ = AsyncMock(return_value=None)

        # get() should return the context manager (not a coroutine)
        mock_session.get = MagicMock(return_value=mock_get_result)
        mock_session_class.return_value = mock_session

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="fr",
            latitude=49.6116,
            longitude=6.13,
        )

        result = await coordinator._async_update_data()

        assert result == mock_meteolux_api
        # Verify the correct parameters were used
        call_args = mock_session.get.call_args
        assert "lat" in call_args.kwargs["params"]
        assert "long" in call_args.kwargs["params"]
        assert call_args.kwargs["params"]["langcode"] == "fr"


async def test_coordinator_http_error(hass: HomeAssistant):
    """Test coordinator handles HTTP errors."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session:
        mock_get = MagicMock()
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.get = mock_get

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
            city_id=490,
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_coordinator_network_error(hass: HomeAssistant):
    """Test coordinator handles network errors."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session:
        mock_get = MagicMock()
        mock_get.side_effect = aiohttp.ClientError("Network error")
        mock_session.return_value.get = mock_get

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
            city_id=490,
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_coordinator_no_location(hass: HomeAssistant):
    """Test coordinator raises error when no location is specified."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession"):
        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
        )

        with pytest.raises(UpdateFailed, match="No location specified"):
            await coordinator._async_update_data()


async def test_coordinator_shutdown(hass: HomeAssistant):
    """Test coordinator session cleanup."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_close = AsyncMock()
        mock_session.close = mock_close
        mock_session_class.return_value = mock_session

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
            city_id=490,
        )

        # Initialize the session by setting it directly (simulating a fetch)
        coordinator._session = mock_session

        await coordinator.async_shutdown()

        mock_close.assert_called_once()

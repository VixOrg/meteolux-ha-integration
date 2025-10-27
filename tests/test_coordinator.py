"""Tests for MeteoLux coordinator."""
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meteolux.coordinator import MeteoLuxDataUpdateCoordinator
from custom_components.meteolux.const import API_URL


async def test_coordinator_success(hass: HomeAssistant, mock_meteolux_api):
    """Test successful data fetch."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session:
        mock_get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_meteolux_api)
        mock_get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.get = mock_get

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
            city_id=490,
        )

        result = await coordinator._async_update_data()

        assert result == mock_meteolux_api
        mock_get.assert_called_once()


async def test_coordinator_with_coordinates(hass: HomeAssistant, mock_meteolux_api):
    """Test coordinator with lat/lon instead of city_id."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session:
        mock_get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_meteolux_api)
        mock_get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.get = mock_get

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
        call_args = mock_get.call_args
        assert "lat" in call_args.kwargs["params"]
        assert "long" in call_args.kwargs["params"]
        assert call_args.kwargs["params"]["langcode"] == "fr"


async def test_coordinator_http_error(hass: HomeAssistant):
    """Test coordinator handles HTTP errors."""
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session:
        mock_get = AsyncMock()
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
        mock_get = AsyncMock()
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
    with patch("custom_components.meteolux.coordinator.aiohttp.ClientSession") as mock_session:
        mock_close = AsyncMock()
        mock_session.return_value.close = mock_close

        coordinator = MeteoLuxDataUpdateCoordinator(
            hass,
            "test",
            update_interval=None,
            language="en",
            city_id=490,
        )

        await coordinator.async_shutdown()

        mock_close.assert_called_once()

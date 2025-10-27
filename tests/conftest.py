"""Fixtures for MeteoLux integration tests."""
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.meteolux.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_meteolux_api():
    """Mock MeteoLux API responses."""
    return {
        "city": {
            "id": 490,
            "name": "Luxembourg",
            "lat": 49.6116,
            "long": 6.13,
        },
        "ephemeris": {
            "date": "2025-10-27",
            "sunrise": "2025-10-27T07:45:00Z",
            "sunset": "2025-10-27T18:30:00Z",
            "sunshine": 8.5,
            "uvIndex": 3,
            "moonrise": "2025-10-27T20:15:00Z",
            "moonset": "2025-10-27T08:30:00Z",
            "moonPhase": 2,
        },
        "forecast": {
            "current": {
                "temperature": {
                    "temperature": 15.5,
                    "felt": 14.2,
                },
                "wind": {
                    "speed": "20-30",
                    "gusts": "40-50",
                    "direction": "O",
                },
                "rain": "0-1",
                "snow": "0",
                "icon": {
                    "id": 3,
                    "name": "Partly cloudy",
                },
                "humidity": 75,
                "pressure": 1013,
                "uv": 3,
                "clouds": 45,
            },
            "hourly": [
                {
                    "date": "2025-10-27T12:00:00Z",
                    "temperature": {
                        "temperature": 16.0,
                        "felt": 15.0,
                    },
                    "wind": {
                        "speed": "15-25",
                        "direction": "NO",
                    },
                    "rain": "0",
                    "icon": {
                        "id": 1,
                        "name": "Clear sky",
                    },
                },
            ],
            "forecast": [
                {
                    "date": "2025-10-27",
                    "maxTemp": 18.0,
                    "minTemp": 10.0,
                    "precipitation": "2-5",
                },
                {
                    "date": "2025-10-28",
                    "maxTemp": 17.0,
                    "minTemp": 9.0,
                    "precipitation": "1-3",
                },
            ],
        },
    }


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain="meteolux",
        title="Luxembourg",
        data={
            "name": "Luxembourg",
            "location_method": "city",
            "city_id": 490,
            "language": "en",
            "update_interval_current": 10,
            "update_interval_hourly": 30,
            "update_interval_daily": 6,
        },
        unique_id="490",
    )

"""Fixtures for MeteoLux integration tests."""
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


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
        "data": {
            "forecast": [
                {"date": "2025-10-27", "maxTemp": 18.0, "minTemp": 10.0, "precipitation": 3.5},
                {"date": "2025-10-28", "maxTemp": 17.0, "minTemp": 9.0, "precipitation": 2.0},
                {"date": "2025-10-29", "maxTemp": 19.0, "minTemp": 11.0, "precipitation": 1.0},
                {"date": "2025-10-30", "maxTemp": 20.0, "minTemp": 12.0, "precipitation": 0.5},
                {"date": "2025-10-31", "maxTemp": 21.0, "minTemp": 13.0, "precipitation": 0.0},
                {"date": "2025-11-01", "maxTemp": 19.0, "minTemp": 11.0, "precipitation": 2.0},
                {"date": "2025-11-02", "maxTemp": 18.0, "minTemp": 10.0, "precipitation": 3.0},
                {"date": "2025-11-03", "maxTemp": 17.0, "minTemp": 9.0, "precipitation": 2.5},
                {"date": "2025-11-04", "maxTemp": 16.0, "minTemp": 8.0, "precipitation": 1.5},
                {"date": "2025-11-05", "maxTemp": 15.0, "minTemp": 7.0, "precipitation": 1.0},
            ],
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
                    "date": "2025-10-27T18:00:00Z",
                    "temperature": {
                        "temperature": 16.0,
                        "felt": 15.0,
                    },
                    "wind": {
                        "speed": "15-25",
                        "gusts": "30-40",
                        "direction": "NO",
                    },
                    "rain": "0",
                    "icon": {
                        "id": 1,
                        "name": "Clear sky",
                    },
                    "humidity": 70,
                    "clouds": 30,
                    "uv": 2,
                },
                {
                    "date": "2025-10-28T00:00:00Z",
                    "temperature": {
                        "temperature": 14.0,
                        "felt": 13.0,
                    },
                    "wind": {
                        "speed": "10-20",
                        "gusts": "25-35",
                        "direction": "N",
                    },
                    "rain": "0",
                    "icon": {
                        "id": 2,
                        "name": "Cloudy",
                    },
                    "humidity": 75,
                    "clouds": 60,
                    "uv": 0,
                },
                {
                    "date": "2025-10-28T06:00:00Z",
                    "temperature": {
                        "temperature": 12.0,
                        "felt": 11.0,
                    },
                    "wind": {
                        "speed": "10-15",
                        "gusts": "20-30",
                        "direction": "N",
                    },
                    "rain": "1-2",
                    "icon": {
                        "id": 4,
                        "name": "Light rain",
                    },
                    "humidity": 80,
                    "clouds": 80,
                    "uv": 1,
                },
                {
                    "date": "2025-10-28T12:00:00Z",
                    "temperature": {
                        "temperature": 15.0,
                        "felt": 14.0,
                    },
                    "wind": {
                        "speed": "15-20",
                        "gusts": "25-35",
                        "direction": "NE",
                    },
                    "rain": "0",
                    "icon": {
                        "id": 3,
                        "name": "Partly cloudy",
                    },
                    "humidity": 72,
                    "clouds": 50,
                    "uv": 3,
                },
            ],
            "daily": [
                {
                    "date": "2025-10-27",
                    "icon": {
                        "id": 3,
                        "name": "Partly cloudy",
                    },
                    "wind": {
                        "speed": "15-25",
                        "gusts": "35-45",
                        "direction": "O",
                    },
                    "rain": "2-5",
                    "snow": "0",
                    "temperatureMin": {
                        "temperature": 10.0,
                        "felt": 9.0,
                    },
                    "temperatureMax": {
                        "temperature": 18.0,
                        "felt": 17.5,
                    },
                    "sunshine": 6,
                    "uvIndex": 3,
                },
                {
                    "date": "2025-10-28",
                    "icon": {
                        "id": 2,
                        "name": "Cloudy",
                    },
                    "wind": {
                        "speed": "10-20",
                        "gusts": "25-35",
                        "direction": "N",
                    },
                    "rain": "1-3",
                    "snow": "0",
                    "temperatureMin": {
                        "temperature": 9.0,
                        "felt": 8.0,
                    },
                    "temperatureMax": {
                        "temperature": 17.0,
                        "felt": 16.0,
                    },
                    "sunshine": 4,
                    "uvIndex": 2,
                },
                {
                    "date": "2025-10-29",
                    "icon": {
                        "id": 1,
                        "name": "Clear sky",
                    },
                    "wind": {
                        "speed": "10-15",
                        "gusts": "20-30",
                        "direction": "NE",
                    },
                    "rain": "0-1",
                    "snow": "0",
                    "temperatureMin": {
                        "temperature": 11.0,
                        "felt": 10.5,
                    },
                    "temperatureMax": {
                        "temperature": 19.0,
                        "felt": 18.5,
                    },
                    "sunshine": 8,
                    "uvIndex": 4,
                },
                {
                    "date": "2025-10-30",
                    "icon": {
                        "id": 3,
                        "name": "Partly cloudy",
                    },
                    "wind": {
                        "speed": "15-20",
                        "gusts": "30-40",
                        "direction": "E",
                    },
                    "rain": "0-1",
                    "snow": "0",
                    "temperatureMin": {
                        "temperature": 12.0,
                        "felt": 11.5,
                    },
                    "temperatureMax": {
                        "temperature": 20.0,
                        "felt": 19.5,
                    },
                    "sunshine": 7,
                    "uvIndex": 3,
                },
                {
                    "date": "2025-10-31",
                    "icon": {
                        "id": 1,
                        "name": "Clear sky",
                    },
                    "wind": {
                        "speed": "10-15",
                        "gusts": "20-25",
                        "direction": "SE",
                    },
                    "rain": "0",
                    "snow": "0",
                    "temperatureMin": {
                        "temperature": 13.0,
                        "felt": 12.5,
                    },
                    "temperatureMax": {
                        "temperature": 21.0,
                        "felt": 20.5,
                    },
                    "sunshine": 9,
                    "uvIndex": 3,
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
            "latitude": 49.6116,
            "longitude": 6.1319,
            "language": "en",
            "update_interval_current": 10,
            "update_interval_hourly": 30,
            "update_interval_daily": 6,
            "display_name": "Luxembourg, Luxembourg",
        },
        unique_id="coords_49.611600000_6.131900000",
    )

"""Tests for MeteoLux weather entity."""
from unittest.mock import AsyncMock

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.meteolux import weather
from custom_components.meteolux.const import DOMAIN


async def test_weather_setup(hass: HomeAssistant, mock_config_entry, mock_meteolux_api):
    """Test weather entity setup."""
    mock_config_entry.add_to_hass(hass)

    # Create mock coordinators
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_meteolux_api
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_meteolux_api

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_meteolux_api

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "coordinator_current": coordinator_current,
        "coordinator_hourly": coordinator_hourly,
        "coordinator_daily": coordinator_daily,
        "name": "Luxembourg",
    }

    entities = []
    async def async_add_entities(new_entities, update_before_add):
        entities.extend(new_entities)

    await weather.async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert len(entities) == 1
    assert isinstance(entities[0], weather.MeteoLuxWeather)


async def test_weather_current_condition(hass: HomeAssistant, mock_meteolux_api):
    """Test weather current condition."""
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_meteolux_api
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_meteolux_api

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_meteolux_api

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    assert weather_entity.condition == "partlycloudy"
    assert weather_entity.native_temperature == 15.5
    assert weather_entity.native_apparent_temperature == 14.2
    assert weather_entity.native_wind_speed == 25.0  # Average of 20-30
    assert weather_entity.wind_bearing == "W"  # "O" translated to "W"
    assert weather_entity.humidity == 75
    assert weather_entity.native_pressure == 1013


async def test_weather_wind_direction_translation(hass: HomeAssistant, mock_meteolux_api):
    """Test wind direction translation in weather entity."""
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_meteolux_api
    coordinator_current.language = "de"  # German

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_meteolux_api

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_meteolux_api

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    # In German, "O" (French) stays as "W" (West)
    assert weather_entity.wind_bearing == "W"


async def test_weather_daily_forecast(hass: HomeAssistant, mock_meteolux_api):
    """Test weather daily forecast."""
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_meteolux_api
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_meteolux_api

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_meteolux_api

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    forecasts = await weather_entity.async_forecast_daily()

    assert forecasts is not None
    assert len(forecasts) == 2
    assert forecasts[0]["datetime"] == "2025-10-27"
    assert forecasts[0]["native_temperature"] == 18.0
    assert forecasts[0]["native_templow"] == 10.0
    assert forecasts[0]["native_precipitation"] == 3.5  # Average of 2-5


async def test_weather_hourly_forecast(hass: HomeAssistant, mock_meteolux_api):
    """Test weather hourly forecast."""
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_meteolux_api
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_meteolux_api

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_meteolux_api

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    forecasts = await weather_entity.async_forecast_hourly()

    assert forecasts is not None
    assert len(forecasts) == 1
    assert forecasts[0]["datetime"] == "2025-10-27T12:00:00Z"
    assert forecasts[0]["native_temperature"] == 16.0
    assert forecasts[0]["native_apparent_temperature"] == 15.0
    assert forecasts[0]["native_wind_speed"] == 20.0  # Average of 15-25
    assert forecasts[0]["wind_bearing"] == "NW"  # "NO" translated to "NW"
    assert forecasts[0]["condition"] == "sunny"


async def test_weather_with_no_data(hass: HomeAssistant):
    """Test weather entity with no data."""
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = None
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = None

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = None

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    assert weather_entity.condition is None
    assert weather_entity.native_temperature is None
    assert await weather_entity.async_forecast_daily() is None
    assert await weather_entity.async_forecast_hourly() is None


async def test_weather_parse_functions(hass: HomeAssistant):
    """Test weather parsing helper functions."""
    # Test wind speed parsing
    assert weather.parse_wind_speed("20-30") == 25.0
    assert weather.parse_wind_speed("0") == 0.0

    # Test temperature parsing
    assert weather.parse_temperature(15.5) == 15.5
    assert weather.parse_temperature([14.0, 16.0]) == 15.0

    # Test precipitation parsing
    assert weather.parse_precipitation("1-2") == 1.5
    assert weather.parse_precipitation("0") == 0.0

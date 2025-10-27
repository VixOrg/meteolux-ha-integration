"""Tests for MeteoLux sensors."""
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.meteolux import sensor
from custom_components.meteolux.const import DOMAIN


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry, mock_meteolux_api):
    """Test sensor setup."""
    mock_config_entry.add_to_hass(hass)

    # Create mock coordinators
    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_meteolux_api
    coordinator_current.language = "en"

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_meteolux_api

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "coordinator_current": coordinator_current,
        "coordinator_daily": coordinator_daily,
        "name": "Luxembourg",
    }

    entities = []
    async def async_add_entities(new_entities, update_before_add):
        entities.extend(new_entities)

    await sensor.async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Verify entities were created
    # 9 current sensors + 4 new sensors (humidity, pressure, uv, clouds)
    # + 2 special sensors (ephemeris, location) + 15 forecast sensors (5 days x 3)
    assert len(entities) == 9 + 4 + 2 + 15


async def test_temperature_sensor(hass: HomeAssistant, mock_meteolux_api):
    """Test temperature sensor."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api
    coordinator.language = "en"

    description = sensor.SENSOR_TYPES[0]  # Temperature sensor
    test_sensor = sensor.MeteoLuxSensor(coordinator, description, "Test", "test_id")

    assert test_sensor.native_value == 15.5
    assert test_sensor.device_class == "temperature"


async def test_wind_direction_translation(hass: HomeAssistant, mock_meteolux_api):
    """Test wind direction translation."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api
    coordinator.language = "en"

    # Find wind direction sensor
    wind_direction_sensor = None
    for desc in sensor.SENSOR_TYPES:
        if desc.key == "wind_direction":
            wind_direction_sensor = sensor.MeteoLuxSensor(
                coordinator, desc, "Test", "test_id"
            )
            break

    assert wind_direction_sensor is not None
    # "O" (French for West) should be translated to "W" in English
    assert wind_direction_sensor.native_value == "W"


async def test_wind_speed_parsing(hass: HomeAssistant):
    """Test wind speed range parsing."""
    # Test range
    assert sensor.parse_wind_speed("20-30") == 25.0
    # Test single value
    assert sensor.parse_wind_speed("25") == 25.0
    # Test zero
    assert sensor.parse_wind_speed("0") == 0.0
    # Test None
    assert sensor.parse_wind_speed(None) == 0.0


async def test_temperature_parsing(hass: HomeAssistant):
    """Test temperature parsing."""
    # Test number
    assert sensor.parse_temperature(15.5) == 15.5
    # Test list (average)
    assert sensor.parse_temperature([14.0, 16.0]) == 15.0
    # Test None
    assert sensor.parse_temperature(None) is None


async def test_precipitation_parsing(hass: HomeAssistant):
    """Test precipitation range parsing."""
    # Test range
    assert sensor.parse_precipitation("1-2") == 1.5
    # Test single value
    assert sensor.parse_precipitation("3") == 3.0
    # Test zero
    assert sensor.parse_precipitation("0") == 0.0


async def test_ephemeris_sensor(hass: HomeAssistant, mock_meteolux_api):
    """Test ephemeris sensor."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api

    ephemeris_sensor = sensor.MeteoLuxEphemerisSensor(coordinator, "Test", "test_id")

    assert ephemeris_sensor.native_value == "2025-10-27"
    assert ephemeris_sensor.icon == "mdi:weather-sunset"

    attributes = ephemeris_sensor.extra_state_attributes
    assert attributes is not None
    assert "sun" in attributes
    assert "moon" in attributes
    assert attributes["sun"]["sunrise"] == "2025-10-27T07:45:00Z"
    assert attributes["sun"]["sunset"] == "2025-10-27T18:30:00Z"
    assert attributes["moon"]["moon_phase"] == 2
    assert attributes["moon"]["moon_icon"] == "first_quarter"


async def test_location_sensor(hass: HomeAssistant, mock_meteolux_api):
    """Test location sensor."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api

    location_sensor = sensor.MeteoLuxLocationSensor(coordinator, "Test", "test_id")

    assert location_sensor.native_value == "Luxembourg"
    assert location_sensor.icon == "mdi:map-marker"

    attributes = location_sensor.extra_state_attributes
    assert attributes is not None
    assert attributes["id"] == 490
    assert attributes["name"] == "Luxembourg"
    assert attributes["lat"] == 49.6116
    assert attributes["long"] == 6.13


async def test_forecast_sensors_lambda_closure(hass: HomeAssistant, mock_meteolux_api):
    """Test that forecast sensors correctly use different day indices."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api

    # Create sensors for day 0 and day 1
    sensor_day0 = sensor.MeteoLuxSensor(
        coordinator,
        sensor.create_forecast_sensor_temperature_high(0),
        "Test",
        "test_id",
    )
    sensor_day1 = sensor.MeteoLuxSensor(
        coordinator,
        sensor.create_forecast_sensor_temperature_high(1),
        "Test",
        "test_id",
    )

    # Verify they access different days
    assert sensor_day0.native_value == 18.0
    assert sensor_day1.native_value == 17.0


async def test_humidity_sensor(hass: HomeAssistant, mock_meteolux_api):
    """Test humidity sensor."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api
    coordinator.language = "en"

    # Find humidity sensor
    for desc in sensor.SENSOR_TYPES:
        if desc.key == "humidity":
            humidity_sensor = sensor.MeteoLuxSensor(
                coordinator, desc, "Test", "test_id"
            )
            assert humidity_sensor.native_value == 75
            assert humidity_sensor.device_class == "humidity"
            break


async def test_pressure_sensor(hass: HomeAssistant, mock_meteolux_api):
    """Test pressure sensor."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api
    coordinator.language = "en"

    # Find pressure sensor
    for desc in sensor.SENSOR_TYPES:
        if desc.key == "pressure":
            pressure_sensor = sensor.MeteoLuxSensor(
                coordinator, desc, "Test", "test_id"
            )
            assert pressure_sensor.native_value == 1013
            assert pressure_sensor.device_class == "pressure"
            break


async def test_sensor_with_no_data(hass: HomeAssistant):
    """Test sensor behavior when coordinator has no data."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = None
    coordinator.language = "en"

    description = sensor.SENSOR_TYPES[0]
    test_sensor = sensor.MeteoLuxSensor(coordinator, description, "Test", "test_id")

    assert test_sensor.native_value is None

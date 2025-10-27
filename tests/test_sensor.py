"""Tests for MeteoLux sensors."""
from unittest.mock import AsyncMock

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

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_meteolux_api

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "coordinator_current": coordinator_current,
        "coordinator_hourly": coordinator_hourly,
        "coordinator_daily": coordinator_daily,
        "name": "Luxembourg",
    }

    entities = []
    def async_add_entities(new_entities, update_before_add):
        entities.extend(new_entities)

    await sensor.async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Verify entities were created:
    # 1 current weather + 1 ephemeris + 1 location = 3 sensors
    # (Forecast data is provided via weather entity's async_forecast_daily/hourly methods)
    assert len(entities) == 3


async def test_current_weather_sensor(hass: HomeAssistant, mock_meteolux_api):
    """Test current weather sensor with all attributes."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api
    coordinator.language = "en"

    current_sensor = sensor.MeteoLuxCurrentWeatherSensor(
        coordinator, "Test", "test_id"
    )

    # State should be temperature
    assert current_sensor.native_value == 15.5
    assert current_sensor.device_class == "temperature"

    # Check attributes
    attributes = current_sensor.extra_state_attributes
    assert attributes is not None
    assert attributes["temperature"] == 15.5
    assert attributes["apparent_temperature"] == 14.2
    assert attributes["wind_speed"] == 25.0  # Midpoint of "20-30"
    assert attributes["wind_gusts"] == 45.0  # Midpoint of "40-50"
    assert attributes["wind_direction"] == "W"  # "O" translated to English
    assert attributes["precipitation"] == 0.5  # Midpoint of "0-1"
    assert attributes["snow"] == 0.0
    assert attributes["condition"] == "partlycloudy"
    assert attributes["condition_text"] == "Partly cloudy"
    assert attributes["humidity"] == 75
    assert attributes["pressure"] == 1013
    assert attributes["uv_index"] == 3
    assert attributes["cloud_cover"] == 45

    # Check calculated values
    assert "dew_point" in attributes
    assert attributes["dew_point"] is not None
    # wind_chill should be None (temp >= 10°C)
    assert attributes["wind_chill"] is None
    # humidex should be calculated
    assert "humidex" in attributes


async def test_wind_direction_translation(hass: HomeAssistant, mock_meteolux_api):
    """Test wind direction translation in current weather."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = mock_meteolux_api
    coordinator.language = "en"

    current_sensor = sensor.MeteoLuxCurrentWeatherSensor(
        coordinator, "Test", "test_id"
    )

    attributes = current_sensor.extra_state_attributes
    # "O" (French for West) should be translated to "W" in English
    assert attributes["wind_direction"] == "W"


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


async def test_calculated_values(hass: HomeAssistant):
    """Test calculated comfort indices."""
    # Test dew point calculation
    dew_point = sensor.calculate_dew_point(20.0, 60.0)
    assert dew_point is not None
    assert 11.0 < dew_point < 13.0  # Expected range

    # Test wind chill (should only work for temp < 10°C and wind > 4.8 km/h)
    wind_chill_none = sensor.calculate_wind_chill(15.0, 20.0)
    assert wind_chill_none is None  # Temp too high

    wind_chill_valid = sensor.calculate_wind_chill(5.0, 20.0)
    assert wind_chill_valid is not None
    assert wind_chill_valid < 5.0  # Should be colder than actual temp

    # Test humidex
    humidex = sensor.calculate_humidex(25.0, 70.0)
    assert humidex is not None
    assert humidex > 25.0  # Should feel hotter


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


async def test_sensor_with_no_data(hass: HomeAssistant):
    """Test sensor behavior when coordinator has no data."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = None
    coordinator.language = "en"

    current_sensor = sensor.MeteoLuxCurrentWeatherSensor(
        coordinator, "Test", "test_id"
    )

    assert current_sensor.native_value is None
    assert current_sensor.extra_state_attributes == {}

"""Tests for MeteoLux weather entity."""
from unittest.mock import AsyncMock


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
    def async_add_entities(new_entities, update_before_add):
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


async def test_weather_daily_forecast(hass: HomeAssistant, mock_meteolux_api, freezer):
    """Test weather daily forecast combines 5-day detailed and 10-day extended data."""
    # Freeze time to match test data date
    freezer.move_to("2025-10-27 12:00:00+00:00")

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
    # Should have 5 detailed (days 0-4) + 5 extended (days 5-9) = 10 total
    assert len(forecasts) == 10

    # Test first day (from detailed forecast, includes today's date)
    assert forecasts[0]["datetime"] == "2025-10-27"
    assert forecasts[0]["native_temperature"] == 18.0
    assert forecasts[0]["native_templow"] == 10.0
    assert forecasts[0]["native_precipitation"] == 3.5  # Average of 2-5
    assert forecasts[0]["native_wind_speed"] == 20.0  # Average of 15-25
    assert forecasts[0]["native_wind_gust_speed"] == 40.0  # Average of 35-45
    assert forecasts[0]["wind_bearing"] == "W"  # "O" translated to English
    assert forecasts[0]["uv_index"] == 3

    # Test second day (from detailed forecast)
    assert forecasts[1]["datetime"] == "2025-10-28"
    assert forecasts[1]["native_temperature"] == 17.0
    assert forecasts[1]["native_templow"] == 9.0
    assert forecasts[1]["native_precipitation"] == 2.0  # Average of 1-3

    # Test fifth day (from detailed forecast - last detailed day)
    assert forecasts[4]["datetime"] == "2025-10-31"
    assert forecasts[4]["native_temperature"] == 21.0
    assert forecasts[4]["native_templow"] == 13.0
    assert forecasts[4]["uv_index"] == 3

    # Test day 5 (from extended forecast - should be 6th entry, index 5)
    assert forecasts[5]["datetime"] == "2025-11-01"
    assert forecasts[5]["native_temperature"] == 19.0
    assert forecasts[5]["native_templow"] == 11.0
    assert forecasts[5]["native_precipitation"] == 2.0
    # Extended forecast entries should not have wind data or UV index
    assert "native_wind_speed" not in forecasts[5]
    assert "wind_bearing" not in forecasts[5]
    assert "uv_index" not in forecasts[5]

    # Test last day (from extended forecast - day 9, index 9)
    assert forecasts[9]["datetime"] == "2025-11-05"
    assert forecasts[9]["native_temperature"] == 15.0
    assert forecasts[9]["native_templow"] == 7.0


async def test_weather_hourly_forecast(hass: HomeAssistant, mock_meteolux_api):
    """Test weather hourly forecast with multiple times per day."""
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
    # Should have 4 hourly forecasts (18:00, 00:00, 06:00, 12:00)
    assert len(forecasts) == 4

    # Test first forecast (18:00)
    assert forecasts[0]["datetime"] == "2025-10-27T18:00:00Z"
    assert forecasts[0]["native_temperature"] == 16.0
    assert forecasts[0]["native_apparent_temperature"] == 15.0
    assert forecasts[0]["native_wind_speed"] == 20.0  # Average of 15-25
    assert forecasts[0]["wind_bearing"] == "NW"  # "NO" translated to "NW"
    assert forecasts[0]["condition"] == "sunny"
    assert forecasts[0]["native_wind_gust_speed"] == 35.0  # Average of 30-40
    assert forecasts[0]["humidity"] == 70
    assert forecasts[0]["cloud_coverage"] == 30
    assert forecasts[0]["uv_index"] == 2

    # Test second forecast (00:00 next day)
    assert forecasts[1]["datetime"] == "2025-10-28T00:00:00Z"
    assert forecasts[1]["native_temperature"] == 14.0
    assert forecasts[1]["uv_index"] == 0  # Nighttime

    # Test third forecast (06:00)
    assert forecasts[2]["datetime"] == "2025-10-28T06:00:00Z"
    assert forecasts[2]["native_precipitation"] == 1.5  # Average of 1-2


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


async def test_weather_daily_forecast_current_weather_merged(hass: HomeAssistant, mock_meteolux_api, freezer):
    """Test that current weather is merged into today's forecast when date matches."""
    # Use pytest-freezer to freeze time to match the first forecast day
    freezer.move_to("2025-10-27 12:00:00+00:00")

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
    assert len(forecasts) == 10

    # First day should have both forecast and current weather data
    today_forecast = forecasts[0]
    assert today_forecast["datetime"] == "2025-10-27"

    # Should have forecast temps (high/low)
    assert today_forecast["native_temperature"] == 18.0
    assert today_forecast["native_templow"] == 10.0

    # Should have current weather attributes merged in
    assert today_forecast["condition"] == "partlycloudy"  # From current weather
    assert today_forecast["humidity"] == 75  # From current weather
    assert today_forecast["native_pressure"] == 1013  # From current weather
    assert today_forecast["cloud_coverage"] == 45  # From current weather

    # Should keep forecast wind data
    assert today_forecast["native_wind_speed"] == 20.0  # From forecast
    assert today_forecast["wind_bearing"] == "W"  # From forecast


async def test_weather_daily_forecast_no_duplicates(hass: HomeAssistant, freezer):
    """Test that duplicate dates are not included in forecast."""
    # Freeze time to match test data date
    freezer.move_to("2025-10-27 12:00:00+00:00")

    # Create mock data with overlapping dates in detailed and extended forecasts
    mock_api_with_duplicates = {
        "forecast": {
            "current": {
                "temperature": {"temperature": 15.5, "felt": 14.2},
                "wind": {"speed": "20-30", "gusts": "40-50", "direction": "O"},
                "rain": "0-1",
                "icon": {"id": 3, "name": "Partly cloudy"},
                "humidity": 75,
                "pressure": 1013,
                "uv": 3,
                "clouds": 45,
            },
            "daily": [
                {
                    "date": "2025-10-27",
                    "icon": {"id": 3, "name": "Partly cloudy"},
                    "wind": {"speed": "15-25", "gusts": "35-45", "direction": "O"},
                    "rain": "2-5",
                    "temperatureMin": {"temperature": 10.0},
                    "temperatureMax": {"temperature": 18.0},
                    "uvIndex": 3,
                },
            ],
        },
        "data": {
            "forecast": [
                # Same date as detailed forecast - should be deduplicated
                {"date": "2025-10-27", "maxTemp": 19.0, "minTemp": 11.0, "precipitation": 4.0},
                {"date": "2025-10-28", "maxTemp": 17.0, "minTemp": 9.0, "precipitation": 2.0},
            ],
        },
    }

    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_api_with_duplicates
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_api_with_duplicates

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_api_with_duplicates

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    forecasts = await weather_entity.async_forecast_daily()

    assert forecasts is not None
    # Should have only 2 days total, with no duplicate for 2025-10-27
    assert len(forecasts) == 2

    # Verify dates are unique
    dates = [f["datetime"] for f in forecasts]
    assert len(dates) == len(set(dates))  # All dates should be unique

    # First entry should use detailed forecast data (not extended)
    assert forecasts[0]["datetime"] == "2025-10-27"
    assert forecasts[0]["native_temperature"] == 18.0  # From detailed, not 19.0 from extended
    assert forecasts[0]["uv_index"] == 3  # Only detailed forecast has UV index

    # Second entry should be from extended forecast
    assert forecasts[1]["datetime"] == "2025-10-28"
    assert forecasts[1]["native_temperature"] == 17.0


async def test_weather_daily_forecast_partial_detailed_data(hass: HomeAssistant, freezer):
    """Test that forecast works correctly with fewer than 5 detailed days."""
    # Freeze time to match test data date
    freezer.move_to("2025-10-27 12:00:00+00:00")

    # Mock API with only 2 detailed days and 10 extended days
    mock_api_partial = {
        "forecast": {
            "current": {
                "temperature": {"temperature": 15.5, "felt": 14.2},
                "wind": {"speed": "20-30", "gusts": "40-50", "direction": "O"},
                "rain": "0-1",
                "icon": {"id": 3, "name": "Partly cloudy"},
                "humidity": 75,
                "pressure": 1013,
                "uv": 3,
                "clouds": 45,
            },
            "daily": [
                {
                    "date": "2025-10-27",
                    "icon": {"id": 3, "name": "Partly cloudy"},
                    "wind": {"speed": "15-25", "gusts": "35-45", "direction": "O"},
                    "rain": "2-5",
                    "temperatureMin": {"temperature": 10.0},
                    "temperatureMax": {"temperature": 18.0},
                    "uvIndex": 3,
                },
                {
                    "date": "2025-10-28",
                    "icon": {"id": 2, "name": "Cloudy"},
                    "wind": {"speed": "10-20", "gusts": "25-35", "direction": "N"},
                    "rain": "1-3",
                    "temperatureMin": {"temperature": 9.0},
                    "temperatureMax": {"temperature": 17.0},
                    "uvIndex": 2,
                },
            ],
        },
        "data": {
            "forecast": [
                {"date": "2025-10-27", "maxTemp": 18.0, "minTemp": 10.0, "precipitation": 3.5},
                {"date": "2025-10-28", "maxTemp": 17.0, "minTemp": 9.0, "precipitation": 2.0},
                {"date": "2025-10-29", "maxTemp": 19.0, "minTemp": 11.0, "precipitation": 1.0},
                {"date": "2025-10-30", "maxTemp": 20.0, "minTemp": 12.0, "precipitation": 0.5},
                {"date": "2025-10-31", "maxTemp": 21.0, "minTemp": 13.0, "precipitation": 0.0},
                {"date": "2025-11-01", "maxTemp": 19.0, "minTemp": 11.0, "precipitation": 2.0},
            ],
        },
    }

    coordinator_current = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_current.data = mock_api_partial
    coordinator_current.language = "en"

    coordinator_hourly = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_hourly.data = mock_api_partial

    coordinator_daily = AsyncMock(spec=DataUpdateCoordinator)
    coordinator_daily.data = mock_api_partial

    weather_entity = weather.MeteoLuxWeather(
        coordinator_current,
        coordinator_hourly,
        coordinator_daily,
        "Test",
        "test_id",
    )

    forecasts = await weather_entity.async_forecast_daily()

    assert forecasts is not None
    # Should have 2 detailed + 4 extended (starting from index 2) = 6 total
    assert len(forecasts) == 6

    # First two days should have detailed data with UV index
    assert forecasts[0]["datetime"] == "2025-10-27"
    assert forecasts[0]["uv_index"] == 3
    assert forecasts[1]["datetime"] == "2025-10-28"
    assert forecasts[1]["uv_index"] == 2

    # Remaining days should be from extended forecast (no UV index)
    assert forecasts[2]["datetime"] == "2025-10-29"
    assert "uv_index" not in forecasts[2]
    assert forecasts[2]["native_temperature"] == 19.0

    assert forecasts[5]["datetime"] == "2025-11-01"
    assert forecasts[5]["native_temperature"] == 19.0

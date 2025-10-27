"""Weather platform for MeteoLux integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONDITION_MAP, DOMAIN, WIND_DIRECTION_MAP
from .coordinator import MeteoLuxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def parse_wind_speed(wind_speed_str: str | None) -> float | None:
    """Parse wind speed from range string like '20-30' to midpoint."""
    if not wind_speed_str or wind_speed_str == "0":
        return 0.0
    try:
        parts = wind_speed_str.split("-")
        if len(parts) == 2:
            return (float(parts[0]) + float(parts[1])) / 2
        return float(parts[0])
    except (ValueError, IndexError):
        return None


def parse_temperature(temp: Any) -> float | None:
    """Parse temperature which can be int, float or list."""
    if temp is None:
        return None
    if isinstance(temp, (int, float)):
        return float(temp)
    if isinstance(temp, list) and len(temp) > 0:
        # Return average of range
        return sum(temp) / len(temp)
    return None


def parse_precipitation(precip_str: str | None) -> float | None:
    """Parse precipitation from range string like '1-2' to midpoint."""
    if not precip_str or precip_str == "0":
        return 0.0
    try:
        parts = precip_str.split("-")
        if len(parts) == 2:
            return (float(parts[0]) + float(parts[1])) / 2
        return float(parts[0])
    except (ValueError, IndexError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MeteoLux weather entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator_current = data["coordinator_current"]
    coordinator_hourly = data["coordinator_hourly"]
    coordinator_daily = data["coordinator_daily"]
    name = data["name"]

    async_add_entities(
        [
            MeteoLuxWeather(
                coordinator_current,
                coordinator_hourly,
                coordinator_daily,
                name,
                entry.entry_id,
            )
        ],
        False,
    )


class MeteoLuxWeather(CoordinatorEntity, WeatherEntity):
    """Implementation of MeteoLux weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        coordinator_current: MeteoLuxDataUpdateCoordinator,
        coordinator_hourly: MeteoLuxDataUpdateCoordinator,
        coordinator_daily: MeteoLuxDataUpdateCoordinator,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator_current)
        self.coordinator_hourly = coordinator_hourly
        self.coordinator_daily = coordinator_daily
        self._attr_unique_id = f"{entry_id}_weather"

        # Set up device info
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="MeteoLux",
            name=name,
        )

    def _translate_wind_direction(self, direction: str | None) -> str | None:
        """Translate wind direction from French to selected language."""
        if not direction:
            return None
        language = self.coordinator.language
        direction_map = WIND_DIRECTION_MAP.get(language, WIND_DIRECTION_MAP["en"])
        return direction_map.get(direction, direction)

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        if not self.coordinator.data:
            return None
        try:
            current = self.coordinator.data["forecast"]["current"]
            icon_id = current["icon"]["id"]
            return CONDITION_MAP.get(icon_id, None)
        except (KeyError, TypeError):
            return None

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None
        try:
            temp_data = self.coordinator.data["forecast"]["current"]["temperature"]
            return parse_temperature(temp_data.get("temperature"))
        except (KeyError, TypeError):
            return None

    @property
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        if not self.coordinator.data:
            return None
        try:
            temp_data = self.coordinator.data["forecast"]["current"]["temperature"]
            return temp_data.get("felt")
        except (KeyError, TypeError):
            return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        if not self.coordinator.data:
            return None
        try:
            wind_data = self.coordinator.data["forecast"]["current"]["wind"]
            return parse_wind_speed(wind_data.get("speed"))
        except (KeyError, TypeError):
            return None

    @property
    def wind_bearing(self) -> str | None:
        """Return the wind bearing."""
        if not self.coordinator.data:
            return None
        try:
            wind_data = self.coordinator.data["forecast"]["current"]["wind"]
            direction = wind_data.get("direction")
            return self._translate_wind_direction(direction)
        except (KeyError, TypeError):
            return None

    @property
    def humidity(self) -> float | None:
        """Return the humidity."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data["forecast"]["current"].get("humidity")
        except (KeyError, TypeError):
            return None

    @property
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data["forecast"]["current"].get("pressure")
        except (KeyError, TypeError):
            return None

    @property
    def uv_index(self) -> float | None:
        """Return the UV index."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data["forecast"]["current"].get("uv")
        except (KeyError, TypeError):
            return None

    @property
    def cloud_coverage(self) -> float | None:
        """Return the cloud coverage percentage."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data["forecast"]["current"].get("clouds")
        except (KeyError, TypeError):
            return None

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast combining current weather, detailed and extended data."""
        if not self.coordinator_daily.data:
            return None

        forecasts: list[Forecast] = []
        forecast_dates: set[str] = set()

        try:
            from datetime import datetime, timezone

            # Get today's date for comparison
            today = datetime.now(timezone.utc).date().isoformat()
            _LOGGER.debug("Today's date (UTC): %s", today)

            # Get both forecast sources
            detailed_data = self.coordinator_daily.data.get("forecast", {}).get("daily", [])
            extended_data = self.coordinator_daily.data.get("data", {}).get("forecast", [])

            _LOGGER.debug(
                "Forecast data sources - Detailed: %d days, Extended: %d days",
                len(detailed_data),
                len(extended_data),
            )

            if detailed_data:
                _LOGGER.debug("First detailed forecast date: %s", detailed_data[0].get("date"))
            if extended_data:
                _LOGGER.debug(
                    "Extended forecast dates: %s",
                    [day.get("date") for day in extended_data[:10]],
                )

            # Check if today is missing from forecasts and add it from current weather
            first_forecast_date = None
            if detailed_data:
                first_forecast_date = detailed_data[0].get("date")
            elif extended_data:
                first_forecast_date = extended_data[0].get("date")

            if first_forecast_date and first_forecast_date != today:
                _LOGGER.debug("Today (%s) is missing from API forecast (starts at %s), adding from current weather", today, first_forecast_date)

                if self.coordinator.data:
                    try:
                        current = self.coordinator.data["forecast"]["current"]
                        current_wind = current.get("wind", {})

                        # Create today's forecast from current weather
                        today_forecast = Forecast(
                            datetime=today,
                            condition=self.condition,
                            native_temperature=self.native_temperature,
                            native_apparent_temperature=self.native_apparent_temperature,
                            native_templow=None,  # Current weather doesn't have low temp
                            native_precipitation=parse_precipitation(current.get("rain")),
                            native_wind_speed=parse_wind_speed(current_wind.get("speed")),
                            native_wind_gust_speed=parse_wind_speed(current_wind.get("gusts")),
                            wind_bearing=self.wind_bearing,
                            humidity=current.get("humidity"),
                            native_pressure=current.get("pressure"),
                            cloud_coverage=current.get("clouds"),
                            uv_index=current.get("uv"),
                        )
                        forecasts.append(today_forecast)
                        forecast_dates.add(today)
                        _LOGGER.debug("Added today's forecast from current weather")
                    except (KeyError, TypeError) as err:
                        _LOGGER.debug("Could not add today from current weather: %s", err)

            # First, add the detailed 5-day forecast (days 0-4)
            for day in detailed_data[:5]:
                date = day["date"]
                _LOGGER.debug("Processing detailed forecast for date: %s (is today? %s)", date, date == today)

                # Extract temperatures from Temperature objects
                temp_max_obj = day.get("temperatureMax", {})
                temp_min_obj = day.get("temperatureMin", {})

                temp_max = parse_temperature(temp_max_obj.get("temperature"))
                temp_min = parse_temperature(temp_min_obj.get("temperature"))

                # Get wind data
                wind_data = day.get("wind", {})
                wind_direction = self._translate_wind_direction(wind_data.get("direction"))

                # Use rain field for precipitation
                precipitation = parse_precipitation(day.get("rain"))

                # Create base forecast from detailed data
                forecast_data = {
                    "datetime": date,
                    "native_temperature": temp_max,
                    "native_templow": temp_min,
                    "native_precipitation": precipitation,
                    "native_wind_speed": parse_wind_speed(wind_data.get("speed")),
                    "native_wind_gust_speed": parse_wind_speed(wind_data.get("gusts")),
                    "wind_bearing": wind_direction,
                    "uv_index": day.get("uvIndex"),
                }

                # If this is today, merge with current weather data
                if date == today and self.coordinator.data:
                    try:
                        current = self.coordinator.data["forecast"]["current"]
                        current_wind = current.get("wind", {})

                        # Enhance with current real-time values where available
                        # Keep forecast's high/low temps, but add current conditions
                        forecast_data.update({
                            "condition": self.condition,  # Current condition
                            "humidity": current.get("humidity"),
                            "native_pressure": current.get("pressure"),
                            "cloud_coverage": current.get("clouds"),
                            # Keep the forecast wind data if available, otherwise use current
                            "native_wind_speed": forecast_data["native_wind_speed"] or parse_wind_speed(current_wind.get("speed")),
                            "wind_bearing": forecast_data["wind_bearing"] or self._translate_wind_direction(current_wind.get("direction")),
                        })

                        _LOGGER.debug("Merged current weather with today's forecast for %s", date)
                    except (KeyError, TypeError) as err:
                        _LOGGER.debug("Could not merge current weather: %s", err)

                forecast = Forecast(**forecast_data)
                forecasts.append(forecast)
                forecast_dates.add(date)

            # Count how many detailed days we processed
            detailed_days = len(forecasts)

            _LOGGER.debug(
                "Processed %d detailed forecast days. Dates so far: %s",
                detailed_days,
                sorted(forecast_dates),
            )

            # Then, add the extended forecast for remaining days
            # Start from the number of detailed days we already have
            _LOGGER.debug(
                "Extended forecast check: len(extended_data)=%d > detailed_days=%d? %s",
                len(extended_data),
                detailed_days,
                len(extended_data) > detailed_days,
            )

            if len(extended_data) > detailed_days:
                _LOGGER.debug(
                    "Processing extended forecast from index %d: %s",
                    detailed_days,
                    [day.get("date") for day in extended_data[detailed_days:]],
                )

                for day in extended_data[detailed_days:]:
                    date = day["date"]

                    # Skip if we already have this date from detailed forecast
                    if date in forecast_dates:
                        _LOGGER.debug("Skipping duplicate date from extended forecast: %s", date)
                        continue

                    _LOGGER.debug("Adding extended forecast for date: %s", date)

                    forecast = Forecast(
                        datetime=date,
                        native_temperature=day.get("maxTemp"),
                        native_templow=day.get("minTemp"),
                        native_precipitation=day.get("precipitation"),
                    )
                    forecasts.append(forecast)
                    forecast_dates.add(date)

            _LOGGER.debug(
                "Generated %d daily forecast entries with dates: %s",
                len(forecasts),
                sorted(forecast_dates),
            )

        except (KeyError, TypeError) as err:
            _LOGGER.error("Error parsing daily forecast: %s", err)
            return None

        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast.

        The API provides forecasts at multiple times throughout each day
        (typically 00:00, 06:00, 12:00, 18:00) spanning approximately 5 days.
        """
        if not self.coordinator_hourly.data:
            return None

        forecasts: list[Forecast] = []
        try:
            hourly_data = self.coordinator_hourly.data["forecast"]["hourly"]
            for hour in hourly_data:
                icon_id = hour["icon"]["id"]
                temp = parse_temperature(hour["temperature"].get("temperature"))
                direction = hour["wind"].get("direction")

                forecast = Forecast(
                    datetime=hour["date"],
                    condition=CONDITION_MAP.get(icon_id),
                    native_temperature=temp,
                    native_apparent_temperature=hour["temperature"].get("felt"),
                    native_wind_speed=parse_wind_speed(hour["wind"].get("speed")),
                    native_wind_gust_speed=parse_wind_speed(hour["wind"].get("gusts")),
                    wind_bearing=self._translate_wind_direction(direction),
                    native_precipitation=parse_precipitation(hour.get("rain")),
                    humidity=hour.get("humidity"),
                    cloud_coverage=hour.get("clouds"),
                    uv_index=hour.get("uv"),
                )
                forecasts.append(forecast)
        except (KeyError, TypeError) as err:
            _LOGGER.error("Error parsing hourly forecast: %s", err)
            return None

        return forecasts

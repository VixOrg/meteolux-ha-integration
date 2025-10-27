"""Weather platform for MeteoLux integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
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

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        if not self.coordinator_daily.data:
            return None
        
        forecasts: list[Forecast] = []
        try:
            daily_data = self.coordinator_daily.data["forecast"]["forecast"]
            for day in daily_data:
                forecast = Forecast(
                    datetime=day["date"],
                    native_temperature=day.get("maxTemp"),
                    native_templow=day.get("minTemp"),
                    native_precipitation=day.get("precipitation"),
                )
                forecasts.append(forecast)
        except (KeyError, TypeError) as err:
            _LOGGER.error("Error parsing daily forecast: %s", err)
            return None
        
        return forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast."""
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
                    wind_bearing=self._translate_wind_direction(direction),
                    native_precipitation=parse_precipitation(hour.get("rain")),
                )
                forecasts.append(forecast)
        except (KeyError, TypeError) as err:
            _LOGGER.error("Error parsing hourly forecast: %s", err)
            return None

        return forecasts

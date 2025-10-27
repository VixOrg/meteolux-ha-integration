"""Sensor platform for MeteoLux integration."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
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


def calculate_dew_point(temperature: float, humidity: float) -> float | None:
    """Calculate dew point using Magnus formula."""
    try:
        a = 17.27
        b = 237.7
        alpha = ((a * temperature) / (b + temperature)) + math.log(humidity / 100.0)
        return round((b * alpha) / (a - alpha), 1)
    except (ValueError, ZeroDivisionError):
        return None


def calculate_wind_chill(temperature: float, wind_speed: float) -> float | None:
    """Calculate wind chill (only applicable when temp < 10°C and wind > 4.8 km/h)."""
    if temperature >= 10 or wind_speed <= 4.8:
        return None
    try:
        wind_chill = (
            13.12
            + 0.6215 * temperature
            - 11.37 * (wind_speed**0.16)
            + 0.3965 * temperature * (wind_speed**0.16)
        )
        return round(wind_chill, 1)
    except (ValueError, ZeroDivisionError):
        return None


def calculate_humidex(temperature: float, humidity: float) -> float | None:
    """Calculate humidex (Canadian humidity index)."""
    try:
        # Calculate dewpoint
        dewpoint = calculate_dew_point(temperature, humidity)
        if dewpoint is None:
            return None

        # Calculate humidex
        e = 6.11 * math.exp(5417.7530 * ((1 / 273.16) - (1 / (dewpoint + 273.15))))
        h = 0.5555 * (e - 10.0)
        humidex = temperature + h

        # Only return if humidex is significantly higher than temperature
        if humidex > temperature + 1:
            return round(humidex, 1)
        return None
    except (ValueError, ZeroDivisionError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MeteoLux sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator_current = data["coordinator_current"]
    name = data["name"]
    entry_id = entry.entry_id

    entities: list[SensorEntity] = []

    # Add current weather sensor (consolidated)
    entities.append(
        MeteoLuxCurrentWeatherSensor(
            coordinator_current,
            name,
            entry_id,
        )
    )

    # Add ephemeris (today) sensor
    entities.append(
        MeteoLuxEphemerisSensor(
            coordinator_current,
            name,
            entry_id,
        )
    )

    # Add location sensor
    entities.append(
        MeteoLuxLocationSensor(
            coordinator_current,
            name,
            entry_id,
        )
    )

    async_add_entities(entities, False)


class MeteoLuxCurrentWeatherSensor(CoordinatorEntity, SensorEntity):
    """Consolidated sensor for all current weather data."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: MeteoLuxDataUpdateCoordinator,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the current weather sensor."""
        super().__init__(coordinator)
        self._attr_name = "Current Weather"
        self._attr_unique_id = f"{entry_id}_current_weather"

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="MeteoLux",
            name=name,
        )

    @property
    def native_value(self) -> float | None:
        """Return current temperature as the state."""
        if not self.coordinator.data:
            return None
        try:
            temp_data = self.coordinator.data["forecast"]["current"]["temperature"]
            return parse_temperature(temp_data.get("temperature"))
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return all current weather data as attributes."""
        if not self.coordinator.data:
            return {}

        try:
            current = self.coordinator.data["forecast"]["current"]
            temp_data = current["temperature"]
            wind_data = current["wind"]
            icon_data = current["icon"]

            # Get basic values
            temperature = parse_temperature(temp_data.get("temperature"))
            apparent_temperature = temp_data.get("felt")
            humidity = current.get("humidity")
            wind_speed = parse_wind_speed(wind_data.get("speed"))

            # Get humidex from API
            humidex_str = temp_data.get("humidex")
            humidex = float(humidex_str) if humidex_str else None

            # Calculate additional comfort values
            dew_point = None
            wind_chill = None
            if temperature is not None and humidity is not None:
                dew_point = calculate_dew_point(temperature, humidity)
                if wind_speed is not None:
                    wind_chill = calculate_wind_chill(temperature, wind_speed)
                # Calculate humidex if not in API
                if humidex is None:
                    humidex = calculate_humidex(temperature, humidity)

            # Translate wind direction
            wind_direction = wind_data.get("direction")
            if wind_direction:
                language = self.coordinator.language
                direction_map = WIND_DIRECTION_MAP.get(language, WIND_DIRECTION_MAP["en"])
                wind_direction = direction_map.get(wind_direction, wind_direction)

            attributes = {
                "temperature": temperature,
                "apparent_temperature": apparent_temperature,
                "dew_point": dew_point,
                "wind_chill": wind_chill,
                "humidex": humidex,
                "wind_speed": wind_speed,
                "wind_gusts": parse_wind_speed(wind_data.get("gusts")),
                "wind_direction": wind_direction,
                "precipitation": parse_precipitation(current.get("rain")),
                "snow": parse_precipitation(current.get("snow")),
                "condition": CONDITION_MAP.get(icon_data.get("id")),
                "condition_text": icon_data.get("name"),
                "humidity": humidity,
                "pressure": current.get("pressure"),
                "uv_index": current.get("uv"),
                "cloud_cover": current.get("clouds"),
            }

            return attributes
        except (KeyError, TypeError) as err:
            _LOGGER.debug("Error getting current weather attributes: %s", err)
            return None


class MeteoLuxEphemerisSensor(CoordinatorEntity, SensorEntity):
    """Sensor for ephemeris data (sun and moon information)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MeteoLuxDataUpdateCoordinator,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the ephemeris sensor."""
        super().__init__(coordinator)
        self._attr_name = "Today"
        self._attr_unique_id = f"{entry_id}_ephemeris"
        self._attr_icon = "mdi:weather-sunset"

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="MeteoLux",
            name=name,
        )

    @property
    def native_value(self) -> str | None:
        """Return the date as the state."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data.get("ephemeris", {}).get("date")
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return ephemeris attributes."""
        if not self.coordinator.data:
            return {}

        try:
            ephemeris = self.coordinator.data.get("ephemeris", {})

            # Map moon phase number to Home Assistant moon phase
            moon_phase_map = {
                0: "new_moon",
                1: "waxing_crescent",
                2: "first_quarter",
                3: "waxing_gibbous",
                4: "full_moon",
                5: "waning_gibbous",
                6: "last_quarter",
                7: "waning_crescent",
            }

            moon_phase_id = ephemeris.get("moonPhase")
            moon_icon = moon_phase_map.get(moon_phase_id) if moon_phase_id is not None else None

            return {
                "date": ephemeris.get("date"),
                "sun": {
                    "sunrise": ephemeris.get("sunrise"),
                    "sunset": ephemeris.get("sunset"),
                    "sunshine": ephemeris.get("sunshine"),
                    "uv_index": ephemeris.get("uvIndex"),
                },
                "moon": {
                    "moonrise": ephemeris.get("moonrise"),
                    "moonset": ephemeris.get("moonset"),
                    "moon_phase": moon_phase_id,
                    "moon_icon": moon_icon,
                },
            }
        except (KeyError, TypeError) as err:
            _LOGGER.debug("Error getting ephemeris attributes: %s", err)
            return None


class MeteoLuxLocationSensor(CoordinatorEntity, SensorEntity):
    """Sensor for location/city information."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MeteoLuxDataUpdateCoordinator,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the location sensor."""
        super().__init__(coordinator)
        self._attr_name = "Location"
        self._attr_unique_id = f"{entry_id}_location"
        self._attr_icon = "mdi:map-marker"

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="MeteoLux",
            name=name,
        )

    @property
    def native_value(self) -> str | None:
        """Return the city name as the state."""
        if not self.coordinator.data:
            return None
        try:
            return self.coordinator.data.get("city", {}).get("name")
        except (KeyError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return all city attributes from API response."""
        if not self.coordinator.data:
            return {}

        try:
            city = self.coordinator.data.get("city", {})
            # Return all properties from the city object as-is
            return dict(city) if city else None
        except (KeyError, TypeError) as err:
            _LOGGER.debug("Error getting location attributes: %s", err)
            return None

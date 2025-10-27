"""Sensor platform for MeteoLux integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfIrradiance,
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


@dataclass(frozen=True, kw_only=True)
class MeteoLuxSensorDescription(SensorEntityDescription):
    """Describes MeteoLux sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


def get_current_temperature(data: dict[str, Any]) -> float | None:
    """Get current temperature."""
    try:
        temp_data = data["forecast"]["current"]["temperature"]
        return parse_temperature(temp_data.get("temperature"))
    except (KeyError, TypeError):
        return None


def get_apparent_temperature(data: dict[str, Any]) -> float | None:
    """Get apparent temperature (feels like)."""
    try:
        return data["forecast"]["current"]["temperature"].get("felt")
    except (KeyError, TypeError):
        return None


def get_wind_speed(data: dict[str, Any]) -> float | None:
    """Get wind speed."""
    try:
        return parse_wind_speed(data["forecast"]["current"]["wind"].get("speed"))
    except (KeyError, TypeError):
        return None


def get_wind_gusts(data: dict[str, Any]) -> float | None:
    """Get wind gusts."""
    try:
        return parse_wind_speed(data["forecast"]["current"]["wind"].get("gusts"))
    except (KeyError, TypeError):
        return None


def get_wind_direction(data: dict[str, Any]) -> str | None:
    """Get wind direction."""
    try:
        return data["forecast"]["current"]["wind"].get("direction")
    except (KeyError, TypeError):
        return None


def get_precipitation(data: dict[str, Any]) -> float | None:
    """Get precipitation."""
    try:
        return parse_precipitation(data["forecast"]["current"].get("rain"))
    except (KeyError, TypeError):
        return None


def get_snow(data: dict[str, Any]) -> float | None:
    """Get snow."""
    try:
        return parse_precipitation(data["forecast"]["current"].get("snow"))
    except (KeyError, TypeError):
        return None


def get_condition(data: dict[str, Any]) -> str | None:
    """Get condition."""
    try:
        icon_id = data["forecast"]["current"]["icon"]["id"]
        return CONDITION_MAP.get(icon_id)
    except (KeyError, TypeError):
        return None


def get_condition_text(data: dict[str, Any]) -> str | None:
    """Get condition text."""
    try:
        return data["forecast"]["current"]["icon"].get("name")
    except (KeyError, TypeError):
        return None


def get_humidity(data: dict[str, Any]) -> float | None:
    """Get humidity."""
    try:
        return data["forecast"]["current"].get("humidity")
    except (KeyError, TypeError):
        return None


def get_pressure(data: dict[str, Any]) -> float | None:
    """Get atmospheric pressure."""
    try:
        return data["forecast"]["current"].get("pressure")
    except (KeyError, TypeError):
        return None


def get_uv_index(data: dict[str, Any]) -> float | None:
    """Get UV index."""
    try:
        uv = data["forecast"]["current"].get("uv")
        if uv is not None:
            return float(uv)
        return None
    except (KeyError, TypeError, ValueError):
        return None


def get_cloud_cover(data: dict[str, Any]) -> float | None:
    """Get cloud cover percentage."""
    try:
        return data["forecast"]["current"].get("clouds")
    except (KeyError, TypeError):
        return None


# Current weather sensors
SENSOR_TYPES: tuple[MeteoLuxSensorDescription, ...] = (
    MeteoLuxSensorDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=get_current_temperature,
    ),
    MeteoLuxSensorDescription(
        key="apparent_temperature",
        name="Apparent Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=get_apparent_temperature,
    ),
    MeteoLuxSensorDescription(
        key="wind_speed",
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=get_wind_speed,
    ),
    MeteoLuxSensorDescription(
        key="wind_gusts",
        name="Wind Gusts",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        value_fn=get_wind_gusts,
        entity_registry_enabled_default=False,
    ),
    MeteoLuxSensorDescription(
        key="wind_direction",
        name="Wind Direction",
        value_fn=get_wind_direction,
        entity_registry_enabled_default=False,
    ),
    MeteoLuxSensorDescription(
        key="precipitation",
        name="Precipitation",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=get_precipitation,
    ),
    MeteoLuxSensorDescription(
        key="snow",
        name="Snow",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=get_snow,
        entity_registry_enabled_default=False,
    ),
    MeteoLuxSensorDescription(
        key="condition",
        name="Condition",
        value_fn=get_condition,
    ),
    MeteoLuxSensorDescription(
        key="condition_text",
        name="Condition Text",
        value_fn=get_condition_text,
        entity_registry_enabled_default=False,
    ),
    MeteoLuxSensorDescription(
        key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=get_humidity,
    ),
    MeteoLuxSensorDescription(
        key="pressure",
        name="Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        value_fn=get_pressure,
    ),
    MeteoLuxSensorDescription(
        key="uv_index",
        name="UV Index",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=get_uv_index,
        entity_registry_enabled_default=False,
    ),
    MeteoLuxSensorDescription(
        key="cloud_cover",
        name="Cloud Cover",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=get_cloud_cover,
        entity_registry_enabled_default=False,
    ),
)


# Forecast sensor generators
def create_forecast_sensor_temperature_high(day: int) -> MeteoLuxSensorDescription:
    """Create forecast high temperature sensor."""
    return MeteoLuxSensorDescription(
        key=f"temperature_high_{day}d",
        name=f"Temperature High Day {day}",
        translation_key="temperature_high",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data, d=day: (
            parse_temperature(data["forecast"]["forecast"][d].get("maxTemp"))
            if len(data.get("forecast", {}).get("forecast", [])) > d
            else None
        ),
        entity_registry_enabled_default=(day == 0),
    )


def create_forecast_sensor_temperature_low(day: int) -> MeteoLuxSensorDescription:
    """Create forecast low temperature sensor."""
    return MeteoLuxSensorDescription(
        key=f"temperature_low_{day}d",
        name=f"Temperature Low Day {day}",
        translation_key="temperature_low",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data, d=day: (
            parse_temperature(data["forecast"]["forecast"][d].get("minTemp"))
            if len(data.get("forecast", {}).get("forecast", [])) > d
            else None
        ),
        entity_registry_enabled_default=(day == 0),
    )


def create_forecast_sensor_precipitation(day: int) -> MeteoLuxSensorDescription:
    """Create forecast precipitation sensor."""
    return MeteoLuxSensorDescription(
        key=f"precipitation_{day}d",
        name=f"Precipitation Day {day}",
        translation_key="precipitation_forecast",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda data, d=day: (
            parse_precipitation(data["forecast"]["forecast"][d].get("precipitation"))
            if len(data.get("forecast", {}).get("forecast", [])) > d
            else None
        ),
        entity_registry_enabled_default=(day == 0),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MeteoLux sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator_current = data["coordinator_current"]
    coordinator_daily = data["coordinator_daily"]
    name = data["name"]
    entry_id = entry.entry_id

    entities: list[SensorEntity] = []

    # Add current weather sensors
    for description in SENSOR_TYPES:
        entities.append(
            MeteoLuxSensor(
                coordinator_current,
                description,
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

    # Add 5-day forecast sensors
    for day in range(5):
        entities.extend(
            [
                MeteoLuxSensor(
                    coordinator_daily,
                    create_forecast_sensor_temperature_high(day),
                    name,
                    entry_id,
                ),
                MeteoLuxSensor(
                    coordinator_daily,
                    create_forecast_sensor_temperature_low(day),
                    name,
                    entry_id,
                ),
                MeteoLuxSensor(
                    coordinator_daily,
                    create_forecast_sensor_precipitation(day),
                    name,
                    entry_id,
                ),
            ]
        )

    async_add_entities(entities, False)


class MeteoLuxSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a MeteoLux sensor."""

    _attr_has_entity_name = True
    entity_description: MeteoLuxSensorDescription

    def __init__(
        self,
        coordinator: MeteoLuxDataUpdateCoordinator,
        description: MeteoLuxSensorDescription,
        name: str,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            manufacturer="MeteoLux",
            name=name,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        try:
            value = self.entity_description.value_fn(self.coordinator.data)

            # Translate wind direction from French to selected language
            if self.entity_description.key == "wind_direction" and value:
                language = self.coordinator.language
                direction_map = WIND_DIRECTION_MAP.get(language, WIND_DIRECTION_MAP["en"])
                value = direction_map.get(value, value)

            return value
        except (KeyError, TypeError, IndexError) as err:
            _LOGGER.debug("Error getting sensor value for %s: %s", self.entity_description.key, err)
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
            return None

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
            return None

        try:
            city = self.coordinator.data.get("city", {})
            # Return all properties from the city object as-is
            return dict(city) if city else None
        except (KeyError, TypeError) as err:
            _LOGGER.debug("Error getting location attributes: %s", err)
            return None

"""Constants for the MeteoLux integration."""
from datetime import timedelta
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
)
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
)

DOMAIN: Final = "meteolux"
CONF_LANGUAGE: Final = "language"
CONF_UPDATE_INTERVAL_CURRENT: Final = "update_interval_current"
CONF_UPDATE_INTERVAL_HOURLY: Final = "update_interval_hourly"
CONF_UPDATE_INTERVAL_DAILY: Final = "update_interval_daily"
API_URL: Final = "https://metapi.ana.lu/api/v1"

# Supported languages
LANGUAGE_ENGLISH: Final = "en"
LANGUAGE_FRENCH: Final = "fr"
LANGUAGE_GERMAN: Final = "de"
LANGUAGE_LUXEMBOURGISH: Final = "lb"

SUPPORTED_LANGUAGES: Final = [
    LANGUAGE_ENGLISH,
    LANGUAGE_FRENCH,
    LANGUAGE_GERMAN,
    LANGUAGE_LUXEMBOURGISH,
]

DEFAULT_LANGUAGE: Final = LANGUAGE_ENGLISH

# Wind direction translations
# API returns directions in French regardless of langcode
# Map from French abbreviations to localized abbreviations
WIND_DIRECTION_MAP: Final[dict[str, dict[str, str]]] = {
    LANGUAGE_ENGLISH: {
        "N": "N",
        "NE": "NE",
        "E": "E",
        "SE": "SE",
        "S": "S",
        "SO": "SW",
        "O": "W",
        "NO": "NW",
    },
    LANGUAGE_FRENCH: {
        "N": "N",
        "NE": "NE",
        "E": "E",
        "SE": "SE",
        "S": "S",
        "SO": "SO",
        "O": "O",
        "NO": "NO",
    },
    LANGUAGE_GERMAN: {
        "N": "N",
        "NE": "NO",
        "E": "O",
        "SE": "SO",
        "S": "S",
        "SO": "SW",
        "O": "W",
        "NO": "NW",
    },
    LANGUAGE_LUXEMBOURGISH: {
        "N": "N",
        "NE": "NO",
        "E": "O",
        "SE": "SO",
        "S": "S",
        "SO": "SW",
        "O": "W",
        "NO": "NW",
    },
}

# Default update intervals (in minutes for current/hourly, hours for daily)
DEFAULT_UPDATE_INTERVAL_CURRENT: Final = 10  # minutes
DEFAULT_UPDATE_INTERVAL_HOURLY: Final = 30  # minutes
DEFAULT_UPDATE_INTERVAL_DAILY: Final = 6  # hours

# Update intervals (legacy constants for backward compatibility)
UPDATE_INTERVAL_CURRENT: Final = timedelta(minutes=DEFAULT_UPDATE_INTERVAL_CURRENT)
UPDATE_INTERVAL_HOURLY: Final = timedelta(minutes=DEFAULT_UPDATE_INTERVAL_HOURLY)
UPDATE_INTERVAL_DAILY: Final = timedelta(hours=DEFAULT_UPDATE_INTERVAL_DAILY)

ATTR_FORECAST: Final = "forecast"

# Weather condition mapping from MeteoLux icons to HA conditions
CONDITION_MAP: Final[dict[int, str]] = {
    1: ATTR_CONDITION_SUNNY,  # Clear sky
    2: ATTR_CONDITION_CLEAR_NIGHT,  # Clear night
    3: ATTR_CONDITION_PARTLYCLOUDY,  # Partly cloudy
    4: ATTR_CONDITION_PARTLYCLOUDY,  # Partly cloudy night
    5: ATTR_CONDITION_CLOUDY,  # Overcast
    6: ATTR_CONDITION_CLOUDY,  # Cloudy
    7: ATTR_CONDITION_FOG,  # Fog
    8: ATTR_CONDITION_CLOUDY,  # High clouds
    9: ATTR_CONDITION_PARTLYCLOUDY,  # Scattered clouds
    10: ATTR_CONDITION_CLOUDY,  # Cloudy
    11: ATTR_CONDITION_FOG,  # Mist
    12: ATTR_CONDITION_FOG,  # Fog
    13: ATTR_CONDITION_FOG,  # Dense fog
    14: ATTR_CONDITION_FOG,  # Freezing fog
    15: ATTR_CONDITION_RAINY,  # Drizzle
    16: ATTR_CONDITION_RAINY,  # Light drizzle
    17: ATTR_CONDITION_RAINY,  # Light rain and drizzle
    18: ATTR_CONDITION_RAINY,  # Moderate rain and drizzle
    19: ATTR_CONDITION_RAINY,  # Heavy drizzle
    20: ATTR_CONDITION_RAINY,  # Rain
    21: ATTR_CONDITION_RAINY,  # Light rain
    22: ATTR_CONDITION_RAINY,  # Moderate rain
    23: ATTR_CONDITION_POURING,  # Heavy rain
    24: ATTR_CONDITION_RAINY,  # Freezing rain
    25: ATTR_CONDITION_RAINY,  # Light freezing rain
    26: ATTR_CONDITION_RAINY,  # Moderate freezing rain
    27: ATTR_CONDITION_RAINY,  # Heavy freezing rain
    28: ATTR_CONDITION_SNOWY_RAINY,  # Rain and snow
    29: ATTR_CONDITION_SNOWY_RAINY,  # Light rain and snow
    30: ATTR_CONDITION_RAINY,  # Light rain shower
    31: ATTR_CONDITION_RAINY,  # Rain shower
    32: ATTR_CONDITION_POURING,  # Heavy rain shower
    33: ATTR_CONDITION_SNOWY,  # Snow
    34: ATTR_CONDITION_SNOWY,  # Light snow
    35: ATTR_CONDITION_SNOWY,  # Moderate snow
    36: ATTR_CONDITION_SNOWY,  # Heavy snow
    37: ATTR_CONDITION_SNOWY,  # Snow grains
    38: ATTR_CONDITION_SNOWY,  # Ice pellets
    39: ATTR_CONDITION_SNOWY,  # Snow shower
    40: ATTR_CONDITION_SNOWY,  # Light snow shower
    41: ATTR_CONDITION_SNOWY,  # Heavy snow shower
    42: ATTR_CONDITION_HAIL,  # Hail
    43: ATTR_CONDITION_HAIL,  # Light hail
    44: ATTR_CONDITION_HAIL,  # Heavy hail
    45: ATTR_CONDITION_LIGHTNING_RAINY,  # Thunderstorm
    46: ATTR_CONDITION_LIGHTNING,  # Lightning
    47: ATTR_CONDITION_LIGHTNING_RAINY,  # Thunderstorm with rain
    48: ATTR_CONDITION_LIGHTNING_RAINY,  # Thunderstorm with hail
    49: ATTR_CONDITION_EXCEPTIONAL,  # Tornado
    50: ATTR_CONDITION_WINDY,  # Windy
}

# Sensor types
SENSOR_TYPES: Final[dict[str, dict]] = {
    "temperature": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    "apparent_temperature": {
        "name": "Apparent Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    "wind_speed": {
        "name": "Wind Speed",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfSpeed.KILOMETERS_PER_HOUR,
    },
    "wind_gusts": {
        "name": "Wind Gusts",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfSpeed.KILOMETERS_PER_HOUR,
    },
    "precipitation": {
        "name": "Precipitation",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfPrecipitationDepth.MILLIMETERS,
    },
    "snow": {
        "name": "Snow",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": UnitOfPrecipitationDepth.MILLIMETERS,
    },
    "condition": {
        "name": "Condition",
        "device_class": None,
        "state_class": None,
        "native_unit_of_measurement": None,
    },
}

# Forecast sensor types for daily forecast
FORECAST_SENSOR_TYPES: Final[dict[str, dict]] = {
    "temperature_high": {
        "name": "Temperature High Day {day}",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": None,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    "temperature_low": {
        "name": "Temperature Low Day {day}",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": None,
        "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    },
    "precipitation_forecast": {
        "name": "Precipitation Day {day}",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": None,
        "native_unit_of_measurement": UnitOfPrecipitationDepth.MILLIMETERS,
    },
}

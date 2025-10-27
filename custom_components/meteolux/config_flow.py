"""Config flow for MeteoLux integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.selector import (
    LocationSelector,
    LocationSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
)

from .const import (
    API_URL,
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL_CURRENT,
    CONF_UPDATE_INTERVAL_DAILY,
    CONF_UPDATE_INTERVAL_HOURLY,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_INTERVAL_CURRENT,
    DEFAULT_UPDATE_INTERVAL_DAILY,
    DEFAULT_UPDATE_INTERVAL_HOURLY,
    DOMAIN,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)

# Nominatim API for reverse geocoding (OpenStreetMap)
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

# Luxembourg boundaries
LUX_LAT_MIN = 49.4
LUX_LAT_MAX = 50.2
LUX_LON_MIN = 5.7
LUX_LON_MAX = 6.5

# Default location (Luxembourg City center)
DEFAULT_LATITUDE = 49.6116
DEFAULT_LONGITUDE = 6.1319


async def reverse_geocode(
    hass: HomeAssistant, latitude: float, longitude: float
) -> str | None:
    """Reverse geocode coordinates to get display address."""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "accept-language": "en",
            }
            headers = {"User-Agent": "MeteoLux HomeAssistant Integration"}

            async with session.get(
                NOMINATIM_REVERSE_URL, params=params, headers=headers, timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("display_name")
                return None
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.warning("Reverse geocoding failed: %s", err)
        return None


async def validate_location(
    hass: HomeAssistant, latitude: float, longitude: float, language: str
) -> dict[str, Any]:
    """Validate location coordinates with MeteoLux API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/metapp/weather"
            params = {"lat": latitude, "long": longitude, "langcode": language}

            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                return {"success": False, "error": f"API returned {response.status}"}
    except (aiohttp.ClientError, TimeoutError) as err:
        _LOGGER.error("API validation failed: %s", err)
        return {"success": False, "error": str(err)}


class MeteoLuxConfigFlow(config_entries.ConfigFlow, domain="meteolux"):
    """Handle a config flow for MeteoLux."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._reconfig_entry: config_entries.ConfigEntry | None = None
        self._temp_user_input: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Get coordinates from location selector
            location = user_input.get("location", {})
            latitude: float | None = location.get("latitude")
            longitude: float | None = location.get("longitude")

            # Validate coordinates are within Luxembourg
            if latitude is None or not (LUX_LAT_MIN <= latitude <= LUX_LAT_MAX):
                errors["location"] = "latitude_out_of_bounds"
            if longitude is None or not (LUX_LON_MIN <= longitude <= LUX_LON_MAX):
                errors["location"] = "longitude_out_of_bounds"

            if not errors:
                # Type narrow: at this point latitude and longitude are not None
                assert latitude is not None and longitude is not None

                # Validate with MeteoLux API
                result = await validate_location(
                    self.hass, latitude, longitude, user_input[CONF_LANGUAGE]
                )

                if not result["success"]:
                    errors["base"] = "cannot_connect"
                else:
                    # Create unique ID from coordinates
                    unique_id = f"coords_{latitude:.9f}_{longitude:.9f}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    # Try to get display name via reverse geocoding
                    display_name = await reverse_geocode(self.hass, latitude, longitude)

                    # Create config entry
                    data = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        CONF_LANGUAGE: user_input[CONF_LANGUAGE],
                        CONF_UPDATE_INTERVAL_CURRENT: user_input[
                            CONF_UPDATE_INTERVAL_CURRENT
                        ],
                        CONF_UPDATE_INTERVAL_HOURLY: user_input[
                            CONF_UPDATE_INTERVAL_HOURLY
                        ],
                        CONF_UPDATE_INTERVAL_DAILY: user_input[
                            CONF_UPDATE_INTERVAL_DAILY
                        ],
                    }

                    if display_name:
                        data["display_name"] = display_name

                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data=data,
                    )

        # Show form with default location
        default_location = {
            "latitude": DEFAULT_LATITUDE,
            "longitude": DEFAULT_LONGITUDE,
        }

        data_schema = vol.Schema(
            {
                vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=lang, label=lang.upper())
                            for lang in SUPPORTED_LANGUAGES
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("location", default=default_location): LocationSelector(
                    LocationSelectorConfig()
                ),
                vol.Required(CONF_NAME, default="Home"): cv.string,
                vol.Required(
                    CONF_UPDATE_INTERVAL_CURRENT, default=DEFAULT_UPDATE_INTERVAL_CURRENT
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL_HOURLY, default=DEFAULT_UPDATE_INTERVAL_HOURLY
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=120,
                        step=5,
                        unit_of_measurement="minutes",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL_DAILY, default=DEFAULT_UPDATE_INTERVAL_DAILY
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="hours",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        self._reconfig_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        errors: dict[str, str] = {}

        if user_input is not None:
            # Get coordinates from location selector
            location = user_input.get("location", {})
            latitude: float | None = location.get("latitude")
            longitude: float | None = location.get("longitude")

            # Validate coordinates are within Luxembourg
            if latitude is None or not (LUX_LAT_MIN <= latitude <= LUX_LAT_MAX):
                errors["location"] = "latitude_out_of_bounds"
            if longitude is None or not (LUX_LON_MIN <= longitude <= LUX_LON_MAX):
                errors["location"] = "longitude_out_of_bounds"

            if not errors:
                # Type narrow: at this point latitude and longitude are not None
                assert latitude is not None and longitude is not None

                # Validate with MeteoLux API
                result = await validate_location(
                    self.hass, latitude, longitude, user_input[CONF_LANGUAGE]
                )

                if not result["success"]:
                    errors["base"] = "cannot_connect"
                else:
                    # Store validated input with actual coordinates
                    validated_input = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        CONF_LANGUAGE: user_input[CONF_LANGUAGE],
                        CONF_UPDATE_INTERVAL_CURRENT: user_input[
                            CONF_UPDATE_INTERVAL_CURRENT
                        ],
                        CONF_UPDATE_INTERVAL_HOURLY: user_input[
                            CONF_UPDATE_INTERVAL_HOURLY
                        ],
                        CONF_UPDATE_INTERVAL_DAILY: user_input[
                            CONF_UPDATE_INTERVAL_DAILY
                        ],
                    }

                    # Check if name changed
                    old_name = self._reconfig_entry.data.get(CONF_NAME, "")
                    new_name = user_input[CONF_NAME]

                    if old_name != new_name:
                        # Name changed - ask user about entity ID regeneration
                        self._temp_user_input = validated_input
                        return await self.async_step_reconfigure_entity_ids()
                    else:
                        # Name unchanged - proceed with update
                        return await self._update_entry_and_reload(
                            validated_input, regenerate_ids=False
                        )

        # Pre-fill with current values
        current_data = self._reconfig_entry.data

        # Get current location for default value
        current_location = {
            "latitude": current_data.get(CONF_LATITUDE, DEFAULT_LATITUDE),
            "longitude": current_data.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
        }

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LANGUAGE, default=current_data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=lang, label=lang.upper())
                            for lang in SUPPORTED_LANGUAGES
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("location", default=current_location): LocationSelector(
                    LocationSelectorConfig()
                ),
                vol.Required(
                    CONF_NAME, default=current_data.get(CONF_NAME, "Home")
                ): cv.string,
                vol.Required(
                    CONF_UPDATE_INTERVAL_CURRENT,
                    default=current_data.get(
                        CONF_UPDATE_INTERVAL_CURRENT, DEFAULT_UPDATE_INTERVAL_CURRENT
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL_HOURLY,
                    default=current_data.get(
                        CONF_UPDATE_INTERVAL_HOURLY, DEFAULT_UPDATE_INTERVAL_HOURLY
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=120,
                        step=5,
                        unit_of_measurement="minutes",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL_DAILY,
                    default=current_data.get(
                        CONF_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="hours",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "name": current_data.get(CONF_NAME, ""),
            },
        )

    async def async_step_reconfigure_entity_ids(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle entity ID regeneration option when name changes."""
        # Assert preconditions (should always be true when reaching this step)
        assert self._temp_user_input is not None
        assert self._reconfig_entry is not None

        if user_input is not None:
            # Get the entity ID action choice
            regenerate_ids = user_input.get("entity_id_action", "keep") == "regenerate"

            # Proceed with update using stored data
            return await self._update_entry_and_reload(
                self._temp_user_input, regenerate_ids=regenerate_ids
            )

        # Show form with radio buttons
        old_name = self._reconfig_entry.data.get(CONF_NAME, "")
        new_name = self._temp_user_input[CONF_NAME]

        data_schema = vol.Schema(
            {
                vol.Required("entity_id_action", default="keep"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value="keep", label="Keep existing entity IDs"),
                            SelectOptionDict(
                                value="regenerate",
                                label="Regenerate entity IDs",
                            ),
                        ],
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="reconfigure_entity_ids",
            data_schema=data_schema,
            description_placeholders={
                "old_name": old_name,
                "new_name": new_name,
            },
        )

    async def _update_entry_and_reload(
        self, validated_input: dict[str, Any], regenerate_ids: bool
    ) -> FlowResult:
        """Update config entry and optionally regenerate entity IDs."""
        assert self._reconfig_entry is not None

        # Try to get display name via reverse geocoding
        display_name = await reverse_geocode(
            self.hass,
            validated_input[CONF_LATITUDE],
            validated_input[CONF_LONGITUDE],
        )

        # Build new data
        new_data = {**validated_input}
        if display_name:
            new_data["display_name"] = display_name

        # Update config entry
        self.hass.config_entries.async_update_entry(
            self._reconfig_entry,
            data=new_data,
            title=validated_input[CONF_NAME],
        )

        # Regenerate entity IDs if requested
        if regenerate_ids:
            await self._regenerate_entity_ids(validated_input[CONF_NAME])

        # Reload the integration
        await self.hass.config_entries.async_reload(self._reconfig_entry.entry_id)

        return self.async_abort(reason="reconfigure_successful")

    async def _regenerate_entity_ids(self, new_name: str) -> None:
        """Regenerate entity IDs based on new integration name."""
        assert self._reconfig_entry is not None

        entity_reg = er.async_get(self.hass)
        entry_id = self._reconfig_entry.entry_id

        # Normalize name for entity ID (lowercase, replace spaces with underscores)
        normalized_name = new_name.lower().replace(" ", "_")

        # Define entity mappings: (unique_id_suffix, domain, entity_id_suffix)
        entity_mappings = [
            ("current_weather", "sensor", "current_weather"),
            ("ephemeris", "sensor", "today"),
            ("location", "sensor", "location"),
            ("weather", "weather", None),  # Weather entity has no suffix
        ]

        for unique_id_suffix, domain, entity_id_suffix in entity_mappings:
            # Build unique_id
            unique_id = f"{entry_id}_{unique_id_suffix}"

            # Find existing entity
            current_entity_id = entity_reg.async_get_entity_id(
                domain, DOMAIN, unique_id
            )

            if current_entity_id:
                # Generate new entity ID
                if entity_id_suffix:
                    suggested_id = f"{normalized_name}_{entity_id_suffix}"
                else:
                    suggested_id = normalized_name

                # Generate full entity ID with domain
                new_entity_id = f"{domain}.{suggested_id}"

                # Check if new ID would conflict
                if new_entity_id == current_entity_id:
                    # No change needed
                    continue

                # Update entity ID
                try:
                    entity_reg.async_update_entity(
                        current_entity_id, new_entity_id=new_entity_id
                    )
                    _LOGGER.info(
                        "Regenerated entity ID: %s -> %s",
                        current_entity_id,
                        new_entity_id,
                    )
                except ValueError as err:
                    # Entity ID might already exist, log warning
                    _LOGGER.warning(
                        "Failed to regenerate entity ID %s to %s: %s",
                        current_entity_id,
                        new_entity_id,
                        err,
                    )

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
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    LocationSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    API_URL,
    CONF_ADDRESS,
    CONF_CITY_ID,
    CONF_LANGUAGE,
    CONF_LOCATION_METHOD,
    CONF_UPDATE_INTERVAL_CURRENT,
    CONF_UPDATE_INTERVAL_DAILY,
    CONF_UPDATE_INTERVAL_HOURLY,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_INTERVAL_CURRENT,
    DEFAULT_UPDATE_INTERVAL_DAILY,
    DEFAULT_UPDATE_INTERVAL_HOURLY,
    DOMAIN,
    LOCATION_METHOD_ADDRESS,
    LOCATION_METHOD_CITY,
    LOCATION_METHOD_MAP,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)

# Nominatim API for geocoding (OpenStreetMap)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def fetch_cities(hass: HomeAssistant, language: str = "en") -> dict[str, int]:
    """Fetch available cities from MeteoLux API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/metapp/bookmarks?langcode={language}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to fetch cities list from MeteoLux API")
                    return {}
                data = await response.json()
                # Return a dictionary mapping city names to city IDs
                # Sort by city name for better UX
                cities = {
                    city["name"]: city["id"]
                    for city in sorted(data.get("cities", []), key=lambda x: x["name"])
                }
                return cities
    except aiohttp.ClientError as err:
        _LOGGER.error("Cannot connect to MeteoLux API: %s", err)
        return {}
    except Exception as err:
        _LOGGER.error("Unexpected error fetching cities: %s", err)
        return {}


async def geocode_address(hass: HomeAssistant, address: str) -> dict[str, Any]:
    """Geocode a Luxembourg address to lat/lon using Nominatim."""
    try:
        async with aiohttp.ClientSession() as session:
            # Add Luxembourg country code to improve results
            search_query = f"{address}, Luxembourg"
            params = {
                "q": search_query,
                "format": "json",
                "limit": 1,
                "countrycodes": "lu",  # Restrict to Luxembourg
            }
            headers = {
                "User-Agent": "HomeAssistant-MeteoLux/1.0"
            }

            async with session.get(
                NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise ValueError("Geocoding service unavailable")

                data = await response.json()
                if not data:
                    raise ValueError("Address not found")

                result = data[0]
                return {
                    "latitude": float(result["lat"]),
                    "longitude": float(result["lon"]),
                    "display_name": result.get("display_name", address),
                }
    except aiohttp.ClientError as err:
        raise ValueError(f"Cannot connect to geocoding service: {err}") from err
    except (KeyError, ValueError, IndexError) as err:
        raise ValueError(f"Invalid geocoding response: {err}") from err


async def validate_location(
    hass: HomeAssistant, latitude: float, longitude: float, language: str = "en"
) -> dict[str, Any]:
    """Validate the location by making a test API call."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/metapp/weather"
            params = {
                "lat": latitude,
                "long": longitude,
                "langcode": language,
            }
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise ValueError("Invalid location")
                data = await response.json()
                return {
                    "city_name": data.get("city", {}).get("name", "Custom Location"),
                }
    except aiohttp.ClientError as err:
        raise ValueError(f"Cannot connect to API: {err}") from err
    except KeyError as err:
        raise ValueError(f"Invalid response from API: {err}") from err


async def validate_city(hass: HomeAssistant, city_id: int, language: str = "en") -> dict[str, Any]:
    """Validate the city ID by making a test API call."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/metapp/weather"
            params = {
                "city": city_id,
                "langcode": language,
            }
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise ValueError("Invalid city ID")
                data = await response.json()
                return {
                    "title": data["city"]["name"],
                    "city_name": data["city"]["name"],
                }
    except aiohttp.ClientError as err:
        raise ValueError(f"Cannot connect to API: {err}") from err
    except KeyError as err:
        raise ValueError(f"Invalid response from API: {err}") from err


class MeteoLuxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MeteoLux."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.location_method: str | None = None
        self.language: str = DEFAULT_LANGUAGE
        self.location_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - select location method."""
        if user_input is not None:
            self.location_method = user_input[CONF_LOCATION_METHOD]

            # Route to the appropriate step based on selection
            if self.location_method == LOCATION_METHOD_CITY:
                return await self.async_step_city()
            elif self.location_method == LOCATION_METHOD_ADDRESS:
                return await self.async_step_address()
            elif self.location_method == LOCATION_METHOD_MAP:
                return await self.async_step_map()

        # Show only location method selection
        data_schema = vol.Schema({
            vol.Required(CONF_LOCATION_METHOD): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": LOCATION_METHOD_CITY, "label": "Select from city list"},
                        {"value": LOCATION_METHOD_ADDRESS, "label": "Enter Luxembourg address"},
                        {"value": LOCATION_METHOD_MAP, "label": "Select on map"},
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_city(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle city selection method."""
        errors: dict[str, str] = {}

        # Fetch cities in English (language will be selected later)
        cities = await fetch_cities(self.hass, DEFAULT_LANGUAGE)

        if not cities:
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="city",
                data_schema=vol.Schema({
                    vol.Required(CONF_NAME, default="Home"): cv.string,
                }),
                errors=errors,
            )

        if user_input is not None:
            # Get the selected city name and look up its ID
            selected_city = user_input.get("city")
            city_id = cities.get(selected_city)

            if city_id is None:
                errors["base"] = "invalid_city"
            else:
                try:
                    info = await validate_city(self.hass, city_id, DEFAULT_LANGUAGE)
                except ValueError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(f"city_{city_id}")
                    self._abort_if_unique_id_configured()

                    # Store location data for language selection step
                    self.location_data = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_LOCATION_METHOD: LOCATION_METHOD_CITY,
                        CONF_CITY_ID: city_id,
                        "city_name": info.get("city_name", selected_city),
                    }

                    # Move to language selection step
                    return await self.async_step_language()

        # Build the schema with city selector
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default="Home"): cv.string,
            vol.Required("city"): SelectSelector(
                SelectSelectorConfig(
                    options=list(cities.keys()),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="city", data_schema=data_schema, errors=errors
        )

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address input method."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input.get(CONF_ADDRESS)

            try:
                # Geocode the address
                geo_result = await geocode_address(self.hass, address)

                # Store geocoding results for confirmation step
                self.location_data = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_ADDRESS: address,
                    CONF_LATITUDE: geo_result["latitude"],
                    CONF_LONGITUDE: geo_result["longitude"],
                    "display_name": geo_result["display_name"],
                }

                # Validate with MeteoLux API (language will be selected later)
                await validate_location(
                    self.hass,
                    geo_result["latitude"],
                    geo_result["longitude"],
                    DEFAULT_LANGUAGE
                )

                # Show confirmation step with coordinates
                return await self.async_step_address_confirm()

            except ValueError as err:
                _LOGGER.error("Geocoding error: %s", err)
                errors["base"] = "address_not_found"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show address input form
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default="Home"): cv.string,
            vol.Required(CONF_ADDRESS): cv.string,
        })

        return self.async_show_form(
            step_id="address",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "example": "1 Rue de la Gare, Luxembourg"
            },
        )

    async def async_step_address_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the geocoded address and coordinates."""
        if user_input is not None:
            # Set unique ID and check for duplicates
            unique_id = f"coords_{self.location_data[CONF_LATITUDE]:.6f}_{self.location_data[CONF_LONGITUDE]:.6f}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Add location method to location_data
            self.location_data[CONF_LOCATION_METHOD] = LOCATION_METHOD_ADDRESS

            # Move to language selection step
            return await self.async_step_language()

        # Show confirmation with coordinates
        return self.async_show_form(
            step_id="address_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "address": self.location_data.get("display_name", ""),
                "latitude": f"{self.location_data[CONF_LATITUDE]:.6f}",
                "longitude": f"{self.location_data[CONF_LONGITUDE]:.6f}",
            },
        )

    async def async_step_map(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle map-based location selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            latitude = user_input["location"]["latitude"]
            longitude = user_input["location"]["longitude"]

            # Validate coordinates are within Luxembourg bounds
            # Luxembourg: lat 49.4-50.2, lon 5.7-6.5
            if not (49.4 <= latitude <= 50.2 and 5.7 <= longitude <= 6.5):
                errors["base"] = "location_outside_luxembourg"
            else:
                try:
                    # Validate with MeteoLux API (language will be selected later)
                    info = await validate_location(self.hass, latitude, longitude, DEFAULT_LANGUAGE)
                except ValueError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    unique_id = f"coords_{latitude:.6f}_{longitude:.6f}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    # Store location data for language selection step
                    self.location_data = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_LOCATION_METHOD: LOCATION_METHOD_MAP,
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        "city_name": info.get("city_name", "Custom Location"),
                    }

                    # Move to language selection step
                    return await self.async_step_language()

        # Default location: Luxembourg City center
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default="Home"): cv.string,
            vol.Required("location", default={
                "latitude": 49.6116,
                "longitude": 6.1319,
            }): LocationSelector(),
        })

        return self.async_show_form(
            step_id="map",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_language(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle weather forecast configuration - final step."""
        if user_input is not None:
            # Get selected language
            language = user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

            # Get update intervals (in minutes for current/hourly, hours for daily)
            interval_current = user_input.get(CONF_UPDATE_INTERVAL_CURRENT, DEFAULT_UPDATE_INTERVAL_CURRENT)
            interval_hourly = user_input.get(CONF_UPDATE_INTERVAL_HOURLY, DEFAULT_UPDATE_INTERVAL_HOURLY)
            interval_daily = user_input.get(CONF_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY)

            # Add configuration to location data
            self.location_data[CONF_LANGUAGE] = language
            self.location_data[CONF_UPDATE_INTERVAL_CURRENT] = interval_current
            self.location_data[CONF_UPDATE_INTERVAL_HOURLY] = interval_hourly
            self.location_data[CONF_UPDATE_INTERVAL_DAILY] = interval_daily

            # Create the config entry with all stored data
            return self.async_create_entry(
                title=self.location_data[CONF_NAME],
                data=self.location_data,
            )

        # Show weather forecast configuration form
        data_schema = vol.Schema({
            vol.Required(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": k, "label": v} for k, v in SUPPORTED_LANGUAGES.items()
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL_CURRENT, default=DEFAULT_UPDATE_INTERVAL_CURRENT): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=60,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="minutes",
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL_HOURLY, default=DEFAULT_UPDATE_INTERVAL_HOURLY): NumberSelector(
                NumberSelectorConfig(
                    min=5,
                    max=120,
                    step=5,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="minutes",
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL_DAILY, default=DEFAULT_UPDATE_INTERVAL_DAILY): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=24,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="hours",
                )
            ),
        })

        return self.async_show_form(
            step_id="language",
            data_schema=data_schema,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration - choose what to reconfigure."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            reconfigure_type = user_input.get("reconfigure_type")

            # Store entry for later steps
            self.reconfig_entry = entry

            if reconfigure_type == "location":
                return await self.async_step_reconfigure_location()
            elif reconfigure_type == "name":
                return await self.async_step_reconfigure_name()
            elif reconfigure_type == "forecast":
                return await self.async_step_reconfigure_forecast()

        # Show reconfiguration options
        data_schema = vol.Schema({
            vol.Required("reconfigure_type"): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": "location", "label": "Change Location"},
                        {"value": "name", "label": "Change Name"},
                        {"value": "forecast", "label": "Change Weather Forecast Settings"},
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            ),
        })

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema,
            description_placeholders={
                "name": entry.data.get(CONF_NAME, "Unknown"),
                "location_method": entry.data.get(CONF_LOCATION_METHOD, "unknown"),
            },
        )

    async def async_step_reconfigure_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle location reconfiguration."""
        entry = self.reconfig_entry

        if user_input is not None:
            self.location_method = user_input[CONF_LOCATION_METHOD]

            # Route to appropriate location step
            if self.location_method == LOCATION_METHOD_CITY:
                return await self.async_step_reconfigure_city()
            elif self.location_method == LOCATION_METHOD_ADDRESS:
                return await self.async_step_reconfigure_address()
            elif self.location_method == LOCATION_METHOD_MAP:
                return await self.async_step_reconfigure_map()

        # Show location method selection
        data_schema = vol.Schema({
            vol.Required(CONF_LOCATION_METHOD, default=entry.data.get(CONF_LOCATION_METHOD)): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": LOCATION_METHOD_CITY, "label": "Select from city list"},
                        {"value": LOCATION_METHOD_ADDRESS, "label": "Enter Luxembourg address"},
                        {"value": LOCATION_METHOD_MAP, "label": "Select on map"},
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            ),
        })

        return self.async_show_form(
            step_id="reconfigure_location",
            data_schema=data_schema,
        )

    async def async_step_reconfigure_city(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle city reconfiguration."""
        entry = self.reconfig_entry
        errors: dict[str, str] = {}

        cities = await fetch_cities(self.hass, DEFAULT_LANGUAGE)

        if not cities:
            errors["base"] = "cannot_connect"

        if user_input is not None and not errors:
            selected_city = user_input.get("city")
            city_id = cities.get(selected_city)

            if city_id is None:
                errors["base"] = "invalid_city"
            else:
                try:
                    await validate_city(self.hass, city_id, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
                except ValueError:
                    errors["base"] = "cannot_connect"
                else:
                    # Update config entry
                    new_data = {**entry.data}
                    new_data[CONF_LOCATION_METHOD] = LOCATION_METHOD_CITY
                    new_data[CONF_CITY_ID] = city_id
                    # Remove old coordinates if switching from address/map
                    new_data.pop(CONF_LATITUDE, None)
                    new_data.pop(CONF_LONGITUDE, None)
                    new_data.pop(CONF_ADDRESS, None)

                    self.hass.config_entries.async_update_entry(entry, data=new_data)
                    await self.hass.config_entries.async_reload(entry.entry_id)

                    return self.async_abort(reason="reconfigure_successful")

        # Get current city if using city method
        current_city_id = entry.data.get(CONF_CITY_ID)
        current_city_name = None
        if current_city_id:
            for name, cid in cities.items():
                if cid == current_city_id:
                    current_city_name = name
                    break

        data_schema = vol.Schema({
            vol.Required("city", default=current_city_name): SelectSelector(
                SelectSelectorConfig(
                    options=list(cities.keys()),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="reconfigure_city",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address reconfiguration."""
        entry = self.reconfig_entry
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input.get(CONF_ADDRESS)

            try:
                geo_result = await geocode_address(self.hass, address)
                await validate_location(
                    self.hass,
                    geo_result["latitude"],
                    geo_result["longitude"],
                    entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                )

                # Update config entry
                new_data = {**entry.data}
                new_data[CONF_LOCATION_METHOD] = LOCATION_METHOD_ADDRESS
                new_data[CONF_ADDRESS] = address
                new_data[CONF_LATITUDE] = geo_result["latitude"]
                new_data[CONF_LONGITUDE] = geo_result["longitude"]
                # Remove old city_id if switching from city method
                new_data.pop(CONF_CITY_ID, None)

                self.hass.config_entries.async_update_entry(entry, data=new_data)
                await self.hass.config_entries.async_reload(entry.entry_id)

                return self.async_abort(reason="reconfigure_successful")

            except ValueError:
                errors["base"] = "address_not_found"

        data_schema = vol.Schema({
            vol.Required(CONF_ADDRESS, default=entry.data.get(CONF_ADDRESS, "")): cv.string,
        })

        return self.async_show_form(
            step_id="reconfigure_address",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "example": "1 Rue de la Gare, Luxembourg"
            },
        )

    async def async_step_reconfigure_map(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle map reconfiguration."""
        entry = self.reconfig_entry
        errors: dict[str, str] = {}

        if user_input is not None:
            latitude = user_input["location"]["latitude"]
            longitude = user_input["location"]["longitude"]

            if not (49.4 <= latitude <= 50.2 and 5.7 <= longitude <= 6.5):
                errors["base"] = "location_outside_luxembourg"
            else:
                try:
                    await validate_location(self.hass, latitude, longitude, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
                except ValueError:
                    errors["base"] = "cannot_connect"
                else:
                    # Update config entry
                    new_data = {**entry.data}
                    new_data[CONF_LOCATION_METHOD] = LOCATION_METHOD_MAP
                    new_data[CONF_LATITUDE] = latitude
                    new_data[CONF_LONGITUDE] = longitude
                    # Remove old city_id and address
                    new_data.pop(CONF_CITY_ID, None)
                    new_data.pop(CONF_ADDRESS, None)

                    self.hass.config_entries.async_update_entry(entry, data=new_data)
                    await self.hass.config_entries.async_reload(entry.entry_id)

                    return self.async_abort(reason="reconfigure_successful")

        # Get current coordinates
        current_lat = entry.data.get(CONF_LATITUDE, 49.6116)
        current_lon = entry.data.get(CONF_LONGITUDE, 6.1319)

        data_schema = vol.Schema({
            vol.Required("location", default={
                "latitude": current_lat,
                "longitude": current_lon,
            }): LocationSelector(),
        })

        return self.async_show_form(
            step_id="reconfigure_map",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure_name(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle name reconfiguration."""
        entry = self.reconfig_entry

        if user_input is not None:
            new_name = user_input.get(CONF_NAME)
            regenerate_ids = user_input.get("regenerate_entity_ids", False)

            # Update config entry
            new_data = {**entry.data}
            new_data[CONF_NAME] = new_name

            if regenerate_ids:
                # Update entry title and reload to regenerate entity IDs
                self.hass.config_entries.async_update_entry(entry, title=new_name, data=new_data)
            else:
                # Just update data, keep entity IDs
                self.hass.config_entries.async_update_entry(entry, data=new_data)

            await self.hass.config_entries.async_reload(entry.entry_id)

            return self.async_abort(reason="reconfigure_successful")

        current_name = entry.data.get(CONF_NAME, "")

        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default=current_name): cv.string,
            vol.Optional("regenerate_entity_ids", default=False): cv.boolean,
        })

        return self.async_show_form(
            step_id="reconfigure_name",
            data_schema=data_schema,
        )

    async def async_step_reconfigure_forecast(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle forecast settings reconfiguration."""
        entry = self.reconfig_entry

        if user_input is not None:
            # Get new configuration
            language = user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
            interval_current = user_input.get(CONF_UPDATE_INTERVAL_CURRENT, DEFAULT_UPDATE_INTERVAL_CURRENT)
            interval_hourly = user_input.get(CONF_UPDATE_INTERVAL_HOURLY, DEFAULT_UPDATE_INTERVAL_HOURLY)
            interval_daily = user_input.get(CONF_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY)

            # Update config entry
            new_data = {**entry.data}
            new_data[CONF_LANGUAGE] = language
            new_data[CONF_UPDATE_INTERVAL_CURRENT] = interval_current
            new_data[CONF_UPDATE_INTERVAL_HOURLY] = interval_hourly
            new_data[CONF_UPDATE_INTERVAL_DAILY] = interval_daily

            self.hass.config_entries.async_update_entry(entry, data=new_data)
            await self.hass.config_entries.async_reload(entry.entry_id)

            return self.async_abort(reason="reconfigure_successful")

        # Get current values
        current_language = entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        current_interval_current = entry.data.get(CONF_UPDATE_INTERVAL_CURRENT, DEFAULT_UPDATE_INTERVAL_CURRENT)
        current_interval_hourly = entry.data.get(CONF_UPDATE_INTERVAL_HOURLY, DEFAULT_UPDATE_INTERVAL_HOURLY)
        current_interval_daily = entry.data.get(CONF_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY)

        data_schema = vol.Schema({
            vol.Required(CONF_LANGUAGE, default=current_language): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": k, "label": v} for k, v in SUPPORTED_LANGUAGES.items()
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL_CURRENT, default=current_interval_current): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=60,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="minutes",
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL_HOURLY, default=current_interval_hourly): NumberSelector(
                NumberSelectorConfig(
                    min=5,
                    max=120,
                    step=5,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="minutes",
                )
            ),
            vol.Required(CONF_UPDATE_INTERVAL_DAILY, default=current_interval_daily): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=24,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="hours",
                )
            ),
        })

        return self.async_show_form(
            step_id="reconfigure_forecast",
            data_schema=data_schema,
        )

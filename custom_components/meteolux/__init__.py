"""The MeteoLux integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL_CURRENT,
    CONF_UPDATE_INTERVAL_DAILY,
    CONF_UPDATE_INTERVAL_HOURLY,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_INTERVAL_CURRENT,
    DEFAULT_UPDATE_INTERVAL_DAILY,
    DEFAULT_UPDATE_INTERVAL_HOURLY,
    DOMAIN,
)
from .coordinator import MeteoLuxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MeteoLux from a config entry."""
    name = entry.data[CONF_NAME]
    language = entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    # Extract location parameters (coordinates-based only)
    latitude = entry.data.get(CONF_LATITUDE)
    longitude = entry.data.get(CONF_LONGITUDE)

    # Get update intervals from config (with defaults)
    interval_current_minutes = entry.data.get(CONF_UPDATE_INTERVAL_CURRENT, DEFAULT_UPDATE_INTERVAL_CURRENT)
    interval_hourly_minutes = entry.data.get(CONF_UPDATE_INTERVAL_HOURLY, DEFAULT_UPDATE_INTERVAL_HOURLY)
    interval_daily_hours = entry.data.get(CONF_UPDATE_INTERVAL_DAILY, DEFAULT_UPDATE_INTERVAL_DAILY)

    # Convert to timedelta objects
    update_interval_current = timedelta(minutes=interval_current_minutes)
    update_interval_hourly = timedelta(minutes=interval_hourly_minutes)
    update_interval_daily = timedelta(hours=interval_daily_hours)

    # Create coordinators for different update intervals
    coordinator_current = MeteoLuxDataUpdateCoordinator(
        hass,
        f"{name}_current",
        update_interval_current,
        language=language,
        city_id=None,
        latitude=latitude,
        longitude=longitude,
    )
    coordinator_hourly = MeteoLuxDataUpdateCoordinator(
        hass,
        f"{name}_hourly",
        update_interval_hourly,
        language=language,
        city_id=None,
        latitude=latitude,
        longitude=longitude,
    )
    coordinator_daily = MeteoLuxDataUpdateCoordinator(
        hass,
        f"{name}_daily",
        update_interval_daily,
        language=language,
        city_id=None,
        latitude=latitude,
        longitude=longitude,
    )

    # Fetch initial data
    await coordinator_current.async_config_entry_first_refresh()
    await coordinator_hourly.async_config_entry_first_refresh()
    await coordinator_daily.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator_current": coordinator_current,
        "coordinator_hourly": coordinator_hourly,
        "coordinator_daily": coordinator_daily,
        "name": name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close coordinator sessions
        coordinators = hass.data[DOMAIN][entry.entry_id]
        await coordinators["coordinator_current"].async_shutdown()
        await coordinators["coordinator_hourly"].async_shutdown()
        await coordinators["coordinator_daily"].async_shutdown()
        
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

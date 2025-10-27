"""Data update coordinator for MeteoLux."""
from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MeteoLuxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MeteoLux data."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        update_interval: timedelta,
        language: str = "en",
        city_id: int | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
            update_interval=update_interval,
        )
        self.city_id = city_id
        self.latitude = latitude
        self.longitude = longitude
        self.language = language
        self._session = aiohttp.ClientSession()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from MeteoLux API."""
        try:
            url = f"{API_URL}/metapp/weather"
            params = {}

            # Use city_id if available, otherwise use lat/lon
            if self.city_id is not None:
                params = {
                    "city": self.city_id,
                    "langcode": self.language,
                }
            elif self.latitude is not None and self.longitude is not None:
                params = {
                    "lat": self.latitude,
                    "long": self.longitude,
                    "langcode": self.language,
                }
            else:
                raise UpdateFailed("No location specified (neither city_id nor coordinates)")

            async with self._session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching data: {response.status}")
                data = await response.json()
                return data
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the aiohttp session."""
        await self._session.close()

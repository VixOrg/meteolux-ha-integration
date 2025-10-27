"""Data update coordinator for MeteoLux."""
import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Exponential backoff retry delays (in seconds): 2s, 4s, 8s, 16s, 30s, 60s
RETRY_DELAYS = [2, 4, 8, 16, 30, 60]


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
        self._session: aiohttp.ClientSession | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from MeteoLux API with exponential backoff retry."""
        # Create session lazily on first use
        if self._session is None:
            self._session = aiohttp.ClientSession()

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

        last_error = None

        # Try initial request + retries with exponential backoff
        for attempt in range(len(RETRY_DELAYS) + 1):
            try:
                _LOGGER.debug(
                    "Fetching MeteoLux data (attempt %d/%d) for %s",
                    attempt + 1,
                    len(RETRY_DELAYS) + 1,
                    params.get("city", f"lat={self.latitude},lon={self.longitude}"),
                )

                async with self._session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        error_msg = f"HTTP {response.status}"
                        _LOGGER.warning(
                            "MeteoLux API returned %s (attempt %d/%d)",
                            error_msg,
                            attempt + 1,
                            len(RETRY_DELAYS) + 1,
                        )
                        last_error = UpdateFailed(f"Error fetching data: {error_msg}")

                        # Don't retry on 4xx client errors (except 429 rate limit)
                        if 400 <= response.status < 500 and response.status != 429:
                            raise last_error

                        # Retry on 5xx server errors and 429 rate limit
                        if attempt < len(RETRY_DELAYS):
                            await asyncio.sleep(RETRY_DELAYS[attempt])
                            continue
                        raise last_error

                    data = await response.json()

                    # Log successful fetch
                    if attempt > 0:
                        _LOGGER.info(
                            "MeteoLux API fetch succeeded after %d retries",
                            attempt,
                        )

                    return data

            except aiohttp.ClientError as err:
                error_msg = f"Network error: {err}"
                _LOGGER.warning(
                    "%s (attempt %d/%d)",
                    error_msg,
                    attempt + 1,
                    len(RETRY_DELAYS) + 1,
                )
                last_error = UpdateFailed(f"Error communicating with API: {err}")

                # Retry on network errors with exponential backoff
                if attempt < len(RETRY_DELAYS):
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue
                raise last_error from err

            except asyncio.TimeoutError as err:
                error_msg = "Request timeout"
                _LOGGER.warning(
                    "%s (attempt %d/%d)",
                    error_msg,
                    attempt + 1,
                    len(RETRY_DELAYS) + 1,
                )
                last_error = UpdateFailed("Request timeout")

                # Retry on timeout with exponential backoff
                if attempt < len(RETRY_DELAYS):
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue
                raise last_error from err

            except Exception as err:
                # Unexpected errors are not retried
                _LOGGER.exception("Unexpected error fetching MeteoLux data")
                raise UpdateFailed(f"Unexpected error: {err}") from err

        # Should not reach here, but if we do, raise the last error
        if last_error:
            raise last_error
        raise UpdateFailed("Failed to fetch data after all retries")

    async def async_shutdown(self) -> None:
        """Close the aiohttp session."""
        if self._session is not None:
            await self._session.close()

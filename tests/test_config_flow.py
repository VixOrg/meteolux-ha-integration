"""Tests for MeteoLux config flow."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant

from custom_components.meteolux.const import (
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL_CURRENT,
    CONF_UPDATE_INTERVAL_DAILY,
    CONF_UPDATE_INTERVAL_HOURLY,
    DOMAIN,
)


@pytest.fixture
def mock_validate_location():
    """Mock validate_location function."""
    with patch(
        "custom_components.meteolux.config_flow.validate_location",
        new_callable=AsyncMock,
    ) as mock_validate:
        mock_validate.return_value = {"success": True}
        yield mock_validate


@pytest.fixture
def mock_reverse_geocode():
    """Mock reverse_geocode function."""
    with patch(
        "custom_components.meteolux.config_flow.reverse_geocode",
        new_callable=AsyncMock,
    ) as mock_geocode:
        mock_geocode.return_value = "Luxembourg, Luxembourg"
        yield mock_geocode


async def test_user_form(
    hass: HomeAssistant, mock_validate_location, mock_reverse_geocode
):
    """Test the initial user configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_form_valid_coordinates(
    hass: HomeAssistant, mock_validate_location, mock_reverse_geocode
):
    """Test user form with valid coordinates creates config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Home",
            "location": {"latitude": 49.6116, "longitude": 6.1319},
            CONF_LANGUAGE: "en",
            CONF_UPDATE_INTERVAL_CURRENT: 10,
            CONF_UPDATE_INTERVAL_HOURLY: 30,
            CONF_UPDATE_INTERVAL_DAILY: 6,
        },
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Home"
    assert result["data"][CONF_NAME] == "Home"
    assert result["data"][CONF_LATITUDE] == 49.6116
    assert result["data"][CONF_LONGITUDE] == 6.1319
    assert result["data"][CONF_LANGUAGE] == "en"
    assert result["data"]["display_name"] == "Luxembourg, Luxembourg"


async def test_user_form_api_connection_error(
    hass: HomeAssistant, mock_reverse_geocode
):
    """Test user form with API connection failure."""
    with patch(
        "custom_components.meteolux.config_flow.validate_location",
        return_value={"success": False, "error": "Connection failed"},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Home",
                "location": {"latitude": 49.6116, "longitude": 6.1319},
                CONF_LANGUAGE: "en",
                CONF_UPDATE_INTERVAL_CURRENT: 10,
                CONF_UPDATE_INTERVAL_HOURLY: 30,
                CONF_UPDATE_INTERVAL_DAILY: 6,
            },
        )

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"


async def test_reconfigure_without_name_change(
    hass: HomeAssistant, mock_config_entry, mock_validate_location, mock_reverse_geocode
):
    """Test reconfiguration without changing name (single-step flow)."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": mock_config_entry.entry_id},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure"

    # Change location but not name
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Luxembourg",  # Same name
            "location": {"latitude": 49.7, "longitude": 6.2},  # Different coordinates
            CONF_LANGUAGE: "fr",  # Different language
            CONF_UPDATE_INTERVAL_CURRENT: 15,  # Different intervals
            CONF_UPDATE_INTERVAL_HOURLY: 45,
            CONF_UPDATE_INTERVAL_DAILY: 12,
        },
    )

    # Should complete directly without Step 2
    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"

    # Verify entry was updated
    assert mock_config_entry.data[CONF_LATITUDE] == 49.7
    assert mock_config_entry.data[CONF_LONGITUDE] == 6.2
    assert mock_config_entry.data[CONF_LANGUAGE] == "fr"


async def test_reconfigure_with_name_change_keep_ids(
    hass: HomeAssistant, mock_config_entry, mock_validate_location, mock_reverse_geocode
):
    """Test reconfiguration with name change - keep entity IDs."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": mock_config_entry.entry_id},
    )

    # Change name
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Office",  # Changed name
            "location": {"latitude": 49.6116, "longitude": 6.1319},
            CONF_LANGUAGE: "en",
            CONF_UPDATE_INTERVAL_CURRENT: 10,
            CONF_UPDATE_INTERVAL_HOURLY: 30,
            CONF_UPDATE_INTERVAL_DAILY: 6,
        },
    )

    # Should show Step 2 for entity ID handling
    assert result["type"] == "form"
    assert result["step_id"] == "reconfigure_entity_ids"

    # Choose to keep entity IDs
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"entity_id_action": "keep"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"

    # Verify name was updated
    assert mock_config_entry.title == "Office"
    assert mock_config_entry.data[CONF_NAME] == "Office"


async def test_reconfigure_with_name_change_regenerate_ids(
    hass: HomeAssistant, mock_config_entry, mock_validate_location, mock_reverse_geocode
):
    """Test reconfiguration with name change - regenerate entity IDs."""
    mock_config_entry.add_to_hass(hass)

    # Mock entity registry
    with patch(
        "custom_components.meteolux.config_flow.er.async_get"
    ) as mock_entity_reg:
        mock_reg = AsyncMock()
        mock_reg.async_get_entity_id.return_value = "sensor.luxembourg_current_weather"
        mock_reg.async_update_entity = Mock()
        mock_entity_reg.return_value = mock_reg

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reconfigure", "entry_id": mock_config_entry.entry_id},
        )

        # Change name
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Office",  # Changed name
                "location": {"latitude": 49.6116, "longitude": 6.1319},
                CONF_LANGUAGE: "en",
                CONF_UPDATE_INTERVAL_CURRENT: 10,
                CONF_UPDATE_INTERVAL_HOURLY: 30,
                CONF_UPDATE_INTERVAL_DAILY: 6,
            },
        )

        # Should show Step 2
        assert result["type"] == "form"
        assert result["step_id"] == "reconfigure_entity_ids"

        # Choose to regenerate entity IDs
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"entity_id_action": "regenerate"},
        )

        assert result["type"] == "abort"
        assert result["reason"] == "reconfigure_successful"

        # Verify entity registry was called for entity ID updates
        assert mock_reg.async_update_entity.called


async def test_reconfigure_location_selector_sync(
    hass: HomeAssistant, mock_config_entry, mock_validate_location, mock_reverse_geocode
):
    """Test that location selector coordinates sync with manual inputs."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": mock_config_entry.entry_id},
    )

    # Use location selector (map)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Luxembourg",
            "location": {
                "latitude": 49.7,
                "longitude": 6.2,
            },
            CONF_LANGUAGE: "en",
            CONF_UPDATE_INTERVAL_CURRENT: 10,
            CONF_UPDATE_INTERVAL_HOURLY: 30,
            CONF_UPDATE_INTERVAL_DAILY: 6,
        },
    )

    # Coordinates should be extracted from location selector
    assert result["type"] == "abort"
    assert mock_config_entry.data[CONF_LATITUDE] == 49.7
    assert mock_config_entry.data[CONF_LONGITUDE] == 6.2


async def test_unique_id_prevents_duplicates(
    hass: HomeAssistant, mock_config_entry, mock_validate_location, mock_reverse_geocode
):
    """Test that duplicate locations are prevented by unique_id."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Try to add same coordinates
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Home 2",
            "location": {"latitude": 49.6116, "longitude": 6.1319},
            CONF_LANGUAGE: "en",
            CONF_UPDATE_INTERVAL_CURRENT: 10,
            CONF_UPDATE_INTERVAL_HOURLY: 30,
            CONF_UPDATE_INTERVAL_DAILY: 6,
        },
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_location_out_of_bounds(
    hass: HomeAssistant, mock_validate_location
):
    """Test user form with coordinates out of Luxembourg boundaries."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Test latitude out of bounds
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Home",
            "location": {"latitude": 48.0, "longitude": 6.1319},  # Below Luxembourg minimum (49.4)
            CONF_LANGUAGE: "en",
            CONF_UPDATE_INTERVAL_CURRENT: 10,
            CONF_UPDATE_INTERVAL_HOURLY: 30,
            CONF_UPDATE_INTERVAL_DAILY: 6,
        },
    )

    assert result["type"] == "form"
    assert result["errors"]["location"] == "latitude_out_of_bounds"

    # Test longitude out of bounds
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Home",
            "location": {"latitude": 49.6116, "longitude": 7.5},  # Above Luxembourg maximum (6.5)
            CONF_LANGUAGE: "en",
            CONF_UPDATE_INTERVAL_CURRENT: 10,
            CONF_UPDATE_INTERVAL_HOURLY: 30,
            CONF_UPDATE_INTERVAL_DAILY: 6,
        },
    )

    assert result["type"] == "form"
    assert result["errors"]["location"] == "longitude_out_of_bounds"

# MeteoLux Weather Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/VixOrg/meteolux-ha-integration)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/VixOrg/meteolux-ha-integration/validation-hacs.yml?label=cron)
[![GitHub](https://img.shields.io/github/license/VixOrg/meteolux-ha-integration)](LICENCE)

A Home Assistant custom integration providing accurate weather data for Luxembourg from [MeteoLux](https://www.meteolux.lu/).

## Features

- **Weather Entity** with current conditions and forecasts (hourly & 10-day)
- **24 Sensor Entities** (9 current + 15 forecast sensors)
- **4 Languages**: English, French, German, Luxembourgish
- **Configurable update intervals** for Current conditions, Hourly and Daily forecasts
- **3 Location selection methods**:
  - **City selector**: 102 Luxembourg Cities available via dropdown
  - **Address input**: derive precise coordinates from an address (Address Geocoding)
  - **Map selection**: location selection using an Interactive Map

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots (⋮) → "Custom repositories"
4. Add repository URL and select "Integration" as category
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/meteolux` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Setup Steps

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "MeteoLux"
4. **Choose location method**:
   - **City selector**: Pick from 102 Luxembourg cities
   - **Address input**: Enter any Luxembourg address (automatically geocoded)
   - **Map selector**: Click on an interactive map
5. Enter a **friendly name** (e.g., "Home", "Office")
6. Complete location setup
7. **Configure weather forecast settings**:
   - **Language**: English, French, German, or Luxembourgish
   - **Current conditions update**: How often to refresh current weather (1-60 minutes, default: 10)
   - **Hourly forecast update**: How often to refresh hourly forecasts (5-120 minutes, default: 30)
   - **Daily forecast update**: How often to refresh daily forecasts (1-24 hours, default: 6)
8. Click **Submit**

### Location Selection Methods

#### 🏙️ City Selector
- Choose from 102 Luxembourg cities
- Searchable dropdown
- Fastest setup method

#### 📍 Address Input
- Enter any Luxembourg address
- Automatically geocoded using OpenStreetMap
- Shows coordinates for confirmation
- Most precise method
- Example: `1 Rue de la Gare, Luxembourg`

#### 🗺️ Map Selector
- Interactive map centered on Luxembourg
- Click to select exact location
- Zoom and pan for precision
- Validates Luxembourg boundaries

### Language Support

Choose from 4 languages for weather condition descriptions:
- **English** (en) - Default
- **French** (fr) - Français
- **German** (de) - Deutsch
- **Luxembourgish** (lb) - Lëtzebuergesch

Language affects weather condition text (e.g., "Cloudy", "Nuageux", "Wolkig", "Wollekeg").

### Update Intervals

Configure how often weather data is refreshed during setup:

**Current Conditions** (1-60 minutes, default: 10)
- How often to update current weather conditions
- Lower values = more up-to-date data but more API requests
- Recommended: 5-15 minutes for frequently changing conditions

**Hourly Forecasts** (5-120 minutes, default: 30)
- How often to update hourly weather forecasts
- Hourly forecasts don't change as rapidly as current conditions
- Recommended: 20-60 minutes for balanced updates

**Daily Forecasts** (1-24 hours, default: 6)
- How often to update daily weather forecasts
- Daily forecasts are stable and rarely change throughout the day
- Recommended: 4-12 hours to minimize API load

### Multiple Locations

Add the integration multiple times for different locations, each with its own name and language.

**Example:**
- "Home" - English, Address-based, 10/30/6 intervals
- "Bureau" - French, Luxembourg City, 15/60/12 intervals
- "Cabin" - Luxembourgish, Map-based, 5/20/4 intervals

## Entities

### Weather Entity

- `weather.<location_name>` - Weather forecast entity
- Compatible with all Home Assistant weather cards
- Hourly forecasts (6-hour intervals)
- Daily forecasts (10 days)

### Sensor Entities

#### Current Weather (Always Enabled)
- **Temperature** - Current temperature in °C
- **Apparent Temperature** - Feels-like temperature in °C
- **Wind Speed** - Current wind speed in km/h
- **Precipitation** - Current precipitation in mm
- **Condition** - Weather condition (sunny, cloudy, rainy, etc.)

#### Additional Current Sensors (Disabled by Default)
- **Wind Gusts** - Wind gust speed in km/h
- **Wind Direction** - Wind direction (N, NE, E, SE, S, SW, W, NW)
- **Snow** - Current snowfall in mm
- **Condition Text** - Textual weather description

#### Forecast Sensors (Day 0 Enabled, Days 1-4 Disabled)
For each of the next 5 days:
- **Temperature High Day X** - Maximum temperature
- **Temperature Low Day X** - Minimum temperature
- **Precipitation Day X** - Expected precipitation

**Total: 24 sensor entities**

To enable additional sensors: Go to **Settings** → **Devices & Services** → **MeteoLux** → Click your device → **Entities** tab → Enable desired entities.

## Usage Examples

### Weather Card

```yaml
type: weather-forecast
entity: weather.home
show_current: true
show_forecast: true
```

### Sensor Card

```yaml
type: entities
entities:
  - entity: sensor.home_temperature
  - entity: sensor.home_apparent_temperature
  - entity: sensor.home_wind_speed
  - entity: sensor.home_precipitation
  - entity: sensor.home_condition_text
```

### Automation Example

```yaml
automation:
  - alias: "Rain Alert"
    trigger:
      - platform: state
        entity_id: sensor.home_condition
        to: "rainy"
    action:
      - service: notify.mobile_app
        data:
          message: "It's raining! Close the windows."
```

## API Information

- **Base URL**: `https://metapi.ana.lu/api/v1`
- **Endpoints**:
  - `/metapp/bookmarks` - List of cities
  - `/metapp/weather` - Weather data (city ID or coordinates)
- **Default Update Intervals** (configurable during setup):
  - Current conditions: 10 minutes
  - Hourly forecast: 30 minutes
  - Daily forecast: 6 hours

## Troubleshooting

### Integration won't load
- Verify internet connectivity
- Check Home Assistant logs for errors
- Ensure MeteoLux API is accessible

### Sensors showing "Unavailable"
- Check integration configuration
- Review Home Assistant logs for API errors
- Verify update intervals

### City not in dropdown
- Use address or map method instead
- Check if your location is in Luxembourg

### Address not found
- Verify address spelling
- Try simpler format (street + city)
- Use map method as alternative

### Location outside Luxembourg error
- Ensure selected coordinates are within Luxembourg boundaries
- Try a different location or use city selector

## Weather Condition Mapping

| MeteoLux Icons | HA Condition | Description |
|----------------|--------------|-------------|
| 1 | sunny | Clear sky |
| 2 | clear-night | Clear night |
| 3, 4, 9 | partlycloudy | Partly cloudy |
| 5, 6, 8, 10 | cloudy | Cloudy/overcast |
| 7, 11-14 | fog | Fog and mist |
| 15-27, 30-32 | rainy | Rain and drizzle |
| 28, 29 | snowy-rainy | Rain and snow mix |
| 33-41 | snowy | Snow |
| 42-44 | hail | Hail |
| 45-48 | lightning-rainy | Thunderstorms |
| 49 | exceptional | Tornado/severe |
| 50 | windy | Windy conditions |

## Reconfiguration

You can reconfigure the integration without removing it. Click the **3-dot menu** (⋮) on the integration and select **Reconfigure**.

### What Can Be Reconfigured

**1. Change Location**
- Switch between city, address, or map method
- Change to a different city
- Update address or map coordinates
- Preserves weather settings

**2. Change Name**
- Update the location's friendly name
- **Optional**: Regenerate entity IDs to match new name
  - ⚠️ WARNING: Regenerating entity IDs will break existing automations and dashboards
  - Leave unchecked to keep existing entity IDs

**3. Change Weather Forecast Settings**
- Update language (English, French, German, Luxembourgish)
- Adjust update intervals:
  - Current conditions (1-60 minutes)
  - Hourly forecast (5-120 minutes)
  - Daily forecast (1-24 hours)

### How to Reconfigure

1. Go to **Settings** → **Devices & Services** → **MeteoLux**
2. Click the **3-dot menu** (⋮) on your integration instance
3. Select **Reconfigure**
4. Choose what to reconfigure
5. Make your changes
6. Click **Submit**

The integration will reload automatically with the new settings.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and feature requests, please use the [GitHub issues page](https://github.com/VixOrg/meteolux-ha-integration/issues).

## Credits

- **MeteoLux API**: [https://www.meteolux.lu/](https://www.meteolux.lu/)
- **OpenStreetMap Nominatim**: Address geocoding service
- Inspired by the AccuWeather Home Assistant integration

## License

MIT License - See LICENSE file for details

---

**Developed for Home Assistant**
**Integration Type**: Cloud Polling
**Version**: 1.0.0

# MeteoLux Weather Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/VixOrg/meteolux-ha-integration.svg)](https://github.com/VixOrg/meteolux-ha-integration/releases)
[![License](https://img.shields.io/github/license/VixOrg/meteolux-ha-integration.svg)](LICENSE)

A comprehensive Home Assistant integration for [MeteoLux](https://www.meteolux.lu/), providing detailed weather information for Luxembourg.

![MeteoLux Logo](lux-meteo.png)

## Features

### 🌍 Flexible Location Setup
- **Interactive Map**: Select your location by clicking on the map
- **Luxembourg Boundaries**: Validated within Luxembourg (lat: 49.4-50.2, lon: 5.7-6.5)
- **Reverse Geocoding**: Selected coordinates automatically resolved to addresses
- **Multi-language Support**: English, French, German, and Luxembourgish
- **Single-Step Configuration**: Simplified setup form with all options in one view
- **Reconfiguration**: Change location, name, or settings without losing data

### 🌤️ Comprehensive Weather Data
- **Weather Entity**: Full-featured weather entity compatible with all Home Assistant weather cards
  - **10-Day Daily Forecast**: Intelligent forecast combining current weather with detailed 5-day and extended 10-day data
    - Today's forecast automatically merges real-time current conditions (humidity, pressure, clouds) with forecast high/low temps
    - Days 1-4: Full weather details (temps, wind, precipitation, UV index)
    - Days 5-9: Extended forecast (temps, precipitation)
  - **Hourly Forecast**: Forecasts at multiple times throughout each day (typically 00:00, 06:00, 12:00, 18:00) spanning ~5 days
  - Enhanced forecast data including wind gusts, humidity, clouds, and UV index
- **Current Weather Sensor**: Single consolidated sensor with 16 attributes
  - Temperature & Apparent Temperature
  - **Calculated Comfort Indices**: Dew Point, Wind Chill, Humidex
  - Wind Speed, Gusts & Direction (translated to selected language)
  - Precipitation & Snow
  - Weather Condition & Text
  - Humidity, Pressure, UV Index, Cloud Cover
- **Ephemeris Sensor**: Sun and moon data (rise/set times, sunshine hours, moon phase, UV index)
- **Location Sensor**: City information and coordinates

**Total**: 4 entities (1 weather entity + 3 sensors) - following modern Home Assistant best practices

### 📊 Advanced Forecast Access
Access forecast data using Home Assistant's modern `weather.get_forecasts` service:
- Retrieve daily or hourly forecasts programmatically
- Use in automations, scripts, and templates
- No need for separate forecast sensor entities

### 🔄 Robust Data Fetching
- **Configurable Update Intervals**:
  - Current weather: 1-60 minutes (default: 10 min)
  - Hourly forecast: 5-120 minutes (default: 30 min)
  - Daily forecast: 1-24 hours (default: 6 hours)
- **Exponential Backoff**: Automatic retry on failures (2s, 4s, 8s, 16s, 30s, 60s)
- **Smart Error Handling**: Retry on 5xx/429 errors, skip on 4xx client errors

### 🏠 Multiple Instances
- Add multiple weather instances for different Luxembourg locations
- Each instance maintains independent configuration
- Entity names automatically namespaced

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add repository URL: `https://github.com/VixOrg/meteolux-ha-integration`
5. Category: "Integration"
6. Click "Add"
7. Search for "MeteoLux" and install
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/VixOrg/meteolux-ha-integration/releases)
2. Extract the `meteolux` folder from the ZIP
3. Copy the `meteolux` folder to `<config_dir>/custom_components/meteolux`
4. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ ADD INTEGRATION"**
3. Search for **"MeteoLux"**
4. Configure in a single form:
   - **Language**: Choose forecast language (English/French/German/Luxembourgish)
   - **Location**: Click on the interactive map to select your Luxembourg location
   - **Name**: Friendly name for this location (e.g., "Home", "Office")
   - **Update Intervals**: Configure data refresh rates
     - Current weather: 1-60 minutes (default: 10 min)
     - Hourly forecast: 5-120 minutes (default: 30 min)
     - Daily forecast: 1-24 hours (default: 6 hours)

The configuration form is designed for easy setup. Simply click on the map to select your location, and the coordinates will be extracted automatically.

### Reconfiguration

You can reconfigure the integration at any time **without losing data**:

1. Go to **Settings** → **Devices & Services** → **MeteoLux**
2. Click **"RECONFIGURE"**
3. Update any settings in the single form (location, name, language, intervals)

#### Entity ID Regeneration

When you change the integration name during reconfiguration, you'll be asked how to handle entity IDs:

- **Keep existing entity IDs** (default): Preserves current entity IDs to maintain all automations, scripts, and dashboards
- **Regenerate entity IDs**: Updates entity IDs to match the new name (e.g., `sensor.home_current_weather` → `sensor.office_current_weather`)

⚠️ **Warning**: Regenerating entity IDs will break existing automations and dashboards that reference these entities. Choose this option only if you understand the implications and are prepared to update your automations.

## Entities

### Weather Entity

**Entity ID**: `weather.<name>`

The weather entity provides current conditions and forecasts compatible with all Home Assistant weather cards.

**Current Conditions**:
- `temperature`: Current temperature (°C)
- `apparent_temperature`: Feels-like temperature (°C)
- `humidity`: Relative humidity (%)
- `pressure`: Atmospheric pressure (hPa)
- `wind_speed`: Wind speed (km/h)
- `wind_bearing`: Wind direction (translated to selected language)
- `uv_index`: UV index (0-12 scale)
- `cloud_coverage`: Cloud coverage (%)
- `condition`: Current weather condition

**Forecast Access**:
- **Daily Forecast**: Up to 10 days (combining detailed 5-day + extended 10-day data)
  - Days 0-4: Full details (temps, wind speed/gusts/direction, precipitation, UV index)
  - Days 5-9: Basic details (high/low temps, precipitation)
- **Hourly Forecast**: Multiple forecasts per day at specific times (typically 00:00, 06:00, 12:00, 18:00) spanning ~5 days
  - Temperature, apparent temperature, precipitation
  - Wind speed, gusts, direction (translated)
  - Condition, humidity, clouds, UV index

Access forecasts using the `weather.get_forecasts` service (see Examples below).

### Sensor Entities

#### Current Weather Sensor

**Entity ID**: `sensor.<name>_current_weather`
**State**: Current temperature (°C)
**Device Class**: Temperature

**Attributes** (16 total):
- `temperature` - Current temperature (°C)
- `apparent_temperature` - Feels-like temperature (°C)
- `dew_point` - Calculated dew point (°C) using Magnus formula
- `wind_chill` - Calculated wind chill (°C, only when temp < 10°C)
- `humidex` - Canadian humidity index
- `wind_speed` - Wind speed (km/h)
- `wind_gusts` - Wind gusts (km/h)
- `wind_direction` - Translated wind direction
- `precipitation` - Precipitation amount (mm)
- `snow` - Snow amount (mm)
- `condition` - Home Assistant weather condition
- `condition_text` - Human-readable condition
- `humidity` - Relative humidity (%)
- `pressure` - Atmospheric pressure (hPa)
- `uv_index` - UV index
- `cloud_cover` - Cloud coverage (%)

#### Ephemeris Sensor (Today)

**Entity ID**: `sensor.<name>_today`
**State**: Current date
**Icon**: `mdi:weather-sunset`

**Attributes**:
- `sun`: Sunrise, sunset, sunshine hours, UV index
- `moon`: Moonrise, moonset, moon phase, moon icon

#### Location Sensor

**Entity ID**: `sensor.<name>_location`
**State**: City name
**Icon**: `mdi:map-marker`

**Attributes**: All city properties from API (id, name, lat, long, etc.)

## Examples

### Lovelace Weather Card

```yaml
type: weather-forecast
entity: weather.luxembourg
show_forecast: true
```

### Accessing Forecasts

Use the `weather.get_forecasts` service to retrieve forecast data programmatically:

#### Daily Forecast (10 days)

```yaml
# In automations or scripts
service: weather.get_forecasts
data:
  type: daily
target:
  entity_id: weather.luxembourg
response_variable: daily_forecast
```

Then access the forecast data in templates:
```yaml
# Get tomorrow's high temperature
{{ daily_forecast['weather.luxembourg'].forecast[1].temperature }}

# Get day 3 precipitation
{{ daily_forecast['weather.luxembourg'].forecast[2].precipitation }}
```

#### Hourly Forecast

```yaml
service: weather.get_forecasts
data:
  type: hourly
target:
  entity_id: weather.luxembourg
response_variable: hourly_forecast
```

Then access hourly data (forecasts at 00:00, 06:00, 12:00, 18:00 each day):
```yaml
# Get first hourly forecast (e.g., today at 18:00)
{{ hourly_forecast['weather.luxembourg'].forecast[0].temperature }}

# Get tomorrow morning forecast (e.g., tomorrow at 06:00)
{{ hourly_forecast['weather.luxembourg'].forecast[2].temperature }}
```

### Automation with Forecast

```yaml
automation:
  - alias: "Notify on Tomorrow's Heavy Rain"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: weather.get_forecasts
        data:
          type: daily
        target:
          entity_id: weather.luxembourg
        response_variable: forecast
      - condition: template
        value_template: "{{ forecast['weather.luxembourg'].forecast[1].precipitation | float(0) > 10 }}"
      - service: notify.mobile_app
        data:
          title: "Heavy Rain Tomorrow"
          message: >
            Tomorrow's forecast: {{ forecast['weather.luxembourg'].forecast[1].precipitation }}mm
            of rain expected!
```

### Automation with Current Conditions

```yaml
automation:
  - alias: "Notify on Heavy Rain"
    trigger:
      - platform: template
        value_template: "{{ state_attr('sensor.luxembourg_current_weather', 'precipitation') | float(0) > 10 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Heavy Rain Alert"
          message: >
            {{ state_attr('sensor.luxembourg_current_weather', 'precipitation') }}mm
            of rain detected in Luxembourg!
```

### Template Sensor Example

```yaml
template:
  - sensor:
      - name: "Luxembourg Weather Summary"
        state: >
          {{ states('weather.luxembourg') | title }},
          {{ state_attr('sensor.luxembourg_current_weather', 'temperature') }}°C
          (feels like {{ state_attr('sensor.luxembourg_current_weather', 'apparent_temperature') }}°C)
```

## Data Source

This integration uses the official [MeteoLux API](https://www.meteolux.lu/) provided by the Luxembourg government's meteorological service.

**Data License**: [CC0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/)

**Geocoding**: Uses [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) for address/coordinate conversion.

## Troubleshooting

### Integration Not Showing Up
- Ensure you've restarted Home Assistant after installation
- Check Home Assistant logs for errors: `Settings → System → Logs`

### Weather Data Not Updating
- Check update intervals in integration configuration
- Enable debug logging to see API requests:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.meteolux: debug
  ```
- Check Home Assistant logs for API errors

### Coordinates Out of Bounds
- Ensure selected location is within Luxembourg boundaries
- Latitude: 49.4 to 50.2
- Longitude: 5.7 to 6.5
- Use the map picker to ensure valid location selection

### Reverse Geocoding Shows Coordinates Only
- Nominatim API may be temporarily unavailable
- Coordinates are still saved and weather data works normally
- Address display is informational only and not required for functionality

## Development

**Contributing**:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass and coverage is 80%+
5. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/VixOrg/meteolux-ha-integration/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/VixOrg/meteolux-ha-integration/issues)
- **Documentation**: [specs/001-enhanced-weather-entities/](specs/001-enhanced-weather-entities/)

## License

This integration is released under the [MIT License](LICENSE).

Weather data is provided by MeteoLux under [CC0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Credits

- **MeteoLux**: Weather data provider
- **OpenStreetMap**: Geocoding service
- **Home Assistant**: Smart home platform
- **Contributors**: See [GitHub Contributors](https://github.com/VixOrg/meteolux-ha-integration/graphs/contributors)

---

**Made with ❤️ for Luxembourg's Home Assistant community**

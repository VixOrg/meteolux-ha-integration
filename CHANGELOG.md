# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-04

### Added

#### Core Integration Features
- Home Assistant custom integration for MeteoLux weather data
- Single-step configuration form with all options in one view
- Interactive map location picker with bidirectional coordinate sync
- Manual latitude/longitude coordinate entry (syncs with map)
- Luxembourg boundaries validation (lat: 49.4-50.2, lon: 5.7-6.5)
- Reverse geocoding for displaying addresses from coordinates (via Nominatim)
- Multi-language support (en, fr, de, lb)
- Multiple location instances support
- Reconfiguration without data loss
- **Optional Entity ID Regeneration**: When changing integration name during reconfiguration:
  - Conditional two-step flow only appears when name changes
  - Radio button choice: Keep existing entity IDs (default) or Regenerate entity IDs
  - Preserves automations and dashboards by default
  - Clear warnings about automation impacts when regenerating

#### Weather Entity
- Full-featured Home Assistant weather entity following 2024 best practices
- Current conditions with enriched attributes
- **10-Day Daily Forecast**: Intelligent forecast combining current weather with detailed 5-day and extended 10-day data
  - Today (Day 0): Automatically merges real-time current weather (condition, humidity, pressure, clouds) with forecast high/low temps
  - Days 1-4: Full details (temps, wind speed/gusts/direction, precipitation, UV index)
  - Days 5-9: Extended forecast (high/low temps, precipitation)
  - Dynamic day counting adapts to available API forecast data
  - Date deduplication ensures no duplicate entries
- **Hourly Forecast**: Forecasts at multiple times per day (typically 00:00, 06:00, 12:00, 18:00) spanning ~5 days
  - Temperature, apparent temperature, precipitation
  - Wind speed, gusts, direction (translated)
  - Condition, humidity, clouds, UV index
- Wind direction translation to selected language
- Condition mapping to Home Assistant standards
- Accessible via modern `weather.get_forecasts` service

#### Current Weather Sensor (1 sensor)
- Single sensor with temperature as state and 16 comprehensive attributes:
  - Temperature, Apparent Temperature
  - **Calculated Comfort Indices**: Dew Point, Wind Chill, Humidex
  - Wind Speed, Gusts, Direction (translated)
  - Precipitation, Snow
  - Condition, Condition Text
  - Humidity, Pressure, UV Index, Cloud Cover

#### Ephemeris Sensor (1 sensor)
- Sun and moon data (rise, set, phase, sunshine hours, UV index)
- State: Current date
- Icon: `mdi:weather-sunset`

#### Location Sensor (1 sensor)
- City information and coordinates
- State: City name
- Icon: `mdi:map-marker`

#### Data Coordinator Features
- Exponential backoff retry logic (2s, 4s, 8s, 16s, 30s, 60s)
- Smart retry on server errors (5xx) and rate limits (429)
- Skip retry on client errors (4xx except 429)
- Configurable update intervals per data type
- Efficient API data maximization

#### Developer Features
- GitHub Actions CI/CD workflows (validate, test, release)
- Comprehensive test suite structure
- HACS compliance
- MIT License
- Developer documentation

### Performance Features
- **Modern entity structure**: 4 total entities (1 weather + 3 sensors)
  - Follows Home Assistant 2024 best practices
  - Uses modern `weather.get_forecasts` service instead of forecast sensor entities
  - 91% reduction from traditional multi-sensor approach
  - All entities enabled by default
- **Comprehensive forecast access**: 10-day daily forecast + hourly forecasts at multiple times per day via weather entity
- Configurable update intervals:
  - Current weather: 10 minutes (default)
  - Hourly forecast: 30 minutes (default)
  - Daily forecast: 6 hours (default)

### Documentation
- Comprehensive README with installation and usage instructions
- Feature specification in specs directory
- Implementation plan and technical documentation
- Developer quickstart guide
- Testing documentation

---

For more information, see the [README](README.md) or visit the [GitHub repository](https://github.com/VixOrg/meteolux-ha-integration).

# Data Model: Enhanced MeteoLux Weather Entities

**Feature**: Enhanced MeteoLux Weather Entities with Multi-Forecast Support
**Date**: 2025-10-28
**Purpose**: Define all data entities, their attributes, relationships, validation rules, and state transitions

> **Note on Implementation**: This data model originally described a 43-entity architecture. The final implementation follows **Home Assistant 2024 best practices** with **4 entities total** (1 weather entity + 3 sensors). Forecasts are accessed via `weather.get_forecasts` service instead of separate sensor entities. Hourly forecasts are provided at multiple times per day (typically 00:00, 06:00, 12:00, 18:00) spanning ~5 days.

## Overview

This data model documents all entities in the MeteoLux integration, from configuration data through runtime weather entities. Entities are organized by lifecycle: Configuration Entities (user-defined setup), API Response Entities (MeteoLux API structure), and Home Assistant Entities (exposed to users).

---

## 1. Configuration Entities

### 1.1 Integration Configuration Entry

**Purpose**: Stores user configuration for a single MeteoLux integration instance.

**Lifecycle**: Created during config flow, updated during reconfiguration, deleted when integration instance is removed.

**Storage**: Home Assistant `ConfigEntry` (persistent across restarts).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `entry_id` | `str` | Unique, auto-generated | Unique identifier for this integration instance |
| `title` | `str` | Length 1-100 chars | User-friendly name (e.g., "Home", "Office") |
| `data.latitude` | `float` | -90.0 to 90.0, within Luxembourg (49.4-50.2) | Location latitude (from map picker or manual input) |
| `data.longitude` | `float` | -180.0 to 180.0, within Luxembourg (5.7-6.5) | Location longitude (from map picker or manual input) |
| `data.display_name` | `str` \| `None` | Length 1-500 chars | Optional reverse-geocoded address (display only) |
| `data.language` | `str` | Enum: `en`, `fr`, `de`, `lb` | Weather description language |
| `data.update_interval_current` | `int` | 1-60 (minutes) | How often to fetch current weather |
| `data.update_interval_hourly` | `int` | 5-120 (minutes) | How often to fetch hourly forecasts |
| `data.update_interval_daily` | `int` | 1-24 (hours) | How often to fetch daily forecasts |

> **Implementation Note**: The integration was simplified to use only coordinate-based configuration. The specification originally included `location_method`, `city_id`, and `address` fields, but the final implementation uses a single-step form with map picker and manual coordinate inputs only. All API requests use coordinates (`lat`/`long` parameters), never city IDs.

**Validation Rules**:
1. **Luxembourg Boundary Check**: `49.4 ≤ latitude ≤ 50.2` AND `5.7 ≤ longitude ≤ 6.5`
2. **Update Interval Ranges**: Current (1-60 min), Hourly (5-120 min), Daily (1-24 hr) per FR-009
3. **Unique Entry Titles**: While not enforced, HA will append suffixes ("Home 2") if duplicates exist

**Relationships**:
- One-to-Three → `CoordinatorInstance` (current, hourly, daily)
- One-to-Many → `WeatherEntity`, `SensorEntity` (one config entry creates ~25 entities)

---

### 1.2 Reconfiguration Options

**Purpose**: Temporary data structure during reconfiguration flow.

**Lifecycle**: Exists only during reconfiguration step, then merged into `ConfigEntry`.

| Attribute | Type | Description |
|-----------|------|-------------|
| *(all fields from Integration Configuration Entry)* | | User can modify any config attribute in a single form |
| `entity_id_action` (Step 2 only) | `str` | Enum: `keep`, `regenerate`. Only appears if name changed. Determines whether to preserve or regenerate entity IDs. |

> **Implementation Note**: When the integration name changes during reconfiguration, a conditional second step appears asking the user to choose between keeping existing entity IDs (default, preserves automations) or regenerating them to match the new name (with clear warnings). This two-step flow only appears when the name is modified.

**Validation Rules**:
1. All validation same as Integration Configuration Entry
2. Entity IDs preserved by default (when `entity_id_action=keep` or when name unchanged)
3. Entity IDs regenerated only when explicitly requested (`entity_id_action=regenerate`)

---

## 2. API Response Entities

### 2.1 Luxembourg City (MeteoLux Bookmarks API)

**Purpose**: Represents a city in Luxembourg from the MeteoLux bookmarks API.

**Source**: `GET https://metapi.ana.lu/api/v1/metapp/bookmarks`

**Lifecycle**: Fetched once during config flow, cached in memory for dropdown population.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `int` | Unique city ID (e.g., `1` for Luxembourg City) |
| `name` | `str` | City name (e.g., "Luxembourg", "Esch-sur-Alzette") |
| `lat` | `float` | City latitude |
| `long` | `float` | City longitude (API uses `long`, not `lon`) |
| `region` | `str` | "N" (North) or "S" (South) |
| `canton` | `str` | Administrative canton (e.g., "Luxembourg", "Esch") |
| `domain` | `str` | "villes" (cities), "lieu" (places), or "fluvial" |

**Validation Rules**:
- None (data from trusted MeteoLux API)

**Relationships**:
- Referenced by `Integration Configuration Entry.city_id`

---

### 2.2 Current Weather (MeteoLux Weather API)

**Purpose**: Current weather conditions from MeteoLux API.

**Source**: `GET https://metapi.ana.lu/api/v1/metapp/weather?lat={lat}&long={lon}&langcode={lang}`

**Lifecycle**: Fetched every `update_interval_current` minutes by `CurrentWeatherCoordinator`.

| Attribute | Type | Guaranteed | Description |
|-----------|------|------------|-------------|
| `date` | `str` (ISO 8601) | ✅ Yes | Timestamp of observation |
| `temperature` | `float` | ✅ Yes | Temperature in °C |
| `humidex` | `float` \| `None` | ❌ Optional | Apparent temperature (humidex) in °C |
| `icon.id` | `int` | ✅ Yes | Weather icon ID (1-50, maps to HA condition) |
| `icon.name` | `str` | ✅ Yes | Weather description in selected language |
| `wind.direction` | `str` | ✅ Yes | Wind direction ("N", "NE", "E", "SE", "S", "SO", "O", "NO") |
| `wind.speed` | `str` | ✅ Yes | Wind speed (e.g., "10 km/h", "5-15 km/h") |
| `wind.gusts` | `str` \| `None` | ❌ Optional | Wind gusts (e.g., "25 km/h") |
| `rain` | `float` \| `None` | ❌ Optional | Precipitation in mm (defaults to 0 if missing) |
| `snow` | `float` \| `None` | ❌ Optional | Snowfall in mm |

**Parsing Rules** (Basic + Enriched Pattern):
1. **Basic Info** (always populated): `temperature`, `icon`, `wind.speed`, `wind.direction`
2. **Enriched Info** (populated if available): `humidex`, `wind.gusts`, `rain`, `snow`
3. **Wind Speed Parsing**: Extract numeric value from string (e.g., "10 km/h" → `10`, "5-15 km/h" → `10` [average])

**Relationships**:
- Fetched by `CurrentWeatherCoordinator`
- Consumed by `WeatherEntity`, `TemperatureSensor`, `WindSpeedSensor`, etc.

---

### 2.3 Hourly Forecast (MeteoLux Weather API)

**Purpose**: Hourly weather forecast for the next 24-48 hours.

**Source**: `forecast.hourly` array in MeteoLux weather API response.

**Lifecycle**: Fetched every `update_interval_hourly` minutes by `HourlyForecastCoordinator`.

| Attribute | Type | Guaranteed | Description |
|-----------|------|------------|-------------|
| `date` | `str` (ISO 8601) | ✅ Yes | Forecast timestamp |
| `temperature` | `float` | ✅ Yes | Forecast temperature in °C |
| `icon.id` | `int` | ✅ Yes | Weather icon ID |
| `icon.name` | `str` | ✅ Yes | Weather description |
| `wind.direction` | `str` | ✅ Yes | Wind direction |
| `wind.speed` | `str` | ✅ Yes | Wind speed |
| `rain` | `float` \| `None` | ❌ Optional | Precipitation in mm |
| `snow` | `float` \| `None` | ❌ Optional | Snowfall in mm |

**Parsing Rules**: Same as Current Weather (Basic + Enriched pattern).

**Relationships**:
- Fetched by `HourlyForecastCoordinator`
- Consumed by `HourlyForecastSensor` (stores array of hourly entries as state attributes)

---

### 2.4 Daily Forecast (Detailed - 5 days)

**Purpose**: Detailed daily forecast for the next 5 days.

**Source**: `forecast.daily` array in MeteoLux weather API response.

**Lifecycle**: Fetched every `update_interval_daily` hours by `DailyForecastCoordinator`.

| Attribute | Type | Guaranteed | Description |
|-----------|------|------------|-------------|
| `date` | `str` (ISO 8601) | ✅ Yes | Forecast date |
| `temperatureMin` | `float` | ✅ Yes | Minimum temperature in °C |
| `temperatureMax` | `float` | ✅ Yes | Maximum temperature in °C |
| `icon.id` | `int` | ✅ Yes | Weather icon ID |
| `icon.name` | `str` | ✅ Yes | Weather description |
| `wind.direction` | `str` | ✅ Yes | Wind direction |
| `wind.speed` | `str` | ✅ Yes | Wind speed |
| `rain` | `float` \| `None` | ❌ Optional | Precipitation in mm |
| `snow` | `float` \| `None` | ❌ Optional | Snowfall in mm |
| `sunshine` | `int` \| `None` | ❌ Optional | Sunshine duration in hours |
| `uvIndex` | `int` \| `None` | ❌ Optional | UV index (0-12 scale) |

**Parsing Rules**: Basic + Enriched pattern. `sunshine` and `uvIndex` are enriched fields.

**Relationships**:
- Fetched by `DailyForecastCoordinator`
- Consumed by `DailyForecastSensor` (Day 0-4 sensors, one per day)

---

### 2.5 Daily Forecast (High-Level - 10 days)

**Purpose**: High-level temperature and precipitation trend for the next 10 days.

**Source**: `data.forecast` array in MeteoLux weather API response.

**Lifecycle**: Fetched every `update_interval_daily` hours by `DailyForecastCoordinator`.

| Attribute | Type | Guaranteed | Description |
|-----------|------|------------|-------------|
| `date` | `str` (ISO 8601) | ✅ Yes | Forecast date |
| `minTemp` | `float` | ✅ Yes | Minimum temperature in °C |
| `maxTemp` | `float` | ✅ Yes | Maximum temperature in °C |
| `precipitation` | `float` | ✅ Yes | Precipitation in mm |

**Parsing Rules**: All fields guaranteed (no enrichment needed).

**Relationships**:
- Fetched by `DailyForecastCoordinator`
- Consumed by `TenDayForecastSensor` (stores array of 10 entries as state attributes)

> **Implementation Note - Enhanced Daily Forecast**: The weather entity's `async_forecast_daily()` method intelligently combines data from sections 2.4 and 2.5 to provide a comprehensive up-to-10-day forecast. When today's date matches the first forecast day (Day 0), current weather data (condition, humidity, pressure, cloud coverage) is automatically merged with that day's forecast to provide a seamless "now + today" experience. The logic dynamically processes available detailed days (typically 5 from `forecast.daily`) and fills remaining days from the extended forecast (`data.forecast`), supporting up to 10 days total. Date deduplication ensures no duplicate entries when the same date appears in both sources, with detailed data taking precedence.

---

## 3. Home Assistant Entities

### 3.1 Weather Entity

**Purpose**: Primary weather entity compatible with HA weather cards.

**Entity ID**: `weather.{title}` (e.g., `weather.home`, `weather.office`)

**Platform**: `weather` (Home Assistant core platform)

**State**: Current weather condition (e.g., `sunny`, `rainy`, `cloudy`)

| Attribute | Type | Source | Description |
|-----------|------|--------|-------------|
| `temperature` | `float` | Current Weather API | Current temperature in °C |
| `apparent_temperature` | `float` \| `None` | Current Weather API (`humidex`) | Feels-like temperature in °C |
| `humidity` | `int` \| `None` | *(not in API, set to None)* | Relative humidity % (not available from MeteoLux) |
| `wind_speed` | `float` | Current Weather API | Wind speed in km/h |
| `wind_bearing` | `float` \| `None` | Current Weather API | Wind direction in degrees (N=0°, E=90°, S=180°, W=270°) |
| `precipitation_unit` | `str` | Constant | "mm" |
| `pressure` | `float` \| `None` | *(not in API, set to None)* | Atmospheric pressure (not available from MeteoLux) |
| `visibility` | `float` \| `None` | *(not in API, set to None)* | Visibility (not available from MeteoLux) |
| `condition` | `str` | Current Weather API (`icon.id`) | HA condition (sunny, cloudy, rainy, etc.) |
| `forecast` | `list[dict]` | Daily Forecast API (`forecast.daily`) | Array of daily forecasts (HA weather card uses this) |

**State Transitions**: None (stateless entity, state = current condition).

**Validation Rules**:
- `temperature` must be float
- `condition` must be one of HA's standard conditions (mapped from MeteoLux icon ID via `CONDITION_MAP`)

**Relationships**:
- Consumes data from `CurrentWeatherCoordinator` and `DailyForecastCoordinator`

---

### 3.2 Current Weather Sensor Entity (Consolidated)

**Purpose**: Single consolidated sensor exposing all current weather data via state and attributes.

**Entity ID**: `sensor.{title}_current_weather` (e.g., `sensor.home_current_weather`, `sensor.office_current_weather`)

**Platform**: `sensor` (Home Assistant core platform)

**State**: Current temperature (float, °C)

**Device Class**: `SensorDeviceClass.TEMPERATURE`

**Unit**: `UnitOfTemperature.CELSIUS`

**State Class**: `SensorStateClass.MEASUREMENT`

**Enabled by Default**: ✅ Yes

**Attributes** (16 total):

| Attribute | Type | Calculated | Description |
|-----------|------|------------|-------------|
| `temperature` | `float` | ❌ API | Current temperature in °C |
| `apparent_temperature` | `float \| None` | ❌ API | Feels-like temperature in °C (from API `humidex` field) |
| `dew_point` | `float \| None` | ✅ Yes | Calculated dew point using Magnus formula: `(b * α) / (a - α)` where `α = ((a * T) / (b + T)) + ln(RH/100)`, `a=17.27`, `b=237.7` |
| `wind_chill` | `float \| None` | ✅ Yes | Calculated wind chill (only when temp < 10°C and wind > 4.8 km/h) using Environment Canada formula: `13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16` |
| `humidex` | `float \| None` | ✅ Yes | Calculated Canadian humidity index: `T + 0.5555 * (e - 10)` where `e = 6.11 * exp(5417.753 * (1/273.16 - 1/(Td + 273.15)))` |
| `wind_speed` | `float` | ❌ API | Wind speed in km/h (parsed from range string, e.g., "20-30" → 25) |
| `wind_gusts` | `float \| None` | ❌ API | Wind gusts in km/h (parsed from range string) |
| `wind_direction` | `str` | ❌ API | Wind direction translated to selected language (e.g., "O" → "W" for English) |
| `precipitation` | `float` | ❌ API | Precipitation amount in mm (parsed from range string) |
| `snow` | `float \| None` | ❌ API | Snow amount in mm (parsed from range string) |
| `condition` | `str` | ❌ API | Home Assistant condition (e.g., "sunny", "rainy", "cloudy") mapped from icon ID |
| `condition_text` | `str` | ❌ API | Localized condition text (e.g., "Partly cloudy", "Partiellement nuageux") |
| `humidity` | `int \| None` | ❌ API | Relative humidity percentage |
| `pressure` | `float \| None` | ❌ API | Atmospheric pressure in hPa |
| `uv_index` | `int \| None` | ❌ API | UV index (0-12 scale) |
| `cloud_cover` | `int \| None` | ❌ API | Cloud coverage percentage |

**Validation Rules**:
- `temperature` must be float
- `wind_direction` must be translated via `WIND_DIRECTION_MAP[language]`
- `condition` must be valid HA condition string from `CONDITION_MAP[icon_id]`
- Calculated comfort indices only populated when sufficient data available (temperature + humidity for dew point/humidex)

**Relationships**:
- Consumes data from `CurrentWeatherCoordinator`
- Updates according to `update_interval_current` configuration

**Total Current Sensors**: 1 (enabled by default)

---

### 3.3 Daily Forecast Sensor Entities (5-Day Detailed)

**Purpose**: Consolidated sensor entities for each of the next 5 days with comprehensive forecast data.

**Entity IDs**: `sensor.{title}_daily_forecast_d{N}` (e.g., `sensor.home_daily_forecast_d0`, `sensor.home_daily_forecast_d1`, N = 0-4)

**Platform**: `sensor`

**Count**: 5 sensors total (1 per day)

**State**: High temperature for day N (float, °C)

**Device Class**: `SensorDeviceClass.TEMPERATURE`

**Unit**: `UnitOfTemperature.CELSIUS`

**State Class**: `SensorStateClass.MEASUREMENT`

**Enabled by Default**: ✅ Yes for Days 0-1, ❌ No for Days 2-4

**Attributes** (12 per sensor):

| Attribute | Type | Description |
|-----------|------|-------------|
| `date` | `str` | Forecast date (ISO 8601) |
| `temperature_high` | `float` | High temperature in °C |
| `temperature_low` | `float` | Low temperature in °C |
| `apparent_temperature_high` | `float \| None` | Feels-like high temperature in °C |
| `apparent_temperature_low` | `float \| None` | Feels-like low temperature in °C |
| `precipitation` | `float` | Precipitation amount in mm (parsed from range string) |
| `wind_speed` | `float` | Wind speed in km/h (parsed from range string) |
| `wind_gusts` | `float \| None` | Wind gusts in km/h (parsed from range string) |
| `wind_direction` | `str` | Wind direction translated to selected language |
| `condition` | `str` | Home Assistant condition mapped from icon ID |
| `condition_text` | `str` | Localized condition text |
| `sunshine_hours` | `int \| None` | Hours of sunshine |
| `uv_index` | `int \| None` | UV index (0-12 scale) |

**Validation Rules**:
- `temperature_high` and `temperature_low` must be floats
- `wind_direction` must be translated via `WIND_DIRECTION_MAP[language]`
- `condition` must be valid HA condition string from `CONDITION_MAP[icon_id]`

**Relationships**:
- Consumes data from `DailyForecastCoordinator` (`forecast.daily` array)
- Updates according to `update_interval_daily` configuration

---

### 3.4 10-Day Extended Forecast Sensor Entities

**Purpose**: Separate sensor entities for each of the next 10 days with basic forecast data.

**Entity IDs**: `sensor.{title}_10day_forecast_d{N}` (e.g., `sensor.home_10day_forecast_d0`, N = 0-9)

**Platform**: `sensor`

**Count**: 10 sensors total (1 per day)

**State**: High temperature for day N (float, °C)

**Device Class**: `SensorDeviceClass.TEMPERATURE`

**Unit**: `UnitOfTemperature.CELSIUS`

**State Class**: `SensorStateClass.MEASUREMENT`

**Enabled by Default**: ❌ No (all 10 sensors disabled by default per FR-022)

**Attributes** (4 per sensor):

| Attribute | Type | Description |
|-----------|------|-------------|
| `date` | `str` | Forecast date (ISO 8601) |
| `temperature_high` | `float` | High temperature in °C |
| `temperature_low` | `float` | Low temperature in °C |
| `precipitation` | `float` | Precipitation in mm (parsed from range string) |

**Validation Rules**:
- `temperature_high` and `temperature_low` must be floats
- `precipitation` defaults to 0 if missing

**Relationships**:
- Consumes data from `DailyForecastCoordinator` (`data.forecast` array)
- Updates according to `update_interval_daily` configuration

---

### 3.5 Hourly Forecast Sensor Entities

**Purpose**: Separate sensor entities for each hour with comprehensive forecast data.

**Entity IDs**: `sensor.{title}_hourly_forecast_h{N}` (e.g., `sensor.home_hourly_forecast_h0`, N = 0-23)

**Platform**: `sensor`

**Count**: 24 sensors total (1 per hour)

**State**: Temperature for hour N (float, °C)

**Device Class**: `SensorDeviceClass.TEMPERATURE`

**Unit**: `UnitOfTemperature.CELSIUS`

**State Class**: `SensorStateClass.MEASUREMENT`

**Enabled by Default**: ✅ Yes for Hours 0-5, ❌ No for Hours 6-23 (per FR-026)

**Attributes** (11 per sensor):

| Attribute | Type | Description |
|-----------|------|-------------|
| `datetime` | `str` | Forecast timestamp (ISO 8601) |
| `temperature` | `float` | Temperature in °C |
| `apparent_temperature` | `float \| None` | Feels-like temperature in °C |
| `precipitation` | `float` | Precipitation in mm (parsed from range string) |
| `wind_speed` | `float` | Wind speed in km/h (parsed from range string) |
| `wind_gusts` | `float \| None` | Wind gusts in km/h (parsed from range string) |
| `wind_direction` | `str` | Wind direction translated to selected language |
| `condition` | `str` | Home Assistant condition mapped from icon ID |
| `condition_text` | `str` | Localized condition text |
| `humidity` | `int \| None` | Relative humidity percentage |
| `cloud_cover` | `int \| None` | Cloud coverage percentage |
| `uv_index` | `int \| None` | UV index (0-12 scale) |

**Validation Rules**:
- `temperature` must be float
- `wind_direction` must be translated via `WIND_DIRECTION_MAP[language]`
- `condition` must be valid HA condition string from `CONDITION_MAP[icon_id]`

**Relationships**:
- Consumes data from `HourlyForecastCoordinator` (`forecast.hourly` array)
- Updates according to `update_interval_hourly` configuration

---

## 4. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Flow                        │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
            ┌──────────────────────────────────┐
            │   Integration Configuration      │
            │   Entry (ConfigEntry.data)       │
            │  - location (lat/lon/city/addr)  │
            │  - language (en/fr/de/lb)        │
            │  - intervals (current/hr/daily)  │
            └──────────────────────────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Current Weather  │ │Hourly Fcst   │ │Daily Fcst    │
    │  Coordinator     │ │Coordinator   │ │Coordinator   │
    │ (every 10 min)   │ │(every 30 min)│ │(every 6 hr)  │
    └──────────────────┘ └──────────────┘ └──────────────┘
            │                   │                 │
            │  API Call         │  API Call       │  API Call
            │  /metapp/weather  │  /metapp/weather│  /metapp/weather
            ▼                   ▼                 ▼
    ┌─────────────────────────────────────────────────────┐
    │        MeteoLux API (metapi.ana.lu)                 │
    │  - forecast.current (current conditions)            │
    │  - forecast.hourly  (hourly forecast array)         │
    │  - forecast.daily   (5-day detailed forecast)       │
    │  - data.forecast    (10-day high-level trend)       │
    └─────────────────────────────────────────────────────┘
            │                   │                 │
            ▼                   ▼                 ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Current Weather  │ │ Hourly Fcst  │ │ Daily Fcst   │
    │ Data (cached)    │ │ Data (cached)│ │ Data (cached)│
    └──────────────────┘ └──────────────┘ └──────────────┘
            │                   │                 │
            └───────────────────┼─────────────────┘
                                ▼
             ┌────────────────────────────────────┐
             │      Home Assistant Entities       │
             │  - Weather Entity (1)              │
             │  - Current Sensors (9)             │
             │  - 5-Day Forecast Sensors (15)     │
             │  - 10-Day Forecast Sensor (1)      │
             │  - Hourly Forecast Sensor (1)      │
             │  Total: ~27 entities per instance  │
             └────────────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  User Dashboards &     │
                    │  Automations           │
                    └────────────────────────┘
```

---

## 5. Entity State Transitions

### 5.1 Entity Availability States

All entities support three availability states:

1. **Available**: Coordinator has fresh data, entity state is valid
2. **Unavailable**: Coordinator failed to fetch data (API error), entity shows "unavailable"
3. **Unknown**: Initial state before first data fetch

**State Transition Rules**:
```
Initial → (first successful fetch) → Available
Available → (coordinator fetch fails) → Unavailable
Unavailable → (coordinator fetch succeeds) → Available
```

### 5.2 Configuration Entry States

1. **Not Loaded**: Entry exists in config but integration not initialized
2. **Loaded**: Entry initialized, coordinators running, entities registered
3. **Setup Retry**: Entry failed to load (API unreachable), retrying
4. **Failed**: Entry failed to load permanently (user must reconfigure)

**State Transition Rules**:
```
Not Loaded → (async_setup_entry succeeds) → Loaded
Not Loaded → (async_setup_entry fails) → Setup Retry → (retry succeeds) → Loaded
Setup Retry → (retry fails after 3 attempts) → Failed
Loaded → (async_unload_entry) → Not Loaded
```

---

## 6. Validation Summary

| Entity | Validation Rules |
|--------|------------------|
| **Integration Configuration** | Luxembourg boundaries (lat 49.4-50.2, lon 5.7-6.5), update intervals (current 1-60 min, hourly 5-120 min, daily 1-24 hr), language enum (en/fr/de/lb) |
| **Luxembourg City** | None (trusted API data) |
| **Current Weather** | Temperature must be numeric, icon ID must map to valid HA condition |
| **Hourly Forecast** | Same as Current Weather |
| **Daily Forecast (5-day)** | Temp min ≤ temp max, UV index 0-12 if present |
| **Daily Forecast (10-day)** | Temp min ≤ temp max |
| **All HA Entities** | State must be valid type (float for numeric, str for text), device class must match unit |

---

## Document Version

**Version**: 1.0.0
**Last Updated**: 2025-10-28
**Changes**: Initial data model documentation for Enhanced MeteoLux Weather Entities feature

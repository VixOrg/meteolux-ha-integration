# Feature Specification: Enhanced MeteoLux Weather Entities with Multi-Forecast Support

**Feature Branch**: `001-enhanced-weather-entities`
**Created**: 2025-10-28
**Status**: Implemented (with modifications)
**Input**: User description: "MeteoLux HACS integration with enhanced multi-entity weather forecasts, comprehensive configuration UI with multiple location input methods, interactive map, multi-language support, reconfiguration capabilities, and HACS compliance"

> **Note on Implementation**: This specification originally described a 43-entity architecture with separate hourly and daily forecast sensors. The final implementation evolved to follow **Home Assistant 2024 best practices**, using only **4 entities** (1 weather entity + 3 sensors) with forecasts accessed via the modern `weather.get_forecasts` service instead of separate sensor entities. Hourly forecasts are provided at multiple times per day (typically 00:00, 06:00, 12:00, 18:00) spanning ~5 days, rather than 24 separate hourly sensors. This represents a 91% entity reduction while providing the same forecast data through the standard weather entity interface.

> **Note on Configuration Flow**: This specification originally described a multi-step wizard with 4 location input methods (city selection, address geocoding, manual coordinates, and interactive map). The final implementation was simplified to a **single-step configuration form** with only **map picker and manual coordinate input** with bidirectional sync. This reduces complexity from a 6-step wizard (887 lines) to a single unified form (429 lines) - a 52% code reduction. Location coordinates are validated within Luxembourg boundaries (lat: 49.4-50.2, lon: 5.7-6.5), and reverse geocoding displays addresses for reference.

> **Note on Entity ID Regeneration**: The implementation includes an optional entity ID regeneration feature during reconfiguration. When users change the integration name, a conditional second step appears with radio buttons asking whether to keep existing entity IDs (default, preserves automations) or regenerate them to match the new name (with clear warnings about breaking automations). This provides flexibility while defaulting to the safest option.

> **Note on Enhanced Daily Forecast**: The daily forecast implementation has been enhanced to provide a more comprehensive forecast experience. When today's date matches the first forecast day, current weather data (condition, humidity, pressure, cloud coverage) is automatically merged with the forecast's high/low temperatures and wind data, providing a seamless transition from "now" to "forecast." Additionally, the forecast logic now dynamically combines detailed forecast data (days 0-4 with full weather details) with extended forecast data (days 5+) based on actual API response length, supporting up to 10-day forecasts. Date deduplication ensures no duplicate entries appear when the same date exists in both data sources.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Flexible Location Setup (Priority: P1)

A Home Assistant user wants to add MeteoLux weather for their Luxembourg home. They open Settings → Integrations → Add Integration → MeteoLux. The system presents multiple location input methods: they can type their address "12 Rue de la Gare, Luxembourg" and see it automatically geocoded to coordinates, OR select "Luxembourg" from a dropdown of 121 Luxembourg cities, OR directly enter latitude/longitude coordinates, OR drag a pin on an interactive map. All four input methods are bidirectional—changing one automatically updates the others. They provide a friendly name "Home Weather" and proceed with defaults for language (English) and update intervals.

**Why this priority**: Location setup is the foundation—without it, no weather data can be fetched. This is the entry point for every user.

**Independent Test**: Can be fully tested by completing the integration setup flow with each of the four location input methods (address, city dropdown, coordinates, map pin), verifying that all methods produce valid coordinates and that bidirectional synchronization works correctly. Delivers a configured integration instance ready to fetch weather data.

**Acceptance Scenarios**:

1. **Given** the user opens Add Integration, **When** they search for "MeteoLux" and select it, **Then** they see a configuration screen with four location input options (address field, city dropdown, lat/long fields, interactive map)
2. **Given** the user types an address "1 Place Guillaume II, Luxembourg", **When** the address is geocoded, **Then** the city dropdown, coordinate fields, and map pin automatically update to match the geocoded location
3. **Given** the user selects "Esch-sur-Alzette" from the city dropdown, **When** the selection is made, **Then** the address field, coordinate fields, and map pin automatically update to show Esch-sur-Alzette's location
4. **Given** the user enters latitude 49.8153 and longitude 6.1296, **When** the coordinates are entered, **Then** the address, city dropdown, and map pin update to the nearest matching Luxembourg location
5. **Given** the user drags the map pin to a new location, **When** the pin is moved, **Then** the address, city dropdown, and coordinate fields update to reflect the new pin position
6. **Given** the user provides a friendly name "Office", **When** setup completes, **Then** the integration instance is named "Office" in Home Assistant
7. **Given** the user leaves language and update interval fields at defaults, **When** setup completes, **Then** the integration uses English language and default update intervals (10 min current, 30 min hourly, 6 hours daily)

---

### User Story 2 - Comprehensive Current Weather Display (Priority: P1)

A Home Assistant user has configured the MeteoLux integration and opens their dashboard. They see a weather entity displaying current conditions, plus a consolidated current weather sensor with temperature as the state and comprehensive attributes including: temperature, apparent temperature, calculated comfort indices (dew point, wind chill, humidex), wind speed/gusts/direction, precipitation, snow, condition, condition text, humidity, pressure, UV index, and cloud coverage. The entities update every 10 minutes (configurable) and are fully compatible with standard Home Assistant weather cards and automations. They can view this data in Lovelace, use it in automations, and see historical trends.

**Why this priority**: Current weather is the most frequently accessed data and the primary value proposition of a weather integration. Users expect real-time conditions immediately after setup.

**Independent Test**: Can be fully tested by setting up the integration, waiting for the first data fetch, and verifying that the weather entity and consolidated current weather sensor appear with all 16 attributes populated from the MeteoLux API. Delivers immediate value by showing real-time weather conditions.

**Acceptance Scenarios**:

1. **Given** the integration is configured, **When** the first data fetch completes, **Then** a weather entity and current weather sensor appear with temperature, apparent temperature, calculated comfort indices, wind data, precipitation, condition, humidity, pressure, UV index, and cloud coverage
2. **Given** current weather data is displayed, **When** the user views it in a weather card, **Then** the card shows the weather icon, temperature, and condition text in the selected language (English/French/German/Luxembourgish)
3. **Given** the update interval is set to 10 minutes, **When** 10 minutes elapse, **Then** the entities automatically refresh with new current conditions from the MeteoLux API
4. **Given** the user creates an automation, **When** they select the current weather sensor, **Then** they can trigger actions based on any of the 16 attributes including calculated comfort indices

---

### User Story 3 - Detailed 5-Day Forecast Entities (Priority: P2)

A Home Assistant user wants detailed daily forecast data for planning their week. They enable the "5-Day Detailed Forecast" sensor entities in the integration settings. Five consolidated sensors appear (Day 0 through Day 4), each with temperature as the state and comprehensive attributes: date, high/low temperatures (actual and apparent), precipitation, wind speed/gusts/direction, condition, condition text, sunshine hours, and UV index. They use these sensors to create a custom Lovelace card showing the week ahead with all relevant weather details per day accessible via attributes.

**Why this priority**: Daily forecasts enable planning (clothing choices, outdoor activities, travel). The 5-day detailed view provides actionable data for the immediate future. This is a natural next step after current conditions.

**Independent Test**: Can be fully tested by enabling the 5-day forecast sensors, waiting for a forecast data fetch, and verifying that 5 separate sensor entities appear (Day 0–Day 4), each with high temperature as state and 12 comprehensive attributes from the MeteoLux API's `forecast.daily` array. Delivers week-ahead planning capability independently from other features.

**Acceptance Scenarios**:

1. **Given** the integration is configured, **When** the user views available entities, **Then** they see 5 daily forecast sensors (Day 0, Day 1, Day 2, Day 3, Day 4) available to enable
2. **Given** the user enables Day 0 forecast sensor, **When** forecast data fetches, **Then** the sensor shows high temperature as state and attributes: date, temperature_high, temperature_low, apparent_temperature_high, apparent_temperature_low, precipitation, wind_speed, wind_gusts, wind_direction, condition, condition_text, sunshine_hours, UV index (0-12 scale)
3. **Given** the forecast update interval is 6 hours, **When** 6 hours elapse, **Then** all 5 daily forecast sensors refresh with updated forecast data from MeteoLux API
4. **Given** the user creates a Lovelace card, **When** they add the 5-day forecast sensors, **Then** they can display a custom weekly forecast layout accessing all detailed attributes per day via sensor attributes

---

### User Story 4 - Extended 10-Day High-Level Forecast (Priority: P3)

A Home Assistant user wants a longer-term weather outlook for trip planning 1-2 weeks ahead. They enable the "10-Day Extended Forecast" sensors. Ten separate sensors appear (Day 0 through Day 9), each with high temperature as the state and basic attributes: date, high/low temperatures, and precipitation, sourced from the MeteoLux API's `data.forecast` array. While less detailed than the 5-day forecast, it gives a quick overview of temperature and rain trends for the extended period. They use this to decide whether to book outdoor activities 10 days from now.

**Why this priority**: Extended forecasts serve longer-term planning needs. While less critical than immediate forecasts, they add value for users making advance commitments (events, travel, outdoor work). Lower priority because forecast accuracy decreases with time, and fewer users need 10-day outlooks daily.

**Independent Test**: Can be fully tested by enabling the 10-day forecast sensors, waiting for data fetch, and verifying that 10 separate sensor entities appear (Day 0–Day 9), each with high temperature as state and 4 basic attributes from the `data.forecast` API field. Delivers extended planning capability independently from detailed forecasts.

**Acceptance Scenarios**:

1. **Given** the integration is configured, **When** the user views available entities, **Then** they see 10 extended forecast sensors (Day 0-Day 9) available to enable, all disabled by default
2. **Given** the user enables Day 7 extended forecast sensor, **When** data fetches, **Then** the sensor displays high temperature as state with attributes: date, temperature_high, temperature_low, precipitation
3. **Given** the forecast update interval is 6 hours, **When** 6 hours elapse, **Then** all 10 extended forecast sensors refresh with updated trend data from MeteoLux API
4. **Given** the user views Days 7–9 sensors, **When** they inspect the attributes, **Then** they see high-level forecast data extending beyond the detailed 5-day forecast

---

### User Story 5 - Hourly Forecast Entities (Priority: P2)

A Home Assistant user wants hour-by-hour weather details for today to plan activities (cycling, walking dog, outdoor meetings). They enable the "Hourly Forecast" sensors. Twenty-four separate sensors appear (Hour 0 through Hour 23), each with temperature as the state and comprehensive attributes: timestamp, temperature, apparent temperature, precipitation, wind speed/gusts/direction, condition, condition text, humidity, cloud coverage, and UV index from the MeteoLux API's `forecast.hourly` array. Hours 0-5 are enabled by default for immediate planning needs. They use these sensors to time outdoor activities when rain is least likely and temperature is most comfortable.

**Why this priority**: Hourly forecasts enable fine-grained intra-day planning. Users can see when rain will start/stop, when wind will pick up, or when temperature will drop. More granular than daily, less immediate than current conditions. Priority P2 because it serves planning needs, but current + daily forecasts already cover the basics.

**Independent Test**: Can be fully tested by enabling hourly forecast sensors, waiting for data fetch, and verifying that 24 separate sensor entities appear (Hour 0–Hour 23), each with temperature as state and 11 comprehensive attributes from the MeteoLux API's `forecast.hourly` array. Delivers hour-by-hour planning capability independently from daily forecasts.

**Acceptance Scenarios**:

1. **Given** the integration is configured, **When** the user views available entities, **Then** they see 24 hourly forecast sensors (Hour 0-Hour 23) available, with Hours 0-5 enabled by default
2. **Given** the user views Hour 0 forecast sensor, **When** data fetches, **Then** the sensor displays temperature as state with attributes: datetime, temperature, apparent_temperature, precipitation, wind_speed, wind_gusts, wind_direction, condition, condition_text, humidity, cloud_cover, uv_index
3. **Given** the hourly update interval is 30 minutes, **When** 30 minutes elapse, **Then** all 24 hourly forecast sensors refresh with updated hourly data from MeteoLux API
4. **Given** the user creates an automation, **When** they check Hour 3 forecast sensor, **Then** they can trigger actions based on predicted conditions 3 hours ahead using sensor state and attributes

---

### User Story 6 - Reconfiguration Without Data Loss (Priority: P2)

A Home Assistant user initially configured MeteoLux for "Home" using an address, English language, and default update intervals. Later, they move to a new house and want to update the location without removing and re-adding the integration. They open the integration options, select "Reconfigure," and update the address to the new home. They also change the friendly name to "New Home" and optionally check a box to regenerate entity IDs (which would break automations, so they leave it unchecked). The integration updates immediately without losing historical data or breaking existing automations and dashboards.

**Why this priority**: Reconfiguration is a quality-of-life feature that prevents users from having to delete and recreate integrations when settings change. It preserves automations, dashboard cards, and historical data. Priority P2 because while valuable, initial setup (P1) must work first, and not all users will need reconfiguration.

**Independent Test**: Can be fully tested by setting up an integration, creating an automation using its entities, then reconfiguring the location, name, language, or update intervals, and verifying that the automation still works, entity IDs remain unchanged (unless regeneration is checked), and data updates with new settings. Delivers flexibility independently from initial setup.

**Acceptance Scenarios**:

1. **Given** an existing MeteoLux integration is configured, **When** the user clicks the integration's options (three-dot menu), **Then** they see a "Reconfigure" option
2. **Given** the user selects Reconfigure, **When** the reconfiguration screen opens, **Then** all current settings are pre-populated (location, name, language, update intervals)
3. **Given** the user updates the address to a new location, **When** they save changes, **Then** the integration immediately fetches weather data for the new location without removing existing entities
4. **Given** the user changes the friendly name from "Home" to "Office", **When** they leave the "Regenerate Entity IDs" checkbox unchecked and save, **Then** entity IDs remain unchanged and existing automations continue working
5. **Given** the user checks the "Regenerate Entity IDs" checkbox and saves, **When** reconfiguration completes, **Then** entity IDs update to match the new name, and the system warns the user that automations and dashboards need manual updates
6. **Given** the user changes the language from English to French, **When** reconfiguration completes, **Then** weather condition text displays in French (e.g., "Nuageux" instead of "Cloudy")
7. **Given** the user changes current weather update interval from 10 minutes to 5 minutes, **When** reconfiguration completes, **Then** current weather data refreshes every 5 minutes

---

### User Story 7 - Multiple Locations (Priority: P3)

A Home Assistant user has a home, an office, and a vacation cabin, all in Luxembourg. They want weather data for all three locations simultaneously. They add the MeteoLux integration three times, each with a different friendly name ("Home", "Office", "Cabin") and different location coordinates. Each instance operates independently with its own entities, update intervals, and language settings. They create separate dashboard cards for each location and automations that react to weather at specific locations (e.g., "close office windows if rain at office").

**Why this priority**: Multi-location support enables users with multiple properties, remote monitoring, or comparing weather across Luxembourg. Lower priority (P3) because single-location setup (P1) must work first, and most users initially need only one location. Advanced users will appreciate this once basic functionality is solid.

**Independent Test**: Can be fully tested by adding the MeteoLux integration three times with different locations and names, verifying that each creates separate entity sets with distinct entity IDs (e.g., `weather.home`, `weather.office`, `weather.cabin`), and confirming that updates happen independently per instance. Delivers multi-site monitoring capability independently from single-location functionality.

**Acceptance Scenarios**:

1. **Given** the user has one MeteoLux integration configured for "Home", **When** they add a second MeteoLux integration, **Then** they can configure a different location with a different name ("Office")
2. **Given** two MeteoLux integrations exist ("Home" and "Office"), **When** data fetches, **Then** each integration creates separate entity sets: `weather.home`, `sensor.home_temperature`, etc. and `weather.office`, `sensor.office_temperature`, etc.
3. **Given** three MeteoLux integrations are configured with different update intervals, **When** time elapses, **Then** each integration fetches data according to its own schedule independently
4. **Given** the user creates an automation, **When** they select `sensor.office_precipitation`, **Then** the automation triggers only for rain at the office location, not home or cabin

---

### User Story 8 - Language-Specific Weather Descriptions (Priority: P3)

A Home Assistant user in Luxembourg prefers to see weather conditions in Luxembourgish, their native language. During setup, they select "Luxembourgish (lb)" from the language dropdown. The integration fetches weather data with the `langcode=lb` parameter, and all condition text displays in Luxembourgish (e.g., "Wollekeg" for "Cloudy"). They can later reconfigure to switch to French, German, or English if needed. This works across all entities—current weather, daily forecasts, and hourly forecasts.

**Why this priority**: Language support respects user preferences and improves usability for non-English speakers. Luxembourg is multilingual (Luxembourgish, French, German), so offering all four languages (including English for internationals) is important for community adoption. Priority P3 because weather data itself (P1-P2) must work first, and language is a presentation concern that can be added once core functionality is stable.

**Independent Test**: Can be fully tested by setting up integrations with each of the four supported languages (en, fr, de, lb), fetching weather data, and verifying that condition text appears in the selected language while numeric data (temperature, wind speed, etc.) remains unchanged. Delivers localization independently from core weather functionality.

**Acceptance Scenarios**:

1. **Given** the user sets up MeteoLux integration, **When** they reach the language selection step, **Then** they see a dropdown with four options: English (en), French (fr), German (de), Luxembourgish (lb)
2. **Given** the user selects Luxembourgish (lb), **When** weather data fetches, **Then** condition text displays in Luxembourgish (e.g., "Reeneg" for "Rainy", "Sonneg" for "Sunny")
3. **Given** the user later reconfigures to change language to French, **When** reconfiguration completes, **Then** condition text updates to French (e.g., "Pluvieux" for "Rainy", "Ensoleillé" for "Sunny")
4. **Given** the integration uses German language, **When** daily forecast entities display, **Then** condition descriptions show in German (e.g., "Wolkig" for "Cloudy")

---

### Edge Cases

- What happens when the user enters an address outside Luxembourg (e.g., "Paris, France")?
  - **Expected**: The system validates that geocoded coordinates fall within Luxembourg boundaries (latitude ~49.4–50.2°N, longitude ~5.7–6.5°E). If outside bounds, display an error: "Location must be within Luxembourg. Please enter a Luxembourg address or coordinates."

- What happens when the MeteoLux API is unreachable (network failure, API downtime)?
  - **Expected**: The integration marks entities as "unavailable" and logs an error. It retries with exponential backoff (2s, 4s, 8s, 16s, 30s, 60s) per the constitution's performance requirements. Once the API is reachable again, entities automatically restore with fresh data.

- What happens when the MeteoLux API returns partial data (e.g., current weather but no forecast)?
  - **Expected**: The integration updates available entities (e.g., current weather sensor) and marks unavailable entities (e.g., daily forecast sensors) as "unavailable" with a state attribute explaining missing data.

- What happens when the user drags the map pin to the edge of Luxembourg (near the border)?
  - **Expected**: If the pin is still within Luxembourg boundaries, the location updates normally. If dragged outside boundaries, the pin snaps back to the nearest in-bounds location, and a warning message appears: "Location adjusted to Luxembourg boundary."

- What happens when the user enters invalid coordinates (latitude > 90, longitude > 180)?
  - **Expected**: The coordinate input fields validate on input. Invalid values are rejected with inline error messages: "Latitude must be between -90 and 90" or "Longitude must be between -180 and 180."

- What happens when two integrations have the same friendly name?
  - **Expected**: Home Assistant automatically appends a suffix (e.g., "Home", "Home 2") to ensure unique integration instances. Entity IDs also receive unique suffixes to prevent collisions.

- What happens when the user selects update intervals that are too aggressive (e.g., 1-minute current weather)?
  - **Expected**: The system allows 1-minute intervals (within the constitution's ≥1 minute constraint) but warns the user: "Very frequent updates may increase API load. Default is 10 minutes." The user can proceed if desired.

- What happens when historical weather data is unavailable from the API?
  - **Expected**: Historical/climatology entities (if implemented) show "unavailable" state. Core current and forecast entities remain functional as they don't depend on historical data.

- What happens when the user enables all entities (current, hourly, 5-day, 10-day) with aggressive update intervals?
  - **Expected**: All entities function independently according to their update schedules. Memory usage should stay under 50MB per location (per constitution's performance targets). If memory exceeds limits during testing, a warning is logged.

- What happens when the city dropdown fails to load from the MeteoLux bookmarks API?
  - **Expected**: The dropdown shows a cached list of 121 Luxembourg cities (bundled with the integration as fallback). If both API and cache fail, the dropdown displays an error message, but address, coordinate, and map input methods remain fully functional.

## Requirements *(mandatory)*

### Functional Requirements

**Location Configuration:**

- **FR-001**: System MUST provide four location input methods: address text field, city dropdown, latitude/longitude coordinate fields, and interactive map with draggable pin
- **FR-002**: System MUST geocode addresses to latitude/longitude coordinates using a geocoding service (OpenStreetMap Nominatim is recommended based on existing implementation)
- **FR-003**: System MUST fetch the list of Luxembourg cities from the MeteoLux bookmarks API (`/api/v1/metapp/bookmarks`) and populate the city dropdown with 121 cities
- **FR-004**: System MUST implement bidirectional location synchronization: updating any one input method (address, city, coordinates, map pin) MUST automatically update the other three to match
- **FR-005**: System MUST validate that all location coordinates fall within Luxembourg boundaries (approximate lat: 49.4–50.2°N, lon: 5.7–6.5°E) and reject locations outside this region with a clear error message
- **FR-006**: Users MUST be able to specify a friendly name for each integration instance (e.g., "Home", "Office") that becomes the integration's display name and entity ID prefix

**Weather Data Fetching:**

- **FR-007**: System MUST fetch current weather data from the MeteoLux API endpoint (`/metapp/weather`) using the configured location coordinates or city ID
- **FR-008**: System MUST support language parameter selection (English, French, German, Luxembourgish) and pass the selected `langcode` (en, fr, de, lb) to the MeteoLux API
- **FR-009**: System MUST allow users to configure three independent update intervals: current conditions (1-60 minutes, default 10), hourly forecast (5-120 minutes, default 30), and daily forecast (1-24 hours, default 6)
- **FR-010**: System MUST use the coordinator pattern for API requests to prevent redundant polling and ensure entities share data efficiently
- **FR-011**: System MUST implement exponential backoff for API failures (2s, 4s, 8s, 16s, 30s, 60s) before marking entities unavailable

**Current Weather Entities:**

- **FR-012**: System MUST create a primary weather entity exposing current conditions: temperature, feels-like temperature (humidex), condition, humidity, wind speed, wind direction, precipitation, snow, and weather icon
- **FR-012a**: System MUST create a consolidated current weather sensor with temperature as state and 16 comprehensive attributes: temperature, apparent_temperature, dew_point (calculated via Magnus formula), wind_chill (calculated when applicable), humidex (calculated), wind_speed, wind_gusts, wind_direction (translated), precipitation, snow, condition, condition_text, humidity, pressure, uv_index, cloud_cover
- **FR-013**: Weather entity MUST be compatible with Home Assistant's standard weather entity platform and render correctly in native weather cards
- **FR-014**: System MUST map MeteoLux icon IDs (integers) to Home Assistant condition states (sunny, cloudy, rainy, snowy, etc.) according to standard mappings
- **FR-015**: System MUST update current weather entities according to the configured current conditions update interval

**5-Day Detailed Forecast Entities:**

- **FR-016**: System MUST create five consolidated daily forecast sensor entities (Day 0, Day 1, Day 2, Day 3, Day 4) using data from the MeteoLux API's `forecast.daily` array, each with high temperature as state
- **FR-017**: Each daily forecast sensor MUST expose 12 comprehensive attributes: date, temperature_high, temperature_low, apparent_temperature_high, apparent_temperature_low, precipitation, wind_speed, wind_gusts, wind_direction (translated), condition, condition_text, sunshine_hours, uv_index (0-12 scale)
- **FR-018**: Daily forecast entities MUST be disabled by default (except Days 0-1) to reduce entity clutter, with users able to enable them via the UI
- **FR-019**: System MUST update daily forecast entities according to the configured daily forecast update interval

**10-Day Extended Forecast Entities:**

- **FR-020**: System MUST create 10 separate extended forecast sensor entities (Day 0, Day 1, ..., Day 9) using data from the MeteoLux API's `data.forecast` array, each with high temperature as state
- **FR-021**: Each 10-day forecast sensor MUST expose 4 basic attributes: date, temperature_high, temperature_low, precipitation
- **FR-022**: All 10-day forecast sensors MUST be disabled by default, with users able to enable them via the UI
- **FR-023**: System MUST update the 10-day forecast sensors according to the configured daily forecast update interval

**Hourly Forecast Entities:**

- **FR-024**: System MUST create 24 separate hourly forecast sensor entities (Hour 0, Hour 1, ..., Hour 23) using data from the MeteoLux API's `forecast.hourly` array, each with temperature as state
- **FR-025**: Each hourly forecast sensor MUST expose 11 comprehensive attributes: datetime, temperature, apparent_temperature, precipitation, wind_speed, wind_gusts, wind_direction (translated), condition, condition_text, humidity, cloud_cover, uv_index
- **FR-026**: Hourly forecast sensors MUST be disabled by default (except Hours 0-5) to reduce entity clutter, with users able to enable them via the UI
- **FR-027**: System MUST update hourly forecast entities according to the configured hourly forecast update interval

**Reconfiguration:**

- **FR-028**: Users MUST be able to reconfigure existing integration instances without removing and re-adding them
- **FR-029**: Reconfiguration MUST allow updating: location (address, city, coordinates, map), friendly name, language, and all three update intervals
- **FR-030**: Reconfiguration MUST preserve entity IDs by default to avoid breaking automations and dashboards
- **FR-031**: Reconfiguration MUST offer an optional "Regenerate Entity IDs" checkbox that, when checked, updates entity IDs to match the new friendly name and warns the user about automation/dashboard impacts
- **FR-032**: System MUST immediately apply configuration changes and fetch fresh data using the new settings without requiring a Home Assistant restart

**Multiple Instances:**

- **FR-033**: System MUST support multiple integration instances, each with independent configuration (location, name, language, update intervals)
- **FR-034**: Each integration instance MUST create separate, uniquely-named entity sets using the friendly name as the entity ID prefix (e.g., `weather.home`, `sensor.home_current_weather`), totaling ~43 entities per instance (1 weather entity + 42 sensors)
- **FR-035**: Multiple instances MUST operate independently: data fetches, update schedules, and configuration changes for one instance MUST NOT affect other instances

**HACS and Home Assistant Compliance:**

- **FR-036**: Integration MUST pass Home Assistant's `hassfest` validation tool with no errors
- **FR-037**: Integration MUST include a valid `manifest.json` with required fields: domain, name, version, documentation, issue_tracker, codeowners, config_flow, iot_class
- **FR-038**: Integration MUST include a `hacs.json` file declaring HACS compatibility
- **FR-039**: Integration MUST use Home Assistant's config flow (UI-based configuration) rather than YAML configuration
- **FR-040**: Integration MUST follow Home Assistant's entity naming conventions (snake_case for entity IDs, Title Case for friendly names)
- **FR-041**: Integration MUST use Home Assistant's standard unit of measurement constants and device classes where applicable

**Documentation and Community:**

- **FR-042**: Integration MUST include comprehensive README.md documentation covering: features, installation (HACS and manual), configuration steps (with screenshots if possible), entity descriptions, troubleshooting, and contribution guidelines
- **FR-043**: Documentation MUST include donation information (BuyMeACoffee or similar) with a simple link for users to support development
- **FR-044**: Documentation MUST explain how to use donated funds and disclose any commission structures to ensure transparency

**CI/CD and Release Management:**

- **FR-045**: Integration repository MUST include GitHub Actions workflows for automated testing, linting, and validation (hassfest, HACS validation)
- **FR-046**: Integration MUST use semantic versioning (MAJOR.MINOR.PATCH) for releases and tags
- **FR-047**: System MUST automate release creation with changelogs when new tags are pushed to the repository
- **FR-048**: Integration MUST be submitted to HACS for inclusion in the default repository list following HACS submission guidelines

### Key Entities

- **Integration Instance**: Represents a single configured MeteoLux weather source. Attributes: friendly name, location (lat/lon or city ID), language (en/fr/de/lb), three update intervals (current, hourly, daily). Each instance creates ~43 entities: 1 weather entity + 42 sensors (1 current + 24 hourly + 5 daily + 10 extended + 2 special). Multiple instances can coexist independently.

- **Weather Entity**: The primary Home Assistant weather entity showing current conditions and forecast. Attributes: temperature, feels-like, condition, humidity, wind speed, wind direction, precipitation, snow, icon. Enhanced forecasts include wind gusts, humidity, cloud coverage, and UV index. Mapped to Home Assistant's weather platform. One per integration instance.

- **Current Weather Sensor**: Single consolidated sensor with temperature as state and 16 comprehensive attributes: temperature, apparent_temperature, dew_point (calculated via Magnus formula), wind_chill (calculated when temp < 10°C), humidex (calculated Canadian humidity index), wind_speed, wind_gusts, wind_direction (translated to selected language), precipitation, snow, condition, condition_text, humidity, pressure, uv_index, cloud_cover. Enabled by default.

- **Hourly Forecast Sensors (24 sensors)**: Twenty-four sensors (Hour 0–Hour 23) representing hourly forecasts. Each has temperature as state and 11 attributes: datetime, temperature, apparent_temperature, precipitation, wind_speed, wind_gusts, wind_direction (translated), condition, condition_text, humidity, cloud_cover, uv_index. Sourced from `forecast.hourly` API array. Hours 0-5 enabled by default, Hours 6-23 disabled by default.

- **Daily Forecast Sensors (5-Day Detailed)**: Five consolidated sensors (Day 0–Day 4) representing detailed daily forecasts. Each has high temperature as state and 12 attributes: date, temperature_high, temperature_low, apparent_temperature_high, apparent_temperature_low, precipitation, wind_speed, wind_gusts, wind_direction (translated), condition, condition_text, sunshine_hours, uv_index. Sourced from `forecast.daily` API array. Days 0-1 enabled by default, Days 2-4 disabled by default.

- **10-Day Extended Forecast Sensors (10 sensors)**: Ten sensors (Day 0–Day 9) providing extended outlook. Each has high temperature as state and 4 basic attributes: date, temperature_high, temperature_low, precipitation. Sourced from `data.forecast` API array. All disabled by default.

- **Special Sensors (2 sensors)**: Ephemeris sensor (sun/moon data) and Location sensor (city information). Both enabled by default.

- **Location**: Conceptual entity representing a geographic point in Luxembourg. Attributes: latitude, longitude, address (optional), city name (optional). Used during configuration to define where weather data is fetched from. Validated to ensure it's within Luxembourg boundaries.

- **Language Setting**: Configuration attribute defining the language for weather condition text and wind direction translations. Values: en (English), fr (French), de (German), lb (Luxembourgish). Passed as `langcode` parameter to MeteoLux API. Affects all text descriptions but not numeric data.

- **Update Interval**: Configuration attribute defining how frequently data is fetched. Three independent intervals: current conditions (1-60 min), hourly forecast (5-120 min), daily forecast (1-24 hours). Controls coordinator refresh rate per data type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete integration setup (location selection, name, language, intervals) in under 3 minutes using any of the four location input methods
- **SC-002**: Integration fetches and displays current weather data within 10 seconds of setup completion
- **SC-003**: Weather entities update automatically according to configured intervals with 95% reliability (no missed updates due to integration bugs)
- **SC-004**: Users can reconfigure location, name, language, or intervals in under 2 minutes without losing existing automations (unless entity ID regeneration is explicitly chosen)
- **SC-005**: Integration supports at least 5 simultaneous instances with different locations, each operating independently without performance degradation
- **SC-006**: Integration memory usage remains under 50MB per instance during normal operation (per constitution's performance targets)
- **SC-007**: Integration startup (load time on Home Assistant restart) completes within 5 seconds per instance
- **SC-008**: API requests complete within 10 seconds including retries, with 95th percentile response time under 2 seconds for current conditions
- **SC-009**: Integration passes all Home Assistant hassfest validation checks and HACS validation checks with zero errors
- **SC-010**: Documentation (README) enables 90% of users to successfully install and configure the integration without external support
- **SC-011**: Integration achieves at least 80% test coverage for core logic (coordinator, API client, data parsing) per constitution's test requirements
- **SC-012**: Bidirectional location synchronization completes in under 1 second when any input method is updated (address, city, coordinates, map)
- **SC-013**: Integration correctly handles MeteoLux API failures (unreachable, partial data, malformed responses) without crashing, marking entities unavailable and retrying with exponential backoff
- **SC-014**: Users can successfully submit the integration to HACS and have it accepted into the default repository list within one submission cycle (no rejections due to technical non-compliance)

## Assumptions

1. **Geocoding Service**: The integration will use OpenStreetMap Nominatim for address geocoding, as it's free, reliable, and already used in the existing implementation. No API key required.

2. **Luxembourg Boundary Validation**: Approximate boundaries (lat: 49.4–50.2°N, lon: 5.7–6.5°E) are sufficient for validation. Precise border polygons are not required; a bounding box check will catch most out-of-bounds errors.

3. **MeteoLux API Stability**: The MeteoLux API (`https://metapi.ana.lu/api/v1`) is assumed to be publicly accessible, free to use under CC0 license (as documented), and reasonably stable. The integration will handle transient failures gracefully but assumes the API won't fundamentally change structure during development.

4. **Entity Defaults**: Most forecast entities will be disabled by default to avoid overwhelming new users with dozens of entities. Enabled by default: current weather sensor, ephemeris sensor, location sensor, hourly forecast Hours 0-5, and daily forecast Days 0-1. Disabled by default: hourly Hours 6-23, daily Days 2-4, and all 10-day extended forecast sensors. This provides immediate value (~10 enabled entities) while keeping entity count manageable.

5. **Update Interval Defaults**: Default values (10 min current, 30 min hourly, 6 hours daily) are based on typical weather integration patterns (AccuWeather, OpenWeatherMap) and balance freshness with API courtesy. Users can adjust based on their needs.

6. **Language Support**: All four languages (en, fr, de, lb) are fully supported by the MeteoLux API. Condition text translations are provided by the API, not the integration.

7. **Map Component**: Home Assistant's Lovelace UI supports interactive maps via the `map` card or custom integrations. The configuration flow will use Home Assistant's built-in map selector (if available) or a simple coordinate input with map preview.

8. **HACS Submission**: The integration will meet HACS technical requirements (manifest.json, hacs.json, README, releases, semantic versioning). Community acceptance depends on code quality, documentation, and usefulness, which we'll ensure via thorough testing and clear docs.

9. **Donation Method**: BuyMeACoffee is chosen as the donation platform due to its simplicity (single link, no complex setup), low fees (~5%), and ease of fund withdrawal. Alternative methods (PayPal, Ko-fi, Liberapay) can be added if requested by the community.

10. **CI/CD Automation**: GitHub Actions will be used for CI/CD due to its tight GitHub integration, free tier for public repositories, and widespread adoption in the Home Assistant community. Workflows will include linting (ruff), type checking (mypy), hassfest validation, and HACS validation.

11. **Home Assistant Version Support**: The integration will target the current and previous major Home Assistant versions (per constitution's maintenance standards), ensuring compatibility with at least 2 releases back (e.g., if current is 2024.11, support 2024.10 and 2024.11).

12. **Test Coverage**: Integration tests will cover config flow, coordinator updates, entity lifecycle, and API contract validation. Unit tests will cover data parsing and validation logic. Target: 80%+ coverage per constitution's test-first development principle.

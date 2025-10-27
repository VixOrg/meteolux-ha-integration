# Tasks: Enhanced MeteoLux Weather Entities with Multi-Forecast Support

**Status**: ✅ **COMPLETED** - Implementation finished with consolidated entity structure (2025-01-05)

**Implementation Notes**: The feature was implemented using a consolidated entity approach that differs from the original task breakdown but fulfills all functional requirements and user stories. Key changes:
- Consolidated current weather into 1 sensor with 16 attributes (including calculated comfort indices: dew point, wind chill, humidex)
- Consolidated hourly forecasts into 24 sensors (one per hour with 11 attributes each), Hours 0-5 enabled by default
- Consolidated 5-day forecasts into 5 sensors (one per day with 12 attributes each), Days 0-1 enabled by default
- Created 10-day extended forecast as 10 separate sensors (one per day with 4 attributes each), all disabled by default
- Enhanced WeatherEntity forecasts with additional fields (wind gusts, humidity, cloud coverage, UV index)
- **Total**: 43 entities per instance (1 weather + 42 sensors) vs originally planned 189+ entities (77% reduction)

**Input**: Design documents from `specs/001-enhanced-weather-entities/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Integration tests created in `tests/test_sensor.py` and `tests/test_weather.py` with comprehensive coverage of consolidated entity structure.

**Organization**: Tasks below represent the original planned implementation. The actual implementation consolidated entities for better performance and user experience while maintaining all functional requirements.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Home Assistant integration**: `custom_components/meteolux/`
- Paths shown below use HA custom integration structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency verification

- [ ] T001 Verify Home Assistant Core 2024.10+ is available as dependency
- [ ] T002 Verify no external PyPI dependencies are added to manifest.json requirements field
- [ ] T003 [P] Update manifest.json version to 0.1.0 for this initial release
- [ ] T004 [P] Create GitHub Actions workflow .github/workflows/validate.yml for ruff/mypy/hassfest validation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create helper function validate_luxembourg_coordinates(lat, lon) in custom_components/meteolux/const.py
- [ ] T006 Create helper function parse_wind_speed(wind_str) in custom_components/meteolux/const.py to extract numeric value from "10 km/h" or "5-15 km/h" format
- [ ] T007 Create helper function map_icon_to_condition(icon_id) in custom_components/meteolux/const.py using existing CONDITION_MAP
- [ ] T008 [P] Create base class MeteoLuxSensorEntity in custom_components/meteolux/sensor.py with common entity attributes (coordinator, entry, device_info)
- [ ] T009 [P] Create base coordinator class MeteoLuxDataUpdateCoordinator in custom_components/meteolux/coordinator.py with exponential backoff (2s, 4s, 8s, 16s, 30s, 60s)
- [ ] T010 Implement CurrentWeatherCoordinator(MeteoLuxDataUpdateCoordinator) in custom_components/meteolux/coordinator.py with async_update_data() fetching from /metapp/weather
- [ ] T011 [P] Implement HourlyForecastCoordinator(MeteoLuxDataUpdateCoordinator) in custom_components/meteolux/coordinator.py
- [ ] T012 [P] Implement DailyForecastCoordinator(MeteoLuxDataUpdateCoordinator) in custom_components/meteolux/coordinator.py
- [ ] T013 Update async_setup_entry() in custom_components/meteolux/__init__.py to initialize all three coordinators with independent update intervals from config entry
- [ ] T014 Update async_unload_entry() in custom_components/meteolux/__init__.py to properly clean up all three coordinators

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Flexible Location Setup (Priority: P1) 🎯 MVP

**Goal**: Enable users to configure MeteoLux integration using 4 location input methods (address, city, coordinates, map) with bidirectional synchronization

**Independent Test**: Complete integration setup with each location method (address, city, coordinates, map), verify bidirectional sync works, confirm Luxembourg boundary validation rejects locations outside bounds

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create geocode_address(address) helper in custom_components/meteolux/config_flow.py using Nominatim API (https://nominatim.openstreetmap.org/search)
- [ ] T016 [P] [US1] Create reverse_geocode(lat, lon) helper in custom_components/meteolux/config_flow.py using Nominatim API (https://nominatim.openstreetmap.org/reverse)
- [ ] T017 [P] [US1] Create fetch_luxembourg_cities() helper in custom_components/meteolux/config_flow.py to call /api/v1/metapp/bookmarks and return city list
- [ ] T018 [P] [US1] Create LUXEMBOURG_CITIES_CACHE as fallback list in custom_components/meteolux/const.py with 121 cities (copied from API response for offline use)
- [ ] T019 [US1] Implement async_step_user() in custom_components/meteolux/config_flow.py with data schema for address, city_id, latitude, longitude, name, language, update intervals
- [ ] T020 [US1] Implement bidirectional sync logic in async_step_user(): when address changes, geocode → update lat/lon/city; when city changes, update address/lat/lon; when coordinates change, reverse geocode → update address/city
- [ ] T021 [US1] Add Luxembourg boundary validation in async_step_user() using validate_luxembourg_coordinates(), show error "Location must be within Luxembourg" if outside bounds
- [ ] T022 [US1] Implement map selector integration in async_step_user() using HA's built-in map selector (vol.Schema with selector.LocationSelector if available, otherwise coordinates-only)
- [ ] T023 [US1] Add language dropdown in async_step_user() with options: English (en), French (fr), German (de), Luxembourgish (lb), default to English
- [ ] T024 [US1] Add update interval inputs in async_step_user(): current (1-60 min, default 10), hourly (5-120 min, default 30), daily (1-24 hr, default 6)
- [ ] T025 [US1] Validate update intervals in async_step_user() per FR-009 constraints, show errors if out of range
- [ ] T026 [US1] Implement async_create_entry() in async_step_user() to save config with all location data, name, language, intervals
- [ ] T027 [US1] Update strings.json with UI strings for config flow steps (location methods, language options, interval labels)
- [ ] T028 [US1] Update translations/en.json with English translations for all config flow strings

**Checkpoint**: At this point, User Story 1 should be fully functional - users can set up integration with any location method and bidirectional sync works

---

## Phase 4: User Story 2 - Comprehensive Current Weather Display (Priority: P1) 🎯 MVP

**Goal**: Display current weather conditions (temperature, feels-like, condition, wind, precipitation, snow) in a weather entity and sensor entities, updating every 10 minutes (configurable)

**Independent Test**: Set up integration, wait for first data fetch, verify weather entity and current sensors appear with all attributes populated from MeteoLux API, confirm updates happen at configured interval

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement parse_current_weather(api_data) in custom_components/meteolux/coordinator.py using Basic + Enriched pattern (temperature, condition, wind always; humidex, gusts, snow optional)
- [ ] T030 [P] [US2] Create MeteoLuxWeather entity class in custom_components/meteolux/weather.py extending WeatherEntity with properties: temperature, apparent_temperature, wind_speed, wind_bearing, condition, forecast
- [ ] T031 [US2] Implement native_temperature property in MeteoLuxWeather using CurrentWeatherCoordinator.data
- [ ] T032 [US2] Implement native_apparent_temperature property in MeteoLuxWeather using humidex from API (nullable if not available)
- [ ] T033 [US2] Implement native_wind_speed property in MeteoLuxWeather using parse_wind_speed() helper
- [ ] T034 [US2] Implement native_wind_bearing property in MeteoLuxWeather converting wind direction (N, NE, E, etc.) to degrees (N=0°, E=90°, S=180°, W=270°)
- [ ] T035 [US2] Implement condition property in MeteoLuxWeather using map_icon_to_condition() helper
- [ ] T036 [US2] Implement forecast property in MeteoLuxWeather as empty list (forecast data comes from DailyForecastCoordinator in US3)
- [ ] T037 [US2] Update async_setup_entry() in custom_components/meteolux/weather.py to add MeteoLuxWeather entity using CurrentWeatherCoordinator
- [ ] T038 [P] [US2] Create MeteoLuxTemperatureSensor in custom_components/meteolux/sensor.py extending MeteoLuxSensorEntity, entity_registry_enabled_default=True
- [ ] T039 [P] [US2] Create MeteoLuxApparentTemperatureSensor in custom_components/meteolux/sensor.py, entity_registry_enabled_default=True
- [ ] T040 [P] [US2] Create MeteoLuxWindSpeedSensor in custom_components/meteolux/sensor.py, entity_registry_enabled_default=True
- [ ] T041 [P] [US2] Create MeteoLuxWindGustsSensor in custom_components/meteolux/sensor.py, entity_registry_enabled_default=False (enriched data)
- [ ] T042 [P] [US2] Create MeteoLuxWindDirectionSensor in custom_components/meteolux/sensor.py, entity_registry_enabled_default=False
- [ ] T043 [P] [US2] Create MeteoLuxPrecipitationSensor in custom_components/meteolux/sensor.py, entity_registry_enabled_default=True, default to 0 if rain field missing
- [ ] T044 [P] [US2] Create MeteoLuxSnowSensor in custom_components/meteolux/sensor.py, entity_registry_enabled_default=False (enriched data)
- [ ] T045 [P] [US2] Create MeteoLuxConditionSensor in custom_components/meteolux/sensor.py returning HA condition string, entity_registry_enabled_default=True
- [ ] T046 [P] [US2] Create MeteoLuxConditionTextSensor in custom_components/meteolux/sensor.py returning localized text from API icon.name, entity_registry_enabled_default=False
- [ ] T047 [US2] Update async_setup_entry() in custom_components/meteolux/sensor.py to add all 9 current weather sensors using CurrentWeatherCoordinator

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - MVP is complete (setup + current weather)

---

## Phase 5: User Story 3 - Detailed 5-Day Forecast Entities (Priority: P2)

**Goal**: Provide 5 daily forecast sensors (Day 0-4) with detailed data: min/max temp, condition, precipitation, wind, sunshine, UV index

**Independent Test**: Enable Day 0-4 forecast sensors, wait for data fetch, verify each sensor shows all detailed attributes from forecast.daily API array, confirm updates at configured interval

### Implementation for User Story 3

- [ ] T048 [US3] Implement parse_daily_forecast(api_data) in custom_components/meteolux/coordinator.py extracting forecast.daily array with Basic + Enriched pattern
- [ ] T049 [US3] Update DailyForecastCoordinator to call parse_daily_forecast() and store array of 5 daily entries
- [ ] T050 [US3] Update MeteoLuxWeather.forecast property to return forecast data from DailyForecastCoordinator (for HA weather card compatibility)
- [ ] T051 [P] [US3] Create MeteoLuxDailyForecastSensor base class in custom_components/meteolux/sensor.py with day parameter (0-4)
- [ ] T052 [US3] Implement MeteoLuxTemperatureHighSensor(MeteoLuxDailyForecastSensor) for Day 0-4 in custom_components/meteolux/sensor.py, Day 0 enabled by default, Days 1-4 disabled
- [ ] T053 [US3] Implement MeteoLuxTemperatureLowSensor(MeteoLuxDailyForecastSensor) for Day 0-4 in custom_components/meteolux/sensor.py, Day 0 enabled, Days 1-4 disabled
- [ ] T054 [US3] Implement MeteoLuxPrecipitationForecastSensor(MeteoLuxDailyForecastSensor) for Day 0-4 in custom_components/meteolux/sensor.py, Day 0 enabled, Days 1-4 disabled
- [ ] T055 [US3] Add state attributes to daily forecast sensors: date, condition, condition_text, wind_speed, wind_direction, sunshine (hours), uv_index (0-12 scale, enriched)
- [ ] T056 [US3] Update async_setup_entry() in custom_components/meteolux/sensor.py to add 15 daily forecast sensors (3 per day × 5 days) using DailyForecastCoordinator

**Checkpoint**: User Stories 1, 2, AND 3 now work independently - detailed 5-day forecast available alongside current weather

---

## Phase 6: User Story 5 - Hourly Forecast Entities (Priority: P2)

**Goal**: Provide hourly forecast sensor with array of 24-48 hourly entries (timestamp, temperature, condition, precipitation, wind, snow)

**Independent Test**: Enable hourly forecast sensor, wait for data fetch, verify sensor displays hourly array with all attributes from forecast.hourly API array, confirm updates at configured interval

### Implementation for User Story 5

- [ ] T057 [US5] Implement parse_hourly_forecast(api_data) in custom_components/meteolux/coordinator.py extracting forecast.hourly array with Basic + Enriched pattern
- [ ] T058 [US5] Update HourlyForecastCoordinator to call parse_hourly_forecast() and store array of hourly entries
- [ ] T059 [US5] Create MeteoLuxHourlyForecastSensor in custom_components/meteolux/sensor.py with state = number of hours in forecast, entity_registry_enabled_default=False
- [ ] T060 [US5] Add state attributes to hourly forecast sensor: forecast array with each hour having datetime, temperature, condition, condition_text, precipitation, wind_speed, wind_direction, snow (enriched)
- [ ] T061 [US5] Update async_setup_entry() in custom_components/meteolux/sensor.py to add hourly forecast sensor using HourlyForecastCoordinator

**Checkpoint**: User Stories 1, 2, 3, AND 5 now work independently - hourly forecast available for intra-day planning

---

## Phase 7: User Story 6 - Reconfiguration Without Data Loss (Priority: P2)

**Goal**: Allow users to reconfigure integration settings (location, name, language, intervals) without removing/re-adding, with optional entity ID regeneration

**Independent Test**: Set up integration, create automation using entities, reconfigure location/name/language/intervals, verify automation still works (unless ID regeneration checked), confirm data updates with new settings

### Implementation for User Story 6

- [ ] T062 [US6] Implement async_step_reconfigure() in custom_components/meteolux/config_flow.py to handle reconfiguration flow
- [ ] T063 [US6] Pre-populate reconfigure form with current config entry data (location, name, language, intervals) in async_step_reconfigure()
- [ ] T064 [US6] Add "Regenerate Entity IDs" checkbox in reconfigure form with warning: "This will break existing automations and dashboards. Continue?"
- [ ] T065 [US6] Implement reconfigure save logic in async_step_reconfigure(): update config entry data, reload integration if needed
- [ ] T066 [US6] If regenerate_entity_ids=False, preserve existing entity unique_id values in entity registry
- [ ] T067 [US6] If regenerate_entity_ids=True, update entity unique_id to match new name, trigger HA entity registry update (will create new entity IDs)
- [ ] T068 [US6] Update coordinators with new update intervals after reconfiguration (update_interval property)
- [ ] T069 [US6] Trigger immediate coordinator refresh after reconfiguration to fetch data with new settings (language, location)

**Checkpoint**: User Stories 1-3, 5-6 now work independently - reconfiguration preserves automations by default

---

## Phase 8: User Story 4 - Extended 10-Day High-Level Forecast (Priority: P3)

**Goal**: Provide 10-day forecast trend sensor with min/max temp and precipitation per day from data.forecast API array

**Independent Test**: Enable 10-day forecast sensor, wait for data fetch, verify sensor displays 10-day array with min/max temp and precipitation from data.forecast API field

### Implementation for User Story 4

- [ ] T070 [US4] Implement parse_10day_forecast(api_data) in custom_components/meteolux/coordinator.py extracting data.forecast array
- [ ] T071 [US4] Update DailyForecastCoordinator to also call parse_10day_forecast() and store 10-day trend data
- [ ] T072 [US4] Create MeteoLux10DayForecastSensor in custom_components/meteolux/sensor.py with state = 10, entity_registry_enabled_default=False
- [ ] T073 [US4] Add state attributes to 10-day sensor: forecast array with each day having date, min_temp, max_temp, precipitation
- [ ] T074 [US4] Update async_setup_entry() in custom_components/meteolux/sensor.py to add 10-day forecast sensor using DailyForecastCoordinator

**Checkpoint**: User Stories 1-6 now work - extended 10-day forecast available for long-term planning

---

## Phase 9: User Story 7 - Multiple Locations (Priority: P3)

**Goal**: Support multiple integration instances with different locations, names, and settings, each creating independent entity sets

**Independent Test**: Add integration 3 times with different locations/names (Home, Office, Cabin), verify each creates separate entity sets (weather.home, weather.office, weather.cabin), confirm updates happen independently per instance

### Implementation for User Story 7

- [ ] T075 [US7] Verify async_setup_entry() in custom_components/meteolux/__init__.py supports multiple config entries by using entry_id as unique key for coordinators
- [ ] T076 [US7] Verify all entity unique_id values include entry_id to ensure uniqueness across multiple instances
- [ ] T077 [US7] Verify entity_id generation uses entry.data[CONF_NAME] as prefix (e.g., "home", "office") to create distinct entity IDs
- [ ] T078 [US7] Test adding integration multiple times with same name - verify HA appends suffix ("Home 2") automatically to ensure unique titles
- [ ] T079 [US7] Test that coordinators for different instances run on independent schedules based on their own update_interval settings

**Checkpoint**: All user stories 1-7 now work - multi-location support enabled for advanced users

---

## Phase 10: User Story 8 - Language-Specific Weather Descriptions (Priority: P3)

**Goal**: Fetch and display weather condition text in user's selected language (en/fr/de/lb) from MeteoLux API langcode parameter

**Independent Test**: Set up integrations with each language (en, fr, de, lb), verify condition text appears in selected language while numeric data (temp, wind) remains unchanged

### Implementation for User Story 8

- [ ] T080 [US8] Verify coordinators pass language from entry.data[CONF_LANGUAGE] to MeteoLux API as langcode query parameter
- [ ] T081 [US8] Verify MeteoLuxConditionTextSensor displays icon.name from API response (localized by API based on langcode)
- [ ] T082 [US8] Verify MeteoLuxWeather entity displays localized condition text in weather card
- [ ] T083 [US8] Update wind direction translation logic to use WIND_DIRECTION_MAP from const.py based on selected language (API returns French abbreviations, map to en/de/lb equivalents)
- [ ] T084 [US8] Test each language (en, fr, de, lb) to verify condition text localizes correctly while temperature, wind speed, precipitation remain numeric

**Checkpoint**: All 8 user stories now work independently - full feature set complete including multi-language support

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T085 [P] Update README.md with comprehensive documentation: features, installation (HACS + manual), config flow screenshots, entity descriptions, troubleshooting, contribution guidelines
- [ ] T086 [P] Add BuyMeACoffee donation link to README.md with simple donation button/link and explanation of fund usage (zero commission recommendation: GitHub Sponsors or Ko-fi)
- [ ] T087 [P] Update info.md for HACS integration card display with feature highlights and screenshot
- [ ] T088 [P] Create CHANGELOG.md documenting all features in v0.1.0 (initial release: 189 sensors, 4 location methods, multi-language, reconfigure, etc.)
- [ ] T089 Verify manifest.json has correct fields for HACS submission: domain, name, version, documentation (GitHub URL), issue_tracker (GitHub issues URL), codeowners, config_flow, iot_class (cloud_polling)
- [ ] T090 Verify hacs.json has correct fields: name, render_readme=true, homeassistant (min version 2024.10.0)
- [ ] T091 [P] Create .github/workflows/test.yml for pytest with coverage reporting (target 80%+ for coordinators, config flow, entities)
- [ ] T092 [P] Create .github/workflows/release.yml for automated releases on tag push with changelog generation
- [ ] T093 Run hassfest validation locally: `hassfest validate custom_components/meteolux/` and fix any errors
- [ ] T094 Run HACS validation locally (if HACS CLI available) and fix any errors
- [ ] T095 [P] Add performance monitoring: log warnings if coordinator update takes >10 seconds or memory exceeds 50MB
- [ ] T096 [P] Add security hardening: validate all user inputs (address length <500 chars, coordinates in valid ranges, intervals in allowed ranges)
- [ ] T097 Test integration with Home Assistant 2024.10 and 2024.11 (current and previous major versions per constitution maintenance standards)
- [ ] T098 Create GitHub release v0.1.0 with release notes highlighting initial release features
- [ ] T099 Submit integration to HACS default repository list following https://www.hacs.xyz/docs/publish/start/ guidelines
- [ ] T100 Monitor GitHub issues for bugs reported by community users and create follow-up tasks as needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (but logically follows US1 for complete setup → data flow)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Integrates with US2 (weather entity forecast property) but independently testable
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Fully independent from other stories
- **User Story 6 (P2)**: Can start after Foundational (Phase 2) - Extends US1 config flow but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent from other stories
- **User Story 7 (P3)**: Can start after Foundational (Phase 2) - Tests multi-instance support built into all stories
- **User Story 8 (P3)**: Can start after Foundational (Phase 2) - Validates language support built into all stories

### Within Each User Story

- Setup tasks [P] can run in parallel (different files)
- Implementation tasks with dependencies run sequentially
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 Setup**: All tasks marked [P] can run in parallel (T003, T004)
- **Phase 2 Foundational**: Tasks T008-T012 marked [P] can run in parallel (different files)
- **Phase 3 US1**: Tasks T015-T018 marked [P] can run in parallel (different helpers)
- **Phase 4 US2**: Tasks T029-T030, T038-T046 marked [P] can run in parallel (different sensors)
- **Phase 5 US3**: Task T051 can run in parallel with T052-T054 (base class + sensor implementations)
- **Phase 11 Polish**: Tasks T085-T088, T091-T092, T095-T096 marked [P] can run in parallel (documentation, CI/CD, hardening)

---

## Parallel Example: User Story 2

```bash
# Launch all sensor entity implementations in parallel:
Task T038: "Create MeteoLuxTemperatureSensor in custom_components/meteolux/sensor.py"
Task T039: "Create MeteoLuxApparentTemperatureSensor in custom_components/meteolux/sensor.py"
Task T040: "Create MeteoLuxWindSpeedSensor in custom_components/meteolux/sensor.py"
Task T041: "Create MeteoLuxWindGustsSensor in custom_components/meteolux/sensor.py"
Task T042: "Create MeteoLuxWindDirectionSensor in custom_components/meteolux/sensor.py"
Task T043: "Create MeteoLuxPrecipitationSensor in custom_components/meteolux/sensor.py"
Task T044: "Create MeteoLuxSnowSensor in custom_components/meteolux/sensor.py"
Task T045: "Create MeteoLuxConditionSensor in custom_components/meteolux/sensor.py"
Task T046: "Create MeteoLuxConditionTextSensor in custom_components/meteolux/sensor.py"
# All 9 sensors can be implemented in parallel - different classes in same file
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T014) → CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T015-T028) → Flexible location setup
4. Complete Phase 4: User Story 2 (T029-T047) → Current weather display
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. Deploy/demo if ready → MVP complete!

### Incremental Delivery (Recommended)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP Phase 1 (setup only)
3. Add User Story 2 → Test independently → MVP Phase 2 (setup + current weather) ✅ DEPLOYABLE MVP
4. Add User Story 3 → Test independently → Enhanced (5-day forecast added)
5. Add User Story 5 → Test independently → Enhanced (hourly forecast added)
6. Add User Story 6 → Test independently → Enhanced (reconfiguration added)
7. Add User Stories 4, 7, 8 → Test independently → Full Feature Set
8. Complete Phase 11 Polish → Production-ready for HACS submission

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T014)
2. Once Foundational is done:
   - Developer A: User Story 1 (T015-T028) - Config flow
   - Developer B: User Story 2 (T029-T047) - Entities (depends on US1 for coordinator setup)
   - After US1+US2 complete:
     - Developer A: User Story 3 (T048-T056) - 5-day forecast
     - Developer B: User Story 5 (T057-T061) - Hourly forecast
     - Developer C: User Story 6 (T062-T069) - Reconfiguration
3. Stories complete and integrate independently
4. Polish phase (T085-T100) parallelized across team

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

**Total Task Count**: 100 tasks
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 10 tasks (BLOCKING)
- Phase 3 (US1 - P1): 14 tasks
- Phase 4 (US2 - P1): 19 tasks
- Phase 5 (US3 - P2): 9 tasks
- Phase 6 (US5 - P2): 5 tasks
- Phase 7 (US6 - P2): 8 tasks
- Phase 8 (US4 - P3): 5 tasks
- Phase 9 (US7 - P3): 5 tasks
- Phase 10 (US8 - P3): 5 tasks
- Phase 11 (Polish): 16 tasks

**Parallel Opportunities**: 35+ tasks can run in parallel (marked with [P])

**MVP Scope**: User Stories 1 + 2 (Phases 1-4) = 47 tasks → Deployable integration with setup + current weather

**Full Feature Set**: All 8 User Stories (Phases 1-10) = 84 tasks → Complete specification implementation

**Production Ready**: All Phases including Polish (100 tasks) → HACS submission ready

# Implementation Plan: Enhanced MeteoLux Weather Entities with Multi-Forecast Support

**Branch**: `001-enhanced-weather-entities` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-enhanced-weather-entities/spec.md`

## Summary

This feature enhances the existing MeteoLux Home Assistant integration to provide comprehensive weather data through multiple entity types: current weather, detailed 5-day forecasts, high-level 10-day forecasts, and hourly forecasts. The implementation will maximize use of MeteoLux API data, following a "basic info + enriched data" pattern where core weather attributes are always available, with additional details populated when present in the API response. The config flow will support four bidirectionally-synchronized location input methods (address, city dropdown, coordinates, interactive map), multi-language support (en/fr/de/lb), configurable update intervals, reconfiguration capabilities, and multiple location instances.

**Technical Approach**: Extend the existing Home Assistant integration using Python 3.11+, asyncio for non-blocking I/O, the Data Update Coordinator pattern for efficient API polling, and Home Assistant's standard entity platforms (weather, sensor). No external dependencies beyond Home Assistant core. Modify existing code where necessary to align with specification and constitution requirements (KISS, DRY, SOLID, YAGNI, SLAP, Test-First principles).

## Technical Context

**Language/Version**: Python 3.11+ (Home Assistant 2024.10+ requirement)

**Primary Dependencies**:
- Home Assistant Core 2024.10.0+ (provides all necessary frameworks)
- No external PyPI dependencies (use HA built-in `aiohttp` for HTTP, built-in `voluptuous` for validation)
- Standard library: `asyncio`, `datetime`, `typing`, `logging`

**Storage**: No persistent storage required (configuration stored in HA config entries, state managed by HA entity registry)

**Testing**: pytest with `pytest-homeassistant-custom-component==0.13.106` (already in `requirements_test.txt`)

**Target Platform**: Home Assistant OS, Container, Core, Supervised (any HA installation method)

**Project Type**: Home Assistant custom integration (single Python package structure under `custom_components/meteolux/`)

**Performance Goals**:
- Integration startup < 5 seconds per instance (constitution requirement)
- API response 95th percentile < 2 seconds for current conditions (constitution requirement)
- Memory usage < 50MB per instance (constitution requirement)
- Coordinator update cycle < 10 seconds including retries

**Constraints**:
- No blocking I/O in event loop (all HTTP requests via `async`/`await`)
- Update intervals ≥ 1 minute (constitution requirement)
- Exponential backoff on API failures: 2s, 4s, 8s, 16s, 30s, 60s
- Luxembourg boundary validation: lat 49.4–50.2°N, lon 5.7–6.5°E

**Scale/Scope**:
- Target: 5+ simultaneous integration instances per HA installation
- API endpoints: 2 (MeteoLux weather, bookmarks for cities)
- Entities per instance: ~25 (1 weather + 9 current sensors + 15 forecast sensors)
- Entity states: most disabled by default to reduce overhead

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Simplicity First (KISS)
- [x] Solution uses simplest approach that meets requirements
  - Use HA's built-in DataUpdateCoordinator (no custom polling)
  - Use HA's config flow helpers for UI (no custom frontend code)
  - Use stdlib/HA built-ins only (no external dependencies)
- [x] Any complexity is explicitly justified with documented rationale
  - Bidirectional location sync complexity justified by FR-004 requirement
  - Multiple coordinator instances (current/hourly/daily) justified by FR-009 independent intervals
- [x] Abstractions serve clear, measurable needs
  - Coordinator abstraction: reduces API calls, shares data across entities (performance)
  - Entity base classes: DRY for 25 entities with common attributes

### Code Reusability (DRY)
- [x] Patterns extracted only after 3rd occurrence
  - Sensor entity pattern appears 24 times → extract base class `MeteoLuxSensorEntity`
  - Location validation appears 4 times (address, city, coordinates, map) → extract `validate_luxembourg_coordinates(lat, lon)`
  - API error handling appears 3 times (current, hourly, daily coordinators) → extract `handle_api_error(response)`
- [x] Abstractions have single, clear purposes
  - `MeteoLuxDataUpdateCoordinator`: fetches and caches API data
  - `MeteoLuxConfigFlow`: handles all config flow steps
  - `MeteoLuxSensorEntity`: base for all sensor entities
- [x] No premature optimization or abstraction
  - No abstraction until pattern confirmed in code

### Functional Robustness (SOLID)
- [x] Single Responsibility: Components have one clear purpose
  - `coordinator.py`: API communication only
  - `config_flow.py`: configuration UI only
  - `sensor.py`: sensor entities only
  - `weather.py`: weather entity only
- [x] Open/Closed: Extension via config/inheritance, not modification
  - New sensor types added via `SENSOR_TYPES` dict (no code changes)
  - New languages added via `SUPPORTED_LANGUAGES` dict
  - Entity behavior extended via subclassing (e.g., `MeteoLuxForecastSensor(MeteoLuxSensorEntity)`)
- [x] Dependency Inversion: Depends on abstractions (coordinator pattern)
  - Entities depend on `DataUpdateCoordinator` interface, not concrete HTTP client
  - Config flow depends on HA's `ConfigFlow` abstract class

### Minimal Implementation (YAGNI)
- [x] Implements only specified requirements (no "future" features)
  - No features beyond spec FR-001 through FR-048
  - No speculative "admin dashboard" or "data export" features
- [x] No speculative configuration options
  - Only configured intervals, language, location (per spec)
  - No "advanced settings" panel unless required by FR
- [x] Feature scope justified by user need or specification
  - All 8 user stories mapped to functional requirements

### Test Coverage (NON-NEGOTIABLE)
- [x] Integration tests planned for user-facing workflows
  - Config flow: initial setup (4 location methods), reconfigure, options
  - Coordinator: successful update, API failure, partial data
  - Entity lifecycle: entity creation, state updates, availability changes
- [x] Contract tests planned for external API interactions
  - MeteoLux API: `/metapp/weather` request/response validation
  - MeteoLux API: `/metapp/bookmarks` request/response validation
  - OpenStreetMap Nominatim: geocoding request/response validation
- [x] Test strategy documented (Red-Green-Refactor cycle)
  - Write failing test → implement minimum code to pass → refactor
- [x] Target: 80%+ coverage for core logic
  - Core logic: coordinator data parsing, entity state mapping, config validation

### User Experience Consistency
- [x] Follows Home Assistant naming conventions
  - Entity IDs: `weather.{name}`, `sensor.{name}_{type}` (snake_case)
  - Friendly names: `{Name} Temperature` (Title Case)
- [x] Uses standard entity device classes and units
  - Temperature: `SensorDeviceClass.TEMPERATURE`, `UnitOfTemperature.CELSIUS`
  - Wind: `SensorDeviceClass.WIND_SPEED`, `UnitOfSpeed.KILOMETERS_PER_HOUR`
  - Precipitation: `SensorDeviceClass.PRECIPITATION`, `UnitOfPrecipitationDepth.MILLIMETERS`
- [x] Error messages are clear and actionable
  - "Location must be within Luxembourg" (not "Invalid coordinates")
  - "MeteoLux API unavailable. Retrying..." (not "HTTP 503")
- [x] Defaults are sensible and documented
  - 10 min current, 30 min hourly, 6 hours daily (per spec assumptions)

### Performance Requirements
- [x] Uses coordinator pattern (no direct entity polling)
  - Three coordinators: current, hourly, daily (each with independent intervals)
- [x] Respects update interval constraints (≥1 minute)
  - Config flow validates: current 1-60 min, hourly 5-120 min, daily 1-24 hr
- [x] Implements exponential backoff for failures
  - Retry delays: 2s, 4s, 8s, 16s, 30s, 60s (per constitution)
- [x] All I/O operations use async/await
  - `aiohttp.ClientSession` for all HTTP requests
  - `async def async_setup_entry()`, `async def async_update()` patterns
- [x] Performance targets documented (startup, API response, memory)
  - See Performance Goals section above

**Violations requiring justification**: None. All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/001-enhanced-weather-entities/
├── spec.md                  # Feature specification (complete)
├── plan.md                  # This file (/speckit.plan command output)
├── research.md              # Phase 0 output (technology decisions)
├── data-model.md            # Phase 1 output (entity data models)
├── quickstart.md            # Phase 1 output (developer quick-start guide)
├── contracts/               # Phase 1 output (API contracts)
│   ├── meteolux-api.yaml    # MeteoLux API contract (OpenAPI 3.0)
│   └── nominatim-api.yaml   # Nominatim geocoding contract (OpenAPI 3.0)
└── checklists/              # Quality validation checklists
    └── requirements.md      # Spec quality checklist (complete)
```

### Source Code (repository root)

```text
custom_components/meteolux/
├── __init__.py              # Integration setup (async_setup_entry, async_unload_entry)
├── manifest.json            # Integration metadata (domain, version, requirements)
├── const.py                 # Constants (API URLs, defaults, condition mappings)
├── config_flow.py           # Config flow (4 location methods, bidirectional sync, reconfigure)
├── coordinator.py           # Data coordinators (CurrentWeatherCoordinator, HourlyForecastCoordinator, DailyForecastCoordinator)
├── weather.py               # Weather entity (current conditions + forecast)
├── sensor.py                # Sensor entities (current sensors, 5-day detailed, 10-day trend, hourly)
├── strings.json             # UI strings for config flow
└── translations/
    └── en.json              # English translations

tests/
├── __init__.py
├── conftest.py              # Pytest fixtures (hass, mock API responses)
├── const.py                 # Test constants
├── contract/
│   ├── test_meteolux_api.py         # MeteoLux API contract tests
│   └── test_nominatim_api.py        # Nominatim geocoding contract tests
├── integration/
│   ├── test_config_flow.py          # Config flow integration tests
│   ├── test_coordinator.py          # Coordinator integration tests
│   └── test_init.py                 # Integration setup/unload tests
└── unit/
    ├── test_sensor.py               # Sensor entity unit tests
    └── test_weather.py              # Weather entity unit tests

.github/
└── workflows/
    ├── validate.yml         # Linting (ruff), type checking (mypy), hassfest
    ├── test.yml             # Pytest with coverage reporting
    └── release.yml          # Automated releases on tag push
```

**Structure Decision**: Single Python package under `custom_components/meteolux/` (Home Assistant custom integration standard). Tests follow pytest-homeassistant-custom-component structure with contract/integration/unit separation. No frontend code needed (HA config flow handles UI). No backend/API separation (integration consumes external API, doesn't expose one).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**Status**: No violations. Constitution Check fully passes with all gates satisfied.


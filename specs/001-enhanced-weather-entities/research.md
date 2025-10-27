# Research & Technology Decisions

**Feature**: Enhanced MeteoLux Weather Entities with Multi-Forecast Support
**Date**: 2025-10-28
**Purpose**: Document technology choices, best practices research, and architectural decisions for implementing the MeteoLux HACS integration

## Overview

This document consolidates research findings for all technical decisions required by the implementation plan. All choices prioritize well-maintained, security-vetted dependencies (per user requirement), maximize MeteoLux API data usage, and follow Home Assistant integration best practices.

---

## 1. Home Assistant Integration Framework

### Decision

**Use Home Assistant Core 2024.10.0+ as the sole dependency**, with no external PyPI packages beyond what HA core provides.

### Rationale

- **Maintenance**: HA core is actively maintained by 1000+ contributors, with security patches released rapidly
- **Security**: No external dependencies = minimal attack surface; HA core is security-audited by the community
- **Compatibility**: HA provides all needed functionality: `aiohttp` (async HTTP), `voluptuous` (validation), config flow helpers, entity platforms
- **HACS compliance**: Integrations with zero external dependencies pass hassfest validation easily and reduce dependency conflicts
- **Constitution alignment**: KISS principle (simplest approach), YAGNI (don't add dependencies speculatively)

### Alternatives Considered

1. **`requests` library for HTTP**: Rejected because it's synchronous (blocks event loop), and HA already provides `aiohttp` for async HTTP
2. **`pydantic` for validation**: Rejected because HA's built-in `voluptuous` is sufficient and adding external deps increases maintenance burden
3. **`geopy` for geocoding**: Rejected because direct OpenStreetMap Nominatim HTTP API calls are simpler and avoid external dependency

---

## 2. Data Update Coordinator Pattern

### Decision

**Implement three separate `DataUpdateCoordinator` instances** (one each for current, hourly, and daily weather data) with independent update intervals.

### Rationale

- **Performance**: Coordinator pattern prevents entities from individually polling the API (reduces API calls from 25 per instance to 3)
- **HA best practice**: Official HA documentation recommends coordinators for polling integrations ([link](https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-multiple-entities))
- **Independent intervals**: FR-009 requires separate update intervals for current (1-60 min), hourly (5-120 min), and daily (1-24 hr). Three coordinators enable this without complex scheduling logic.
- **Caching**: Coordinator caches API responses; entities access cached data instantly (no wait for HTTP)
- **Error handling**: Coordinator handles API failures once; all entities automatically mark unavailable together (consistent UX)

### Implementation Approach

```python
# coordinator.py structure (simplified)
class MeteoLuxCurrentWeatherCoordinator(DataUpdateCoordinator):
    """Fetch current weather data."""

    async def _async_update_data(self):
        """Fetch data from MeteoLux API."""
        url = f"{API_URL}/metapp/weather"
        params = {"lat": self.lat, "long": self.lon, "langcode": self.language}
        async with self.session.get(url, params=params) as response:
            data = await response.json()
            return parse_current_weather(data)  # Extract current conditions

class MeteoLuxHourlyForecastCoordinator(DataUpdateCoordinator):
    """Fetch hourly forecast data."""
    # Similar pattern, but parse forecast.hourly

class MeteoLuxDailyForecastCoordinator(DataUpdateCoordinator):
    """Fetch daily forecast data."""
    # Similar pattern, but parse forecast.daily + data.forecast
```

### Alternatives Considered

1. **Single coordinator for all data**: Rejected because it forces all entities to update on the same interval (violates FR-009)
2. **Entity-level polling**: Rejected because it creates 25 concurrent API requests per instance (performance nightmare, violates constitution)
3. **Custom polling service**: Rejected because it reinvents HA's DataUpdateCoordinator (violates KISS)

---

## 3. Config Flow Bidirectional Location Sync

### Decision

**Use JavaScript-free bidirectional synchronization via Home Assistant's `config_flow` framework** with `async_step_*` methods and data schema dependencies.

### Rationale

- **No custom frontend code**: HA's config flow system renders UI automatically from `vol.Schema` definitions
- **Bidirectional sync implementation**: When user changes one field (e.g., address), the `async_step_user` method geocodes it, updates the `data_schema` with new coordinates/city, and re-renders the form with all fields synchronized
- **HA best practice**: Config flows are the standard UI pattern for integrations (YAML config is deprecated)
- **Simplicity**: No need for custom Vue/React components, no WebSocket communication—just Python async functions

### Implementation Approach

```python
# config_flow.py pattern (simplified)
class MeteoLuxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        """Handle user-initiated config step with bidirectional sync."""
        errors = {}

        if user_input is not None:
            # User changed a field—sync all location inputs
            if user_input.get(CONF_ADDRESS):
                # Geocode address → coordinates
                coords = await self._geocode_address(user_input[CONF_ADDRESS])
                user_input[CONF_LATITUDE] = coords["lat"]
                user_input[CONF_LONGITUDE] = coords["lon"]
                # Reverse geocode → nearest city
                user_input[CONF_CITY_ID] = await self._find_nearest_city(coords)
            elif user_input.get(CONF_CITY_ID):
                # City selected → coordinates + address
                city_data = await self._fetch_city_data(user_input[CONF_CITY_ID])
                user_input[CONF_LATITUDE] = city_data["lat"]
                user_input[CONF_LONGITUDE] = city_data["lon"]
                user_input[CONF_ADDRESS] = city_data["name"]
            # Repeat for coordinates, map pin changes...

            # Validate Luxembourg boundaries
            if not self._validate_luxembourg(user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE]):
                errors["base"] = "location_outside_luxembourg"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        # Render form with current user_input (synced fields)
        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(user_input),  # Pre-populate synced values
            errors=errors,
        )
```

### Alternatives Considered

1. **Custom JavaScript frontend**: Rejected because it requires maintaining separate JS code, violates KISS, and HA config flow is sufficient
2. **Separate config steps per location method**: Rejected because it creates disjointed UX (user has to pick method first, can't switch easily)
3. **Post-submit sync**: Rejected because bidirectional sync must happen in real-time per FR-004 requirement

---

## 4. Multiple Entity Management Strategy

### Decision

**Disable most forecast entities by default** (enabled: weather entity, Day 0 detailed forecast, current weather sensors; disabled: Days 1-4, 10-day, hourly).

### Rationale

- **Performance**: Reducing enabled entities from 25 to ~12 by default lowers HA's entity registry overhead
- **User experience**: New users aren't overwhelmed by dozens of entities; they enable what they need
- **HA best practice**: Many integrations (e.g., AccuWeather, OpenWeatherMap) disable forecast sensors by default
- **Spec alignment**: FR-018, FR-022, FR-026 explicitly require most forecast entities disabled by default

### Implementation Approach

```python
# sensor.py pattern
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up MeteoLux sensor entities."""
    entities = []

    # Current weather sensors (some enabled, some disabled)
    entities.append(MeteoLuxTemperatureSensor(..., entity_registry_enabled_default=True))
    entities.append(MeteoLuxWindGustsSensor(..., entity_registry_enabled_default=False))  # Disabled by default

    # Daily forecast sensors (Day 0 enabled, Days 1-4 disabled)
    for day in range(5):
        enabled = (day == 0)  # Only Day 0 enabled by default
        entities.append(MeteoLuxForecastSensor(..., day=day, entity_registry_enabled_default=enabled))

    # 10-day forecast sensor (disabled by default per FR-022)
    entities.append(MeteoLux10DayForecastSensor(..., entity_registry_enabled_default=False))

    async_add_entities(entities)
```

### Alternatives Considered

1. **Enable all entities by default**: Rejected because it overwhelms users and wastes resources (violates UX consistency gate)
2. **Make entities opt-in during setup**: Rejected because it complicates config flow (violates KISS)
3. **Use entity categories to hide entities**: Rejected because "disabled by default" is the standard HA pattern for optional entities

---

## 5. API Data Maximization Strategy: Basic + Enriched Pattern

### Decision

**Implement "basic info + enriched data" pattern** where core attributes (temperature, condition, wind, precipitation) are always populated from guaranteed API fields, with optional attributes (UV index, sunshine, snow, gusts) populated only when present in the response.

### Rationale

- **Robustness**: Integration never fails due to missing optional fields (graceful degradation)
- **API maximization**: Uses all available MeteoLux API data (user requirement: "use API data to the maximum extent")
- **Flexibility**: Handles API changes where optional fields are added/removed without breaking the integration

### Implementation Approach

```python
# coordinator.py data parsing (simplified)
def parse_current_weather(api_response):
    """Parse current weather with basic + enriched pattern."""
    current = api_response["forecast"]["current"]

    # Basic info (always available)
    data = {
        "temperature": current["temperature"],  # Always present
        "condition": map_icon_to_condition(current["icon"]["id"]),  # Always present
        "wind_speed": parse_wind_speed(current["wind"]["speed"]),  # Always present
        "precipitation": current.get("rain", 0),  # Default to 0 if missing
    }

    # Enriched data (populate if available)
    if "humidex" in current:
        data["apparent_temperature"] = current["humidex"]
    if "felt" in current.get("temperature", {}):
        data["feels_like"] = current["temperature"]["felt"]
    if "snow" in current:
        data["snow"] = current["snow"]
    if "wind" in current and "gusts" in current["wind"]:
        data["wind_gusts"] = parse_wind_speed(current["wind"]["gusts"])

    return data
```

### Alternatives Considered

1. **Require all fields**: Rejected because API might not always provide optional fields (integration would fail unnecessarily)
2. **Ignore optional fields**: Rejected because it violates user requirement to "use API data to maximum extent"
3. **Different entities for basic vs. enriched**: Rejected because it creates entity proliferation (violates YAGNI)

---

## 6. Testing Strategy

### Decision

**Implement pytest-based testing with three layers**: contract tests (API validation), integration tests (HA workflows), unit tests (pure logic).

### Rationale

- **Constitution requirement**: 80%+ test coverage for core logic (NON-NEGOTIABLE gate)
- **HA best practice**: `pytest-homeassistant-custom-component` is the standard testing framework for custom integrations
- **Contract tests ensure API stability**: Validate that MeteoLux API structure matches expectations (catches breaking changes early)
- **Integration tests ensure HA compatibility**: Test config flow, coordinator updates, entity lifecycle in real HA test environment
- **Unit tests ensure business logic correctness**: Test data parsing, validation, transformations in isolation (fast, no HA fixtures needed)

### Test Coverage Breakdown

| Layer | Coverage Target | What's Tested |
|-------|----------------|---------------|
| Contract | 100% of API interactions | MeteoLux `/metapp/weather` and `/metapp/bookmarks` requests/responses, Nominatim geocoding |
| Integration | 100% of user workflows | Config flow (4 location methods, reconfigure), coordinator (success, failure, partial data), entity lifecycle |
| Unit | 80%+ of pure functions | Data parsing (`parse_current_weather`, `map_icon_to_condition`), validation (`validate_luxembourg_coordinates`) |

### Tools & Framework

- **pytest**: Test runner
- **pytest-homeassistant-custom-component 0.13.106**: Provides HA fixtures (`hass`, `enable_custom_integrations`)
- **pytest-aiohttp**: Mock async HTTP requests
- **pytest-cov**: Coverage reporting

### Alternatives Considered

1. **Manual testing only**: Rejected because it violates constitution's NON-NEGOTIABLE test-first requirement
2. **Unittest instead of pytest**: Rejected because pytest is the HA standard and has better async support
3. **Mocking all API calls in integration tests**: Rejected because contract tests are needed to catch real API changes

---

## 7. CI/CD & Release Automation

### Decision

**Use GitHub Actions with three workflows**: validation (lint, type check, hassfest), testing (pytest with coverage), and release automation (semantic versioning + changelog).

### Rationale

- **GitHub Actions standard**: Free for public repos, tight GitHub integration, widely used in HA community
- **Spec requirement FR-045**: Must include CI/CD for automated testing, linting, validation
- **Spec requirement FR-046, FR-047**: Must use semantic versioning and automate releases

### Workflow Structure

1. **`.github/workflows/validate.yml`** (runs on every PR):
   - `ruff` linting (per constitution quality gates)
   - `mypy` type checking in strict mode (per constitution quality gates)
   - `hassfest` validation (ensures HA compliance)
   - HACS validation (ensures HACS compliance)

2. **`.github/workflows/test.yml`** (runs on every PR):
   - Pytest with coverage reporting
   - Coverage threshold: 80% (fails if below per constitution)
   - Matrix testing: HA 2024.10, 2024.11 (current and previous versions per constitution maintenance standards)

3. **`.github/workflows/release.yml`** (runs on tag push):
   - Automated changelog generation from commits (Conventional Commits format)
   - GitHub release creation with changelog
   - Version bump in `manifest.json`

### Alternatives Considered

1. **Travis CI or CircleCI**: Rejected because GitHub Actions is free for open source and has better GitHub integration
2. **Manual releases**: Rejected because it violates FR-047 automation requirement
3. **No CI/CD**: Rejected because it violates FR-045 and constitution quality gates

---

## 8. Geocoding Service Selection

### Decision

**Use OpenStreetMap Nominatim API** (`https://nominatim.openstreetmap.org/search`) for address geocoding.

### Rationale

- **Free and well-maintained**: OSM Nominatim is actively maintained, free (no API key), and widely used
- **No security vulnerabilities**: Open-source project with community security audits
- **Already in use**: Existing MeteoLux integration uses Nominatim (no new dependencies)
- **Luxembourg coverage**: Excellent address coverage for Luxembourg

### Usage Policy Compliance

Per Nominatim Usage Policy ([link](https://operations.osmfoundation.org/policies/nominatim/)):
- **User-Agent**: Set custom User-Agent header (e.g., `MeteoLuxHA/0.1.0`)
- **Rate limiting**: Max 1 request/second (enforced by exponential backoff in coordinator)
- **Caching**: Cache geocoding results in config entry (avoid redundant requests)

### Alternatives Considered

1. **Google Geocoding API**: Rejected because it requires API key and has usage quotas (complicates setup)
2. **Mapbox Geocoding**: Rejected because it requires API key and has free tier limits
3. **Manual coordinate entry only**: Rejected because FR-002 explicitly requires address geocoding

---

## 9. Exponential Backoff Implementation

### Decision

**Use Home Assistant's built-in retry mechanism** in `DataUpdateCoordinator` with custom backoff sequence: 2s, 4s, 8s, 16s, 30s, 60s.

### Rationale

- **Constitution requirement**: Exponential backoff on API failures (Performance Requirements gate)
- **HA built-in support**: `DataUpdateCoordinator` has `async_refresh()` method with retry support
- **Graceful degradation**: Entities mark unavailable after 60s timeout, then coordinator retries indefinitely until API recovers

### Implementation Approach

```python
# coordinator.py (simplified)
class MeteoLuxCurrentWeatherCoordinator(DataUpdateCoordinator):

    async def _async_update_data(self):
        """Fetch data with exponential backoff."""
        backoff_sequence = [2, 4, 8, 16, 30, 60]  # seconds

        for attempt, delay in enumerate(backoff_sequence):
            try:
                async with self.session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                if attempt < len(backoff_sequence) - 1:
                    _LOGGER.warning(f"API request failed (attempt {attempt+1}). Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    _LOGGER.error(f"API request failed after {len(backoff_sequence)} attempts.")
                    raise UpdateFailed(f"MeteoLux API unavailable: {err}")
```

### Alternatives Considered

1. **Linear backoff (5s, 10s, 15s)**: Rejected because exponential backoff is more gentle on API during outages
2. **No retries**: Rejected because it violates constitution's performance requirements
3. **Infinite retries without backoff**: Rejected because it hammers the API (violates API courtesy)

---

## 10. Security Best Practices

### Decision

**Follow OWASP best practices for API integrations**: validate all user input, sanitize coordinates, use HTTPS exclusively, log no sensitive data.

### Rationale

- **User requirement**: "Dependencies must be free of known security vulnerabilities"
- **Constitution requirement**: Security section in Maintenance Standards

### Security Checklist

- [x] **Input validation**: Validate coordinates (lat -90 to 90, lon -180 to 180), address length (max 500 chars), update intervals (per FR-009 constraints)
- [x] **HTTPS only**: All API requests use `https://` URLs (MeteoLux, Nominatim)
- [x] **No sensitive logging**: Never log full API responses (may contain user location data)
- [x] **SQL injection prevention**: N/A (no SQL database)
- [x] **XSS prevention**: N/A (no HTML rendering)
- [x] **CSRF prevention**: N/A (no web UI, only HA config flow)
- [x] **Dependency scanning**: GitHub Dependabot alerts enabled for `pytest-homeassistant-custom-component`

### Alternatives Considered

1. **Allow HTTP fallback**: Rejected because HTTPS is mandatory per constitution security requirements
2. **Log full API responses for debugging**: Rejected because it leaks user location data (privacy violation)

---

## Summary of Key Decisions

| Decision Area | Choice | Primary Rationale |
|---------------|--------|-------------------|
| Dependencies | HA Core 2024.10+ only (zero external PyPI deps) | Security, simplicity, maintainability |
| Data fetching | Three separate `DataUpdateCoordinator` instances | Independent update intervals (FR-009), performance |
| Location sync | HA config flow with async schema updates | No custom frontend, HA best practice |
| Entity management | Disable most forecast entities by default | Performance, UX (per FR-018, FR-022, FR-026) |
| API data usage | Basic + enriched pattern | Robustness + maximization per user requirement |
| Testing | pytest with contract/integration/unit layers | 80%+ coverage (constitution NON-NEGOTIABLE) |
| CI/CD | GitHub Actions (validate, test, release workflows) | FR-045, FR-046, FR-047 compliance |
| Geocoding | OpenStreetMap Nominatim (free, no API key) | Well-maintained, no security issues, good Luxembourg coverage |
| Error handling | Exponential backoff (2s, 4s, 8s, 16s, 30s, 60s) | Constitution performance requirements |
| Security | OWASP best practices, HTTPS only, input validation | User requirement + constitution security standards |

All decisions align with the project constitution (KISS, DRY, SOLID, YAGNI, SLAP, Test-First) and meet the feature specification requirements (FR-001 through FR-048).

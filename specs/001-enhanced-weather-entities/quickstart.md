# Developer Quickstart: Enhanced MeteoLux Weather Entities

**Feature**: Enhanced MeteoLux Weather Entities with Multi-Forecast Support
**Date**: 2025-10-28
**Purpose**: Get developers up and running quickly with the MeteoLux Home Assistant integration codebase

## Overview

This quickstart guide helps developers set up their development environment, understand the codebase structure, run tests, and make their first contribution to the MeteoLux integration.

---

## Prerequisites

- **Home Assistant Dev Container** OR **Local Python 3.11+ environment**
- **Git** for version control
- **Code editor** (VS Code recommended for HA development)

---

## 1. Clone and Setup

### Option A: Home Assistant Dev Container (Recommended)

```bash
# Clone the repository
git clone https://github.com/VixOrg/meteolux-ha-integration.git
cd meteolux-ha-integration

# Open in VS Code
code .

# VS Code will prompt to reopen in Dev Container
# Click "Reopen in Container"
# Container includes:
# - Home Assistant development environment
# - Python 3.11+
# - pytest, mypy, ruff pre-installed
```

### Option B: Local Python Environment

```bash
# Clone the repository
git clone https://github.com/VixOrg/meteolux-ha-integration.git
cd meteolux-ha-integration

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install test dependencies
pip install -r tests/requirements_test.txt

# Install linting/type checking tools
pip install ruff mypy

# Install Home Assistant (for local testing)
pip install homeassistant>=2024.10.0
```

---

## 2. Repository Structure

```
meteolux-ha-integration/
├── custom_components/meteolux/    # Integration code (THIS IS WHERE YOU WORK)
│   ├── __init__.py                # Integration entry point
│   ├── manifest.json              # Integration metadata
│   ├── const.py                   # Constants (API URLs, defaults, mappings)
│   ├── config_flow.py             # Configuration UI
│   ├── coordinator.py             # Data fetching coordinators
│   ├── weather.py                 # Weather entity
│   ├── sensor.py                  # Sensor entities
│   ├── strings.json               # UI strings
│   └── translations/en.json       # English translations
├── tests/                         # Test files (WRITE TESTS HERE)
│   ├── contract/                  # API contract tests
│   ├── integration/               # Integration tests
│   └── unit/                      # Unit tests
├── specs/001-enhanced-weather-entities/  # Design docs
│   ├── spec.md                    # Feature specification
│   ├── plan.md                    # Implementation plan
│   ├── research.md                # Technology decisions
│   ├── data-model.md              # Data entities
│   ├── quickstart.md              # This file
│   └── contracts/                 # API contracts (OpenAPI)
├── .github/workflows/             # CI/CD (validate, test, release)
└── README.md                      # User-facing documentation
```

---

## 3. Run Tests

### Run All Tests

```bash
# From repository root
pytest

# Expected output: All tests pass (green)
# Coverage report shows 80%+ for core logic
```

### Run Specific Test Categories

```bash
# Contract tests (API validation)
pytest tests/contract/

# Integration tests (HA workflows)
pytest tests/integration/

# Unit tests (pure logic)
pytest tests/unit/
```

### Run Tests with Coverage

```bash
pytest --cov=custom_components.meteolux --cov-report=html

# Open htmlcov/index.html in browser to see coverage report
```

---

## 4. Run Linting and Type Checking

```bash
# Linting with ruff
ruff check custom_components/meteolux/

# Auto-fix linting issues
ruff check --fix custom_components/meteolux/

# Type checking with mypy
mypy custom_components/meteolux/

# Format code with ruff
ruff format custom_components/meteolux/
```

---

## 5. Test in Home Assistant

### Method 1: Symlink Integration (Quick Iteration)

```bash
# Find your HA config directory
# Common locations:
#   - Linux: ~/.homeassistant/
#   - macOS: ~/.homeassistant/
#   - Windows: %APPDATA%\.homeassistant\

# Create custom_components directory if it doesn't exist
mkdir -p ~/.homeassistant/custom_components/

# Symlink the integration
ln -s /path/to/meteolux-ha-integration/custom_components/meteolux \
      ~/.homeassistant/custom_components/meteolux

# Restart Home Assistant
# Integration will appear in Settings → Integrations → Add Integration
```

### Method 2: Copy Integration (Stable Testing)

```bash
# Copy integration to HA config directory
cp -r custom_components/meteolux ~/.homeassistant/custom_components/

# Restart Home Assistant
```

### Method 3: Dev Container with Test HA Instance

```bash
# From Dev Container terminal
hass -c config/

# Home Assistant starts at http://localhost:8123
# Integration auto-loads from custom_components/meteolux/
```

---

## 6. Common Development Tasks

### Add a New Sensor Entity

1. **Define sensor type** in `const.py`:
   ```python
   SENSOR_TYPES = {
       "humidity": {  # New sensor
           "name": "Humidity",
           "device_class": SensorDeviceClass.HUMIDITY,
           "state_class": SensorStateClass.MEASUREMENT,
           "native_unit_of_measurement": PERCENTAGE,
       },
   }
   ```

2. **Create sensor class** in `sensor.py`:
   ```python
   class MeteoLuxHumiditySensor(MeteoLuxSensorEntity):
       """Humidity sensor."""

       def __init__(self, coordinator, entry):
           super().__init__(coordinator, entry, "humidity")

       @property
       def native_value(self):
           """Return humidity value."""
           return self.coordinator.data.get("humidity")
   ```

3. **Register sensor** in `sensor.py`'s `async_setup_entry()`:
   ```python
   entities.append(MeteoLuxHumiditySensor(coordinator, entry))
   ```

4. **Write tests** in `tests/unit/test_sensor.py`:
   ```python
   def test_humidity_sensor(hass, mock_coordinator):
       """Test humidity sensor."""
       sensor = MeteoLuxHumiditySensor(mock_coordinator, mock_entry)
       assert sensor.native_value == 75  # Mock data
   ```

### Add a New Config Flow Step

1. **Add step method** in `config_flow.py`:
   ```python
   async def async_step_advanced(self, user_input=None):
       """Handle advanced settings step."""
       if user_input is not None:
           # Process advanced settings
           return self.async_create_entry(title="...", data=user_input)

       return self.async_show_form(
           step_id="advanced",
           data_schema=vol.Schema({
               # Advanced settings schema
           })
       )
   ```

2. **Link to step** from another step:
   ```python
   # In async_step_user:
   if user_input.get("show_advanced"):
       return await self.async_step_advanced()
   ```

3. **Write tests** in `tests/integration/test_config_flow.py`:
   ```python
   async def test_advanced_step(hass):
       """Test advanced config flow step."""
       result = await hass.config_entries.flow.async_init(
           DOMAIN, context={"source": config_entries.SOURCE_USER}
       )
       result = await hass.config_entries.flow.async_configure(
           result["flow_id"], user_input={"show_advanced": True}
       )
       assert result["step_id"] == "advanced"
   ```

### Modify Coordinator Data Fetching

1. **Update `_async_update_data()` in `coordinator.py`**:
   ```python
   async def _async_update_data(self):
       """Fetch data from API."""
       url = f"{API_URL}/metapp/weather"
       params = {"lat": self.lat, "long": self.lon, "langcode": self.language}

       async with self.session.get(url, params=params, timeout=10) as response:
           response.raise_for_status()
           data = await response.json()

           # Parse new data field
           parsed_data = {
               "temperature": data["forecast"]["current"]["temperature"],
               "humidity": data["forecast"]["current"].get("humidity", 0),  # New field
           }
           return parsed_data
   ```

2. **Write contract test** in `tests/contract/test_meteolux_api.py`:
   ```python
   async def test_weather_api_response_schema(aiohttp_client):
       """Test MeteoLux API response matches expected schema."""
       async with aiohttp_client.get(
           "https://metapi.ana.lu/api/v1/metapp/weather",
           params={"lat": 49.6116, "long": 6.1319, "langcode": "en"}
       ) as response:
           data = await response.json()
           assert "forecast" in data
           assert "current" in data["forecast"]
           assert "humidity" in data["forecast"]["current"]  # New assertion
   ```

---

## 7. Debugging Tips

### Enable Debug Logging in Home Assistant

Edit `~/.homeassistant/configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.meteolux: debug
```

Restart HA, then check logs:
```bash
tail -f ~/.homeassistant/home-assistant.log | grep meteolux
```

### Use Home Assistant Dev Tools

- **States**: View entity states at `Developer Tools → States`
- **Services**: Test entity updates at `Developer Tools → Services`
- **Logs**: View logs at `Settings → System → Logs`

### Debugging in VS Code

1. Set breakpoints in Python code
2. Run Home Assistant in debug mode:
   ```bash
   hass -c config/ --debug
   ```
3. Attach VS Code debugger to running HA process

---

## 8. Contribution Workflow

### Step 1: Create Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### Step 2: Make Changes

- Write failing tests first (TDD: Red-Green-Refactor)
- Implement code to pass tests
- Refactor while keeping tests green

### Step 3: Validate Changes

```bash
# Run linting
ruff check custom_components/meteolux/

# Run type checking
mypy custom_components/meteolux/

# Run all tests
pytest

# Check coverage (must be 80%+)
pytest --cov=custom_components.meteolux
```

### Step 4: Commit and Push

```bash
# Stage changes
git add .

# Commit with Conventional Commits format
git commit -m "feat: add humidity sensor entity"
# OR
git commit -m "fix: correct wind direction parsing"
# OR
git commit -m "test: add contract test for MeteoLux API"

# Push to GitHub
git push origin feature/your-feature-name
```

### Step 5: Create Pull Request

1. Go to GitHub repository
2. Click "Pull Requests" → "New Pull Request"
3. Select your feature branch
4. Fill in PR description:
   ```markdown
   ## Summary
   Add humidity sensor entity to MeteoLux integration

   ## Changes
   - Added `humidity` sensor type to `const.py`
   - Implemented `MeteoLuxHumiditySensor` in `sensor.py`
   - Added unit tests in `tests/unit/test_sensor.py`

   ## Testing
   - [x] All tests pass
   - [x] Coverage 80%+
   - [x] Linting passes
   - [x] Type checking passes
   - [x] Tested in Home Assistant 2024.10.0

   ## Related Issues
   Closes #123
   ```
5. Wait for CI/CD checks (validate, test workflows)
6. Address reviewer feedback
7. Merge when approved

---

## 9. Useful Commands Reference

| Task | Command |
|------|---------|
| **Run all tests** | `pytest` |
| **Run specific test file** | `pytest tests/unit/test_sensor.py` |
| **Run tests with coverage** | `pytest --cov=custom_components.meteolux` |
| **Lint code** | `ruff check custom_components/meteolux/` |
| **Fix linting** | `ruff check --fix custom_components/meteolux/` |
| **Format code** | `ruff format custom_components/meteolux/` |
| **Type check** | `mypy custom_components/meteolux/` |
| **Run Home Assistant** | `hass -c config/` |
| **View HA logs** | `tail -f ~/.homeassistant/home-assistant.log` |
| **Validate HACS** | `hacs validate` (requires HACS CLI) |
| **Validate hassfest** | `hassfest validate custom_components/meteolux/` |

---

## 10. Key Files to Know

| File | Purpose |
|------|---------|
| `manifest.json` | Integration metadata (domain, version, dependencies) |
| `const.py` | All constants (API URLs, defaults, sensor types, condition mappings) |
| `config_flow.py` | Configuration UI (location setup, reconfigure, options) |
| `coordinator.py` | Data fetching coordinators (current, hourly, daily) |
| `weather.py` | Weather entity (compatible with HA weather cards) |
| `sensor.py` | Sensor entities (current, forecast, 5-day, 10-day, hourly) |
| `strings.json` | UI strings for config flow |
| `tests/conftest.py` | Pytest fixtures (hass, mock coordinators, mock API responses) |

---

## 11. Getting Help

- **Integration Spec**: `specs/001-enhanced-weather-entities/spec.md` (feature requirements)
- **Implementation Plan**: `specs/001-enhanced-weather-entities/plan.md` (technical approach)
- **Data Model**: `specs/001-enhanced-weather-entities/data-model.md` (entity structure)
- **API Contracts**: `specs/001-enhanced-weather-entities/contracts/` (MeteoLux API, Nominatim API)
- **Constitution**: `.specify/memory/constitution.md` (code quality principles)
- **HA Dev Docs**: https://developers.home-assistant.io/
- **GitHub Issues**: https://github.com/VixOrg/meteolux-ha-integration/issues

---

## 12. Cheat Sheet: Common Gotchas

1. **Coordinator data not updating**: Did you call `await coordinator.async_request_refresh()` after setup?
2. **Entity not showing in HA**: Check if entity is disabled by default (`entity_registry_enabled_default=False`)
3. **Tests failing with "hass not available"**: Did you use the `hass` fixture from `conftest.py`?
4. **Type checking fails**: Did you add type hints (`def func(arg: str) -> int:`)?
5. **Linting fails**: Run `ruff format` to auto-format code
6. **Coverage below 80%**: Write tests for untested code paths (especially error handling)
7. **API tests fail**: Check if MeteoLux API is reachable (network issue or API change)

---

## Quick Start Summary

```bash
# 1. Clone and setup
git clone https://github.com/VixOrg/meteolux-ha-integration.git
cd meteolux-ha-integration
python3.11 -m venv venv
source venv/bin/activate
pip install -r tests/requirements_test.txt

# 2. Run tests
pytest

# 3. Run linting
ruff check custom_components/meteolux/

# 4. Make changes
# - Edit code in custom_components/meteolux/
# - Write tests in tests/

# 5. Validate
pytest --cov=custom_components.meteolux
ruff check custom_components/meteolux/
mypy custom_components/meteolux/

# 6. Commit and PR
git checkout -b feature/your-feature
git commit -m "feat: your feature"
git push origin feature/your-feature
# Create PR on GitHub
```

Happy coding! 🚀

# MeteoLux Integration Tests

This directory contains comprehensive tests for the MeteoLux Home Assistant integration.

## Running Tests

**Note for Windows users**: Due to a compatibility issue between `pytest-homeassistant-custom-component` (which blocks sockets for security) and Windows asyncio (which requires sockets for event loop pipes), tests cannot be run locally on Windows. Tests will run automatically via GitHub Actions on every push and pull request.

### Prerequisites (Linux/macOS/WSL only)

Install test dependencies:
```bash
pip install -r tests/requirements_test.txt
```

### Run All Tests (Linux/macOS/WSL only)

```bash
pytest tests/ -v
```

### Run Specific Test File (Linux/macOS/WSL only)

```bash
pytest tests/test_sensor.py -v
```

### Run with Coverage (Linux/macOS/WSL only)

```bash
pytest tests/ --cov=custom_components.meteolux --cov-report=html
```

### Windows Users

On Windows, please use one of these alternatives:
1. **GitHub Actions (Recommended)**: Tests run automatically on push/PR
2. **WSL (Windows Subsystem for Linux)**: Install WSL and run tests there
3. **Docker**: Run tests in a Linux container

## Test Structure

- **conftest.py**: Shared fixtures and mocks
- **test_coordinator.py**: Tests for data coordinator
- **test_sensor.py**: Tests for all sensor entities
- **test_weather.py**: Tests for weather entity

## Test Coverage

The tests cover:

### Coordinator Tests
- Successful API data fetch
- Coordinate-based location queries
- HTTP error handling
- Network error handling
- Missing location error handling
- Session cleanup

### Sensor Tests
- Current weather sensors (temperature, wind, precipitation, etc.)
- Ephemeris sensor (sun/moon data)
- Location sensor (city information)
- Forecast sensors (5-day temperature and precipitation)
- Wind direction translation
- Data parsing functions (wind speed ranges, temperature arrays, precipitation ranges)
- Lambda closure bug fix verification
- Humidity, pressure, UV, cloud cover sensors

### Weather Entity Tests
- Current condition mapping
- Temperature and wind data
- Wind direction translation
- Daily forecast generation
- Hourly forecast generation
- Humidity and pressure properties

## Mock Data

All tests use mock API responses defined in `conftest.py`:
- City ID: 490 (Luxembourg)
- Includes complete ephemeris data
- Includes current, hourly, and daily forecasts
- Tests various data formats (ranges, arrays, etc.)

## CI/CD

Tests run automatically on:
- Every push to main branch
- Every pull request
- Python versions: 3.11, 3.12

GitHub Actions also runs:
- Ruff linting
- Hassfest validation

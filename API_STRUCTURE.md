# MeteoLux API Structure

## API Endpoint
```
https://metapi.ana.lu/api/v1/metapp/weather
```

## Request Parameters

The integration uses coordinate-based queries:

### By Coordinates
```
?lat={latitude}&long={longitude}&langcode={language}
```

**Note**: While the API also supports city ID parameters (`?city={city_id}&langcode={language}`), the integration only uses coordinate-based queries. Users select locations via an interactive map picker or manual latitude/longitude entry. Luxembourg boundaries are validated (lat: 49.4-50.2, lon: 5.7-6.5).

## Expected Response Structure

Based on the integration code, the API is expected to return the following structure:

### City Information (`city`)
```json
{
  "city": {
    // All properties from this object are exposed via the Location sensor
    // Properties may include: id, name, lat, long, country, timezone, etc.
  }
}
```

### Ephemeris Information (`ephemeris`)
```json
{
  "ephemeris": {
    "date": "<ISO8601>",            // Current date
    "sunrise": "<ISO8601>",          // Sunrise time
    "sunset": "<ISO8601>",           // Sunset time
    "sunshine": <number>,            // Hours of sunshine
    "uvIndex": <number>,             // UV index
    "moonrise": "<ISO8601>",         // Moonrise time
    "moonset": "<ISO8601>",          // Moonset time
    "moonPhase": <number>            // Moon phase (0-7)
  }
}
```

### Current Weather (`forecast.current`)
```json
{
  "forecast": {
    "current": {
      "temperature": {
        "temperature": <number|array>,  // Current temperature in Celsius
        "felt": <number>                 // Apparent/feels-like temperature
      },
      "wind": {
        "speed": "<string>",             // e.g., "20-30" or "25"
        "gusts": "<string>",             // e.g., "40-50" or "0"
        "direction": "<string>"          // e.g., "N", "NE", "O" (for East in some languages)
      },
      "rain": "<string>",                // Precipitation e.g., "0-1" or "0"
      "snow": "<string>",                // Snow e.g., "0-1" or "0"
      "icon": {
        "id": <number>,                  // Icon ID (1-50+)
        "name": "<string>"               // Condition text
      },
      "humidity": <number>,              // Relative humidity percentage
      "pressure": <number>,              // Atmospheric pressure in hPa
      "uv": <number>,                    // UV index
      "clouds": <number>                 // Cloud cover percentage
    }
  }
}
```

### Hourly Forecast (`forecast.hourly`)
```json
{
  "forecast": {
    "hourly": [
      {
        "date": "<ISO8601>",
        "temperature": {
          "temperature": <number|array>,
          "felt": <number>
        },
        "wind": {
          "speed": "<string>",
          "direction": "<string>"
        },
        "rain": "<string>",
        "icon": {
          "id": <number>,
          "name": "<string>"
        }
      }
    ]
  }
}
```

### Daily Forecast (`forecast.daily`)
```json
{
  "forecast": {
    "daily": [
      {
        "date": "<ISO8601>",
        "icon": {
          "id": <number>,
          "name": "<string>"
        },
        "wind": {
          "speed": "<string>",
          "direction": "<string>"
        },
        "rain": "<string>",              // Rain amount (e.g., "2-5" or "0")
        "snow": "<string>",              // Snow amount (e.g., "0-1" or "0")
        "temperatureMin": {              // Minimum temperature (Temperature object)
          "temperature": <number|array>,
          "felt": <number>,
          "humidex": "<string>"
        },
        "temperatureMax": {              // Maximum temperature (Temperature object)
          "temperature": <number|array>,
          "felt": <number>,
          "humidex": "<string>"
        },
        "sunshine": <number>,            // Hours of sunshine
        "uvIndex": <number>              // UV index (0-12)
      }
    ]
  }
}
```

## Data Type Notes

1. **Temperature**: Can be either a number or an array. If it's an array, the integration calculates the average.

2. **Wind Speed/Gusts**: String format, can be:
   - A range: "20-30" (integration uses midpoint: 25)
   - Single value: "25"
   - Zero: "0"

3. **Precipitation/Snow**: String format, same as wind speed

4. **Wind Direction**: String representing compass direction
   - **Important**: The API always returns directions in French regardless of the langcode parameter
   - French abbreviations from API: N, NE, E, SE, S, SO (Sud-Ouest), O (Ouest), NO (Nord-Ouest)
   - The integration automatically translates these to the user's selected language:
     - English: N, NE, E, SE, S, SW, W, NW
     - French: N, NE, E, SE, S, SO, O, NO (unchanged)
     - German: N, NO, O, SO, S, SW, W, NW
     - Luxembourgish: N, NO, O, SO, S, SW, W, NW

5. **Icon ID**: Integer mapping to weather conditions (see CONDITION_MAP in const.py)

## Integration Entities

The integration creates **4 entities total** (1 weather entity + 3 sensors) following modern Home Assistant 2024 best practices:

### Weather Entity (1 entity)
Full-featured weather entity providing current conditions and comprehensive forecasts.

**Current Conditions**:
- Temperature, apparent temperature, humidity, pressure
- Wind speed, wind bearing (translated direction)
- UV index, cloud coverage, condition

**Forecast Access** (via `weather.get_forecasts` service):

**Daily Forecast** (up to 10 days):
- Today (Day 0): Enhanced with current weather
  - When today's date matches the first forecast day, current weather data is merged in
  - Includes real-time: condition, humidity, pressure, cloud coverage
  - Retains forecast: high/low temperatures, wind data, UV index
- Days 0-4 (from `forecast.daily`): Full details
  - High/low temperatures (native and apparent)
  - Precipitation, wind speed, wind gusts, wind direction (translated)
  - UV index
- Days 5+ (from `data.forecast`): Basic details
  - Dynamically fills remaining days based on available extended forecast data
  - High/low temperatures, precipitation
  - Note: API typically provides up to 10 days total

**Hourly Forecast** (from `forecast.hourly` - typically ~21 entries spanning ~5 days):
- Forecasts at multiple times per day (typically 00:00, 06:00, 12:00, 18:00)
- Temperature, apparent temperature, condition
- Wind speed, wind gusts, wind direction (translated)
- Precipitation, humidity, cloud coverage, UV index

### Current Weather Sensor (1 entity)
Consolidated sensor with **state** = temperature (°C) and **16 attributes**:
- `temperature` - Current temperature (°C)
- `apparent_temperature` - Feels-like temperature (°C)
- `dew_point` - Calculated dew point (°C)
- `wind_chill` - Calculated wind chill (°C, only when temp < 10°C)
- `humidex` - Canadian humidity index
- `wind_speed` - Wind speed (km/h)
- `wind_gusts` - Wind gusts (km/h)
- `wind_direction` - Translated wind direction (N, NE, E, etc.)
- `precipitation` - Precipitation amount (mm)
- `snow` - Snow amount (mm)
- `condition` - Home Assistant weather condition
- `condition_text` - Human-readable condition text
- `humidity` - Relative humidity (%)
- `pressure` - Atmospheric pressure (hPa)
- `uv_index` - UV index
- `cloud_cover` - Cloud coverage (%)

### Ephemeris Sensor (1 entity)
Entity ID: `sensor.<name>_today`

Single sensor with **state** = date and attributes containing:
- **sun**: sunrise, sunset, sunshine (hours), uv_index
- **moon**: moonrise, moonset, moon_phase (0-7), moon_icon (HA moon phase name)

Moon phase mapping:
- 0: new_moon
- 1: waxing_crescent
- 2: first_quarter
- 3: waxing_gibbous
- 4: full_moon
- 5: waning_gibbous
- 6: last_quarter
- 7: waning_crescent

### Location Sensor (1 entity)
Entity ID: `sensor.<name>_location`

Single sensor with **state** = city name and attributes containing all properties from the API's `city` object (dynamically exposed based on API response).

## Known Issues / Observations

1. **Wind Gusts**: May return "0" or may not be provided by API for all locations
2. **Wind Direction**: API always returns French abbreviations (N, NE, E, SE, S, SO, O, NO) regardless of langcode. The integration automatically translates these to the user's selected language.
3. **Temperature Arrays**: Some API responses return temperature as arrays instead of single values
4. **Humidity, Pressure, UV, Clouds**: These fields may not be available for all locations or in all API responses

## Testing Recommendations

When testing the integration:
1. Check that all 4 entities are created (1 weather + 3 sensors)
2. Verify current weather sensor shows correct state and all 16 attributes are populated
3. Verify ephemeris sensor shows correct date state and sun/moon attributes
4. Verify location sensor shows correct city name and all city attributes
5. Test weather entity current conditions (temperature, humidity, pressure, wind, UV, clouds)
6. Test `weather.get_forecasts` service with type=daily returns up to 10 days:
   - Days 0-4 should have full details (temps, wind, precipitation, UV)
   - Days 5-9 should have basic details (temps, precipitation)
7. Test `weather.get_forecasts` service with type=hourly returns all available forecasts (typically ~21 entries at 00:00, 06:00, 12:00, 18:00 each day)
8. Verify wind data is parsed correctly from string ranges (midpoint calculation)
9. Test with different language codes to ensure wind direction translations work
10. Verify calculated values (dew_point, wind_chill, humidex) are computed correctly
11. Verify weather entity forecasts include enhanced fields (wind gusts, humidity, clouds, UV)

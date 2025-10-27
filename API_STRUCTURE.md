# MeteoLux API Structure

## API Endpoint
```
https://metapi.ana.lu/api/v1/metapp/weather
```

## Request Parameters

### By City ID
```
?city={city_id}&langcode={language}
```

### By Coordinates
```
?lat={latitude}&long={longitude}&langcode={language}
```

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

### Daily Forecast (`forecast.forecast`)
```json
{
  "forecast": {
    "forecast": [
      {
        "date": "<ISO8601>",
        "maxTemp": <number|array>,       // Maximum temperature
        "minTemp": <number|array>,       // Minimum temperature
        "precipitation": "<string>"      // Precipitation amount
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

### Current Weather Sensors
- Temperature (°C)
- Apparent Temperature (°C)
- Wind Speed (km/h)
- Wind Gusts (km/h) - disabled by default
- Wind Direction
- Precipitation (mm)
- Snow (mm) - disabled by default
- Condition (HA weather condition)
- Condition Text
- Humidity (%)
- Pressure (hPa)
- UV Index - disabled by default
- Cloud Cover (%) - disabled by default

### Ephemeris Sensor (Today)
Single sensor with state showing the date and attributes containing:
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

### Location Sensor
Single sensor with state showing the city name and attributes containing all properties from the API's `city` object (dynamically exposed based on API response).

### Forecast Sensors (Day 0-4)
- Temperature High (°C)
- Temperature Low (°C)
- Precipitation (mm)

### Weather Entity
Provides current conditions and forecasts (hourly and daily) for the weather card.

## Known Issues / Observations

1. **Wind Gusts**: May return "0" or may not be provided by API for all locations
2. **Wind Direction**: API always returns French abbreviations (N, NE, E, SE, S, SO, O, NO) regardless of langcode. The integration automatically translates these to the user's selected language.
3. **Temperature Arrays**: Some API responses return temperature as arrays instead of single values
4. **Humidity, Pressure, UV, Clouds**: These fields may not be available for all locations or in all API responses

## Testing Recommendations

When testing the integration:
1. Check that forecast sensors correctly show data for each day (0-4)
2. Verify wind data is parsed correctly from string ranges
3. Test with different language codes to ensure translations work
4. Verify new sensors (humidity, pressure, UV, cloud cover) show data if available from API

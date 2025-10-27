# MeteoLux Weather Integration

Get accurate weather forecasts for Luxembourg using data from [MeteoLux](https://www.meteolux.lu/).

## Key Features

✨ **3 Location Selection Methods**
- 🏙️ Choose from 102 Luxembourg cities
- 📍 Enter any address (auto-geocoded)
- 🗺️ Click on an interactive map

🌍 **4 Languages Available**
- English, French, German, Luxembourgish

📊 **Comprehensive Weather Data**
- Weather entity with hourly & 10-day forecasts
- 24 sensor entities (current conditions + forecasts)
- Current: temperature, feels-like, wind, precipitation
- Forecast: daily highs/lows, precipitation amounts

⚙️ **Easy Configuration**
- UI-based setup (no YAML required)
- Multiple locations supported
- Auto-updates: 10min (current), 30min (hourly), 6hr (daily)

## Quick Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "MeteoLux"
4. Follow the setup wizard:
   - Select location method
   - Provide location details & name
   - Choose language
5. Done! Start using your weather data

## Usage Example

```yaml
type: weather-forecast
entity: weather.home
show_current: true
show_forecast: true
```

Perfect for Luxembourg residents wanting local, accurate weather data in their preferred language!

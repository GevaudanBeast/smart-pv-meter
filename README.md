# 🎯 Smart PV Meter (SPVM) v0.6.3

[![Version](https://img.shields.io/badge/version-0.6.3-blue.svg)](https://github.com/GevaudanBeast/smart-pv-meter/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Smart PV Meter** is a Home Assistant integration that calculates expected solar production using a physical solar model based on astronomical calculations. It provides accurate predictions and surplus calculations for solar optimizers.

---

## ✨ Features

### 🌞 Physical Solar Model
- **NOAA-style sun position** calculations (elevation, azimuth, declination)
- **Clear-sky irradiance** modeling with atmospheric transmittance
- **Plane-of-array (POA)** projection using incidence angle
- **Weather adjustments** (cloud coverage, temperature derating)
- **No external dependencies** - pure Python implementation

### 📊 Sensors
- `sensor.spvm_expected_production` - Expected solar production (W)
- `sensor.spvm_yield_ratio` - Performance ratio (actual / expected × 100%)
- `sensor.spvm_surplus_net` - Net surplus for solar optimizers (W)

### ⚡ Performance
- **Instant calculations** (< 1s vs 5-10s with legacy k-NN)
- **Low memory** (< 5 MB vs 50-100 MB with k-NN)
- **No historical data required** (works immediately)
- **Real-time updates** (configurable interval)

---

## 📦 Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add: `https://github.com/GevaudanBeast/smart-pv-meter`
5. Category: Integration
6. Search for "Smart PV Meter" and install

### Manual Installation
```bash
cd /config/custom_components/
git clone https://github.com/GevaudanBeast/smart-pv-meter.git spvm
```

Then restart Home Assistant.

---

## ⚙️ Configuration

### 1. Add Integration
**Settings** → **Devices & Services** → **Add Integration** → Search "Smart PV Meter"

### 2. Required Sensors
- **PV production sensor** - Your solar production power sensor
- **House consumption sensor** - Your house consumption power sensor

### 3. Optional Sensors (Recommended)
- **Grid power sensor** - Grid import/export (+/−)
- **Battery sensor** - Battery charge/discharge (+/−)
- **Brightness sensor (lux)** - For better cloud detection
- **Temperature sensor** - For temperature derating
- **Cloud coverage sensor** - Direct cloud percentage (0-100%)

### 4. Solar Parameters
Configure your solar installation:

| Parameter | Description | Example | Range |
|-----------|-------------|---------|-------|
| `panel_peak_power` | Panel peak power | 2800 W | 100-20000 W |
| `panel_tilt` | Panel tilt angle | 30° | 0-90° |
| `panel_azimuth` | Panel orientation | 180° (South) | 0-360° |
| `site_latitude` | Installation latitude | 48.8566° | -90 to 90° |
| `site_longitude` | Installation longitude | 2.3522° | -180 to 180° |
| `site_altitude` | Altitude above sea level | 35 m | -500 to 6000 m |
| `system_efficiency` | System efficiency | 0.85 (85%) | 0.5-1.0 |

**Note:** Latitude/longitude/altitude default to your Home Assistant location if not specified.

### 5. Advanced Settings
- **Reserve (W)** - Battery reserve to keep (default: 150W)
- **Cap max (W)** - Hard power cap (default: 3000W)
- **Degradation (%)** - Panel aging/degradation (default: 0%)
- **Update interval** - Sensor update frequency (default: 60s)

---

## 🧪 Diagnostic Guide

If your sensors show **0W** or **"unknown"**, see [DIAGNOSTIC.md](DIAGNOSTIC.md) for troubleshooting.

### Quick Diagnostic Script

Create `/config/spvm_diagnostic.py`:
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/config/custom_components/spvm')

from datetime import datetime, timezone
from solar_model import SolarInputs, compute as solar_compute

now_utc = datetime.now(timezone.utc)
inputs = SolarInputs(
    dt_utc=now_utc,
    lat_deg=48.8566,      # ⬅️ YOUR LATITUDE
    lon_deg=2.3522,       # ⬅️ YOUR LONGITUDE
    altitude_m=35.0,      # ⬅️ YOUR ALTITUDE
    panel_tilt_deg=30.0,  # ⬅️ YOUR PANEL TILT
    panel_azimuth_deg=180.0,  # ⬅️ YOUR ORIENTATION
    panel_peak_w=2800.0,  # ⬅️ YOUR PEAK POWER
    system_efficiency=0.85,
    cloud_pct=None,
    temp_c=None,
)

model = solar_compute(inputs)
print(f"Sun elevation: {model.elevation_deg:.2f}° ({'DAY' if model.elevation_deg > 0 else 'NIGHT'})")
print(f"Expected production: {model.expected_corrected_w:.1f}W")
```

Run: `python3 /config/spvm_diagnostic.py`

---

## 📊 Sensor Attributes

Each sensor includes detailed attributes for monitoring and debugging:

```yaml
sensor.spvm_expected_production:
  state: 1250.5  # W
  attributes:
    model_elevation_deg: 45.23  # Sun elevation
    model_azimuth_deg: 180.45   # Sun direction
    model_declination_deg: -12.34
    model_incidence_deg: 23.45  # Angle of incidence
    ghi_clear_wm2: 823.4        # Global horizontal irradiance
    poa_clear_wm2: 956.2        # Plane-of-array irradiance
    site:
      lat: 48.8566
      lon: 2.3522
      alt_m: 35.0
    panel:
      tilt_deg: 30.0
      azimuth_deg: 180.0
      peak_w: 2800.0
    system_efficiency: 0.85
    reserve_w: 150
    cap_max_w: 3000
```

---

## 🔧 Usage with Solar Optimizer

SPVM is designed to work seamlessly with solar optimizers:

```yaml
# Use sensor.spvm_surplus_net for your solar optimizer
automation:
  - alias: "Solar Optimizer Control"
    trigger:
      - platform: state
        entity_id: sensor.spvm_surplus_net
    action:
      - service: number.set_value
        target:
          entity_id: number.solar_optimizer_power
        data:
          value: "{{ states('sensor.spvm_surplus_net') | float }}"
```

---

## 📈 Optimization Tips

### 1. Tune System Efficiency
Start with `0.85` and adjust based on actual vs expected production:
- **Expected > Actual** → Decrease efficiency (e.g., 0.80)
- **Expected < Actual** → Increase efficiency (e.g., 0.90)

### 2. Verify Panel Parameters
- Measure actual tilt and azimuth of your panels
- Check peak power matches your installation
- Consider shading and dust (reduce efficiency)

### 3. Add Weather Sensors
- **Brightness (lux)** - Improves cloud detection
- **Temperature** - Enables temperature derating
- **Cloud coverage** - Direct cloud percentage

### 4. Monitor Yield Ratio
The yield ratio shows performance:
- **90-110%** - Normal range
- **> 110%** - Better than expected (cold weather, clean panels)
- **< 90%** - Worse than expected (check configuration)

---

## 🐛 Troubleshooting

### Expected production always 0W during daytime

**Cause:** Bug in solar position calculation (fixed in v0.6.3)

**Solution:** Update to v0.6.3 or later

### Configuration menu not accessible

**Cause:** Bug in config flow (fixed in v0.6.3)

**Solution:** Update to v0.6.3 or later

### Sensors show "unknown"

**Possible causes:**
1. Sun is below horizon (normal at night)
2. Required sensors (PV/house) unavailable
3. Configuration error

**Solution:** Check [DIAGNOSTIC.md](DIAGNOSTIC.md)

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes.

### Version 0.6.3 (Current - November 2025)
- 🐛 **CRITICAL FIX:** Solar position calculation bug
- 🐛 Fixed 400 Bad Request in config flow
- 🐛 Fixed 500 Internal Server Error
- 🐛 Fixed diagnostics coordinator access
- 🏷️ Shorter entity names (English)
- 📖 Added diagnostic guide

### Version 0.6.0 (November 2025)
- 🆕 Physical solar model (NOAA calculations)
- ⚡ 10x faster than k-NN model
- 💾 95% less memory usage
- 🎯 No historical data required

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Home Assistant community
- NOAA for solar calculation algorithms
- Contributors and beta testers

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)
- **Discussions:** [GitHub Discussions](https://github.com/GevaudanBeast/smart-pv-meter/discussions)

---

**Smart PV Meter v0.6.3** - Built with ❤️ by [@GevaudanBeast](https://github.com/GevaudanBeast)

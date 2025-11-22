# 🎯 Smart PV Meter (SPVM) v0.6.9

[![Version](https://img.shields.io/badge/version-0.6.9-blue.svg)](https://github.com/GevaudanBeast/smart-pv-meter/releases)
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

### 5. Sensor Units (v0.6.4+) ⭐

Each power sensor can now have its own unit configuration:

| Sensor | Unit Options | Example |
|--------|--------------|---------|
| PV sensor | W or kW | kW (Enphase Envoy) |
| House sensor | W or kW | kW (Enphase Envoy) |
| Grid sensor | W or kW | W (Shelly) |
| Battery sensor | W or kW | W (Zendure) |

**Why this matters:**
- **Enphase Envoy** sensors report in kW
- **Shelly** sensors report in W
- **Zendure** sensors report in W

Configure each sensor's unit separately to ensure accurate calculations!

### 6. Special Configurations ⚙️

#### Multiple Panel Tilts

If you have panels at **different tilt angles**, calculate a weighted average based on power:

**Example:**
```
Group 1: 6 × 450W = 2700W at 30° tilt
Group 2: 6 × 550W = 3300W at 10° tilt

Weighted average tilt = (2700W × 30° + 3300W × 10°) / 6000W
                      = (81000 + 33000) / 6000
                      = 19°

Configuration:
  panel_peak_power: 6000 W    (total of all panels)
  panel_tilt: 19°             (weighted average)
```

**Formula:**
```
weighted_tilt = (power1 × tilt1 + power2 × tilt2 + ...) / total_power
```

#### Capped/Clipped Installations

If your production is **limited** (inverter capacity or grid contract):

**Example:**
```
Panel capacity: 6000W peak
Inverter limit: 3000W max output

Configuration:
  panel_peak_power: 6000 W      (actual panel capacity)
  cap_max_w: 3000 W             (production limit)
  system_efficiency: 0.90
```

**Why this matters:**
- SPVM calculates theoretical production (e.g., 5000W at noon)
- `cap_max_w` clips to your limit (3000W max)
- Solar Optimizer receives realistic available power
- Yield ratio stays accurate (compares actual vs theoretical before clipping)

**Common scenarios:**
- Micro-inverter system limited by inverter capacity
- Grid contract limiting export power
- Self-consumption mode with production cap

### 7. Correction Parameters (v0.6.9+) 🎛️

Fine-tune SPVM predictions for your specific installation conditions:

#### Lux Correction (Cloudy Weather)
| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `lux_min_elevation_deg` | Minimum sun elevation to use lux correction | 5° | 0-15° |
| `lux_floor_factor` | Minimum correction floor (prevents zeroing) | 0.1 (10%) | 0.01-0.5 |

**When to adjust:**
- **Lux overestimates on thick clouds** → Lower `lux_floor_factor` to 0.02-0.05
- **Lux readings erratic at low sun** → Increase `lux_min_elevation_deg` to 8-10°

#### Seasonal Shading (Trees, Buildings)
| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `shading_winter_pct` | Additional shading in winter (%) | 0% | 0-100% |
| `shading_month_start` | Month when shading starts | 11 (Nov) | 1-12 |
| `shading_month_end` | Month when shading ends | 2 (Feb) | 1-12 |

**Example scenarios:**
- **Trees block sun in winter:** Set `shading_winter_pct: 40`, period Nov-Feb
- **Building shadows in summer:** Set `shading_winter_pct: 20`, period Jun-Aug
- **Year-round obstacle:** Set period Jan-Dec

**📖 Complete guide:** See [PARAMETRES_CORRECTION.md](PARAMETRES_CORRECTION.md) for calibration instructions and use cases.

### 8. Advanced Settings
- **Reserve (W)** - Battery reserve to keep (default: 150W)
- **Cap max (W)** - Hard power cap (default: 3000W)
- **Degradation (%)** - Panel aging/degradation (default: 0%)
- **Update interval** - Sensor update frequency (default: 60s)

---

## 🧪 Diagnostic Guide

If your sensors show **0W** or **"unknown"**, see [DIAGNOSTIC.md](DIAGNOSTIC.md) for troubleshooting.

### Debug Attributes (v0.6.4+) 🔍

The `sensor.spvm_surplus_net` now includes debug attributes to help troubleshoot issues:

```yaml
debug_pv_w: 966.0           # PV production in watts (after unit conversion)
debug_house_w: 920.0        # House consumption in watts (after unit conversion)
debug_surplus_virtual: 58.3 # Surplus before reserve
reserve_w: 150              # Configured reserve
```

**Quick check:** If `debug_pv_w` or `debug_house_w` show very low values (< 10W), you probably have a unit configuration issue (kW vs W).

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

## 🔧 Integration with Solar Optimizer

SPVM provides sensors specifically designed for solar optimization integrations like [Solar Optimizer](https://github.com/jmcollin78/solar_optimizer).

### Understanding SPVM Sensors

SPVM exposes three sensors with different purposes:

| Sensor | What it shows | Use case |
|--------|---------------|----------|
| `spvm_expected_production` | **Theoretical production** based on sun position, weather, and panel specs | Solar Optimizer: "Production solaire" field |
| `spvm_surplus_net` | **Current real surplus** after house consumption and reserve | Real-time monitoring, simple automations |
| `spvm_yield_ratio` | Performance ratio (actual / expected) | Installation health monitoring |

### Configuration for Solar Optimizer

#### For Bridled/Self-Consumption Installations ⚡

If your installation is **bridled to match consumption** (common with Enphase, some micro-inverters), use:

```yaml
Solar Optimizer configuration:
  Production solaire: sensor.spvm_expected_production  # Theoretical potential
  Consommation nette: sensor.your_house_consumption    # Actual house consumption
```

**Why?**
- Your PV production sensor shows **current limited output** (e.g., 800W)
- `expected_production` shows **theoretical available power** (e.g., 3000W)
- Solar Optimizer uses this to know it can activate up to **2200W more** of appliances
- Your inverter will automatically increase production to match the new load

**Example scenario:**
```
Current state:
  - PV bridled: 800W (following consumption)
  - House consumption: 800W
  - Expected production: 3000W (sunny conditions)
  - surplus_net: 0W ✅ Normal - no surplus currently

Solar Optimizer sees:
  - Can produce: 3000W
  - Already consuming: 800W
  - Available to activate: 2200W

Action:
  - SO activates 2kW water heater
  - Your inverter ramps up to 2800W
  - Perfect solar optimization! ☀️
```

#### For Non-Bridled Installations (Export Mode)

If your installation **exports to grid** freely:

```yaml
Solar Optimizer configuration:
  Production solaire: sensor.your_pv_production       # Actual PV production
  Consommation nette: sensor.your_grid_power          # Grid import/export
```

Or use SPVM's real-time calculation:

```yaml
Solar Optimizer configuration:
  Production solaire: sensor.spvm_surplus_net  # Real surplus available now
```

### Why `surplus_net = 0W` is Normal

If you see `surplus_net` constantly at **0W**, this is **normal** for bridled installations:

- `surplus_net` shows **current real surplus** (what's exported now)
- In bridled mode, you don't export, so surplus = 0W ✅
- Use `expected_production` to tell optimizers about **potential** available power

### Advanced Automation Example

```yaml
automation:
  - alias: "Solar Optimizer - Dynamic Power Control"
    trigger:
      - platform: state
        entity_id: sensor.spvm_expected_production
    condition:
      - condition: numeric_state
        entity_id: sensor.spvm_expected_production
        above: 1000  # Only activate if 1kW+ available
    action:
      - service: number.set_value
        target:
          entity_id: number.water_heater_power
        data:
          value: >
            {{ [
              (states('sensor.spvm_expected_production') | float -
               states('sensor.house_consumption') | float - 150) | round(0),
              0
            ] | max }}
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

### Version 0.6.9 (Current - November 2025)
- 🎛️ **Configurable lux correction** - Fine-tune `lux_min_elevation_deg` and `lux_floor_factor`
- 🌲 **Seasonal shading support** - Compensate for trees/buildings blocking sun
- 📖 **Complete user guide** - [PARAMETRES_CORRECTION.md](PARAMETRES_CORRECTION.md) with calibration examples
- 🎯 Better accuracy at low sun angles and very cloudy conditions

### Version 0.6.8 (November 2025)
- 🆕 **Lux-based correction** - More accurate predictions in cloudy conditions
- ✨ Uses real lux sensor to detect thick clouds vs thin clouds
- 📊 New attributes: `lux_factor`, `lux_correction_active`
- 🎯 Fixes overestimation when cloud_pct underestimates actual conditions

### Version 0.6.7 (November 2025)
- 🐛 **CRITICAL FIX:** ZIP extraction path - files now extracted to correct location
- 🐛 Fixed double nesting issue in Home Assistant installation

### Version 0.6.3 (November 2025)
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

**Smart PV Meter v0.6.9** - Built with ❤️ by [@GevaudanBeast](https://github.com/GevaudanBeast)

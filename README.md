# Smart PV Meter (SPVM)

**Home Assistant integration for intelligent solar energy management**

[![Version](https://img.shields.io/badge/version-0.5.2-blue.svg)](https://github.com/GevaudanBeast/smart-pv-meter/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Compatible-orange.svg)](https://hacs.xyz/)

Smart PV Meter calculates real-time solar surplus and predicts PV production using k-NN machine learning with 3 years of historical data - all locally in Home Assistant, no cloud required.

---

## ✨ Features

### 📊 Core Sensors

| Sensor | Description | Usage |
|--------|-------------|-------|
| **sensor.spvm_surplus_net** ⭐ | Net solar surplus with reserve & cap | Use with Solar Optimizer |
| **sensor.spvm_expected_similar** | k-NN predicted production | Compare actual vs expected |
| **sensor.spvm_grid_power_auto** | Auto-calculated grid power | When grid sensor unavailable |
| **sensor.spvm_surplus_virtual** | Raw surplus calculation | Before reserve applied |
| **sensor.spvm_pv_effective_cap_now_w** | PV capacity with degradation | Monitor system health |

### 🧠 Intelligent Predictions

- **k-NN Algorithm**: Uses 3 years of historical data
- **Multi-factor Analysis**: Weather (lux, temp, humidity) + sun elevation + time
- **Seasonal Aware**: Compares similar days across years
- **Automatic Fallback**: Graceful degradation when data limited

### ⚡ Real-time Calculations

- **150W Zendure Reserve**: Automatically applied
- **3kW Hard Cap**: System protection
- **45s Smoothing**: Temporal averaging for stability
- **Real-time Updates**: 60-second default interval

---

## 🚀 Quick Start

### Prerequisites

- Home Assistant 2024.1 or newer
- At least 1 month of historical data (3+ months recommended)
- Required sensors: PV production, house consumption
- Optional: Grid power, battery, weather sensors (lux, temp, humidity)

### Installation via HACS (Recommended)

1. Open HACS
2. Go to "Integrations"
3. Click "+" and search for "Smart PV Meter"
4. Click "Install"
5. Restart Home Assistant
6. Add integration via UI

### Manual Installation

```bash
# 1. Download latest release
cd /config/custom_components
wget https://github.com/GevaudanBeast/smart-pv-meter/releases/download/v0.5.2/spvm.tar.gz

# 2. Extract
mkdir -p spvm
tar -xzf spvm.tar.gz -C spvm/

# 3. Restart Home Assistant
ha core restart
```

### Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Smart PV Meter"
4. Configure:
   - **Required**: PV sensor, House consumption sensor
   - **Optional**: Grid power, Battery, Weather sensors
   - **Parameters**: Reserve (150W), Cap (3000W), k-NN settings

---

## 📖 Documentation

### Sensor Details

#### sensor.spvm_surplus_net ⭐
**The main sensor for solar optimization**

```yaml
# Calculation
surplus_net = smooth(min(surplus_virtual - 150W, 3000W))

# Attributes
reserve_w: 150          # Zendure battery reserve
cap_max_w: 3000         # System cap
cap_limit_w: 3000       # Hard limit
smoothed: true          # 45s temporal smoothing
note: "Reserve + cap + hard limit applied"
```

**Usage with Solar Optimizer**:
```yaml
# configuration.yaml
solar_optimizer:
  surplus_sensor: sensor.spvm_surplus_net
```

#### sensor.spvm_expected_similar ⭐
**k-NN prediction of solar production**

```yaml
# Attributes
method: "knn"                    # or "fallback"
k: 5                             # Number of neighbors
neighbors: 5                     # Actually found
samples_total: 2543              # Historical data points
window_min_minutes: 30           # Time window
window_max_minutes: 90
weights:
  lux: 0.4                       # Weather importance
  temp: 0.2
  hum: 0.1
  elev: 0.3                      # Sun elevation
```

### k-NN Configuration

Optimize predictions by adjusting weights:

```yaml
# For sunny locations
knn_weight_lux: 0.5      # Increase lux importance
knn_weight_temp: 0.2
knn_weight_elev: 0.3

# For cloudy locations
knn_weight_lux: 0.6      # Even higher lux weight
knn_weight_temp: 0.15
knn_weight_hum: 0.15     # Humidity matters more
knn_weight_elev: 0.1

# For stable weather
knn_k: 3                 # Fewer neighbors
knn_window_max: 60       # Tighter time window

# For variable weather
knn_k: 7                 # More neighbors
knn_window_max: 120      # Wider time window
```

---

## 🛠️ Services

### spvm.recompute_expected_now
Force immediate recalculation of expected production.

```yaml
service: spvm.recompute_expected_now
```

### spvm.reset_cache
Clear k-NN cache and normalization data.

```yaml
service: spvm.reset_cache
```

---

## 📊 Example Automations

### Notify on High Production

```yaml
automation:
  - alias: "High PV Production Expected"
    trigger:
      platform: numeric_state
      entity_id: sensor.spvm_expected_similar
      above: 2.5  # kW
    action:
      service: notify.mobile_app
      data:
        title: "Solar Production Alert"
        message: >
          High production expected: {{ states('sensor.spvm_expected_similar') }} kW
          Current surplus: {{ states('sensor.spvm_surplus_net') }} W
```

### Track Performance

```yaml
automation:
  - alias: "Track PV Yield"
    trigger:
      platform: time_pattern
      hours: "/1"
    action:
      service: logbook.log
      data:
        name: "PV Performance"
        message: >
          Actual: {{ states('sensor.pv_power') }} W
          Expected: {{ states('sensor.spvm_expected_similar') | float * 1000 }} W
          Yield: {{ (states('sensor.pv_power') | float / (states('sensor.spvm_expected_similar') | float * 1000) * 100) | round(1) }}%
```

---

## 🔧 Troubleshooting

### No Historical Data (samples_total = 0)

**Cause**: PV sensor has no history

**Solution**:
1. Check recorder is enabled
2. Wait 24-48 hours for data accumulation
3. Verify PV sensor is recording values
4. Call `spvm.reset_cache` service

### Method = "fallback"

**Cause**: Not enough k-NN neighbors found

**Solution**:
1. Add weather sensors (lux, temp, humidity)
2. Increase `knn_window_max` (90 → 120 minutes)
3. Wait for more historical data
4. Check sun.sun entity exists

### Expected = 0 at midday

**Cause**: Elevation filter too strict or no sun.sun

**Solution**:
1. Enable sun.sun: Add `sun:` to configuration.yaml
2. Wait for data with proper elevation
3. Check if it's actually nighttime 😉

### Logs: "No candidates after elevation filter"

**This is NORMAL at night!** Message is INFO level.

If happening during day:
1. Check sun.sun entity is available
2. Verify elevation attribute exists
3. Increase elevation threshold in code if needed

---

## 🎓 Understanding the Algorithm

### Data Collection
1. **Historical Data**: 3 years (1095 days) from HA recorder
2. **Sensors Used**: PV, sun elevation, lux, temperature, humidity
3. **Filtering**: ±45 days seasonal window + elevation ±15°

### k-NN Prediction
1. Get current conditions (time, weather, sun position)
2. Find k=5 most similar historical points
3. Calculate weighted distance using configured weights
4. Weighted average of neighbor production values
5. Apply temporal smoothing (45s window)

### Fallback Chain
1. **k-NN with weather** (best)
2. **k-NN time only** (good)
3. **Time ±2h + elevation** (acceptable)
4. **Daily median** (last resort)

---

## 📈 Performance Tips

### Optimize Data Collection

```yaml
# Extend recorder history (recommended)
recorder:
  purge_keep_days: 1095  # 3 years

# Exclude unnecessary sensors
recorder:
  exclude:
    entities:
      - sensor.not_needed_1
      - sensor.not_needed_2
```

### Add Weather Sensors

Better predictions with more data:
- **Lux sensor**: Most important (40% default weight)
- **Temperature**: Secondary (20% weight)
- **Humidity**: Tertiary (10% weight)
- **Sun elevation**: Built-in (30% weight)

### Monitor Performance

```yaml
# Template sensor for yield ratio
template:
  - sensor:
      - name: "PV Yield Ratio"
        unit_of_measurement: "%"
        state: >
          {% set actual = states('sensor.pv_power') | float %}
          {% set expected = states('sensor.spvm_expected_similar') | float * 1000 %}
          {% if expected > 0 %}
            {{ ((actual / expected) * 100) | round(1) }}
          {% else %}
            0
          {% endif %}
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
# Clone repo
git clone https://github.com/GevaudanBeast/smart-pv-meter.git
cd smart-pv-meter

# Create development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt

# Run tests
pytest
```

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/GevaudanBeast/smart-pv-meter/discussions)
- **Documentation**: See `/docs` folder

### Reporting Issues

When reporting issues, please include:
1. Home Assistant version
2. SPVM version (check manifest.json)
3. Relevant logs (search "spvm" in HA logs)
4. Configuration (hide sensitive data)
5. Diagnostics download from integration

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Home Assistant community
- Solar Optimizer integration
- k-NN algorithm researchers
- All contributors and testers

---

## 🔗 Related Projects

- [Solar Optimizer](https://github.com/...): Device control based on solar surplus
- [Zendure](https://www.zendure.com/): Battery systems
- [Home Assistant](https://www.home-assistant.io/): Home automation platform

---

**Made with ☀️ by [GevaudanBeast](https://github.com/GevaudanBeast)**

**Version**: 0.5.2 | **Updated**: 2025-11-10

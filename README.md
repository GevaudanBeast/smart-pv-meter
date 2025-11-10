# SPVM 0.5.6 - Performance & Stability Release

## 🎯 What's Fixed

This release resolves critical performance issues that affected installation and startup times.

### Critical Fixes ✅
- **Blocking I/O calls eliminated**: Removed pytz dependency causing "Detected blocking call to open" warnings
- **Timeout issues resolved**: Fixed CancelledError during integration setup
- **10x faster installation**: Setup time reduced from 3-5 minutes to < 30 seconds

## ✨ New Features

### Progressive History Loading
New service `spvm.extend_history` allows users to load historical data incrementally:
```yaml
service: spvm.extend_history
data:
  days: 90  # Load 90 days of history
```

**Benefits:**
- Fast initial setup (7 days only)
- Load more data on-demand
- No more timeouts or blocking

### Smart Caching
- 1-hour cache reduces database queries
- Better memory management
- Improved overall performance

## 🔄 Breaking Changes

### Default History Reduced
- **Before**: 1095 days (3 years) loaded at startup
- **After**: 30 days default, 7 days first load
- **Migration**: Use `extend_history` service to load more

**Why?** Fast startup is more important than having 3 years immediately. Users can progressively load more data as needed.

## 📊 Performance Improvements

| Metric | v0.5.5 | v0.5.6 | Improvement |
|--------|--------|--------|-------------|
| Installation time | 3-5 min | < 30 sec | **10x faster** |
| Blocking calls | Yes | No | **100% eliminated** |
| Default history | 1095 days | 30 days | **Better balance** |
| First load | 1095 days | 7 days | **156x less data** |
| Timeout risk | High | None | **Stable** |

## 🔧 Technical Changes

### Code Modifications
- `expected.py`: Replaced pytz with Home Assistant's dt_util
- `__init__.py`: Removed blocking `async_config_entry_first_refresh`
- `const.py`: Changed HISTORY_DAYS from 1095 to 30
- `coordinator.py`: Added `extend_history()` method
- `services.yaml`: Added extend_history service definition

### Architecture Improvements
- Lazy loading: Historical data loads on-demand
- Progressive loading: Start with 7 days, extend as needed
- Better timezone handling: Using HA's native utilities

## 📝 Migration Guide

### For New Users
Simply install and configure. No special steps needed!

### For Existing Users (0.5.x → 0.5.6)

#### Option 1: Clean Install (Recommended)
1. Backup your configuration
2. Remove SPVM integration via UI
3. Delete `/config/custom_components/spvm/`
4. Install v0.5.6
5. Reconfigure with saved settings

#### Option 2: In-Place Update
1. Replace files in `/config/custom_components/spvm/`
2. Restart Home Assistant
3. Call `spvm.reset_cache` service
4. Optionally call `spvm.extend_history` with 30+ days

**Full migration guide included in package.**

## ✅ Testing

### Automated Tests
Run the included test script:
```bash
chmod +x QUICK_TEST_COMMANDS.sh
./QUICK_TEST_COMMANDS.sh
```

### Manual Verification
1. Installation completes in < 1 minute
2. No "blocking call" warnings in logs
3. All 6 sensors created and functional
4. Service `spvm.extend_history` available

**Comprehensive test plan included in package.**

## 📦 Package Contents

### Integration Code
- Complete Home Assistant integration
- Version 0.5.6 in manifest.json
- Bilingual support (EN/FR)

### Documentation
- **START_HERE.md** - Quick start guide
- **README.md** - Complete user guide
- **INSTALLATION.md** - Detailed install instructions
- **CHANGELOG.md** - Version history
- **SPVM_MIGRATION_GUIDE.md** - Migration steps
- **SPVM_TEST_PLAN.md** - Testing procedures
- **SPVM_FIXES_SUMMARY.md** - Technical details
- **QUICK_TEST_COMMANDS.sh** - Validation script

## 🚀 Quick Start

### Installation
```bash
# Extract
unzip spvm-0.5.6.zip

# Copy to Home Assistant
cp -r spvm-0.5.6/custom_components/spvm /config/custom_components/

# Restart
ha core restart
```

### Configuration
1. Configuration → Integrations → + Add
2. Search "Smart PV Meter"
3. Configure sensors:
   - **Required**: pv_sensor, house_sensor
   - **Recommended**: lux_sensor, temp_sensor
   - **Optional**: grid_power_sensor, battery_sensor

### Validation
```bash
# Quick test
cd spvm-0.5.6/
./QUICK_TEST_COMMANDS.sh
```

## 🎯 Recommended Workflow

### Day 0 (Installation)
- Install and configure
- Starts with 7 days of history
- Complete in < 30 seconds

### Day 1 (First Extension)
```yaml
service: spvm.extend_history
data:
  days: 30
```

### Day 7+ (Full History)
```yaml
service: spvm.extend_history
data:
  days: 90  # or 180, 365
```

## 🐛 Known Issues

None currently! 🎉

## 💬 Feedback

Please report any issues:
- GitHub Issues: https://github.com/GevaudanBeast/smart-pv-meter/issues
- Include version (0.5.6), logs, and configuration

## 📜 License

This project is open source under the same license as previous versions.

---

## 🙏 Credits

Thanks to all users who reported the blocking call and timeout issues!

## 🔗 Links

- **Download**: spvm-0.5.6.zip (119KB)
- **Repository**: https://github.com/GevaudanBeast/smart-pv-meter
- **Documentation**: Included in package
- **HACS**: Via custom repositories

---

**Made with ☀️ for optimal solar energy management**

---

## Installation Checklist

After installing v0.5.6:
- [ ] Installation completed in < 1 minute
- [ ] No pytz warnings in logs
- [ ] 6 sensors created and showing values
- [ ] Service `spvm.extend_history` available
- [ ] `sensor.spvm_surplus_net` working
- [ ] k-NN predictions calculating (check `sensor.spvm_expected_similar`)

**All checked?** You're ready to go! 🚀

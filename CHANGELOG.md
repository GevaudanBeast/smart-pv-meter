# Changelog

All notable changes to Smart PV Meter (SPVM) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.2] - 2025-11-10

### Fixed
- Fixed UTF-8 encoding issues throughout codebase (â€" → -, Â° → °)
- Fixed "Sun entity not available" error - sun.sun is now completely optional
- Fixed "Cannot get current conditions" error when sun.sun missing
- Fixed elevation filter causing unnecessary warnings at night
- Fixed confusing "expected_sensor" configuration field that served no purpose

### Changed
- sun.sun entity is now optional (uses elevation=0 if unavailable)
- Elevation filter is skipped automatically when sun.sun is not available
- Log message "No candidates after elevation filter" changed from WARNING to INFO
- More descriptive messages explaining normal behavior (e.g., "normal at night")
- Elevation filter threshold increased from 10° to 15° for better matching

### Removed
- Removed `CONF_EXPECTED_SENSOR` from configuration
- Removed "expected_sensor" field from config flow UI
- Removed automatic entity pre-fill that created confusion
- Removed all references to external expected sensor

### Improved
- Clearer log messages for normal night-time behavior
- Better handling of missing sun.sun entity
- Simplified configuration interface
- More user-friendly error messages with context

## [0.5.1] - 2025-11-10

### Fixed
- Fixed blocking I/O calls in event loop (manifest reading, pytz timezone)
- Fixed missing `HARD_CAP_W` constant causing ImportError
- Fixed `history.state_changes_during_period` API usage - entity_id must be string
- Fixed deprecated `config_entry` explicit assignment in OptionsFlow
- Fixed coordinator access pattern in sensor.py and diagnostics.py
- Fixed missing helper functions (state_to_float, convert_to_w, etc.)

### Changed
- Extended historical data period from 90 days to 3 years (1095 days)
- Improved error handling and logging in historical data retrieval
- Refactored `_get_historical_data()` to fetch each entity separately
- Lazy-loaded pytz timezone to avoid blocking calls during initialization

### Added
- Added 6 new helper functions to helpers.py
- Added proper async handling for all I/O operations
- Added NOTE_HARD_CAP constant for sensor attributes

### Technical
- All I/O operations are now properly async
- Historical data retrieval completely refactored
- Better separation of concerns in expected.py

## [0.5.0] - 2025-11-09

### Added
- Complete native Python implementation replacing Node-RED
- k-NN algorithm for production prediction using historical data
- Native coordination via DataUpdateCoordinator
- Complete UI configuration flows (config_flow + options_flow)
- Temporal smoothing for stable surplus calculations
- Full diagnostic support
- Comprehensive bilingual support (French/English)
- GitHub Actions CI/CD pipeline
- Unit tests
- HACS configuration

### Changed
- Migrated all calculations from Node-RED to Python
- Calculation rules now in Python:
  - `grid_power_auto = house_w - pv_w - battery_w`
  - `surplus_net` with 150W reserve, 3kW cap, and smoothing
- Historical data handling now native
- All state management via coordinator

### Removed
- Node-RED dependency completely removed
- External MQTT requirements removed
- Old flow-based architecture

## [0.4.0] - 2024-XX-XX

### Added
- Node-RED based implementation
- Basic surplus calculations
- Manual configuration via flows

### Changed
- Flow-based architecture
- External dependencies (Node-RED, MQTT)

## [0.3.0] - 2024-XX-XX

### Added
- Initial release
- Basic PV monitoring
- Simple surplus calculation

---

## Migration Guides

### From 0.5.1 to 0.5.2

**Automatic Migration**: No action required. Configuration is preserved.

**Optional Cleanup**:
1. Go to SPVM configuration
2. Save without changes
3. Old `expected_sensor` field will be removed from config

**Benefits**:
- No more encoding issues in UI
- Works without sun.sun entity
- Clearer log messages
- Simpler configuration

### From 0.5.0 to 0.5.1

**Automatic Migration**: Configuration preserved.

**Action Required**: None, but recommended:
1. Wait 24-48 hours for 3-year history to load
2. Call `spvm.reset_cache` to rebuild k-NN cache
3. Verify `samples_total` attribute increases

**Benefits**:
- Better seasonal predictions (3 years vs 90 days)
- All blocking calls eliminated
- More stable operation

### From 0.4.0 to 0.5.0

**Manual Migration Required**:

1. **Backup Node-RED flows**
2. **Install SPVM 0.5.0**
3. **Configure via UI**:
   - Map old sensors to new config
   - Set reserve_w (default: 150)
   - Set cap_max_w (default: 3000)
4. **Disable Node-RED flows**
5. **Test thoroughly**
6. **Remove Node-RED flows** when confirmed working

**Breaking Changes**:
- No Node-RED compatibility
- Different sensor naming
- New configuration system

---

## Version Support

| Version | Home Assistant | Support Status |
|---------|---------------|----------------|
| 0.5.2   | 2024.1+       | ✅ Supported   |
| 0.5.1   | 2024.1+       | ⚠️ Upgrade to 0.5.2 |
| 0.5.0   | 2024.1+       | ❌ Upgrade required |
| 0.4.x   | 2023.x+       | ❌ End of life |

---

## Known Issues

### Current Issues (0.5.2)

None currently known.

**Report issues**: https://github.com/GevaudanBeast/smart-pv-meter/issues

### Fixed Issues

- ✅ UTF-8 encoding problems
- ✅ sun.sun requirement
- ✅ Blocking I/O calls
- ✅ Missing HARD_CAP_W constant
- ✅ History API usage
- ✅ Deprecated config_entry assignment
- ✅ Confusing expected_sensor field

---

## Deprecation Notices

### Deprecated in 0.5.2
- **CONF_EXPECTED_SENSOR**: Removed, no replacement needed

### Deprecated in 0.5.0
- **Node-RED flows**: Completely replaced by native Python
- **MQTT configuration**: No longer needed

---

## Upgrade Instructions

### To 0.5.2 from 0.5.1

```bash
# 1. Download latest release
cd /config/custom_components/spvm
wget https://github.com/GevaudanBeast/smart-pv-meter/releases/download/v0.5.2/spvm.tar.gz

# 2. Backup current version
cd /config/custom_components
cp -r spvm spvm.backup

# 3. Extract new version
tar -xzf spvm.tar.gz -C spvm/

# 4. Restart Home Assistant
ha core restart

# 5. Verify version
grep version /config/custom_components/spvm/manifest.json
```

### To 0.5.2 from 0.5.0 or older

Follow same steps as above. Configuration will be automatically migrated.

---

## Future Roadmap

### Planned for 0.6.0
- [ ] Machine learning model improvements
- [ ] Additional prediction algorithms
- [ ] Performance optimization for large datasets
- [ ] Advanced weather integration
- [ ] Multi-inverter support

### Under Consideration
- Cloud-based predictions (optional)
- Mobile app integration
- Advanced analytics dashboard
- Export prediction data
- API for third-party integrations

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Project**: Smart PV Meter (SPVM)  
**Repository**: https://github.com/GevaudanBeast/smart-pv-meter  
**License**: MIT  
**Maintainer**: GevaudanBeast

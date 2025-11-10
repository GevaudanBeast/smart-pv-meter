# Changelog

All notable changes to Smart PV Meter will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-11-09

### Added
- Complete integration rebuild from scratch
- Native k-NN algorithm for expected production calculation
  - Weather-based similarity matching (lux, temperature, humidity, sun elevation)
  - Configurable weights and time windows
  - Automatic fallback to time-based prediction
  - 90-day historical analysis
- Rolling average smoothing for `surplus_net`
  - Configurable smoothing window (default 45s)
  - Stable control signal for Solar Optimizer
- DataUpdateCoordinator for efficient data management
- Comprehensive diagnostics support
- Two new services:
  - `spvm.recompute_expected_now` - Force immediate recalculation
  - `spvm.reset_cache` - Clear cached historical data
- Optional debug sensor (`spvm_expected_debug`) for troubleshooting
- Full bilingual documentation (English + French)
- GitHub Actions workflow for automatic releases
- Unit tests for all calculations
- pyproject.toml for code quality (black, ruff)
- HACS compatibility

### Changed
- **BREAKING**: Configuration structure updated
  - New k-NN parameters
  - Update interval now configurable
  - Smoothing window configurable
- Sensor names and IDs standardized
- Improved configuration flow with detailed descriptions
- Better error handling and logging
- All unit conversions (kW ↔ W) now handled internally
- Options flow now properly registered

### Fixed
- Options flow "Configure" button now visible
- Unit conversion issues resolved
- Cache management improved
- State updates more reliable
- Type hints added throughout

### Security
- Sensor ID redaction in diagnostics

## [0.4.0] - 2025-10-XX (Previous version)

### Initial features
- Basic surplus calculations
- Grid power auto-calculation
- Battery integration
- External expected production sensor support
- Basic configuration flow

## [Unreleased]

### Planned
- Machine learning model training UI
- Advanced weather integration (forecast.solar, etc.)
- Historical performance analytics dashboard
- Energy flow visualization
- Multi-inverter support
- Cloud storage for model backups

---

## Migration Guide: 0.4.x → 0.5.0

### Breaking Changes

1. **Configuration Parameters**
   - New k-NN parameters added (k, windows, weights)
   - `update_interval` and `smoothing_window` are now configurable
   - Old configurations will need manual update via Options

2. **Sensor Names**
   - All sensor IDs now prefixed with `spvm_`
   - Labels improved for clarity

### Migration Steps

1. **Backup your current configuration**
   ```bash
   cp -r custom_components/spvm custom_components/spvm.backup
   ```

2. **Update the integration**
   - Via HACS: Update to v0.5.0
   - Manually: Replace files with new version

3. **Restart Home Assistant**

4. **Reconfigure the integration**
   - Go to Settings → Devices & Services
   - Find "Smart PV Meter"
   - Click "Configure"
   - Review and adjust new parameters (k-NN settings, intervals)

5. **Update automations/Solar Optimizer**
   - Change sensor references if needed
   - No changes needed if using `sensor.spvm_surplus_net`

6. **Monitor for 24 hours**
   - Check that k-NN is learning (view debug sensor if enabled)
   - Verify calculations are correct
   - Adjust parameters if needed

### New Capabilities

After migrating, you can:
- Fine-tune k-NN weights for your specific system
- Adjust smoothing for optimal Solar Optimizer response
- Use services to force recalculation or clear cache
- Enable debug sensor to understand predictions

### Support

If you encounter issues during migration:
1. Check the [Troubleshooting](README.md#troubleshooting) section
2. Enable debug logging:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.spvm: debug
   ```
3. Open an issue on GitHub with debug logs

---

**For detailed documentation, see [README.md](README.md)**

#!/usr/bin/env python3
"""
SPVM Diagnostic Script - Standalone solar model tester.

Run this script to test the solar model with your configuration.
Usage: python3 diagnostic.py
"""

import sys
from datetime import datetime, timezone

# Add the SPVM path for Home Assistant installations
sys.path.insert(0, '/config/custom_components/spvm')

from solar_model import SolarInputs, compute as solar_compute

# =============================================================================
# CONFIGURATION - MODIFY THESE VALUES FOR YOUR INSTALLATION
# =============================================================================

# Location (use Google Maps to find your coordinates)
LATITUDE = 43.45       # Your latitude (e.g., 43.45 for southern France)
LONGITUDE = 5.61       # Your longitude (e.g., 5.61 for Provence)
ALTITUDE_M = 300       # Altitude in meters

# Panel configuration - Array 1 (main)
PANEL_PEAK_W = 3000    # Total peak power in Watts
PANEL_TILT = 30        # Tilt angle in degrees (0 = flat, 90 = vertical)
PANEL_AZIMUTH = 180    # Azimuth (0 = North, 90 = East, 180 = South, 270 = West)

# Panel configuration - Array 2 (optional, set to 0 to disable)
ARRAY2_PEAK_W = 0      # Second array peak power (0 = disabled)
ARRAY2_TILT = 15       # Second array tilt
ARRAY2_AZIMUTH = 180   # Second array azimuth

# System parameters
SYSTEM_EFFICIENCY = 0.85  # Efficiency (0.80 - 0.90 typical)

# Weather inputs (set to None if not available)
CLOUD_PCT = None       # Cloud coverage 0-100%
TEMP_C = None          # Temperature in Celsius
LUX = None             # Lux sensor reading

# =============================================================================
# DIAGNOSTIC CODE - DO NOT MODIFY BELOW
# =============================================================================

def main():
    now_utc = datetime.now(timezone.utc)

    print("=" * 60)
    print("SPVM DIAGNOSTIC - Solar Model Test")
    print("=" * 60)
    print(f"\nDate/Time UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Local time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📍 Location Configuration:")
    print(f"   Latitude: {LATITUDE}°")
    print(f"   Longitude: {LONGITUDE}°")
    print(f"   Altitude: {ALTITUDE_M}m")

    print("\n⚡ Panel Configuration (Array 1):")
    print(f"   Peak power: {PANEL_PEAK_W}W")
    print(f"   Tilt: {PANEL_TILT}°")
    print(f"   Azimuth: {PANEL_AZIMUTH}° (180 = South)")

    if ARRAY2_PEAK_W > 0:
        print(f"\n⚡ Panel Configuration (Array 2):")
        print(f"   Peak power: {ARRAY2_PEAK_W}W")
        print(f"   Tilt: {ARRAY2_TILT}°")
        print(f"   Azimuth: {ARRAY2_AZIMUTH}°")

    print(f"\n⚙️  System efficiency: {SYSTEM_EFFICIENCY * 100:.0f}%")

    # Create inputs
    inputs = SolarInputs(
        dt_utc=now_utc,
        lat_deg=LATITUDE,
        lon_deg=LONGITUDE,
        altitude_m=ALTITUDE_M,
        panel_tilt_deg=PANEL_TILT,
        panel_azimuth_deg=PANEL_AZIMUTH,
        panel_peak_w=PANEL_PEAK_W,
        system_efficiency=SYSTEM_EFFICIENCY,
        cloud_pct=CLOUD_PCT,
        temp_c=TEMP_C,
        lux=LUX,
        array2_peak_w=ARRAY2_PEAK_W,
        array2_tilt_deg=ARRAY2_TILT,
        array2_azimuth_deg=ARRAY2_AZIMUTH,
    )

    # Compute
    result = solar_compute(inputs)

    print("\n" + "=" * 60)
    print("☀️  SOLAR POSITION")
    print("=" * 60)
    print(f"   Elevation: {result.elevation_deg:.1f}° {'(DAY)' if result.elevation_deg > 0 else '(NIGHT)'}")
    print(f"   Azimuth: {result.azimuth_deg:.1f}°")
    print(f"   Declination: {result.declination_deg:.1f}°")
    print(f"   Incidence angle: {result.incidence_deg:.1f}°")

    print("\n" + "=" * 60)
    print("🌤️  IRRADIANCE (Clear-sky model)")
    print("=" * 60)
    print(f"   GHI (horizontal): {result.ghi_clear_wm2:.1f} W/m²")
    print(f"   POA (on panels): {result.poa_clear_wm2:.1f} W/m²")

    print("\n" + "=" * 60)
    print("⚡ EXPECTED PRODUCTION")
    print("=" * 60)
    print(f"   Clear-sky (no corrections): {result.expected_clear_w:.1f}W")
    print(f"   Corrected (with weather): {result.expected_corrected_w:.1f}W")

    if ARRAY2_PEAK_W > 0 and result.array2_expected_clear_w:
        print(f"\n   Array 2 contribution:")
        print(f"     Clear-sky: {result.array2_expected_clear_w:.1f}W")
        print(f"     Corrected: {result.array2_expected_corrected_w:.1f}W")

    # Diagnostics
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSTIC")
    print("=" * 60)

    if result.elevation_deg <= 0:
        print("   ⚠️  Sun is below horizon (nighttime)")
        print("      Production = 0W is expected")
    elif result.expected_corrected_w < 10:
        print("   ⚠️  Very low production expected")
        print("      Check your panel configuration:")
        print("      - Azimuth (180 = South in northern hemisphere)")
        print("      - Tilt angle (typically 20-40° for optimal)")
        print("      - Peak power setting")
    else:
        print("   ✅ Solar model working correctly")
        print(f"      Expected production: {result.expected_corrected_w:.0f}W")

    print("\n" + "=" * 60)
    print("💡 TIP: With Open-Meteo enabled (default in v0.7.5+),")
    print("    real irradiance data replaces this clear-sky model")
    print("    for more accurate predictions.")
    print("=" * 60)


if __name__ == "__main__":
    main()

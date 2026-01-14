"""Diagnostics support for SPVM."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SPVMCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Redact sensitive information (sensor entity IDs)
    def redact_sensors(data: dict) -> dict:
        return {k: "**REDACTED**" if k.endswith("_sensor") else v for k, v in data.items()}

    diagnostics = {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "version": entry.version,
        },
        "config": redact_sensors(dict(entry.data)),
        "options": redact_sensors(dict(entry.options)),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_time": (
                coordinator.last_update_success_time.isoformat()
                if coordinator.last_update_success_time
                else None
            ),
        },
    }

    # Add current data if available
    if coordinator.data:
        diagnostics["current_data"] = {
            "expected_w": coordinator.data.expected_w,
            "yield_ratio_pct": coordinator.data.yield_ratio_pct,
            "surplus_net_w": coordinator.data.surplus_net_w,
        }
        # Add key model attributes (non-sensitive)
        attrs = coordinator.data.attrs or {}
        diagnostics["model_info"] = {
            "irradiance_source": attrs.get("irradiance_source"),
            "open_meteo_enabled": attrs.get("open_meteo_enabled"),
            "elevation_deg": attrs.get("model_elevation_deg"),
            "ghi_wm2": attrs.get("ghi_clear_wm2"),
            "poa_wm2": attrs.get("poa_clear_wm2"),
        }

    return diagnostics

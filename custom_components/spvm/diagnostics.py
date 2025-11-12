"""Diagnostics support pour SPVM v0.6.0."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# ⚠️ CHANGEMENT v0.6.0: Imports depuis modules v06
from .const_v06 import DOMAIN
from .coordinator_v06 import SPVMCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Retourner les diagnostics pour une config entry."""
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    diagnostics = {
        "entry_id": entry.entry_id,
        "entry_title": entry.title,
        "entry_version": entry.version,
        "config_data": {k: v for k, v in entry.data.items() if not k.endswith("_sensor")},
        "options_data": {k: v for k, v in entry.options.items() if not k.endswith("_sensor")},
        "coordinator_data": coordinator.data if coordinator.data else "No data",
        "last_update_success": coordinator.last_update_success,
        "last_update_time": (
            coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None
        ),
    }

    # Note: Solar model n'a pas de cache contrairement au k-NN
    if coordinator.data:
        diagnostics["model_type"] = coordinator.data.get("model_type", "unknown")
        diagnostics["solar_elevation"] = coordinator.data.get("solar_elevation")
        diagnostics["expected_w"] = coordinator.data.get("expected_w")

    return diagnostics

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
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    diagnostics = {
        "entry_id": entry.entry_id,
        "entry_title": entry.title,
        "entry_version": entry.version,
        "config_data": {
            k: v for k, v in entry.data.items() 
            if not k.endswith("_sensor")
        },
        "options_data": {
            k: v for k, v in entry.options.items() 
            if not k.endswith("_sensor")
        },
        "coordinator_data": coordinator.data if coordinator.data else "No data",
        "last_update_success": coordinator.last_update_success,
        "last_update_time": (
            coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None
        ),
        "last_calculation_time": (
            coordinator.last_calculation_time.isoformat()
            if coordinator.last_calculation_time
            else None
        ),
    }

    # Add k-NN cache info safely using public property
    if coordinator.data:
        diagnostics["knn_cache_size"] = coordinator.cache_size
        
        # Add calculator status
        if coordinator.calculator:
            diagnostics["calculator_initialized"] = True
        else:
            diagnostics["calculator_initialized"] = False

    return diagnostics

"""Diagnostics support pour SPVM."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SPVMCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Retourner les diagnostics pour une config entry."""
    coordinator: SPVMCoordinator = hass.data[DOMAIN][entry.entry_id]

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

    # Ajouter les info k-NN si disponibles
    if coordinator.data:
        diagnostics["knn_cache_size"] = len(coordinator.expected_calculator._cache)
        diagnostics["knn_normalization"] = coordinator.expected_calculator._normalization

    return diagnostics

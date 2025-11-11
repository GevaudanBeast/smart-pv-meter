"""Smart PV Meter (SPVM) integration for Home Assistant."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import SPVMCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up SPVM integration (YAML not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SPVM from a config entry."""
    # Log version for diagnostics (async file read)
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        version = await hass.async_add_executor_job(
            lambda: json.loads(manifest_path.read_text()).get("version", "unknown")
        )
    except Exception:
        version = "unknown"
    
    _LOGGER.info(
        "Setting up SPVM integration (version=%s, entry_id=%s)",
        version,
        entry.entry_id,
    )

    # Create coordinator for expected production calculation
    coordinator = SPVMCoordinator(hass, entry)
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Fetch initial data
    _LOGGER.debug("Starting initial data fetch...")
    await coordinator.async_config_entry_first_refresh()

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Register services
    await _async_register_services(hass, coordinator)

    _LOGGER.info("SPVM integration setup complete")
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("SPVM options updated Ã¢â€ â€™ reloading entry %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("SPVM entry %s unloaded", entry.entry_id)
    
    return unload_ok


async def _async_register_services(
    hass: HomeAssistant, coordinator: SPVMCoordinator
) -> None:
    """Register SPVM services."""
    
    async def handle_recompute_expected(call) -> None:
        """Handle recompute_expected_now service call."""
        _LOGGER.info("Service spvm.recompute_expected_now called")
        await coordinator.async_request_refresh()
    
    async def handle_reset_cache(call) -> None:
        """Handle reset_cache service call."""
        _LOGGER.info("Service spvm.reset_cache called")
        coordinator.reset_cache()
        await coordinator.async_request_refresh()
    
    hass.services.async_register(
        DOMAIN, "recompute_expected_now", handle_recompute_expected
    )
    hass.services.async_register(
        DOMAIN, "reset_cache", handle_reset_cache
    )

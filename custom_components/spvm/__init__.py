"""Smart PV Meter (SPVM) integration for Home Assistant."""
from __future__ import annotations

import asyncio
import json
import logging
import time
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
    
    _LOGGER.info("=" * 60)
    _LOGGER.info("SPVM setup starting (version=%s, entry_id=%s)", version, entry.entry_id)
    
    try:
        # Create coordinator for expected production calculation
        _LOGGER.info("Creating coordinator...")
        coordinator = SPVMCoordinator(hass, entry)
        
        # Store coordinator
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
        }
        _LOGGER.info("Coordinator stored in hass.data")

        # Fetch initial data with timeout (non-blocking)
        _LOGGER.info("Fetching initial data (timeout: 120s)...")
        fetch_start = time.time()
        
        try:
            async with asyncio.timeout(120):  # 2 minutes max
                await coordinator.async_config_entry_first_refresh()
            
            fetch_elapsed = time.time() - fetch_start
            _LOGGER.info("Initial data loaded successfully in %.2fs", fetch_elapsed)
            
        except asyncio.TimeoutError:
            _LOGGER.warning(
                "Initial data fetch TIMEOUT after 120s - continuing setup, "
                "data will be fetched in background"
            )
            # Don't fail setup, coordinator will retry
            
        except Exception as err:
            _LOGGER.warning(
                "Initial data fetch failed: %s - continuing setup, "
                "data will be fetched in background",
                err
            )
            # Don't fail setup, coordinator will retry

        # Setup platforms
        _LOGGER.info("Setting up sensor platform...")
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info("Sensor platform setup completed")

        # Register update listener for options changes
        entry.async_on_unload(entry.add_update_listener(_async_update_listener))

        # Register services
        _LOGGER.info("Registering services...")
        await _async_register_services(hass, coordinator)
        _LOGGER.info("Services registered")
        
        _LOGGER.info("SPVM setup COMPLETED successfully")
        _LOGGER.info("=" * 60)
        return True
        
    except Exception as err:
        _LOGGER.error("SPVM setup FAILED: %s", err, exc_info=True)
        _LOGGER.info("=" * 60)
        raise


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("SPVM options updated → reloading entry %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading SPVM entry %s", entry.entry_id)
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("SPVM entry %s unloaded successfully", entry.entry_id)
    else:
        _LOGGER.warning("SPVM entry %s unload failed", entry.entry_id)
    
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
    _LOGGER.debug("Services registered: recompute_expected_now, reset_cache")

"""Smart PV Meter (SPVM) integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .coordinator import SPVMCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart PV Meter from a config entry."""
    # ✅ Récupérer la version du manifest SANS lire le fichier en synchrone.
    integration = await async_get_integration(hass, DOMAIN)
    version = integration.version or "unknown"

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["version"] = version

    # Coordinator par entry_id (pour services & reload d’options)
    coordinator = SPVMCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Premier refresh (async, safe)
    await coordinator.async_config_entry_first_refresh()

    # Charger plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listener d’options
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Services
    await _async_register_services(hass, coordinator)

    _LOGGER.debug("SPVM initialized (version: %s, entry_id: %s)", version, entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update: reload the entry to apply changes cleanly."""
    _LOGGER.info("SPVM options updated; reloading config entry %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_services(hass: HomeAssistant, coordinator: SPVMCoordinator) -> None:
    """Register SPVM services (recompute_expected_now, reset_cache)."""
    import logging
    _log = logging.getLogger(__name__)

    async def handle_recompute_expected(call) -> None:
        """Force recompute of expected_now and refresh entities."""
        _log.info("Service spvm.recompute_expected_now called")
        # Pas de param pour l’instant; simple refresh
        await coordinator.async_request_refresh()

    async def handle_reset_cache(call) -> None:
        """Reset any internal caches and refresh."""
        _log.info("Service spvm.reset_cache called")
        coordinator.reset_cache()
        await coordinator.async_request_refresh()

    # Idempotent: si déjà enregistrés, HA ignore silencieusement
    hass.services.async_register(DOMAIN, "recompute_expected_now", handle_recompute_expected)
    hass.services.async_register(DOMAIN, "reset_cache", handle_reset_cache)

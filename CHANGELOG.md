# SPVM - CHANGELOG & RELEASE NOTES

## 📦 Version 0.7.7 - Correctif Open-Meteo (August 2026)

### Fixed
- 🐛 **f-string invalide dans `coordinator.py`** - `f"{real_gti:.1f if real_gti else 'N/A'}"` levait une `ValueError` à chaque cycle de rafraîchissement
  - Le spécificateur de format d'une f-string ne peut pas contenir d'expression conditionnelle
  - Le journal affichait `Open-Meteo fetch failed, using clear-sky model: Invalid format specifier ...` alors qu'aucun échec réseau n'avait eu lieu
  - Corrigé via une variable intermédiaire, en reprenant l'idiome déjà utilisé dans `open_meteo.py`

### Improved
- 🎯 **Portée du `try` Open-Meteo réduite au seul appel réseau `fetch_current()`**
  - Le traitement des données et la journalisation sont sortis du `try`
  - Une erreur de journalisation ne peut plus déclencher le repli sur le modèle de ciel clair

### Technical Details
- Les neuf fichiers Python ont été analysés par parcours d'arbre syntaxique, cette occurrence était la seule
- Aucune logique de calcul photovoltaïque modifiée
- Aucune dépendance ajoutée

---

## 📦 Version 0.7.6 - Code Cleanup & Maintenance (January 2026)

### Removed
- 🗑️ **Obsolete files removed** - Cleaned up legacy code from k-NN era
  - `helpers.py` - Dead code (unused k-NN distance functions)
  - `services.yaml` - Referenced obsolete k-NN services
  - `tests/` directory - Empty/unused test structure
  - Various user-specific diagnostic MD files

### Improved
- 🔧 **diagnostics.py** - Cleaned up, removed k-NN references, modern data structure
- 📝 **diagnostic.py** - Rewritten as standalone test script with multi-array support
- 📖 **README.md** - Updated with latest features (Open-Meteo, Multi-Array, Lux validation)

### Technical Details
- Removed ~300 lines of dead code
- Codebase is now cleaner and more maintainable
- No functional changes - same features as v0.7.5

---

## 📦 Version 0.7.5 - Open-Meteo Real Irradiance (January 2026)

### Added
- 🌍 **Open-Meteo API integration** - Real solar irradiance data instead of theoretical clear-sky model
  - Fetches actual GHI (Global Horizontal Irradiance) from Open-Meteo
  - Uses GTI (Global Tilted Irradiance) for accurate POA calculation
  - Automatic fallback to clear-sky model if API unavailable
  - 5-minute cache to avoid API rate limits
- 📊 **New diagnostic attributes**:
  - `irradiance_source`: "open_meteo" or "clear_sky_model"
  - `open_meteo_enabled`: Whether Open-Meteo is configured
  - `open_meteo_ghi_wm2`: Real GHI from Open-Meteo
  - `open_meteo_gti_wm2`: Real GTI (POA) from Open-Meteo
- 🔍 **Lux sensor as trend validator** - Cross-validates Open-Meteo with local lux
  - `lux_validation`: "consistent", "lux_high", or "lux_low"
  - `lux_ghi_ratio`: Ratio of actual lux vs expected from GHI
  - Detects if Open-Meteo data differs from local conditions
- 🌡️ **Weather data fallback** - Uses Open-Meteo cloud/temp if local sensors unavailable

### Benefits
- **More accurate predictions** - Real weather data vs theoretical clear-sky
- **No calibration needed** - Works out of the box for any location
- **Universal** - Same accuracy regardless of local sensors
- **Future-ready** - Foundation for forecast features (J+1, J+7)

### Configuration
Open-Meteo is **enabled by default**. To disable:
```yaml
use_open_meteo: false  # Reverts to clear-sky model
```

### Technical Details
- API endpoint: `https://api.open-meteo.com/v1/forecast`
- Parameters: `shortwave_radiation`, `global_tilted_irradiance`, `cloud_cover`, `temperature_2m`
- GTI uses panel tilt/azimuth for accurate POA calculation
- When real irradiance is available, cloud/lux corrections are skipped (already in data)
- Only temperature and seasonal shading corrections are applied

---

## 📦 Version 0.7.4 - Multi-Array Support (January 2026)

### Added
- 🆕 **Multi-array support** - Model installations with multiple panel orientations
  - `array2_peak_w`: Peak power of second array (W), 0 = disabled
  - `array2_tilt_deg`: Tilt angle of second array (default: 15°)
  - `array2_azimuth_deg`: Azimuth of second array (default: 180° South)
- 📊 **New diagnostic attributes** for array 2:
  - `array2_incidence_deg`: Incidence angle on array 2
  - `array2_poa_clear_wm2`: POA irradiance on array 2
  - `array2_expected_clear_w`: Clear-sky power for array 2
  - `array2_expected_corrected_w`: Corrected power for array 2
- 📝 **Enhanced logging** - Separate breakdown for each array

### Use Cases
- **Mixed roof orientations** - Main array on south-facing roof + second array on east/west
- **Pergola installations** - Main panels at 30° + pergola panels at 15°
- **Ground + roof systems** - Different tilts and orientations
- **Split installations** - Any two-group configuration with different geometries

### Configuration Example
```yaml
# Main array (e.g., 6 panels × 450W at 30° tilt)
panel_peak_w: 2700
panel_tilt_deg: 30
panel_azimuth_deg: 180

# Second array (e.g., 4 panels × 500W on pergola at 15°)
array2_peak_w: 2000
array2_tilt_deg: 15
array2_azimuth_deg: 180
```

### Technical Details
- Each array calculates its own incidence angle and POA irradiance
- Same weather corrections (cloud, lux, temperature, shading) apply to both arrays
- Results are summed for total expected production
- `cap_max_w` applies to the combined total (for inverter/contract limits)

---

## 📦 Version 0.7.3 - Lux Spike Filter (January 2026)

### Added
- ⚡ **Lux spike filter** - Rejects sudden lux variations caused by reflections
  - New parameter `lux_max_change_pct` (default: 100%)
  - Detects when lux changes > threshold between readings
  - Falls back to cloud% correction when spike detected
  - Logs warning with details when filtering occurs
- 🔍 **New diagnostic attributes**
  - `lux_raw`: Raw lux value from sensor (even when filtered)
  - `lux_spike_filtered`: `true` when a reflection spike was detected

### Use Case
Metallic surfaces (stainless steel tubes, window frames) can reflect sunlight onto the lux sensor, causing unrealistic spikes. This filter detects and ignores these readings.

### Example Log
```
⚡ SPVM LUX SPIKE FILTERED: Variation de 300% détectée (1500 → 6000 lux).
   Probable reflet (seuil: 100%). Valeur ignorée, utilisation de la correction cloud.
```

### Configuration
```yaml
lux_max_change_pct: 100   # Max 100% change between readings (default)
lux_max_change_pct: 150   # More tolerant (allows 150% changes)
lux_max_change_pct: 50    # Stricter (filters smaller variations)
```

---

## 📦 Version 0.7.2 - Lux Sensor Placement Detection (December 2025)

### Added
- ⚠️ **Automatic lux sensor placement warning** - Detects when lux sensor may be incorrectly placed
  - Triggers when lux readings are < 25% of theoretical clear-sky value
  - Warns if sensor might be under panels, in shade, or obstructed
  - Provides actionable solutions in log warnings
  - Includes comparison: actual lux vs theoretical lux at current sun elevation
- 📖 **Comprehensive lux sensor documentation** - Added placement requirements to README
  - Clear guidance on correct vs incorrect placement
  - Examples of common placement mistakes (under panels, under overhangs, etc.)
  - Solutions for incorrectly placed sensors
  - Cross-references in configuration parameter sections

### Improved
- 🎯 **Better diagnostic feedback** - Users now immediately see when low estimates are caused by sensor placement
- 📝 **Enhanced README** - Lux sensor section now prominently warns about placement requirements
- 🔍 **Proactive issue detection** - System alerts users to configuration issues before they need to debug

### Technical Details
- Coordinator: Added lux placement validation after diagnostic logging
- Theoretical lux calculation: GHI × 120 (approximate W/m² to lux conversion)
- Warning threshold: lux_factor < 0.25 AND lux_ratio < 0.25 AND sun elevation > 10°
- README: Added dedicated "Lux Sensor Placement Requirements" section with visual indicators

### Use Cases
1. **Troubleshooting low estimates** - Log warnings immediately identify sensor placement issues
2. **Initial setup** - Users know upfront how to place lux sensor correctly
3. **Post-installation validation** - System validates sensor placement automatically during operation

### Example Warning Log
```
⚠️  SPVM LUX SENSOR PLACEMENT WARNING:
  Your lux sensor is reading 751 lux while theoretical clear-sky lux
  should be ~28800 lux at 21.1° sun elevation.
  This is only 2.6% of expected, causing production estimate
  to be reduced to 10% of clear-sky value.
  ⚡ COMMON CAUSE: Lux sensor placed under solar panels or in shaded location.
  📍 SOLUTION: Either:
     1. Remove lux sensor from SPVM configuration (use cloud% instead)
     2. Relocate sensor to unobstructed sky view
     3. Increase 'lux_floor_factor' to 0.5-0.7 in configuration
```

## 📦 Version 0.7.1 - Robustness & Diagnostics (December 2025)

### Fixed
- 🐛 **Config flow error 500 resolved** - Configuration editor now opens reliably
  - Complete try/except protection in schema builder
  - Fallback to minimal schema if errors occur
  - Detailed error logging with stack traces for debugging
- 🔧 **Sensor unavailability tolerance** - Integration no longer crashes when sensors temporarily unavailable
  - Cache of last known PV value used when sensor becomes "unknown" or "unavailable"
  - Detailed warning logs showing exact sensor state when issues occur
  - Prevents "pv_sensor has no numeric state" errors during Home Assistant restarts

### Added
- 📊 **Comprehensive diagnostic logging** - Detailed production estimate breakdown
  - All solar model parameters (panel_peak_w, efficiency, tilt, azimuth, location)
  - Solar geometry (elevation, azimuth, incidence angles)
  - Irradiance values (GHI, POA clear-sky)
  - Step-by-step power calculation (clear-sky → corrections → degradation → cap)
  - All correction factors (lux, cloud, temperature) with actual sensor values
  - Current production vs expected with yield ratio
- 🔍 **Enhanced error messages** - Config validation errors now show field-specific details

### Improved
- 🛡️ **Config flow resilience** - Robust error handling at all levels
  - Schema construction protected with try/except
  - Validation errors caught and logged
  - User-friendly error messages with troubleshooting hints
- 📝 **Better debugging** - All errors logged with `exc_info=True` for full stack traces
- ⚡ **Startup reliability** - No longer fails if PV sensor not ready at startup

### Technical Details
- Coordinator: Added `_last_pv_w` cache for sensor fallback
- Config flow: Full try/except wrapping of `_schema()` function with minimal fallback schema
- New error message strings: "unknown", "schema_error" in translations
- Diagnostic logs use INFO level for easy visibility in Home Assistant logs

### Use Cases
1. **Configuration issues** - Open logs after config flow errors to see exact cause
2. **Low production estimates** - Check "SPVM DIAGNOSTIC" logs to identify misconfigured parameters
3. **Sensor reliability** - System continues running even when PV sensor becomes temporarily unavailable
4. **Home Assistant restarts** - Integration survives restarts even if Envoy integration loads later

### Debugging Guide
When facing issues:
1. Check Home Assistant logs (Settings → System → Logs)
2. Search for "SPVM DIAGNOSTIC" to see full production estimate breakdown
3. Search for "SPVM _schema" or "SPVM config flow" to see configuration errors
4. All errors include full stack traces for GitHub issue reports

---

## 📦 Version 0.6.9 - Configurable Lux Correction & Seasonal Shading (November 2025)

### Added
- ✨ **Configurable lux correction parameters** - Fine-tune predictions based on your installation
  - `lux_min_elevation_deg` (default: 5°) - Minimum elevation to use lux correction
  - `lux_floor_factor` (default: 0.1) - Minimum correction factor floor (0.01-0.5)
- 🌲 **Seasonal shading support** - Compensate for trees, buildings casting shadows
  - `shading_winter_pct` (default: 0%) - Additional shading percentage in winter
  - `shading_month_start` (default: 11) - Month when shading period starts
  - `shading_month_end` (default: 2) - Month when shading period ends
- 📖 **Complete user guide** - [PARAMETRES_CORRECTION.md](PARAMETRES_CORRECTION.md) with examples and FAQ

### Improved
- 🎯 **More accurate predictions at low sun angles** - Configurable lux floor prevents overestimation
- 🌤️ **Better thick cloud detection** - Lower lux_floor_factor (0.02-0.05) for very cloudy conditions
- 📅 **Year-wrapping logic** - Shading periods crossing year boundary (Nov→Feb) handled automatically

### Use Cases
1. **Trees blocking winter sun** - Set shading_winter_pct to reduce predictions in winter months
2. **Very overcast conditions** - Lower lux_floor_factor to allow predictions down to 2-5%
3. **Buildings casting shadows** - Define custom shading period (e.g., June-August for high sun)

### Technical Details
- `_lux_correction_factor()` now accepts configurable min_elevation and floor_factor parameters
- New `_seasonal_shading_factor()` function applies temporal corrections
- All corrections cumulative: lux × temperature × shading
- Configuration via Home Assistant UI (Settings → Devices & Services → SPVM → Configure)

### Documentation
- Added PARAMETRES_CORRECTION.md with calibration guide
- 3 detailed use case examples
- FAQ section
- Monitoring section showing how to verify corrections

## 📦 Version 0.6.8 - Lux-based Correction (November 2025)

### Added
- 🆕 **Lux-based correction** - More accurate predictions in cloudy conditions
- ✨ Uses real lux sensor to detect thick clouds vs thin clouds
- 📊 New attributes: `lux_factor`, `lux_correction_active`, `lux_now`
- 🎯 Fixes overestimation when cloud_pct underestimates actual conditions

### Technical Details
- Compares actual lux vs theoretical clear-sky lux (80000 × sin(elevation))
- Minimum elevation 5° to avoid unreliable low-sun readings
- Floor factor 0.1 prevents complete zeroing
- Only activates when lux sensor available and sun > 5° elevation

## 📦 Version 0.6.7 - Fix ZIP Extraction Path (November 2025)

### Fixed
- ✅ **Fix ZIP extraction path** : Le ZIP contient maintenant les fichiers directement à la racine (sans préfixe `custom_components/spvm/`)
- ✅ **Fix double nesting** : Correction du problème où les fichiers étaient extraits dans `/config/custom_components/spvm/custom_components/spvm/`

### Technical Details
- When Home Assistant extracts the ZIP to `/config/custom_components/spvm/`, it expects the ZIP to contain files directly at root level
- Previous structure included `custom_components/spvm/` prefix in the ZIP, causing double nesting
- Workflow now creates ZIP from within the component directory: `cd custom_components/spvm && zip -r ../../spvm.zip .`
- ZIP now contains: `__init__.py`, `manifest.json`, `translations/`, etc. directly at root

## 📦 Version 0.6.6 - Hotfix HACS Structure (November 2025)

### Fixed
- ✅ **Fix HACS ZIP structure** : Le ZIP contient maintenant `custom_components/spvm/` au lieu de `spvm/`
- ✅ **Fix installation HACS** : Correction du problème de structure `spvm/spvm` lors de l'installation
- ✅ **Fix workflow release** : Le ZIP est créé avec la bonne structure pour HACS

### Technical Details
- With `"content_in_root": false`, HACS expects ZIP structure: `custom_components/integration_name/`
- Previous releases had incorrect structure: `spvm/` instead of `custom_components/spvm/`
- This caused HACS to create `custom_components/spvm/spvm/` structure (double nesting)
- Workflow now uses: `zip -r spvm.zip custom_components/spvm/`

## 📦 Version 0.6.5 - Hotfix HACS (November 2025)

### Fixed
- ✅ **Fix HACS installation** : Correction de la configuration HACS pour permettre l'installation depuis HACS
- ✅ **Fix workflow release** : Le fichier ZIP généré s'appelle maintenant `spvm.zip` (sans numéro de version)
- ✅ **Fix hacs.json** : Le champ `filename` pointe maintenant vers `spvm.zip` au lieu de `spvm-0.6.4.zip`

### Technical Details
- HACS requires a static filename (without version number) in `hacs.json`
- The release workflow now creates `spvm.zip` instead of `spvm-{version}.zip`
- This allows HACS to automatically download the latest release without hardcoding version numbers

## 📦 Version 0.6.4 - Release (November 2025)

### Changed
- Version bump to 0.6.4
- Updated GitHub workflow for automatic releases on tag push
- Minor documentation improvements

## 🐛 Version 0.6.3 - Hotfix (November 2025)

### Corrections de bugs critiques
- ✅ **Fix 400 Bad Request** : Correction de l'erreur lors du chargement du flux de configuration
- ✅ **Fix 500 Internal Server Error** : Correction due aux fonctions de coercition non sérialisables
- ✅ **Fix SyntaxError** : Correction de la syntaxe invalide dans les fonctions helper
- ✅ **Fix diagnostics** : Correction de l'accès au coordinator dans diagnostics.py
- ✅ **Fix calcul solaire** : Correction du bug dans l'équation du temps (double conversion math.degrees)
- ✅ **Fix calcul production attendue** : La réserve ne doit plus être soustraite de expected_w (uniquement de surplus_net_w)
- ✅ **Fix unités mixtes** : Ajout d'unités par capteur (W/kW) au lieu d'une seule unité globale
- ✅ **Options restaurées** : Le menu "Configurer" est de nouveau accessible dans les paramètres

### Nettoyage du code
- 🧹 Suppression de **234 lignes** de code mort et fichiers legacy :
  - `expected.py` : Ancien modèle solaire v0.6.0 non utilisé
  - `const_old.py` : Constantes k-NN v0.5.x obsolètes
  - `tests/test_units.py` : Tests cassés avec imports incorrects
- 📦 Mise à jour de la version dans sensor.py (v0.6.2 → v0.6.3)

### Causes des problèmes
- La fonction `async_get_options_flow` devait être une méthode statique de la classe `SPVMConfigFlow`
- Les fonctions personnalisées `_coerce_float` et `_coerce_int` n'étaient pas sérialisables par `voluptuous_serialize`
- Syntaxe invalide dans les fonctions helper `req_entity` et `opt_entity`
- Accès incorrect au coordinator dans diagnostics.py avec `["coordinator"]`

### Fichiers modifiés
- `config_flow.py` : Méthode statique `async_get_options_flow`, utilisation de `vol.Coerce()`
- `diagnostics.py` : Correction de l'accès au coordinator
- `sensor.py` : Mise à jour de la version
- `.gitignore` : Ajout pour ignorer les fichiers cache Python

### Améliorations
- 🏷️ **Noms d'entités courts (anglais)** : Les entités utilisent maintenant des noms courts en anglais
  - `sensor.spvm_expected_production` au lieu de `sensor.smart_pv_meter_spvm_production_attendue`
  - `sensor.spvm_yield_ratio` au lieu de `sensor.smart_pv_meter_spvm_rendement`
  - `sensor.spvm_surplus_net` au lieu de `sensor.smart_pv_meter_spvm_surplus_net`
- 📖 **Guide de diagnostic** : Ajout de DIAGNOSTIC.md pour comprendre les valeurs à 0W
- 🔧 **Script de diagnostic amélioré** :
  - Déplacement dans custom_components/spvm/ pour maintenance simplifiée
  - Simulateur interactif de calcul surplus_net
  - Détection automatique des problèmes d'unités (W vs kW)
  - Diagnostic étape par étape du calcul
- 🐛 **Logging de debug** : Nouveaux logs et attributs debug (debug_pv_w, debug_house_w, debug_surplus_virtual)
- ⚡ **Configuration d'unités par capteur** :
  - Possibilité de spécifier W ou kW individuellement pour chaque capteur (PV, house, grid, battery)
  - Résout le problème des installations mixtes (ex: Enphase en kW, Shelly en W)
  - Rétrocompatible avec l'ancienne configuration globale
- 🎨 **Interface de configuration réorganisée** :
  - Les unités apparaissent maintenant juste après leur capteur associé
  - Hiérarchie visuelle avec préfixe └─ pour les champs d'unité
  - Suppression des boutons radio globaux "Unité de puissance" (legacy conservé en interne)
  - Label amélioré pour cloud_sensor : "Couverture nuageuse" / "Cloud cover"

### Commits
- `ef548eb` - fix: Move async_get_options_flow to SPVMConfigFlow class
- `b4bd0f5` - chore(release): v0.6.3
- `1f5541b` - fix: Remove unused helper functions with invalid syntax
- `bef925f` - chore: Add .gitignore to ignore Python cache files
- `41de04a` - fix: Use vol.Coerce instead of custom coercion functions
- `d579907` - fix: Critical diagnostics bug and code cleanup
- `317964d` - docs: Update CHANGELOG and translations for v0.6.3
- `4a4bcd2` - feat: Shorter entity names and diagnostic guide
- `03e6384` - fix: Critical solar calculation bug (equation of time) ⭐
- `4e461df` - docs: Improve diagnostic script labels
- `268f559` - docs: Update documentation for v0.6.3
- `3903c8f` - docs: Add remaining commits to CHANGELOG
- `d23db25` - fix: Remove incorrect reserve subtraction from expected production ⭐
- `b89710b` - docs: Update CHANGELOG for reserve fix and diagnostic move
- `2b6d3fa` - debug: Add detailed logging for surplus_net calculation
- `0ff082f` - feat: Enhanced diagnostic script for surplus_net troubleshooting
- `f3a5458` - docs: Update CHANGELOG with debug features and diagnostic enhancements
- `2104cf6` - feat: Add per-sensor unit configuration (W vs kW) ⭐
- `2e02557` - docs: Update CHANGELOG for per-sensor unit configuration feature
- `320642c` - feat: Reorganize config UI for better clarity
- `323a55e` - docs: Update CHANGELOG for UI reorganization
- `b6097f8` - docs: Update documentation for v0.6.3 features

---

## 📝 Version 0.6.2 - Patch (November 2025)

### Améliorations
- 🔧 Améliorations mineures du flux de configuration
- 📖 Documentation mise à jour

---

## 🎉 Version 0.6.0 - "Solar Physics Model" (November 2025)

### ⚡ MAJOR CHANGES - BREAKING RELEASE

Cette version remplace complètement l'algorithme k-NN par un **modèle solaire physique** basé sur les calculs astronomiques. C'est une refonte majeure qui simplifie l'intégration tout en améliorant les performances.

---

## 🆕 Nouveautés

### Modèle solaire physique
- ✨ **Nouveau module `solar_model.py`** avec calculs astronomiques complets
- ☀️ **Position du soleil** : Élévation, azimut, déclinaison calculés en temps réel
- 🌅 **Lever/coucher du soleil** : Calcul précis selon coordonnées GPS
- ☁️ **Ajustements météo** : Prise en compte nuages, température, luminosité
- ⚡ **Irradiance clear-sky** : Modèle Kasten-Czeplak pour estimation baseline
- 📐 **Angle d'incidence** : Calcul de projection sur les panneaux

### Nouveaux paramètres de configuration
- 🔧 `panel_peak_power` : Puissance crête des panneaux (W)
- 📐 `panel_tilt` : Inclinaison des panneaux (0-90°)
- 🧭 `panel_azimuth` : Orientation des panneaux (0-360°)
- 📍 `site_latitude` : Latitude du site (° décimaux)
- 📍 `site_longitude` : Longitude du site (° décimaux)
- ⛰️ `site_altitude` : Altitude du site (mètres)
- ⚙️ `system_efficiency` : Efficacité système (0.5-1.0)
- ☁️ `cloud_sensor` : Capteur de couverture nuageuse (optionnel)

### Interface utilisateur
- 🎨 **Nouveau formulaire de configuration** avec tous les champs solaires
- 📝 **Traductions FR/EN** complètes pour tous les nouveaux champs
- 📊 **Nouveaux attributs** sur `sensor.spvm_expected_production`

---

## 🗑️ Suppressions (Breaking Changes)

### Algorithme k-NN retiré
- ❌ Suppression de `k-NN` et dépendances historiques
- ❌ Plus besoin de 3 ans d'historique
- ❌ Plus de cache en mémoire (50-100 MB économisés)
- ❌ Suppression de tous les paramètres k-NN :
  - `knn_k`
  - `knn_window_min` / `knn_window_max`
  - `knn_weight_lux` / `knn_weight_temp` / `knn_weight_hum` / `knn_weight_elev`

### Capteur renommé
- 🔄 `sensor.spvm_expected_similar` → `sensor.spvm_expected_production`
  - ⚠️ **Breaking** : Mettre à jour automations/dashboards si tu utilisais l'ancien nom
  - ✅ `sensor.spvm_surplus_net` reste identique (Solar Optimizer non impacté)

### Version de configuration
- 📌 `CONF_ENTRY_VERSION` : 1 → 2
  - Migration automatique lors de la mise à jour
  - Nouveaux champs requis au premier démarrage

---

## ⚡ Améliorations

### Performances
- 🚀 **Calculs 10x plus rapides** : < 1s vs 5-10s (k-NN)
- 💾 **Mémoire réduite** : < 5 MB vs 50-100 MB (k-NN)
- ⏱️ **Démarrage instantané** : Plus besoin d'attendre le chargement de l'historique
- 🔄 **Update ultra-léger** : Pas de requêtes lourdes à la BDD

### Précision
- 🎯 **Modèle physique** : Basé sur les lois de l'astronomie
- 🌤️ **Ajustements temps réel** : Nuages, température, luminosité
- 🔧 **Paramètres ajustables** : Optimisation manuelle possible
- 📏 **Calculs exacts** : Lever/coucher soleil précis au lieu d'estimation

### Code
- 📖 **Code simplifié** : 500 lignes (solar_model) vs 400 lignes (k-NN)
- 🧪 **Plus testable** : Fonctions pures, pas d'état global
- 🐛 **Debugging facile** : Tous les calculs sont traçables
- 📚 **Bien documenté** : Chaque fonction expliquée

---

## 🔧 Modifications techniques

### Fichiers modifiés
- `const.py` : Nouvelles constantes pour modèle solaire
- `config_flow.py` : Nouveau formulaire avec champs GPS et panneaux
- `coordinator.py` : Simplifié (plus de gestion de cache)
- `expected.py` : Complètement réécrit pour utiliser SolarModel
- `sensor.py` : Adapté pour nouveaux attributs
- `__init__.py` : Imports mis à jour
- `diagnostics.py` : Adapté pour nouveau modèle
- `en.json` / `fr.json` : Traductions mises à jour

### Nouveaux fichiers
- `solar_model.py` : Module de calculs astronomiques

### Fichiers inchangés
- `helpers.py` : Conservé tel quel
- `services.yaml` : Conservé tel quel
- `strings.json` : Conservé tel quel
- `icon.png` / `logo.png` : Conservés tels quels

---

## 🆚 Comparaison v0.5.x vs v0.6.0

| Aspect | v0.5.x (k-NN) | v0.6.0 (Solar Model) |
|--------|---------------|----------------------|
| **Temps de calcul** | 5-10 secondes | < 1 seconde |
| **Mémoire utilisée** | 50-100 MB | < 5 MB |
| **Données requises** | 3 ans d'historique | Aucune |
| **Démarrage** | 30-60 secondes | Instantané |
| **Précision (ciel clair)** | Bonne après adaptation | Excellente |
| **Précision (nuageux)** | Très bonne | Bonne avec capteur nuages |
| **Configuration** | Automatique | Manuelle (ajustable) |
| **Debugging** | Difficile (boîte noire) | Facile (tout est explicite) |

---

## 📦 Compatibilité

### ✅ Compatible
- Home Assistant 2024.1+
- Python 3.11+
- Existing `sensor.spvm_surplus_net` (Solar Optimizer)
- Tous les capteurs de surplus (identiques)

### ⚠️ Attention - Migration requise
- Config entry version 1 → 2
- Nouveaux champs obligatoires lors reconfiguration
- Capteur `expected_similar` renommé en `expected_production`

### ❌ Non compatible
- Configurations k-NN existantes (seront ignorées)
- Automations utilisant `sensor.spvm_expected_similar` (renommer)

---

## 🔄 Guide de migration depuis v0.5.x

### Option A : Migration automatique (recommandé)
1. **Backup** : Sauvegarder `/config/custom_components/spvm/`
2. **Update** : Remplacer tous les fichiers par ceux de v0.6.0
3. **Restart** : Redémarrer Home Assistant
4. **Reconfigure** : Ouvrir l'intégration et renseigner les nouveaux champs
5. **Vérifier** : Tester `sensor.spvm_expected_production`

### Option B : Installation propre
1. **Désinstaller** : Supprimer l'intégration depuis l'UI
2. **Nettoyer** : Supprimer `/config/custom_components/spvm/`
3. **Installer** : Copier les fichiers v0.6.0
4. **Restart** : Redémarrer Home Assistant
5. **Configurer** : Ajouter l'intégration via UI

### Paramètres à préparer avant migration
- Puissance crête de tes panneaux (ex: 3000 W)
- Inclinaison des panneaux (ex: 30°)
- Orientation des panneaux (ex: 180° pour Sud)
- Coordonnées GPS de ton installation
- Altitude approximative (peut utiliser Google Maps)

---

## 🐛 Bugs corrigés

### v0.5.x
- ❌ k-NN : Cache volumineux causant ralentissements
- ❌ k-NN : Requêtes BDD lourdes au démarrage
- ❌ k-NN : Prédictions instables lors changements météo brutaux
- ❌ k-NN : Nécessitait 3 ans de données pour être efficace

### v0.6.0
- ✅ Pas de cache = pas de problème mémoire
- ✅ Pas de requêtes BDD = démarrage instantané
- ✅ Modèle physique = prédictions stables
- ✅ Fonctionne immédiatement = pas d'attente

---

## 📊 Nouveaux attributs `sensor.spvm_expected_production`

```yaml
state: 1.2505  # kW

attributes:
  # Valeurs de production
  expected_w: 1250.5
  expected_kw: 1.2505
  
  # Méthode de calcul
  method: "solar_physics_model"
  model_type: "clear_sky_with_weather_adjustments"
  
  # Position solaire
  solar_elevation: 45.23      # Hauteur du soleil (°)
  solar_azimuth: 180.45       # Direction du soleil (°)
  solar_declination: -12.34   # Déclinaison (°)
  
  # Production théorique
  theoretical_w: 1500.0       # Sans ajustements météo
  theoretical_kw: 1.5
  
  # Facteurs d'ajustement
  cloud_factor: 0.834         # Réduction nuages (1.0 = ciel clair)
  temperature_factor: 0.988   # Réduction température
  lux_factor: 1.002           # Ajustement luminosité
  
  # Configuration panneaux
  panel_tilt: 30.0
  panel_azimuth: 180.0
  panel_peak_power: 3000
  
  # Horaires solaires
  sunrise: "2024-11-12T07:23:15+01:00"
  sunset: "2024-11-12T17:45:32+01:00"
  solar_noon: "2024-11-12T12:34:24+01:00"
  
  # Disponibilité capteurs
  cloud_sensor_available: true
  temp_sensor_available: true
  lux_sensor_available: false
```

---

## 🎯 Roadmap future

### v0.6.1 (Patch)
- 🐛 Corrections de bugs mineurs
- 📝 Améliorations documentation
- 🧪 Tests supplémentaires

### v0.7.0 (Future)
- 🌐 **API météo** : Intégration prévisions météo en ligne
- 📈 **Historique** : Comparaison prédiction vs réel
- 🎨 **Dashboard** : Interface de monitoring
- 🔮 **Prévisions** : Production attendue J+1 / J+7

---

## 📞 Support & Feedback

### Bugs & Issues
- GitHub Issues : https://github.com/GevaudanBeast/smart-pv-meter/issues
- Inclure : logs, version HA, config anonymisée

### Questions & Discussions
- GitHub Discussions : https://github.com/GevaudanBeast/smart-pv-meter/discussions
- Forum Home Assistant : Communauté française

### Contributions
- Pull Requests bienvenues !
- Suivre le style de code existant
- Tester avant de proposer

---

## 🙏 Remerciements

- Communauté Home Assistant pour les retours sur v0.5.x
- Contributeurs aux algorithmes de calcul solaire
- Testeurs de la version beta

---

## 📄 Licence

MIT License - Voir fichier LICENSE

---

## ✨ Résumé

**SPVM v0.6.0** transforme complètement l'intégration :
- 🚀 **Plus rapide** (10x)
- 💾 **Plus léger** (95% mémoire en moins)
- 🎯 **Plus précis** (modèle physique)
- 🔧 **Plus flexible** (paramètres ajustables)
- 📖 **Plus simple** (code clair et documenté)

Le passage au modèle solaire est un **changement majeur** qui va **simplifier ton installation** tout en **améliorant les performances**.

Solar Optimizer continue de fonctionner **parfaitement** avec `sensor.spvm_surplus_net` qui reste **identique**.

---

**🎊 Bonne mise à jour et profite du nouveau modèle solaire !**

*Smart PV Meter v0.6.0 - Built with ❤️ by GevaudanBeast*

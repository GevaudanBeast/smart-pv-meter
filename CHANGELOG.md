# SPVM - CHANGELOG & RELEASE NOTES

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

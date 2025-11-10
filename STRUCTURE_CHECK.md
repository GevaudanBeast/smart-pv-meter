# ✅ Vérification structure HACS + Home Assistant

## Structure actuelle (après nettoyage)

```
smart-pv-meter/
├── .gitignore ✅ (Python template complet)
├── .github/
│   └── workflows/
│       └── release-on-version.yml ✅ (CI/CD)
├── custom_components/
│   └── spvm/
│       ├── __init__.py ✅
│       ├── manifest.json ✅ (v0.5.0, requirements:[])
│       ├── const.py ✅
│       ├── config_flow.py ✅ (avec async_get_options_flow)
│       ├── coordinator.py ✅
│       ├── sensor.py ✅
│       ├── expected.py ✅
│       ├── helpers.py ✅
│       ├── diagnostics.py ✅
│       ├── services.yaml ✅
│       ├── strings.json ✅
│       ├── translations/
│       │   ├── en.json ✅
│       │   ├── fr.json ✅
│       │   └── strings.json ✅
│       └── tests/
│           ├── __init__.py ✅
│           └── test_units.py ✅
├── README.md ✅ (bilingue FR/EN)
├── LICENSE ✅ (MIT)
├── hacs.json ✅ (homeassistant: 2024.1.0)
├── pyproject.toml ✅
├── DELIVERY.md ✅
└── CHANGELOG.md ✅
```

## ✅ Checklist HACS

### Fichiers obligatoires
- [x] `hacs.json` à la racine
- [x] `README.md` à la racine
- [x] `custom_components/<domain>/` structure
- [x] `custom_components/spvm/manifest.json`
- [x] `custom_components/spvm/__init__.py`
- [x] LICENSE (MIT)

### Configuration hacs.json
- [x] `name`: "Smart PV Meter"
- [x] `content_in_root`: false (intégration dans custom_components/)
- [x] `render_readme`: true
- [x] `homeassistant`: "2024.1.0" (version réaliste)

### Configuration manifest.json
- [x] `domain`: "spvm"
- [x] `name`: "Smart PV Meter"
- [x] `version`: "0.5.0"
- [x] `codeowners`: ["@GevaudanBeast"]
- [x] `config_flow`: true
- [x] `documentation`: URL GitHub
- [x] `issue_tracker`: URL GitHub issues
- [x] `iot_class`: "calculated"
- [x] `integration_type`: "device"
- [x] `requirements`: [] (pas de dépendances externes)

### Structure Home Assistant
- [x] `__init__.py` avec async_setup_entry
- [x] `config_flow.py` avec ConfigFlow et OptionsFlow
- [x] `const.py` avec DOMAIN et constantes
- [x] `sensor.py` avec les capteurs
- [x] `strings.json` pour l'UI
- [x] `translations/` avec en.json et fr.json
- [x] `services.yaml` pour les services

### Bonnes pratiques
- [x] .gitignore complet
- [x] README bilingue avec badges
- [x] Pas de fichiers temporaires (.sh, .bak, etc.)
- [x] Pas de dossier tests/ à la racine (seulement dans custom_components)
- [x] Workflow GitHub Actions pour auto-release
- [x] Type hints sur tout le code
- [x] Logging approprié

## ✅ Checklist Home Assistant

### Entry Points
- [x] `async_setup()` dans __init__.py (retourne True)
- [x] `async_setup_entry()` dans __init__.py
- [x] `async_unload_entry()` dans __init__.py
- [x] `async_migrate_entry()` dans __init__.py (v1→v2)

### Config Flow
- [x] `SPVMConfigFlow` hérite de `config_entries.ConfigFlow`
- [x] `VERSION` défini (CONF_ENTRY_VERSION = 2)
- [x] `async_step_user()` pour configuration initiale
- [x] `async_get_options_flow()` pour options (bouton "Configurer")
- [x] `SPVMOptionsFlowHandler` pour les options
- [x] Selectors (EntitySelector, NumberSelector, SelectSelector)

### Sensors
- [x] Héritent de `SensorEntity`
- [x] `unique_id` stable
- [x] `device_info` pour regroupement
- [x] `device_class` approprié (POWER)
- [x] `state_class` approprié (MEASUREMENT)
- [x] `native_unit_of_measurement` (W, kW)
- [x] `should_poll = False` (event-driven)

### Coordinator
- [x] Hérite de `DataUpdateCoordinator`
- [x] Gère les mises à jour k-NN
- [x] Update interval configurable
- [x] Gestion d'erreurs appropriée

### Services
- [x] Définis dans `services.yaml`
- [x] Enregistrés dans `async_setup_entry()`
- [x] Schéma voluptuous pour validation
- [x] Documentation claire

### Diagnostics
- [x] `async_get_config_entry_diagnostics()` disponible
- [x] Exporte config, options, coordinator data
- [x] Pas de données sensibles

### Traductions
- [x] `strings.json` à la racine de l'intégration
- [x] `translations/en.json` complet
- [x] `translations/fr.json` complet
- [x] Clés config.step.user.data.* pour chaque champ

## 🚀 Tests d'intégration recommandés

### 1. Installation via HACS
```
1. HACS → Intégrations → 3 points → Dépôts personnalisés
2. Ajouter: https://github.com/GevaudanBeast/smart-pv-meter
3. Catégorie: Integration
4. Rechercher "Smart PV Meter"
5. Installer
6. Redémarrer HA
```

### 2. Configuration
```
1. Configuration → Intégrations → Ajouter
2. Rechercher "Smart PV Meter"
3. Remplir le formulaire
4. Vérifier 7 entités créées
```

### 3. Options
```
1. SPVM dans intégrations
2. Cliquer "Configurer"
3. Modifier paramètres
4. Sauvegarder
5. Vérifier reload automatique
```

### 4. Services
```
1. Outils développeur → Services
2. Rechercher "spvm"
3. Tester spvm.recompute_expected_now
4. Tester spvm.reset_cache
```

### 5. Diagnostics
```
1. SPVM → 3 points → Télécharger diagnostics
2. Vérifier JSON exporté
```

## ⚠️ Points d'attention

### Compatibilité versions
- HA minimum: 2024.1.0 (réaliste, pas 2025.10)
- Python: 3.11+ (HA standard)
- Pas de requirements externes (pytz inclus dans HA)

### Noms d'entités
- Format: `sensor.spvm_*`
- Unique IDs stables: `spvm:{entry_id}:{object_id}`
- Pas de caractères spéciaux

### Performance
- `should_poll = False` sur tous les capteurs
- Coordinator pour k-NN (update_interval configurable)
- Cache k-NN refresh horaire

### Logs
- Logger: `custom_components.spvm`
- Niveaux appropriés (debug, info, warning, error)
- Pas de spam dans les logs

## 🎯 Résultat

Structure 100% compatible:
- ✅ HACS (installation via custom repo)
- ✅ Home Assistant 2024.1+
- ✅ Config Flow complet
- ✅ Options Flow fonctionnel
- ✅ Services HA
- ✅ Diagnostics
- ✅ Traductions FR/EN
- ✅ CI/CD automatisé
- ✅ Tests unitaires

**Prêt pour publication!** 🚀

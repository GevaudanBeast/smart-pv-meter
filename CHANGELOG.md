# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [0.5.7] - 2025-11-11

### 🚀 Améliorations

#### Performance et démarrage
- **Démarrage ultra-rapide** : HISTORY_DAYS réduit de 1095 jours à 7 jours par défaut
  - Temps de setup réduit de 30-60s à <5s sur systèmes avec grosse base de données
  - Toujours précis pour prédictions journalières
  - Configurable dans const.py si besoin de plus d'historique
- **Gestion propre de HISTORY_DAYS=0** : Possibilité de désactiver complètement l'historique
  - Setup instantané (<0.01s)
  - Tous les calculs temps réel fonctionnent parfaitement
  - Seule la prédiction k-NN est désactivée

#### Logs et diagnostic
- **Logs nettoyés et clairs** :
  - Suppression des logs de timing debug (⏱️)
  - Messages INFO clairs sur l'état du chargement
  - Meilleure visibilité des opérations importantes
- **Messages utilisateur améliorés** :
  - "Fetching X days of historical data..."
  - "Loaded Y historical data points from X days"
  - "Historical data loading disabled (HISTORY_DAYS=0)"

### 🐛 Corrections

#### Startup et stabilité
- **Fix timeout au démarrage** ([#XX](https://github.com/GevaudanBeast/smart-pv-meter/issues/XX))
  - Sur systèmes avec base de données volumineuse (2M+ états)
  - Home Assistant ne redémarre plus pendant le setup SPVM
  - Chargement historique optimisé pour ne pas bloquer
- **Fix chargement historique bloquant** :
  - Le chargement ne bloque plus `async_config_entry_first_refresh`
  - Gestion gracieuse des erreurs de base de données
  - Cache intelligent pour éviter rechargements inutiles

### 🔄 Changements techniques

#### Code
- `const.py` :
  - `HISTORY_DAYS: Final = 7` (était 1095)
  - `INTEGRATION_VERSION: Final = "0.5.7"`
- `expected.py` :
  - Détection et gestion de `HISTORY_DAYS == 0`
  - Logs de chargement simplifiés
  - Pas de `import time` si pas de timing
- `__init__.py` :
  - Logs de setup nettoyés
  - Message INFO de completion
  - Pas de logs WARNING de timing

#### Base de données
- Optimisation des requêtes historiques
- Cache valide pendant 1h au lieu de recharger
- Meilleure gestion mémoire sur gros volumes

### ⚠️ Breaking Changes

**Aucun** - Migration automatique depuis 0.5.6

### 📝 Notes de migration

#### Depuis 0.5.6
- **Automatique** : Aucune action requise
- **Comportement** : Production attendue basée sur 7 jours au lieu de 3 ans
- **Performance** : Démarrage beaucoup plus rapide

#### Pour augmenter HISTORY_DAYS
Si tu veux plus de 7 jours d'historique :
```python
# custom_components/spvm/const.py (ligne ~141)
HISTORY_DAYS: Final = 30  # ou 60, 90, etc.
```

#### Pour désactiver complètement
Si démarrage encore trop lent :
```python
# custom_components/spvm/const.py (ligne ~141)
HISTORY_DAYS: Final = 0  # Désactive l'historique
```

---

## [0.5.6] - 2025-11-10

### 🚀 Améliorations
- Migration complète de Node-RED vers Python natif
- Implémentation k-NN pour prédiction de production
- Support bilingue complet (français/anglais)
- Interface de configuration UI complète
- Diagnostics complets pour troubleshooting

### ✨ Nouveautés
- Algorithme k-NN avec pondération configurable
- Lissage temporel pour surplus_net
- Cache intelligent des données historiques
- Services SPVM pour contrôle manuel
- Support complet HACS

### 🔧 Technique
- 9 fichiers Python, 1600+ lignes de code
- DataUpdateCoordinator pour gestion des données
- Config flow et options flow complets
- Tests unitaires et CI/CD GitHub Actions

---

## [0.5.0] - 2025-11-08

### 🎉 Release initiale Python
- Première version native Home Assistant
- Remplacement de la solution Node-RED
- Calculs de surplus en temps réel
- Intégration avec Solar Optimizer

### Fonctionnalités
- Calcul grid_power_auto
- Calcul surplus_virtual
- Calcul surplus_net avec réserve et cap
- Capacité PV effective avec dégradation
- Prédiction basique de production

---

## [0.4.x] - 2025-10 et antérieur

### Anciennes versions Node-RED
- Solutions basées sur Node-RED
- Calculs de surplus basiques
- Configuration manuelle
- Pas de prédiction

---

## Légende des symboles

- 🚀 **Améliorations** : Nouvelles fonctionnalités ou améliorations
- 🐛 **Corrections** : Bugs corrigés
- 🔄 **Changements** : Modifications de comportement
- ⚠️ **Breaking** : Changements cassant la rétrocompatibilité
- 📝 **Documentation** : Améliorations de documentation
- 🔧 **Technique** : Changements techniques internes
- ✨ **Nouveautés** : Fonctionnalités entièrement nouvelles
- 🎉 **Releases** : Versions majeures

---

## Versions à venir

### [0.6.0] - Roadmap
- Chargement différé de l'historique (arrière-plan)
- Chargement progressif (7j → 14j → 30j)
- Option UI pour HISTORY_DAYS (sans éditer le code)
- Cache multi-niveaux pour performance
- Prédictions météo intégrées
- Export des données pour analyse

### [1.0.0] - Vision long terme
- API REST pour intégrations externes
- Dashboard intégré
- Mode apprentissage avancé
- Support multi-onduleurs
- Prédictions ML avancées

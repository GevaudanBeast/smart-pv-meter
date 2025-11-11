# Changelog - SPVM v0.5.6b

## [0.5.6b] - 2024-11-11

### 🔧 Correctifs critiques (Patch de stabilité)

Cette version corrige les problèmes de redémarrages en boucle et améliore la stabilité globale de l'intégration.

#### Problèmes résolus

**1. Blocage du event loop (CRITIQUE)**
- ✅ Remplacement de `pytz.timezone()` par `dt_util.get_time_zone()`
- ✅ Ajout de fallback sur `dt_util.DEFAULT_TIME_ZONE` si la timezone ne charge pas
- ✅ Évite le blocage du event loop de Home Assistant lors de l'initialisation

**2. Timeout lors du setup initial**
- ✅ Ajout d'un timeout de 120 secondes sur `async_config_entry_first_refresh()`
- ✅ Le setup continue même si le chargement initial échoue (retry en background)
- ✅ Évite que Home Assistant kill l'intégration après 30s

**3. Timeout sur les requêtes historiques**
- ✅ Ajout d'un timeout de 90 secondes sur `_get_historical_data()`
- ✅ Fallback automatique vers le modèle théorique si timeout
- ✅ Évite les blocages lors du chargement de 3 ans de données

**4. Gestion des timezones sécurisée**
- ✅ Gestion robuste des timestamps sans timezone
- ✅ Utilisation de `dt_util.as_local()` comme fallback
- ✅ Pas de crash si `_timezone` est None

**5. Accès aux attributs privés**
- ✅ Ajout de propriétés publiques `cache_size` et `calculator` dans SPVMCoordinator
- ✅ Utilisation de ces propriétés dans diagnostics.py
- ✅ Gestion sécurisée avec try/except si le calculator n'existe pas

#### Améliorations du logging

**Setup process**
- Logging détaillé du processus de setup avec séparateurs visuels
- Timestamps précis pour chaque étape (création coordinator, fetch data, setup platforms)
- Messages clairs en cas d'erreur ou de timeout

**Coordinator updates**
- Logging du début/fin de chaque update
- Temps d'exécution pour chaque calcul
- Méthode utilisée et résultat de la prédiction

**Expected production calculator**
- Logging détaillé du chargement des données historiques
- Nombre de points chargés et temps d'exécution
- Détails du processus k-NN (candidats, filtres, voisins trouvés)
- Messages informatifs pour chaque fallback

#### Robustesse

**Error handling**
- Tous les blocs critiques sont dans des try/except avec logging détaillé
- Fallback en cascade si une méthode échoue
- Aucune exception ne remonte jusqu'à Home Assistant sans être catchée

**Cache**
- Méthode `reset_cache()` sécurisée avec vérification de l'existence du calculator
- Logging du nombre d'items supprimés

**Diagnostics**
- Utilisation de propriétés publiques uniquement
- Vérification de l'existence des données avant accès
- Informations supplémentaires (last_calculation_time, calculator_initialized)

### 📊 Performance

Aucun changement de performance dans cette version, l'objectif était uniquement la stabilité.

### ⚠️ Breaking Changes

Aucun breaking change. Cette version est 100% compatible avec la v0.5.5/v0.5.6.

### 🔄 Migration

Aucune migration nécessaire. Remplacer simplement les fichiers et redémarrer Home Assistant.

### 📝 Notes

Cette version se concentre exclusivement sur la stabilité. Les optimisations de performance (fenêtres saisonnières, filtrage nuit, etc.) seront implémentées dans la v0.5.7.

### 🐛 Debugging

Si vous rencontrez toujours des problèmes, activez le logging debug :

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.spvm: debug
    custom_components.spvm.coordinator: debug
    custom_components.spvm.expected: debug
```

Puis consultez les logs :
```bash
tail -f /config/home-assistant.log | grep -i spvm
```

Recherchez particulièrement :
- "SPVM setup starting" (doit apparaître)
- "Fetching initial data" (doit apparaître)
- Timeout ou erreurs entre ces deux lignes
- "SPVM setup COMPLETED" (doit apparaître à la fin)

### 🔗 Liens

- GitHub: https://github.com/GevaudanBeast/smart-pv-meter
- Issues: https://github.com/GevaudanBeast/smart-pv-meter/issues

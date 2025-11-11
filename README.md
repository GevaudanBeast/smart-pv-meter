# 🌞 Smart PV Meter (SPVM)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/GevaudanBeast/smart-pv-meter.svg)](https://github.com/GevaudanBeast/smart-pv-meter/releases)
[![License](https://img.shields.io/github/license/GevaudanBeast/smart-pv-meter.svg)](LICENSE)

**Smart PV Meter** est une intégration Home Assistant qui calcule votre surplus solaire en temps réel avec prédiction intelligente de la production photovoltaïque via algorithme k-NN.

## ✨ Caractéristiques principales

- 🔋 **Calcul automatique du surplus net** - Prêt pour Solar Optimizer
- 🤖 **Prédiction k-NN** - Basée sur 3 ans d'historique et conditions météo
- 📊 **6 capteurs dédiés** - Grid power, surplus virtual/raw/net, capacité effective, prédiction
- ⚙️ **Configuration intuitive** - Via interface graphique Home Assistant
- 🔄 **Mise à jour temps réel** - Intervalle configurable (défaut: 60s)
- 🌐 **Multilingue** - Français et Anglais

## 📦 Version actuelle : 0.5.6b (Patch de stabilité)

### 🔧 Correctifs critiques

Cette version corrige les problèmes de redémarrages en boucle :

- ✅ **Blocage event loop** - Remplacement pytz par dt_util
- ✅ **Timeout au setup** - Timeout de 120s avec continuation en background
- ✅ **Timeout requêtes SQL** - Timeout de 90s avec fallback théorique
- ✅ **Gestion timezone** - Fallbacks robustes
- ✅ **Attributs privés** - Propriétés publiques pour diagnostics

[📝 Voir le CHANGELOG complet](CHANGELOG.md)

## 🚀 Installation

### Via HACS (recommandé)

1. Ouvrir HACS dans Home Assistant
2. Aller dans "Intégrations"
3. Cliquer sur "⋮" (menu) → "Dépôts personnalisés"
4. Ajouter l'URL : `https://github.com/GevaudanBeast/smart-pv-meter`
5. Catégorie : "Intégration"
6. Chercher "Smart PV Meter"
7. Cliquer sur "Télécharger"
8. Redémarrer Home Assistant

### Installation manuelle

1. Télécharger la dernière version depuis [Releases](https://github.com/GevaudanBeast/smart-pv-meter/releases)
2. Extraire le contenu dans `custom_components/spvm/`
3. Redémarrer Home Assistant

## ⚙️ Configuration

### 1. Ajouter l'intégration

**Paramètres** → **Appareils et services** → **Ajouter une intégration** → Chercher "**Smart PV Meter**"

### 2. Capteurs requis

| Capteur | Description | Exemple |
|---------|-------------|---------|
| **Production PV** | Puissance produite par les panneaux | `sensor.pv_power` |
| **Consommation maison** | Puissance consommée par la maison | `sensor.house_power` |

### 3. Capteurs optionnels

| Capteur | Description | Utilité |
|---------|-------------|---------|
| **Puissance réseau** | Import/export réseau | Calcul surplus précis |
| **Puissance batterie** | Charge/décharge batterie | Prise en compte batterie |
| **Luminosité** | Capteur lux | ⭐ k-NN précis |
| **Température** | Température extérieure | ⭐ k-NN précis |
| **Humidité** | Humidité relative | k-NN amélioré |

### 4. Paramètres système

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| **Réserve batterie** | 150 W | Réserve Zendure permanente |
| **Cap système** | 3000 W | Limite onduleur (hard cap à 3kW) |
| **Dégradation panneaux** | 0 % | Usure des panneaux solaires |

## 📊 Entités créées

L'intégration crée automatiquement 6 capteurs :

### Capteurs principaux

**`sensor.spvm_surplus_net`** ⭐  
→ **Surplus net final** - À utiliser avec Solar Optimizer  
→ Inclut réserve 150W et cap 3kW, lissé sur 45s

**`sensor.spvm_expected_similar`**  
→ **Production attendue** via k-NN (kW)  
→ Basée sur historique 3 ans + conditions actuelles

### Capteurs intermédiaires

- `sensor.spvm_grid_power_auto` - Puissance réseau calculée
- `sensor.spvm_surplus_virtual` - Surplus brut (avant réserve)
- `sensor.spvm_surplus_net_raw` - Surplus après réserve (avant lissage)
- `sensor.spvm_pv_effective_cap_now_w` - Capacité effective avec dégradation

## 🎯 Utilisation avec Solar Optimizer

```yaml
# configuration.yaml
solar_optimizer:
  surplus_sensor: sensor.spvm_surplus_net  # ⭐ Utiliser ce capteur
  # La réserve Zendure (150W) et le cap (3kW) sont déjà appliqués
```

## 🔧 Services disponibles

### `spvm.recompute_expected_now`

Force un recalcul immédiat de la production attendue.

```yaml
service: spvm.recompute_expected_now
```

### `spvm.reset_cache`

Vide le cache historique et recharge les données.

```yaml
service: spvm.reset_cache
```

## 🐛 Debug et diagnostics

### Activer le logging debug

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.spvm: debug
```

### Télécharger les diagnostics

**Paramètres** → **Appareils et services** → **Smart PV Meter** → **⋮** → **Télécharger les diagnostics**

### Vérifier les logs

```bash
tail -f /config/home-assistant.log | grep -i spvm
```

Chercher cette séquence au démarrage :
```
SPVM setup starting (version=0.5.6b)
Creating coordinator...
Fetching initial data...
SPVM setup COMPLETED successfully
```

## 📈 Comportement de la prédiction k-NN

| Période | Méthode | Précision | Normal |
|---------|---------|-----------|--------|
| Jour 1-7 | `theoretical_capacity` | 40% | ✅ |
| Jour 7-30 | `time_only_fallback` | 60-80% | ✅ |
| Jour 30+ | `knn` | 85-95% | ✅ |
| Nuit | `night_time` (0W) | 100% | ✅ |

La précision s'améliore automatiquement au fil du temps avec l'accumulation de données historiques.

## ⚡ Performance

| Métrique | Première fois | Suivantes |
|----------|---------------|-----------|
| Setup initial | 30-120s | 2-5s |
| Update coordinator | 5-15s | 0.5-2s |
| Calcul k-NN | 3-10s | 0.5-1s |

## 🔄 Migration depuis v0.5.5

Aucune action requise, la v0.5.6b est 100% compatible.

Simplement :
1. Installer la nouvelle version via HACS
2. Redémarrer Home Assistant
3. Vérifier les logs

## 🚧 Prochaines versions

### v0.5.7 (Optimisations performance) - Prévue

- Fenêtres saisonnières (±15j au lieu de 1095j)
- Filtrage nuit basé sur luminosité (LUX)
- Échantillonnage intelligent 5 minutes
- Cache 24h au lieu de 1h

**Gain attendu : -90% de données, 10x plus rapide**

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

- 🐛 Signaler des bugs via [Issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)
- 💡 Proposer des améliorations
- 🌐 Aider à la traduction
- 📝 Améliorer la documentation

## 📝 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- Home Assistant community
- HACS pour la distribution
- Tous les contributeurs et testeurs

## 📞 Support

- **Issues GitHub** : [smart-pv-meter/issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)
- **Discussions** : [smart-pv-meter/discussions](https://github.com/GevaudanBeast/smart-pv-meter/discussions)

---

**Développé avec ❤️ par @GevaudanBeast**

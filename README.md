# Smart PV Meter (SPVM) v0.5.7

<div align="center">
  <img src="custom_components/spvm/logo.png" alt="SPVM Logo" width="200"/>
  
  [![GitHub Release](https://img.shields.io/github/v/release/GevaudanBeast/smart-pv-meter)](https://github.com/GevaudanBeast/smart-pv-meter/releases)
  [![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
  [![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.11.0-blue.svg)](https://www.home-assistant.io/)
</div>

**Smart PV Meter** est une intégration Home Assistant qui calcule le surplus solaire en temps réel pour optimiser la consommation d'énergie domestique. Elle prend en compte la production PV, la consommation de la maison, l'état de la batterie et applique automatiquement une réserve configurable.

---

## 🎯 Fonctionnalités principales

### ⚡ Calcul en temps réel
- **Surplus net** : Production PV - Consommation - Batterie - Réserve (plafonné à 3000W)
- **Puissance réseau auto** : Calculée automatiquement si non disponible
- **Capacité PV effective** : Prend en compte la dégradation des panneaux

### 📊 Prédiction par k-NN
- **Prédiction de production** basée sur l'historique et les conditions actuelles
- Algorithme k-NN utilisant luminosité, température, humidité et élévation solaire
- Cache intelligent pour performances optimales

### 🔋 Optimisations
- **Réserve Zendure** : 150W par défaut (configurable)
- **Cap système** : Limite à 3000W (hard cap)
- **Lissage temporel** : Moyennes mobiles pour stabilité

---

## 📦 Installation

### Via HACS (Recommandé)

1. Ouvre **HACS** dans Home Assistant
2. Clique sur **Intégrations**
3. Cherche **"Smart PV Meter"**
4. Clique sur **Télécharger**
5. Redémarre Home Assistant
6. Va dans **Paramètres** → **Appareils et services** → **Ajouter une intégration**
7. Cherche **"Smart PV Meter"** et configure

### Installation manuelle

1. Télécharge la dernière release depuis [GitHub](https://github.com/GevaudanBeast/smart-pv-meter/releases)
2. Copie le dossier `custom_components/spvm` dans ton dossier `config/custom_components/`
3. Redémarre Home Assistant
4. Ajoute l'intégration via l'interface

---

## ⚙️ Configuration

### Capteurs requis
- **Capteur de production PV** (puissance en W ou kW)
- **Capteur de consommation maison** (puissance en W)

### Capteurs optionnels
- **Capteur de puissance réseau** (import/export)
- **Capteur de batterie** (charge/décharge)
- **Capteur de luminosité** (lux) - recommandé pour k-NN
- **Capteur de température** - recommandé pour k-NN
- **Capteur d'humidité** - optionnel pour k-NN

### Paramètres système
- **Réserve batterie** : 150W par défaut (Zendure)
- **Cap maximum** : 3000W (limite onduleur)
- **Dégradation panneaux** : 0% par défaut
- **Unités** : W ou kW, °C ou °F

### Paramètres k-NN
- **k voisins** : 5 par défaut
- **Fenêtre temporelle** : 30-90 minutes
- **Poids** : Luminosité (0.4), Température (0.2), Humidité (0.1), Élévation (0.3)
- **Historique** : 7 jours par défaut (optimisé pour démarrage rapide)

---

## 📊 Entités créées

| Entité | Description | Usage |
|--------|-------------|-------|
| `sensor.spvm_surplus_net` | **Surplus net final** (avec réserve et cap) | ⭐ **Pour Solar Optimizer** |
| `sensor.spvm_surplus_net_raw` | Surplus brut (avant lissage) | Diagnostic |
| `sensor.spvm_surplus_virtual` | Surplus virtuel calculé | Diagnostic |
| `sensor.spvm_grid_power_auto` | Puissance réseau auto-calculée | Diagnostic |
| `sensor.spvm_pv_effective_cap_now_w` | Capacité PV effective | Info |
| `sensor.spvm_expected_similar` | Production attendue (k-NN) | Prédiction |

### 🎯 Capteur principal pour Solar Optimizer

**Utilise `sensor.spvm_surplus_net`** - Il inclut déjà :
- ✅ Réserve Zendure (150W)
- ✅ Cap système (3000W)
- ✅ Lissage temporel
- ✅ Calcul temps réel parfait

---

## 🔧 Services disponibles

### `spvm.recompute_expected_now`
Force un recalcul immédiat de la production attendue

### `spvm.reset_cache`
Vide le cache historique et force un rechargement des données

---

## 📈 Changelog v0.5.7

### 🚀 Améliorations
- **Démarrage ultra-rapide** : `HISTORY_DAYS` réduit à 7 jours par défaut
- **Gestion propre de HISTORY_DAYS=0** : Désactivation complète possible
- **Logs nettoyés** : Suppression des logs de debug, logs INFO clairs
- **Performance optimisée** : Cache intelligent, moins de requêtes DB

### 🐛 Corrections
- **Fix timeout au démarrage** : Sur systèmes avec large base de données (2M+ états)
- **Fix chargement historique** : Ne bloque plus le démarrage de Home Assistant
- **Fix logs** : Messages clairs sur l'état du chargement d'historique

### 🔄 Changements techniques
- `HISTORY_DAYS` : 1095 jours → 7 jours (configurable)
- Chargement historique non-bloquant si HISTORY_DAYS=0
- Messages utilisateur améliorés

### ⚠️ Breaking Changes
Aucun - Migration automatique depuis 0.5.6

---

## 🚨 Migration depuis 0.5.6

### Automatique
La migration est **automatique** - aucune action requise.

### Changements de comportement
- **Production attendue** : Basée sur 7 jours au lieu de 3 ans
  - Plus rapide au démarrage
  - Toujours précise pour prédictions journalières
  - Peut être augmenté dans les options si besoin

### Si démarrage lent
Si tu as une grosse base de données (>2M états) et que le démarrage est lent :

1. Édite `/config/custom_components/spvm/const.py`
2. Change `HISTORY_DAYS: Final = 0` (désactive complètement)
3. Redémarre Home Assistant
4. Les calculs temps réel fonctionnent parfaitement
5. Seule `sensor.spvm_expected_similar` affichera 0.0 kW

---

## 🎓 Exemples d'utilisation

### Avec Solar Optimizer

```yaml
# configuration.yaml
solar_optimizer:
  surplus_sensor: sensor.spvm_surplus_net
  # SPVM gère déjà la réserve et le cap !
```

### Automation basique

```yaml
automation:
  - alias: "Démarrer chauffe-eau sur surplus"
    trigger:
      - platform: numeric_state
        entity_id: sensor.spvm_surplus_net
        above: 2000  # 2kW de surplus
        for: "00:05:00"  # Pendant 5 minutes
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.chauffe_eau
```

---

## 🔍 Diagnostic

### Logs utiles
```bash
# Voir les logs SPVM
ha core logs | grep "custom_components.spvm"

# Voir le chargement d'historique
ha core logs | grep "Fetching.*days"

# Voir les erreurs
ha core logs | grep -E "(ERROR|WARNING)" | grep spvm
```

### Vérifier les valeurs
```bash
# Lister toutes les entités SPVM
ha states list | grep spvm
```

### Performance
- **Démarrage attendu** : < 5 secondes avec HISTORY_DAYS=7
- **Utilisation mémoire** : ~50-100 Mo selon historique
- **CPU** : Négligeable en fonctionnement normal

---

## 📚 Documentation complète

Consulte le [Wiki GitHub](https://github.com/GevaudanBeast/smart-pv-meter/wiki) pour :
- Guide de configuration détaillé
- Explications des algorithmes k-NN
- Exemples d'automations avancées
- FAQ et troubleshooting

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Crée une branche (`git checkout -b feature/AmazingFeature`)
3. Commit tes changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvre une Pull Request

---

## 🐛 Bugs et suggestions

Ouvre une issue sur [GitHub](https://github.com/GevaudanBeast/smart-pv-meter/issues)

---

## 📜 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 💡 Crédits

Développé par [@GevaudanBeast](https://github.com/GevaudanBeast)

Inspiré par les besoins de la communauté Home Assistant française pour l'optimisation solaire.

---

## ⭐ Support

Si ce projet t'aide, n'hésite pas à mettre une étoile sur GitHub ! ⭐

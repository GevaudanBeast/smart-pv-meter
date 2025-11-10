# 🌞 Smart PV Meter (SPVM)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/GevaudanBeast/smart-pv-meter.svg)](https://github.com/GevaudanBeast/smart-pv-meter/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Smart PV Meter** est une intégration Home Assistant qui calcule et optimise intelligemment les données photovoltaïques pour piloter des charges (via Solar Optimizer ou autres automations).

📖 **[English version below](#english-version)** | 🇫🇷 **[Version française](#version-française)**

---

## 🇫🇷 Version française

### Fonctionnalités principales

- ✅ **Calculs de surplus PV en temps réel** (virtuel, net brut, net lissé)
- ✅ **Prédiction de production PV** via algorithme k-NN (jours similaires)
- ✅ **Réserve automatique batterie** (150W par défaut, configurable)
- ✅ **Cap système 3kW** (respecte la limitation d'installation)
- ✅ **Lissage temporel** du surplus net pour éviter les variations
- ✅ **Compatible Solar Optimizer** (fournit `sensor.spvm_surplus_net`)
- ✅ **Configuration entièrement graphique** (UI)
- ✅ **Support HACS**

### Installation

#### Via HACS (recommandé)

1. Ouvrir HACS dans Home Assistant
2. Aller dans "Intégrations"
3. Cliquer sur les 3 points en haut à droite → "Dépôts personnalisés"
4. Ajouter : `https://github.com/GevaudanBeast/smart-pv-meter`
5. Catégorie : "Intégration"
6. Chercher "Smart PV Meter" et l'installer
7. Redémarrer Home Assistant

#### Installation manuelle

1. Télécharger la dernière release depuis [GitHub Releases](https://github.com/GevaudanBeast/smart-pv-meter/releases)
2. Extraire le dossier `custom_components/spvm/` dans votre dossier `config/custom_components/`
3. Redémarrer Home Assistant

### Configuration

1. Aller dans **Paramètres** → **Appareils et services** → **Ajouter une intégration**
2. Chercher **"Smart PV Meter"**
3. Remplir le formulaire :

#### Capteurs obligatoires

- **Capteur production PV** : Votre production solaire instantanée (W ou kW)
- **Capteur consommation maison** : Votre consommation totale (W)

#### Capteurs optionnels mais recommandés

- **Capteur réseau** : Puissance réseau (+import / -export)
- **Capteur batterie** : Puissance batterie (+décharge / -charge)
- **Capteur luminosité** (lux) : Améliore la précision k-NN
- **Capteur température** : Améliore la précision k-NN
- **Capteur humidité** : Améliore la précision k-NN

#### Paramètres système

- **Réserve batterie** (W) : Surplus réservé pour charger la batterie Zendure (défaut: 150W)
- **Cap onduleur** (W) : Limite système (défaut: 3000W, cap dur à 3kW)
- **Dégradation panneaux** (%) : Usure des panneaux dans le temps (défaut: 0%)
- **Unité de puissance** : W ou kW
- **Unité de température** : °C ou °F

#### Paramètres k-NN (avancés)

- **k** : Nombre de voisins (défaut: 5)
- **Fenêtre temporelle** : Min/Max en minutes (défaut: 15-60 min)
- **Poids** : Luminosité (1.5), Température (1.0), Humidité (0.5), Élévation solaire (2.0)
- **Intervalle de mise à jour** : Secondes entre les calculs (défaut: 45s)
- **Fenêtre de lissage** : Pour surplus_net (défaut: 45s)
- **Jours d'historique** : Période analysée (défaut: 90 jours)

### Entités créées

L'intégration crée automatiquement les capteurs suivants :

| Entité | Description | Unité |
|--------|-------------|-------|
| `sensor.spvm_grid_power_auto` | Puissance réseau calculée (house - pv - battery) | W |
| `sensor.spvm_surplus_virtual` | Surplus virtuel = max(export, pv - house) | W |
| `sensor.spvm_surplus_net_raw` | Surplus net brut (avant lissage) | W |
| **`sensor.spvm_surplus_net`** | **Surplus net final (à utiliser pour SO)** | **W** |
| `sensor.spvm_pv_effective_cap_now_w` | Capacité PV effective avec dégradation | W |
| `sensor.spvm_expected_similar` | Production attendue (k-NN) | kW |
| `sensor.spvm_expected_debug` | Debug k-NN (si activé) | JSON |

### Règles de calcul

```
grid_power_auto = house_w − pv_w − battery_w

surplus_virtual = max(export, pv_w − house_w)

surplus_net_raw = max(surplus_virtual − reserve_w, 0)

surplus_net = lissage(min(surplus_net_raw, min(cap_max_w, 3000W)))

pv_effective_cap = min(cap_max_w × (1 − degradation_pct/100), 3000W)
```

### Usage avec Solar Optimizer

Pour utiliser SPVM avec Solar Optimizer, configurez SO pour utiliser **`sensor.spvm_surplus_net`** comme source de production disponible.

Exemple de configuration YAML Solar Optimizer :

```yaml
sensor:
  - platform: solar_optimizer
    name: "Solar Optimizer"
    power_production_entity: sensor.spvm_surplus_net  # ← SPVM surplus net
    power_consumption_entity: sensor.house_consumption
    devices:
      - entity_id: switch.chauffe_eau
        power: 2000
        duration: 120
      - entity_id: switch.lave_linge
        power: 1500
        duration: 90
```

### Services disponibles

#### `spvm.recompute_expected_now`

Force un recalcul immédiat de la production attendue.

```yaml
service: spvm.recompute_expected_now
data:
  entry_id: "optionnel"  # Si absent, toutes les entrées
```

#### `spvm.reset_cache`

Réinitialise le cache k-NN (historique et normalisation).

```yaml
service: spvm.reset_cache
data:
  entry_id: "optionnel"
```

### Troubleshooting

#### Le bouton "Configurer" n'apparaît pas

- Vérifier que vous avez bien `async_get_options_flow` dans `config_flow.py`
- Redémarrer Home Assistant

#### Les conversions kW/W ne fonctionnent pas

- Vérifier que l'unité de puissance est correctement configurée dans les options
- Regarder les attributs des capteurs pour voir les valeurs converties

#### Le cache HACS ne se rafraîchit pas

- Aller dans HACS → 3 points → "Recharger les fenêtres"
- Vider le cache navigateur

#### La prédiction k-NN retourne toujours 0

- Vérifier qu'il y a au moins 90 jours d'historique dans l'enregistreur HA
- Vérifier que les capteurs météo sont bien configurés
- Activer `debug_expected` dans les options pour voir les détails

### FAQ

**Q: Puis-je utiliser SPVM sans Solar Optimizer ?**  
R: Oui ! Les capteurs SPVM peuvent être utilisés dans n'importe quelle automation HA.

**Q: La réserve batterie est-elle obligatoire ?**  
R: Non, vous pouvez la mettre à 0W si vous n'avez pas de batterie Zendure.

**Q: Pourquoi un cap dur à 3kW ?**  
R: C'est la configuration réelle de l'installation PV. Le cap peut être ajusté dans le code si nécessaire.

**Q: Combien de temps prend le calcul k-NN ?**  
R: Environ 1-5 secondes selon la taille de l'historique. Il est mis en cache et rafraîchi toutes les heures.

### Changelog

Voir [RELEASES](https://github.com/GevaudanBeast/smart-pv-meter/releases)

---

## 🇬🇧 English version

### Main Features

- ✅ **Real-time PV surplus calculations** (virtual, raw net, smoothed net)
- ✅ **PV production prediction** via k-NN algorithm (similar days)
- ✅ **Automatic battery reserve** (150W default, configurable)
- ✅ **3kW system cap** (respects installation limits)
- ✅ **Temporal smoothing** of net surplus to avoid spikes
- ✅ **Solar Optimizer compatible** (provides `sensor.spvm_surplus_net`)
- ✅ **Fully graphical configuration** (UI)
- ✅ **HACS support**

### Installation

#### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click 3 dots top-right → "Custom repositories"
4. Add: `https://github.com/GevaudanBeast/smart-pv-meter`
5. Category: "Integration"
6. Search for "Smart PV Meter" and install
7. Restart Home Assistant

#### Manual installation

1. Download latest release from [GitHub Releases](https://github.com/GevaudanBeast/smart-pv-meter/releases)
2. Extract `custom_components/spvm/` folder to your `config/custom_components/`
3. Restart Home Assistant

### Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **"Smart PV Meter"**
3. Fill the form:

#### Required sensors

- **PV production sensor**: Your solar production (W or kW)
- **House consumption sensor**: Your total consumption (W)

#### Optional but recommended sensors

- **Grid sensor**: Grid power (+import / -export)
- **Battery sensor**: Battery power (+discharge / -charge)
- **Lux sensor**: Improves k-NN accuracy
- **Temperature sensor**: Improves k-NN accuracy
- **Humidity sensor**: Improves k-NN accuracy

#### System parameters

- **Battery reserve** (W): Surplus reserved for Zendure battery charging (default: 150W)
- **Inverter cap** (W): System limit (default: 3000W, hard cap at 3kW)
- **Panel degradation** (%)Panel wear over time (default: 0%)
- **Power unit**: W or kW
- **Temperature unit**: °C or °F

#### k-NN parameters (advanced)

- **k**: Number of neighbors (default: 5)
- **Time window**: Min/Max in minutes (default: 15-60 min)
- **Weights**: Luminosity (1.5), Temperature (1.0), Humidity (0.5), Sun elevation (2.0)
- **Update interval**: Seconds between calculations (default: 45s)
- **Smoothing window**: For surplus_net (default: 45s)
- **History days**: Analyzed period (default: 90 days)

### Created entities

The integration automatically creates these sensors:

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.spvm_grid_power_auto` | Calculated grid power (house - pv - battery) | W |
| `sensor.spvm_surplus_virtual` | Virtual surplus = max(export, pv - house) | W |
| `sensor.spvm_surplus_net_raw` | Raw net surplus (before smoothing) | W |
| **`sensor.spvm_surplus_net`** | **Final net surplus (use for SO)** | **W** |
| `sensor.spvm_pv_effective_cap_now_w` | Effective PV capacity with degradation | W |
| `sensor.spvm_expected_similar` | Expected production (k-NN) | kW |
| `sensor.spvm_expected_debug` | k-NN debug (if enabled) | JSON |

### Calculation rules

```
grid_power_auto = house_w − pv_w − battery_w

surplus_virtual = max(export, pv_w − house_w)

surplus_net_raw = max(surplus_virtual − reserve_w, 0)

surplus_net = smoothing(min(surplus_net_raw, min(cap_max_w, 3000W)))

pv_effective_cap = min(cap_max_w × (1 − degradation_pct/100), 3000W)
```

### Usage with Solar Optimizer

To use SPVM with Solar Optimizer, configure SO to use **`sensor.spvm_surplus_net`** as available production source.

Example Solar Optimizer YAML config:

```yaml
sensor:
  - platform: solar_optimizer
    name: "Solar Optimizer"
    power_production_entity: sensor.spvm_surplus_net  # ← SPVM net surplus
    power_consumption_entity: sensor.house_consumption
    devices:
      - entity_id: switch.water_heater
        power: 2000
        duration: 120
      - entity_id: switch.washing_machine
        power: 1500
        duration: 90
```

### Available services

#### `spvm.recompute_expected_now`

Forces immediate recalculation of expected production.

```yaml
service: spvm.recompute_expected_now
data:
  entry_id: "optional"  # If absent, all entries
```

#### `spvm.reset_cache`

Resets k-NN cache (history and normalization).

```yaml
service: spvm.reset_cache
data:
  entry_id: "optional"
```

### Troubleshooting

#### "Configure" button doesn't appear

- Check that you have `async_get_options_flow` in `config_flow.py`
- Restart Home Assistant

#### kW/W conversions don't work

- Check that power unit is correctly configured in options
- Look at sensor attributes to see converted values

#### HACS cache doesn't refresh

- Go to HACS → 3 dots → "Reload windows"
- Clear browser cache

#### k-NN prediction always returns 0

- Check that there's at least 90 days of history in HA recorder
- Check that weather sensors are properly configured
- Enable `debug_expected` in options to see details

### FAQ

**Q: Can I use SPVM without Solar Optimizer?**  
A: Yes! SPVM sensors can be used in any HA automation.

**Q: Is battery reserve mandatory?**  
A: No, you can set it to 0W if you don't have a Zendure battery.

**Q: Why a hard 3kW cap?**  
A: It's the actual PV installation configuration. The cap can be adjusted in code if needed.

**Q: How long does k-NN calculation take?**  
A: About 1-5 seconds depending on history size. It's cached and refreshed hourly.

### Changelog

See [RELEASES](https://github.com/GevaudanBeast/smart-pv-meter/releases)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 💖 Support

If you find this integration useful, consider ⭐ starring the repo!

---

**Made with ❤️ by [GevaudanBeast](https://github.com/GevaudanBeast)**

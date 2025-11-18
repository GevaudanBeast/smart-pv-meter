# 📊 Analyse comparative : Solar Optimizer vs SPVM

**Date :** 18 novembre 2025
**Auteur :** Claude
**Version SPVM :** 0.6.7

---

## 🎯 Résumé exécutif

### Positionnement des solutions

| Aspect | Solar Optimizer / PVOptimizer | SPVM |
|--------|-------------------------------|------|
| **Type** | Contrôleur actif d'optimisation | Capteur de prédiction physique |
| **Rôle** | Décide et active des appareils | Fournit des données de production attendue |
| **Algorithme** | Recuit simulé / Seuil coût-bénéfice | Modèle astronomique NOAA |
| **Horizon** | Multi-périodes (minutes à heures) | Instant présent uniquement |
| **Tarification** | Intègre HC/HP/Tempo | Non pris en compte |
| **Autoconso** | 95% (PVOptimizer sur 3 kWc) | N/A (fournisseur de données) |

### Conclusion principale

**SPVM et Solar Optimizer sont complémentaires, pas concurrents.**
- **SPVM** = "Cerveau de prédiction" qui calcule la production théorique disponible
- **Solar Optimizer** = "Cerveau de décision" qui active les appareils au bon moment

---

## 📖 Analyse détaillée

### 1️⃣ Solar Optimizer (jmcollin78)

#### Stratégie d'optimisation

**Algorithme :** Recuit simulé (Simulated Annealing)
- À chaque cycle, simule des modifications d'état des appareils
- Calcule un coût pour chaque configuration
- Minimise la fonction : **`Coût = a × puissance_importée + b × puissance_exportée`**

**Coefficients dynamiques :**
- `a` et `b` s'ajustent selon le prix réel de l'électricité
- Adaptation automatique aux tarifs HC/HP et contrats dynamiques

#### Gestion des appareils

**Deux catégories :**

1. **Appareils On/Off** (binaire)
   - Consommation fixe prédéterminée
   - Activation/désactivation simple

2. **Appareils à puissance variable**
   - Ajustement dynamique de la consommation
   - Alignement précis avec la production disponible

**5 règles d'usabilité** (réévaluées à chaque cycle) :
1. **Commutateur d'activation** - Désactivation manuelle utilisateur
2. **Template de vérification** - Condition personnalisée (ex: "seulement si T° < 60°C")
3. **Seuil de batterie** - Utilisation conditionnelle au niveau de charge
4. **Temps maximal quotidien** - Limite la durée d'utilisation
5. **Temps minimal quotidien** - Garantit activation minimale (activable en HC)

#### Fonctionnalités avancées

- **Anti-scintillement** : Durées minimales d'activation/arrêt (`duration_min`, `duration_stop_min`)
- **Gestion batterie** : Prise en compte charge/décharge pour puissance réelle
- **Priorités d'appareils** : Classement par importance
- **Cycle configurable** : Période de recalcul (recommandé : 5 min)

#### Paramètres clés

| Paramètre | Fonction |
|-----------|----------|
| `duration_min` | Durée minimale d'activation (anti-scintillement) |
| `duration_stop_min` | Durée minimale d'arrêt |
| `power_min/max` | Plage de puissance pour appareils variables |
| `power_step` | Incrément d'ajustement de puissance |
| `offpeak_time` | Heure de début des tarifs réduits |

---

### 2️⃣ PVOptimizer (loudemer)

#### Stratégie d'optimisation

**Objectif :** Maximiser l'autoconsommation de la production solaire

**Algorithme de seuil :**
```
P_seuil = P_appareil × (1 - (Prix_HC - Prix_rachat) / Prix_HP)
```

Cette formule permet une **analyse coût-bénéfice** pour déterminer si l'activation est rentable.

#### Architecture de gestion

**Définition des appareils :**
- Puissance nominale (W)
- Durée de fonctionnement (min)
- Entité de commande (switch)
- Heure de démarrage en HC (optionnelle)

**Cycle d'optimisation (exécution minutière) :**
1. Lecture de la puissance solaire disponible
2. Vérification des appareils ayant atteint leur durée → arrêt
3. Évaluation des appareils en attente vs seuil de puissance
4. Activation si conditions satisfaites

**Gestion des déficits :**
- Appareils non activés de jour programmés automatiquement en HC
- Évite les surconsommations en période creuse

#### Fonctionnalités principales

- **Support multi-abonnements** : Tempo, HC, Base
- **Évitement jours rouges Tempo** : Économies sur surcoûts
- **Gestion multi-périodes** : Plusieurs créneaux HC quotidiens
- **Routeur ECS intelligent** : `P_disponible = P_export + P_ballon_ECS`
- **Communication inter-apps** : Booléens (`input_boolean.device_request_x`)

#### Résultats observés

**95% d'autoconsommation** avec installation 3 kWc après 4 mois.

---

### 3️⃣ SPVM (Smart PV Meter)

#### Architecture technique

**Type :** Capteur de prédiction physique (pas un contrôleur)

**Modèle physique :** Calculs astronomiques NOAA
- Position solaire (élévation, azimuth, déclinaison)
- Irradiance ciel clair (GHI - Global Horizontal Irradiance)
- Projection plane-of-array (POA) via angle d'incidence
- Corrections météo et température

#### Algorithmes

**1. Position solaire (`_sun_position`)**
```python
# Calculs NOAA-style
- Julian Day depuis J2000
- Anomalie moyenne, longitude écliptique
- Ascension droite, déclinaison
- Équation du temps
- Élévation et azimuth solaire
```

**2. Irradiance ciel clair (`_clear_sky_ghi`)**
```python
GHI = SOLAR_CONSTANT × (τ^AM) × sin(elevation)
# τ = transmittance atmosphérique (0.75 + 2e-5 × altitude)
# AM = air mass (Kasten & Young 1989)
```

**3. Projection sur panneau (`_incidence_angle`)**
```python
# Calcul vectoriel:
# - Vecteur soleil (coordonnées horizontales)
# - Vecteur normale panneau (inclinaison, orientation)
# - cos(θ) = produit scalaire
POA = GHI × (cos(incidence) / sin(elevation))
```

**4. Corrections**
```python
# Nuages (Kasten-Czeplak-like)
cloud_factor = 1 - 0.75 × (cloud_pct/100)³

# Température (dérating PV)
temp_factor = 1 - 0.005 × (T - 25°C)  # -0.5%/°C

# Dégradation panneaux
degradation_factor = 1 - (degradation_pct / 100)

# Production finale
P_expected = POA × efficiency × peak_W × cloud_factor × temp_factor × degradation_factor
P_expected = min(P_expected, cap_max_W)
```

#### Trois capteurs exposés

| Capteur | Formule | Usage |
|---------|---------|-------|
| **`expected_production`** | Modèle physique complet | Solar Optimizer (installations bridées), prévisions |
| **`yield_ratio`** | `(PV_réel / PV_attendu) × 100%` | Monitoring santé installation |
| **`surplus_net`** | `max(PV - Maison - Réserve, 0)` | Monitoring temps réel, automations simples |

#### Calcul du surplus (`coordinator.py:172-183`)

```python
# Surplus virtuel de base
surplus_virtual = pv_w - house_w

# Ajustement avec réseau si disponible
if grid_w is not None:
    export_w = max(-grid_w, 0.0)  # grid: +import/-export
    surplus_virtual = max(surplus_virtual, export_w)

# Surplus net après réserve
surplus_net_w = max(surplus_virtual - reserve_w, 0.0)
```

**Note importante :** Pour installations **bridées** (Enphase, micro-onduleurs), `surplus_net` sera systématiquement à **0W** car l'onduleur limite la production à la consommation. **C'est normal.**

#### Performance

- **Calcul instantané** : < 1s (vs 5-10s avec k-NN legacy)
- **Mémoire** : < 5 MB (vs 50-100 MB avec k-NN)
- **Pas de données historiques** : Fonctionne immédiatement après installation
- **Mises à jour** : Configurable (défaut: 30s)

---

## 🔍 Analyse de cohérence avec l'autoconsommation

### ✅ SPVM est cohérent avec l'autoconsommation

#### Pour installations bridées (Enphase, micro-onduleurs)

**Comportement attendu :**
```
État actuel:
  - PV bridé: 800W (suit la consommation)
  - Maison: 800W
  - expected_production: 3000W (conditions ensoleillées)
  - surplus_net: 0W ✅ NORMAL - pas d'export

Solar Optimizer voit:
  - Peut produire: 3000W (expected_production)
  - Consomme déjà: 800W
  - Disponible pour activation: 2200W

Action SO:
  - Active chauffe-eau 2kW
  - Onduleur monte à 2800W automatiquement
  - Optimisation parfaite ! ☀️
```

**Configuration recommandée :**
```yaml
Solar Optimizer:
  Production solaire: sensor.spvm_expected_production  # Production POTENTIELLE
  Consommation nette: sensor.your_house_consumption     # Consommation réelle
```

#### Pour installations non bridées (export libre)

**Comportement attendu :**
```
État actuel:
  - PV: 3000W (production maximale)
  - Maison: 800W
  - Export: 2200W
  - surplus_net: 2050W (après réserve 150W) ✅ NORMAL
```

**Configuration recommandée :**
```yaml
Solar Optimizer:
  Production solaire: sensor.your_pv_production  # Production réelle
  Consommation nette: sensor.your_grid_power     # Import/Export réseau
```

Ou directement :
```yaml
Solar Optimizer:
  Production solaire: sensor.spvm_surplus_net    # Surplus disponible maintenant
```

### ⚠️ Pièges à éviter

1. **Ne pas utiliser `surplus_net` avec installations bridées pour Solar Optimizer**
   - Sera toujours à 0W
   - Solar Optimizer ne verra aucune puissance disponible
   - Aucun appareil ne sera activé

2. **Ne pas confondre "production bridée" et "production potentielle"**
   - Bridée = ce que l'onduleur produit actuellement
   - Potentielle = ce que l'onduleur PEUT produire si la consommation augmente

---

## 🚀 Points d'amélioration pour SPVM

### 1. Prédiction multi-horizon ⭐⭐⭐

**Problème actuel :**
- SPVM calcule uniquement l'instant présent
- Solar Optimizer et PVOptimizer fonctionnent sur des cycles de 5-60 minutes
- Pas de vision à court/moyen terme (1h, 2h, 4h)

**Amélioration proposée :**
```python
# Nouveau capteur
sensor.spvm_forecast_1h  # Production attendue dans 1 heure
sensor.spvm_forecast_2h  # Production attendue dans 2 heures
sensor.spvm_forecast_4h  # Production attendue dans 4 heures

# Ou attributs du capteur principal
attributes:
  forecast:
    - time: "14:00"
      production: 2800
    - time: "15:00"
      production: 2600
    - time: "16:00"
      production: 2200
```

**Bénéfices :**
- Planification des appareils gourmands (lave-linge, lave-vaisselle)
- Anticipation des pics de production
- Meilleure optimisation avec Solar Optimizer

**Complexité :** Moyenne (calculs astronomiques déjà disponibles)

---

### 2. Historique et apprentissage ⭐⭐

**Problème actuel :**
- Aucune mémoire des prédictions passées
- Pas d'ajustement automatique de `system_efficiency`
- L'utilisateur doit tuner manuellement

**Amélioration proposée :**
```python
# Nouveau service
service: spvm.auto_tune_efficiency
# Analyse 7-30 derniers jours
# Ajuste system_efficiency automatiquement

# Nouveaux attributs
attributes:
  auto_tune:
    efficiency_suggested: 0.87
    confidence: 0.92
    samples: 2156
    last_update: "2025-11-15 10:00:00"
```

**Bénéfices :**
- Calibration automatique
- Amélioration progressive de la précision
- Moins de maintenance utilisateur

**Complexité :** Moyenne-élevée (stockage historique, algorithme de calibration)

---

### 3. Intégration des tarifs électriques ⭐⭐⭐

**Problème actuel :**
- Pas de notion de coût/bénéfice
- Pas d'intégration Tempo/HC/HP
- Décisions uniquement basées sur la puissance

**Amélioration proposée :**
```python
# Nouveaux capteurs
sensor.spvm_value_now        # Valeur financière production actuelle (€/h)
sensor.spvm_value_forecast   # Valeur financière prévision 4h (€)

# Configuration
CONF_TARIF_IMPORT_HC: 0.1568  # €/kWh
CONF_TARIF_IMPORT_HP: 0.2228  # €/kWh
CONF_TARIF_EXPORT: 0.10       # €/kWh (OA ou surplus)
CONF_TEMPO_ENABLED: true

# Intégration avec sensor.rte_tempo
attributes:
  financial:
    current_period: "HP"
    tempo_color: "blue"
    import_cost: 0.2228
    export_value: 0.10
    net_value_now: 0.45  # €/h économisés
```

**Bénéfices :**
- Meilleur pilotage avec Solar Optimizer
- Décisions financièrement optimales
- Support contrats dynamiques (Tempo, EJP futur)

**Complexité :** Moyenne (intégration API RTE, calculs financiers)

---

### 4. Gestion prédictive des batteries ⭐⭐

**Problème actuel :**
- Batterie lue mais peu utilisée dans les calculs
- Pas de stratégie de charge/décharge optimale
- Pas d'intégration avec prévisions météo

**Amélioration proposée :**
```python
# Nouveaux capteurs
sensor.spvm_battery_strategy  # "charge" / "discharge" / "hold"
sensor.spvm_battery_target    # Niveau cible (%)

# Attributs enrichis
attributes:
  battery:
    current_soc: 45  # %
    recommended_action: "charge"
    reasoning: "Forte production prévue 14h-16h, puis nuageux"
    target_soc: 85
    estimated_time: "2h15"
```

**Bénéfices :**
- Optimisation charge/décharge batterie
- Anticipation des périodes creuses production
- Maximisation autoconsommation avec stockage

**Complexité :** Élevée (stratégie complexe, intégration prévisions)

---

### 5. Détection d'anomalies et alertes ⭐

**Problème actuel :**
- `yield_ratio` affiché mais pas d'alertes actives
- Pas de détection automatique de problèmes (ombrage, salissure, panne)

**Amélioration proposée :**
```python
# Nouveaux capteurs binaires
binary_sensor.spvm_performance_issue  # On si yield < 80% pendant 3 jours
binary_sensor.spvm_shading_detected   # On si production matinale anormalement basse
binary_sensor.spvm_soiling_suspected  # On si dégradation progressive

# Événements
event: spvm_anomaly_detected
data:
  type: "low_yield"
  severity: "warning"
  yield_7d_avg: 72.3
  expected: 95.0
  message: "Production 23% sous l'attendu sur 7 jours"
```

**Bénéfices :**
- Maintenance prédictive
- Détection rapide de problèmes
- Alertes automatiques

**Complexité :** Moyenne (analyse tendances, règles de détection)

---

### 6. Intégration prévisions météo ⭐⭐⭐

**Problème actuel :**
- Dépend des capteurs `cloud_coverage`, `temp`, `lux` en temps réel
- Pas de prévisions météo intégrées
- Corrections uniquement sur l'instant présent

**Amélioration proposée :**
```python
# Intégration avec Met.no / OpenWeatherMap
# Attributs enrichis
attributes:
  weather_forecast:
    - time: "14:00"
      cloud_pct: 25
      temp_c: 18
      production_w: 2650
    - time: "15:00"
      cloud_pct: 60
      temp_c: 19
      production_w: 1840
```

**Bénéfices :**
- Prédictions plus précises
- Planification sur plusieurs heures
- Meilleure intégration avec optimiseurs

**Complexité :** Moyenne (API météo, parsing prévisions)

---

### 7. Capteur de consigne pour Solar Optimizer ⭐⭐⭐

**Problème actuel :**
- `expected_production` donne la production brute
- Solar Optimizer doit soustraire manuellement la consommation actuelle
- Pas de capteur "puissance disponible pour activation"

**Amélioration proposée :**
```python
# Nouveau capteur
sensor.spvm_available_power  # Puissance disponible pour activer des appareils

# Formule (installations bridées)
available_power = expected_production - house_consumption - reserve

# Formule (installations non bridées)
available_power = surplus_net  # Déjà calculé

# Configuration
CONF_MODE: "bridled" / "export"  # Auto-détection possible via grid_sensor
```

**Bénéfices :**
- Simplification configuration Solar Optimizer
- Capteur "tout-en-un" pour optimiseurs
- Moins de calculs templates côté utilisateur

**Complexité :** Faible (réutilisation code existant)

---

### 8. API de service pour planification ⭐

**Problème actuel :**
- Pas de service pour interroger production future
- Automations complexes pour planifier appareils

**Amélioration proposée :**
```python
# Nouveau service
service: spvm.get_production_forecast
data:
  start_time: "2025-11-18 14:00:00"
  end_time: "2025-11-18 18:00:00"
  resolution: 15  # minutes
response:
  total_energy: 8.5  # kWh sur la période
  peak_power: 2850   # W
  peak_time: "15:30"
  average_power: 2125  # W
  forecast:
    - time: "14:00"
      power: 2600
    - time: "14:15"
      power: 2680
    [...]
```

**Bénéfices :**
- Automations avancées simplifiées
- Planification optimale des cycles appareils
- Intégration avec scripts Python

**Complexité :** Moyenne (service HA, validation données)

---

## 📋 Tableau récapitulatif des améliorations

| # | Amélioration | Priorité | Complexité | Impact autoconso | Impact SO/PVO |
|---|--------------|----------|------------|------------------|---------------|
| 1 | Prédiction multi-horizon | ⭐⭐⭐ | Moyenne | +++++ | +++++ |
| 2 | Historique et apprentissage | ⭐⭐ | Moyenne-élevée | +++ | ++ |
| 3 | Intégration tarifs électriques | ⭐⭐⭐ | Moyenne | ++++ | +++++ |
| 4 | Gestion prédictive batteries | ⭐⭐ | Élevée | ++++ | +++ |
| 5 | Détection d'anomalies | ⭐ | Moyenne | ++ | + |
| 6 | Intégration prévisions météo | ⭐⭐⭐ | Moyenne | +++++ | +++++ |
| 7 | Capteur available_power | ⭐⭐⭐ | Faible | ++++ | +++++ |
| 8 | API planification | ⭐ | Moyenne | +++ | +++ |

**Légende :**
- Priorité : ⭐ (nice-to-have) → ⭐⭐⭐ (très important)
- Impact : + (faible) → +++++ (très fort)

---

## 🎯 Recommandations prioritaires

### Phase 1 - Quick wins (1-2 semaines)

**#7 - Capteur `available_power`**
- Complexité faible
- Impact immédiat sur intégration Solar Optimizer
- Réutilise code existant

**#1 - Prédiction multi-horizon (version simple)**
- Calculs astronomiques déjà présents
- Version basique : prédiction +1h, +2h, +4h sans météo
- Impact majeur sur optimisation

### Phase 2 - Améliorations moyennes (1 mois)

**#6 - Intégration prévisions météo**
- Utiliser API existantes (Met.no intégré HA)
- Améliore drastiquement précision prédictions
- Synergie avec #1 (prédiction multi-horizon)

**#3 - Intégration tarifs électriques**
- Utiliser sensors Tempo/HC existants
- Ajout de valeur financière aux décisions
- Complémentaire avec Solar Optimizer

### Phase 3 - Améliorations avancées (2-3 mois)

**#2 - Historique et apprentissage**
- Auto-calibration `system_efficiency`
- Amélioration continue de la précision

**#4 - Gestion prédictive batteries**
- Stratégies charge/décharge
- Maximisation autoconsommation avec stockage

---

## 💡 Conclusion

### SPVM est-il cohérent avec l'autoconsommation ?

**✅ OUI**, complètement :
- Le capteur `expected_production` est **parfait** pour installations bridées
- Le comportement `surplus_net = 0W` est **normal et attendu** pour ces installations
- L'intégration avec Solar Optimizer est **bien documentée** dans le README
- Le modèle physique est **scientifiquement rigoureux** (NOAA, Kasten-Czeplak)

### Points forts actuels de SPVM

1. **Modèle physique robuste** - Calculs astronomiques précis
2. **Performance exceptionnelle** - Instantané, faible mémoire
3. **Complémentarité Solar Optimizer** - Fournit les données nécessaires
4. **Flexibilité** - Support installations bridées et non bridées
5. **Maintenance faible** - Pas de dépendance données historiques

### Axes d'amélioration stratégiques

Pour transformer SPVM de "bon capteur" à "outil d'optimisation indispensable" :

1. **Vision temporelle** (prédictions multi-horizon + météo)
2. **Intelligence financière** (tarifs, Tempo, coûts/bénéfices)
3. **Simplicité d'usage** (capteur `available_power`, auto-calibration)

### Positionnement futur recommandé

```
┌─────────────────────────────────────────────┐
│  Écosystème autoconsommation Home Assistant │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │    SPVM      │─────▶│ Solar Optimizer │ │
│  │ (Prédiction) │      │   (Décision)    │ │
│  └──────────────┘      └─────────────────┘ │
│         │                       │          │
│         ▼                       ▼          │
│  ┌──────────────────────────────────────┐  │
│  │   Appareils (chauffe-eau, PAC, etc.) │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

**SPVM** = Le cerveau qui comprend le soleil et prédit la production
**Solar Optimizer** = Le cerveau qui décide quand activer les appareils
**Ensemble** = Système d'autoconsommation optimal

---

## 📚 Références

- [Solar Optimizer (jmcollin78)](https://github.com/jmcollin78/solar_optimizer)
- [PVOptimizer (loudemer)](https://github.com/loudemer/PVOptimizer)
- [SPVM Documentation](README.md)
- [NOAA Solar Calculations](https://gml.noaa.gov/grad/solcalc/)
- [Kasten-Czeplak Cloud Model](https://doi.org/10.1016/0038-092X(80)90391-6)

---

**Document généré le 18 novembre 2025**
**Pour questions/suggestions :** [GitHub Issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)

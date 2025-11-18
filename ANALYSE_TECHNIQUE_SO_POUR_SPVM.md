# 🔬 Analyse technique pointue de Solar Optimizer
## Voies d'optimisation pour SPVM

**Date :** 18 novembre 2025
**Auteur :** Claude
**Version SPVM :** 0.6.7
**Version Solar Optimizer :** 3.5.0+

---

## 🎯 Objectif de l'analyse

Cette analyse disséque les mécanismes internes de **Solar Optimizer** (jmcollin78) pour identifier des techniques, algorithmes et patterns architecturaux **transposables à SPVM** afin d'en améliorer les capacités d'optimisation solaire.

**Focus :** Extraction de principes techniques réutilisables, pas une simple comparaison fonctionnelle.

---

## 📐 Architecture algorithmique de Solar Optimizer

### 1. Recuit simulé (Simulated Annealing)

#### Implémentation

```python
# Pseudo-code basé sur l'analyse
def simulated_annealing(devices, production, consumption, costs):
    current_solution = initial_solution(devices)
    temperature = 1000  # initial_temp

    while temperature > 0.1:  # min_temp
        for iteration in range(max_iteration_number):
            # Génération voisin (perturbation aléatoire)
            neighbor = generate_neighbor(current_solution)

            # Calcul des coûts
            current_cost = objective_function(current_solution, ...)
            neighbor_cost = objective_function(neighbor, ...)

            # Critère d'acceptation Metropolis
            delta = neighbor_cost - current_cost
            if delta < 0 or random() < exp(-delta / temperature):
                current_solution = neighbor

        # Refroidissement
        temperature *= 0.95  # cooling_factor

    return current_solution
```

#### Fonction objectif multi-critères

```python
def objective_function(solution, production, consumption, costs, priority_weight):
    # Calcul bilan énergétique
    total_consumption = consumption + sum(device.power for device in solution if device.is_on)
    net_power = production - total_consumption

    # Coût énergétique
    if net_power < 0:  # Import depuis réseau
        energy_cost = abs(net_power) * costs.buy_price
    else:  # Export vers réseau
        energy_cost = net_power * costs.sell_price

    # Normalisation
    consumption_coef = energy_cost / max_possible_cost

    # Coefficient priorité
    priority_coef = sum(device.priority_level for device in solution if not device.is_on) / total_priority

    # Fonction hybride
    objective = consumption_coef * (1 - priority_weight) + priority_coef * priority_weight

    return objective
```

**Points clés :**
- **Double optimisation** : Coût énergétique ET satisfaction des priorités utilisateur
- **Pondération dynamique** : `priority_weight` (0-100%) ajuste le trade-off
- **Asymétrie import/export** : Coefficients `a` et `b` différenciés

---

### 2. Gestion des contraintes

Solar Optimizer implémente un système de **contraintes multi-niveaux** :

#### Contraintes temporelles

```python
class ManagedDevice:
    # Anti-scintillement
    duration_min: int  # Durée minimale d'activation (secondes)
    duration_stop_min: int  # Durée minimale d'arrêt
    duration_power_min: int  # Durée minimale entre changements de puissance

    # Quotas quotidiens
    max_on_time_per_day_min: int  # Limite supérieure
    min_on_time_per_day_min: int  # Garantie minimale (activé en HC si non atteint)

    # Tracking état
    _next_date_available: datetime  # Prochaine action autorisée
    _on_time_sec: int  # Cumul du jour
```

**Mécanisme de validation :**
```python
def can_activate(device, now):
    # Vérification temporelle
    if now < device._next_date_available:
        return False

    # Quota quotidien atteint ?
    if device._on_time_sec >= device.max_on_time_per_day_min * 60:
        return False

    # Quota minimal non atteint + heure creuse ?
    if device._on_time_sec < device.min_on_time_per_day_min * 60:
        if is_offpeak_time(now, device.offpeak_time):
            return True  # Force activation

    return True
```

#### Contraintes énergétiques

```python
class ManagedDevice:
    battery_soc_threshold: float  # Seuil batterie (%)
    power_min: float  # Puissance minimale de fonctionnement
    power_max: float  # Puissance maximale
    power_step: float  # Granularité d'ajustement

    def can_operate(self, battery_soc):
        if battery_soc < self.battery_soc_threshold:
            return False
        return True

    def quantize_power(self, requested_power):
        # Arrondi au step supérieur
        steps = ceil((requested_power - self.power_min) / self.power_step)
        return self.power_min + steps * self.power_step
```

#### Contraintes conditionnelles (templates)

```python
class ManagedDevice:
    check_usable_template: str  # Condition d'usabilité
    active_template: str  # Condition d'état actif
    enable_switch: bool  # Override manuel utilisateur

    def is_usable(self, context):
        # 5 règles réévaluées chaque cycle
        if not self.enable_switch:
            return False
        if self.check_usable_template:
            if not eval_template(self.check_usable_template, context):
                return False
        # ... autres vérifications
        return True
```

---

### 3. Stratégies de convergence

#### Paramètres adaptatifs

| Installation | `initial_temp` | `cooling_factor` | `max_iteration_number` |
|--------------|----------------|------------------|------------------------|
| Petite (1-3 appareils) | 500 | 0.90 | 500 |
| Moyenne (4-8 appareils) | 1000 | 0.95 | 1000 |
| Grande (9+ appareils) | 2000 | 0.97 | 2000 |

**Critères d'arrêt anticipé :**
```python
def optimize(self):
    best_cost = float('inf')
    iterations_without_improvement = 0

    while temperature > min_temp:
        # ... optimisation ...

        if current_cost <= 0:  # Optimal trouvé
            break

        if current_cost == best_cost:
            iterations_without_improvement += 1
            if iterations_without_improvement > 100:
                break  # Convergence prématurée
        else:
            best_cost = current_cost
            iterations_without_improvement = 0
```

#### Gestion de l'espace de recherche

**Perturbations intelligentes :**
```python
def generate_neighbor(current_solution):
    # Stratégies de perturbation pondérées
    strategies = [
        (0.5, flip_random_device),      # 50% - Toggle un appareil
        (0.3, adjust_variable_power),   # 30% - Ajuster puissance
        (0.15, swap_two_devices),       # 15% - Échanger 2 appareils
        (0.05, random_restart),         # 5% - Redémarrage aléatoire
    ]

    strategy = weighted_choice(strategies)
    return strategy(current_solution)
```

---

## 🧠 Mécanismes transposables à SPVM

### 🔹 Mécanisme #1 : Optimisation multi-objectifs

**Ce que fait SO :**
- Équilibre coût énergétique et priorités utilisateur
- Pondération dynamique via `priority_weight`

**Transposition SPVM :**

```python
# Nouveau capteur sensor.spvm_optimization_target
class SPVMOptimizationTarget:
    """Calcule un objectif d'optimisation multi-critères pour Solar Optimizer."""

    def calculate(self, production, consumption, costs, weather_forecast):
        # Critère 1 : Maximiser autoconsommation
        autoconso_score = self._autoconsommation_score(production, consumption)

        # Critère 2 : Minimiser coût financier
        financial_score = self._financial_score(production, consumption, costs)

        # Critère 3 : Anticiper variations météo
        forecast_score = self._forecast_stability_score(weather_forecast)

        # Critère 4 : Optimiser charge batterie
        battery_score = self._battery_optimization_score(...)

        # Agrégation pondérée (configurable)
        weights = self.config.optimization_weights  # [0.4, 0.3, 0.2, 0.1]
        total_score = (
            autoconso_score * weights[0] +
            financial_score * weights[1] +
            forecast_score * weights[2] +
            battery_score * weights[3]
        )

        return {
            "total_score": total_score,
            "autoconso_score": autoconso_score,
            "financial_score": financial_score,
            "forecast_score": forecast_score,
            "battery_score": battery_score,
        }
```

**Configuration utilisateur :**
```yaml
spvm:
  optimization_weights:
    autoconsumption: 0.4   # Priorité autoconso
    financial: 0.3         # Priorité économie
    forecast: 0.2          # Anticipation météo
    battery: 0.1           # Gestion batterie
```

**Bénéfices :**
- Décisions holistiques (pas uniquement wattage)
- Adaptation aux préférences utilisateur
- Intégration naturelle avec Solar Optimizer

---

### 🔹 Mécanisme #2 : Tracking temporel et réinitialisation quotidienne

**Ce que fait SO :**
- Cumule `_on_time_sec` par appareil
- Réinitialise à une heure configurable (par défaut 05:00)
- Utilise pour quotas min/max quotidiens

**Transposition SPVM :**

```python
# Nouveau module : temporal_tracking.py
class SPVMTemporalTracker:
    """Tracking de métriques temporelles avec réinitialisation quotidienne."""

    def __init__(self, reset_time: str = "05:00"):
        self.reset_time = reset_time
        self.metrics = {
            "total_production_kwh": 0.0,
            "total_consumption_kwh": 0.0,
            "total_export_kwh": 0.0,
            "total_import_kwh": 0.0,
            "peak_production_w": 0.0,
            "peak_time": None,
            "low_production_periods": [],
            "high_production_periods": [],
        }
        self.last_reset = None

    def update(self, dt, production_w, consumption_w, grid_w):
        # Vérifier réinitialisation
        if self._should_reset(dt):
            self._reset_daily_metrics()

        # Intégration énergie (méthode des trapèzes)
        delta_t = (dt - self.last_update).total_seconds() / 3600  # heures
        self.metrics["total_production_kwh"] += production_w * delta_t / 1000
        self.metrics["total_consumption_kwh"] += consumption_w * delta_t / 1000

        if grid_w < 0:  # Export
            self.metrics["total_export_kwh"] += abs(grid_w) * delta_t / 1000
        else:  # Import
            self.metrics["total_import_kwh"] += grid_w * delta_t / 1000

        # Tracking peak
        if production_w > self.metrics["peak_production_w"]:
            self.metrics["peak_production_w"] = production_w
            self.metrics["peak_time"] = dt

        # Détection périodes haute/basse production
        self._update_production_periods(dt, production_w)

    def _should_reset(self, dt):
        if self.last_reset is None:
            return True

        reset_hour, reset_minute = map(int, self.reset_time.split(':'))
        last_reset_today = dt.replace(hour=reset_hour, minute=reset_minute, second=0)

        if dt >= last_reset_today and self.last_reset < last_reset_today:
            return True
        return False
```

**Nouveaux capteurs exposés :**
```python
# sensor.spvm_daily_production (kWh)
# sensor.spvm_daily_consumption (kWh)
# sensor.spvm_daily_export (kWh)
# sensor.spvm_daily_import (kWh)
# sensor.spvm_daily_autoconso_rate (%)
# sensor.spvm_daily_peak_production (W)
# sensor.spvm_daily_peak_time (datetime)
```

**Bénéfices :**
- Statistiques quotidiennes précises
- Base pour objectifs quotidiens (ex: "viser 80% autoconso aujourd'hui")
- Détection de patterns (ex: "pic habituel à 14h")

---

### 🔹 Mécanisme #3 : Gestion fine des coûts énergétiques

**Ce que fait SO :**
- Différencie coût achat (`buy_price`) et revente (`sell_price`)
- Ajuste coefficients `a` et `b` dans la fonction objectif
- Supporte tarifs dynamiques (Tempo, HC/HP)

**Transposition SPVM :**

```python
# Nouveau module : energy_costs.py
class SPVMEnergyCostCalculator:
    """Calcul de la valeur financière de l'énergie produite/consommée."""

    def __init__(self, config):
        self.buy_price_hc = config.get(CONF_TARIF_BUY_HC, 0.1568)  # €/kWh
        self.buy_price_hp = config.get(CONF_TARIF_BUY_HP, 0.2228)
        self.sell_price = config.get(CONF_TARIF_SELL, 0.10)
        self.tempo_sensor = config.get(CONF_TEMPO_SENSOR)

    def get_current_prices(self, dt):
        """Retourne les prix achat/vente actuels."""
        # Détection période HC/HP
        is_offpeak = self._is_offpeak(dt)

        # Intégration Tempo si disponible
        tempo_color = self._get_tempo_color()

        if tempo_color == "red":
            buy_price = 0.7562 if not is_offpeak else 0.1568
        elif tempo_color == "white":
            buy_price = 0.2228 if not is_offpeak else 0.1568
        else:  # blue
            buy_price = self.buy_price_hp if not is_offpeak else self.buy_price_hc

        return {
            "buy_price": buy_price,
            "sell_price": self.sell_price,
            "period": "HC" if is_offpeak else "HP",
            "tempo_color": tempo_color,
        }

    def calculate_energy_value(self, production_w, consumption_w, grid_w, dt):
        """Calcule la valeur financière de l'énergie à l'instant t."""
        prices = self.get_current_prices(dt)

        # Autoconsommation (économie)
        autoconso_w = min(production_w, consumption_w)
        autoconso_value = autoconso_w * prices["buy_price"] / 1000  # €/h

        # Export (revenu)
        if grid_w < 0:  # Export
            export_value = abs(grid_w) * prices["sell_price"] / 1000
        else:
            export_value = 0

        # Import (coût)
        if grid_w > 0:  # Import
            import_cost = grid_w * prices["buy_price"] / 1000
        else:
            import_cost = 0

        net_value = autoconso_value + export_value - import_cost

        return {
            "autoconso_value_eur_h": autoconso_value,
            "export_value_eur_h": export_value,
            "import_cost_eur_h": import_cost,
            "net_value_eur_h": net_value,
            "prices": prices,
        }
```

**Nouveaux capteurs exposés :**
```python
# sensor.spvm_energy_value_now (€/h)
# sensor.spvm_autoconso_value (€/h)
# sensor.spvm_export_value (€/h)
# sensor.spvm_import_cost (€/h)
# sensor.spvm_daily_financial_balance (€)
```

**Intégration avec expected_production :**
```python
def calculate_forecast_value(self, expected_production_w, dt, horizon_hours=4):
    """Calcule la valeur financière prévisionnelle sur N heures."""
    total_value = 0.0
    forecast_details = []

    for h in range(horizon_hours):
        future_dt = dt + timedelta(hours=h)
        prices = self.get_current_prices(future_dt)

        # Valeur si autoconso totale (meilleur cas)
        value_autoconso = expected_production_w * prices["buy_price"] / 1000

        # Valeur si export total (pire cas autoconso)
        value_export = expected_production_w * prices["sell_price"] / 1000

        forecast_details.append({
            "hour": h,
            "datetime": future_dt,
            "expected_w": expected_production_w,
            "value_autoconso": value_autoconso,
            "value_export": value_export,
            "period": prices["period"],
            "tempo_color": prices["tempo_color"],
        })

        total_value += value_autoconso  # Hypothèse autoconso

    return {
        "total_value_eur": total_value,
        "forecast": forecast_details,
    }
```

**Configuration :**
```yaml
spvm:
  tarifs:
    buy_hc: 0.1568  # €/kWh heures creuses
    buy_hp: 0.2228  # €/kWh heures pleines
    sell: 0.10      # €/kWh revente (OA ou surplus)
  tempo:
    enabled: true
    sensor: sensor.rte_tempo_couleur_jour_j0
  offpeak_periods:
    - start: "02:00"
      end: "07:00"
    - start: "14:00"
      end: "17:00"
```

**Bénéfices :**
- Prise de décision financièrement optimale
- Visualisation économies réalisées
- Intégration contrats dynamiques (Tempo, EJP futur)
- Incitation forte à l'autoconsommation en HP

---

### 🔹 Mécanisme #4 : Prédiction avec fenêtre glissante

**Ce que fait SO :**
- Optimise sur un horizon de `refresh_period_sec` (300s par défaut)
- Réévalue toutes les 5 minutes avec nouvelles données

**Transposition SPVM :**

```python
# Extension du modèle solaire avec fenêtrage
class SPVMSlidingWindowPredictor:
    """Prédictions avec fenêtre glissante pour optimisation continue."""

    def __init__(self, window_size_minutes=30, step_minutes=5):
        self.window_size = timedelta(minutes=window_size_minutes)
        self.step = timedelta(minutes=step_minutes)

    def predict_window(self, start_dt, solar_inputs):
        """Prédit production sur fenêtre glissante."""
        predictions = []
        current_dt = start_dt
        end_dt = start_dt + self.window_size

        while current_dt < end_dt:
            # Calcul production à current_dt
            inputs = replace(solar_inputs, dt_utc=current_dt)
            model = solar_compute(inputs)

            # Application corrections météo si prévisions dispo
            cloud_forecast = self._get_cloud_forecast(current_dt)
            temp_forecast = self._get_temp_forecast(current_dt)

            if cloud_forecast:
                inputs = replace(inputs, cloud_pct=cloud_forecast)
            if temp_forecast:
                inputs = replace(inputs, temp_c=temp_forecast)

            model_corrected = solar_compute(inputs)

            predictions.append({
                "datetime": current_dt,
                "expected_w": model_corrected.expected_corrected_w,
                "elevation_deg": model_corrected.elevation_deg,
                "cloud_pct": cloud_forecast,
                "temp_c": temp_forecast,
            })

            current_dt += self.step

        return predictions

    def calculate_window_statistics(self, predictions):
        """Statistiques sur la fenêtre de prédiction."""
        powers = [p["expected_w"] for p in predictions]

        return {
            "avg_power_w": mean(powers),
            "min_power_w": min(powers),
            "max_power_w": max(powers),
            "std_power_w": stdev(powers) if len(powers) > 1 else 0,
            "total_energy_kwh": sum(powers) * (self.step.total_seconds() / 3600) / 1000,
            "stability_index": 1 - (stdev(powers) / mean(powers)) if mean(powers) > 0 else 0,
        }
```

**Nouveau capteur :**
```python
# sensor.spvm_forecast_window
# État : énergie totale sur fenêtre (kWh)
# Attributs :
{
  "window_size_min": 30,
  "step_min": 5,
  "predictions": [...],
  "statistics": {
    "avg_power_w": 2456,
    "min_power_w": 1980,
    "max_power_w": 2850,
    "stability_index": 0.87,  # 0-1, 1 = très stable
  }
}
```

**Utilisation par Solar Optimizer :**
```yaml
# SO peut interroger SPVM pour anticiper 30min à l'avance
automation:
  - alias: "SO - Update with SPVM forecast"
    trigger:
      platform: time_pattern
      minutes: "/5"
    action:
      service: solar_optimizer.refresh
      data:
        production_forecast: "{{ state_attr('sensor.spvm_forecast_window', 'predictions') }}"
```

**Bénéfices :**
- Décisions anticipatives (pas uniquement réactives)
- Lissage des variations météo à court terme
- Meilleure planification des cycles d'appareils

---

### 🔹 Mécanisme #5 : Gestion d'état avec persistance

**Ce que fait SO :**
- Persiste `_on_time_sec` via Home Assistant
- Restaure état après redémarrage
- Tracking continu même en cas de crash

**Transposition SPVM :**

```python
# Extension coordinator avec persistance
class SPVMCoordinator(DataUpdateCoordinator):

    async def _async_setup(self):
        """Setup avec restauration état."""
        # Restaurer métriques quotidiennes
        self.daily_metrics = await self._restore_daily_metrics()
        if not self.daily_metrics:
            self.daily_metrics = self._initialize_daily_metrics()

    async def _restore_daily_metrics(self):
        """Restaure métriques depuis store."""
        store = Store(self.hass, 1, f"spvm_{self.entry.entry_id}_daily")
        data = await store.async_load()

        if data and data.get("date") == date.today().isoformat():
            return data.get("metrics")
        return None

    async def _save_daily_metrics(self):
        """Sauvegarde métriques."""
        store = Store(self.hass, 1, f"spvm_{self.entry.entry_id}_daily")
        await store.async_save({
            "date": date.today().isoformat(),
            "metrics": self.daily_metrics,
        })

    async def _async_update_data(self):
        # ... calculs existants ...

        # Mise à jour métriques quotidiennes
        self._update_daily_metrics(pv_w, house_w, grid_w)

        # Sauvegarde périodique (toutes les 10 mises à jour)
        if self.update_count % 10 == 0:
            await self._save_daily_metrics()

        return data
```

**Bénéfices :**
- Continuité des statistiques quotidiennes
- Résilience aux redémarrages
- Historique fiable pour calibration

---

### 🔹 Mécanisme #6 : Configuration adaptative

**Ce que fait SO :**
- Paramètres d'algorithme ajustables (temp, cooling, iterations)
- Recommandations selon taille installation

**Transposition SPVM :**

```python
# Nouveau module : adaptive_config.py
class SPVMAdaptiveConfig:
    """Ajuste automatiquement la configuration selon l'installation."""

    def analyze_installation(self, panel_peak_w, num_batteries, num_phases):
        """Analyse installation et recommande paramètres."""

        # Classification taille
        if panel_peak_w < 3000:
            size_class = "small"
        elif panel_peak_w < 9000:
            size_class = "medium"
        else:
            size_class = "large"

        # Recommandations
        recommendations = {
            "small": {
                "update_interval_s": 60,
                "smoothing_window_s": 120,
                "cap_max_w": panel_peak_w * 0.9,  # Micro-onduleurs bridés
                "system_efficiency": 0.88,
            },
            "medium": {
                "update_interval_s": 30,
                "smoothing_window_s": 90,
                "cap_max_w": panel_peak_w * 0.95,
                "system_efficiency": 0.85,
            },
            "large": {
                "update_interval_s": 15,
                "smoothing_window_s": 60,
                "cap_max_w": panel_peak_w,
                "system_efficiency": 0.82,
            }
        }

        config = recommendations[size_class]

        # Ajustements spécifiques
        if num_batteries > 0:
            config["reserve_w"] = 200 * num_batteries

        if num_phases == 3:
            config["system_efficiency"] *= 0.98  # Meilleur rendement triphasé

        return config

    def auto_tune_system_efficiency(self, historical_data):
        """Calibration automatique de system_efficiency."""
        # Analyse 7 derniers jours
        ratios = []
        for day_data in historical_data[-7:]:
            daily_actual = day_data["total_production_kwh"]
            daily_expected = day_data["total_expected_kwh"]
            if daily_expected > 1.0:  # Ignorer jours très faibles
                ratios.append(daily_actual / daily_expected)

        if not ratios:
            return None

        # Médiane pour robustesse aux outliers
        median_ratio = median(ratios)
        current_efficiency = self.system_efficiency

        # Ajustement conservateur
        new_efficiency = current_efficiency * median_ratio
        new_efficiency = max(0.5, min(1.0, new_efficiency))  # Clamping

        confidence = 1 - (stdev(ratios) / mean(ratios)) if mean(ratios) > 0 else 0

        return {
            "current_efficiency": current_efficiency,
            "suggested_efficiency": new_efficiency,
            "confidence": confidence,
            "samples": len(ratios),
            "adjustment_pct": (new_efficiency - current_efficiency) / current_efficiency * 100,
        }
```

**Nouveau service :**
```yaml
# Service SPVM
service: spvm.auto_configure
# Analyse installation et propose configuration optimale

service: spvm.calibrate_efficiency
# Calibration automatique basée sur historique
```

**Bénéfices :**
- Configuration "zéro effort" pour utilisateurs
- Amélioration continue de la précision
- Adaptation automatique aux conditions réelles

---

## 🚀 Voies d'optimisation concrètes pour SPVM

### Roadmap d'implémentation

#### Phase 1 : Fondations (2-3 semaines)

**#1 - Module de coûts énergétiques** ⭐⭐⭐⭐⭐
- Implémentation `energy_costs.py`
- Nouveaux capteurs valeur énergétique
- Configuration tarifs HC/HP/Tempo
- Intégration `sensor.rte_tempo_couleur_jour_j0`

**Impact :**
- Décisions financièrement optimales
- Incitation forte autoconsommation en HP
- Base pour optimisations futures

**Complexité :** Moyenne

---

**#2 - Tracking temporel quotidien** ⭐⭐⭐⭐
- Implémentation `temporal_tracking.py`
- Capteurs daily_production, daily_consumption, etc.
- Réinitialisation configurable
- Persistance avec Store

**Impact :**
- Statistiques quotidiennes fiables
- Détection de patterns
- Base pour objectifs quotidiens

**Complexité :** Moyenne

---

#### Phase 2 : Prédictions (3-4 semaines)

**#3 - Prédictions fenêtre glissante** ⭐⭐⭐⭐⭐
- Implémentation `sliding_window_predictor.py`
- Capteur `forecast_window` avec stats
- Intégration prévisions météo (Met.no)
- API de service pour requêtes custom

**Impact :**
- Décisions anticipatives pour SO
- Lissage variations court terme
- Meilleure planification appareils

**Complexité :** Moyenne-élevée

---

**#4 - Optimisation multi-objectifs** ⭐⭐⭐⭐
- Implémentation fonction objectif hybride
- Capteur `optimization_target`
- Configuration poids critères
- Exposition scores détaillés

**Impact :**
- Vision holistique (pas que wattage)
- Adaptation préférences utilisateur
- Synergie maximale avec SO

**Complexité :** Moyenne

---

#### Phase 3 : Intelligence (4-6 semaines)

**#5 - Configuration adaptative** ⭐⭐⭐
- Auto-détection taille installation
- Recommandations paramètres
- Service `auto_configure`
- Interface guidée setup

**Impact :**
- Setup "zéro effort"
- Configuration optimale instantanée
- Réduction erreurs utilisateur

**Complexité :** Moyenne

---

**#6 - Calibration automatique** ⭐⭐⭐⭐
- Historique 7-30 jours
- Auto-tune `system_efficiency`
- Service `calibrate_efficiency`
- Indicateur confiance

**Impact :**
- Précision améliorée automatiquement
- Maintenance zéro
- Adaptation conditions réelles

**Complexité :** Moyenne-élevée

---

**#7 - Détection d'anomalies** ⭐⭐
- Analyse tendances yield_ratio
- Binary sensors performance_issue, shading_detected
- Alertes automatiques
- Recommandations maintenance

**Impact :**
- Maintenance prédictive
- Détection problèmes rapide
- Optimisation long terme

**Complexité :** Moyenne

---

#### Phase 4 : Avancé (6-8 semaines)

**#8 - Stratégies batterie prédictives** ⭐⭐⭐⭐
- Calcul charge/décharge optimale
- Capteur `battery_strategy`
- Anticipation creux production
- Maximisation autoconso avec stockage

**Impact :**
- Utilisation optimale batterie
- Économies supplémentaires
- Résilience coupures

**Complexité :** Élevée

---

## 📊 Tableau de synthèse

| # | Optimisation | Inspiré SO | Priorité | Complexité | Impact | Durée |
|---|--------------|------------|----------|------------|--------|-------|
| 1 | Module coûts énergétiques | ✅ Fonction objectif | ⭐⭐⭐⭐⭐ | Moyenne | Très fort | 2-3 sem |
| 2 | Tracking temporel | ✅ `_on_time_sec` + reset | ⭐⭐⭐⭐ | Moyenne | Fort | 1-2 sem |
| 3 | Fenêtre glissante | ✅ `refresh_period` | ⭐⭐⭐⭐⭐ | Moy-Élev | Très fort | 3-4 sem |
| 4 | Multi-objectifs | ✅ Priority weight | ⭐⭐⭐⭐ | Moyenne | Fort | 2-3 sem |
| 5 | Config adaptative | ✅ Params adaptatifs | ⭐⭐⭐ | Moyenne | Moyen | 2 sem |
| 6 | Calibration auto | ✅ (inspiré SO) | ⭐⭐⭐⭐ | Moy-Élev | Fort | 3-4 sem |
| 7 | Détection anomalies | ✅ Contraintes | ⭐⭐ | Moyenne | Moyen | 2-3 sem |
| 8 | Stratégies batterie | ✅ SOC threshold | ⭐⭐⭐⭐ | Élevée | Très fort | 4-6 sem |

**Total estimation :** 16-27 semaines (4-7 mois) pour implémentation complète

---

## 🎯 Recommandations stratégiques

### Quick Wins (Sprint 1 - 3 semaines)

1. **Module coûts énergétiques** (#1)
   - ROI immédiat pour utilisateurs
   - Différenciateur fort vs concurrence
   - Base pour toutes optimisations futures

2. **Tracking temporel** (#2)
   - Fonctionnalité très demandée
   - Relativement simple à implémenter
   - Valeur perçue élevée

### Différenciateurs (Sprint 2-3 - 6 semaines)

3. **Fenêtre glissante** (#3)
   - Fonctionnalité unique vs concurrents
   - Synergie maximale avec Solar Optimizer
   - Impact majeur sur optimisation

4. **Multi-objectifs** (#4)
   - Vision holistique innovante
   - Flexibilité utilisateur
   - Positionnement "premium"

### Perfectionnement (Sprint 4+ - long terme)

5-8. Fonctionnalités avancées selon feedback utilisateurs

---

## 💡 Innovations originales SPVM

Au-delà de l'inspiration Solar Optimizer, voici des innovations spécifiques à SPVM :

### Innovation #1 : Prédiction physique hybride

```python
class HybridPhysicalPredictor:
    """Combine modèle physique SPVM avec apprentissage statistique."""

    def predict(self, dt, weather_forecast):
        # 1. Prédiction physique (NOAA)
        physical_prediction = self.solar_model.compute(dt, weather_forecast)

        # 2. Correction statistique (historique)
        if self.has_sufficient_history():
            correction_factor = self._calculate_correction(dt, weather_forecast)
            hybrid_prediction = physical_prediction * correction_factor
        else:
            hybrid_prediction = physical_prediction

        # 3. Intervalle de confiance
        confidence_interval = self._calculate_confidence(dt, weather_forecast)

        return {
            "expected_w": hybrid_prediction,
            "confidence_lower_w": hybrid_prediction - confidence_interval,
            "confidence_upper_w": hybrid_prediction + confidence_interval,
            "confidence_pct": self._confidence_to_percent(confidence_interval),
        }
```

**Avantage :** Combine rigueur physique et adaptation réelle

---

### Innovation #2 : Cartographie énergétique quotidienne

```python
class DailyEnergyMap:
    """Cartographie production/consommation sur 24h."""

    def generate_heatmap(self, date):
        """Génère carte chaleur production vs consommation."""
        hourly_data = []

        for hour in range(24):
            dt = datetime.combine(date, time(hour=hour))

            # Prédiction production
            expected_w = self.predict(dt)

            # Historique consommation (moyenne sur 30j)
            avg_consumption_w = self.get_average_consumption(hour)

            # Calcul surplus/déficit
            surplus_w = expected_w - avg_consumption_w

            # Classification période
            if surplus_w > 1000:
                period_type = "high_surplus"
            elif surplus_w > 0:
                period_type = "low_surplus"
            elif surplus_w > -500:
                period_type = "low_deficit"
            else:
                period_type = "high_deficit"

            hourly_data.append({
                "hour": hour,
                "expected_w": expected_w,
                "avg_consumption_w": avg_consumption_w,
                "surplus_w": surplus_w,
                "period_type": period_type,
            })

        return hourly_data
```

**Visualisation Lovelace :**
```yaml
# Carte chaleur montrant meilleurs créneaux d'activation appareils
type: custom:apexcharts-card
series:
  - entity: sensor.spvm_daily_energy_map
    data_generator: |
      return entity.attributes.hourly_data.map(d => [d.hour, d.surplus_w])
```

**Avantage :** Vision instantanée des créneaux optimaux

---

### Innovation #3 : Score d'opportunité solaire

```python
class SolarOpportunityScore:
    """Calcule un score d'opportunité pour activation appareils."""

    def calculate_score(self, dt, device_power_w, device_duration_min):
        """Score 0-100 indiquant pertinence activation maintenant."""

        # Critère 1 : Production actuelle vs demandée (40%)
        current_surplus = self.get_current_surplus()
        production_score = min(100, (current_surplus / device_power_w) * 100)

        # Critère 2 : Stabilité sur durée appareil (30%)
        window_forecast = self.predict_window(dt, device_duration_min)
        stability_score = window_forecast["stability_index"] * 100

        # Critère 3 : Valeur financière période (20%)
        current_value = self.get_energy_value(dt)
        max_daily_value = max(self.get_energy_value(h) for h in range(24))
        financial_score = (current_value / max_daily_value) * 100

        # Critère 4 : Opportunité relative (10%)
        # Compare maintenant vs prochaines heures
        future_scores = [self._quick_score(dt + timedelta(hours=h)) for h in range(1, 5)]
        opportunity_score = 100 if production_score > max(future_scores) else 50

        # Agrégation pondérée
        total_score = (
            production_score * 0.4 +
            stability_score * 0.3 +
            financial_score * 0.2 +
            opportunity_score * 0.1
        )

        return {
            "total_score": round(total_score, 1),
            "production_score": round(production_score, 1),
            "stability_score": round(stability_score, 1),
            "financial_score": round(financial_score, 1),
            "opportunity_score": round(opportunity_score, 1),
            "recommendation": self._get_recommendation(total_score),
        }

    def _get_recommendation(self, score):
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "average"
        else:
            return "poor"
```

**Nouveau capteur :**
```python
# sensor.spvm_opportunity_score_2000w_60min
# État : 87.3 (score 0-100)
# Attributs : détail scores + recommandation
```

**Usage automation :**
```yaml
automation:
  - alias: "Smart Dishwasher Start"
    trigger:
      platform: numeric_state
      entity_id: sensor.spvm_opportunity_score_1800w_90min
      above: 75
    condition:
      - condition: state
        entity_id: binary_sensor.dishwasher_ready
        state: 'on'
    action:
      service: switch.turn_on
      entity_id: switch.dishwasher
```

**Avantage :** Automatisation intelligente sans algorithme complexe

---

## 📖 Conclusion

### Ce que SPVM peut apprendre de Solar Optimizer

1. **Fonction objectif multi-critères** - Équilibrer coût et préférences
2. **Gestion temporelle fine** - Tracking quotidien avec reset
3. **Intégration coûts énergétiques** - Tarifs HC/HP/Tempo
4. **Fenêtrage prédictif** - Optimisation sur horizon court
5. **Configuration adaptative** - Paramètres selon installation
6. **Persistance d'état** - Continuité données quotidiennes

### Ce que SPVM apporte d'unique

1. **Modèle physique rigoureux** - Calculs astronomiques NOAA
2. **Zéro dépendance historique** - Fonctionne immédiatement
3. **Performance exceptionnelle** - Calcul instantané, mémoire minimale
4. **Prédictions scientifiques** - Pas de "boîte noire"
5. **Potentiel innovations** - Hybridation physique/stats, opportunité score

### Positionnement cible

```
┌─────────────────────────────────────────────────┐
│         Écosystème Optimisation Solaire         │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────┐    ┌──────────────────┐  │
│  │  SPVM Enhanced   │───▶│ Solar Optimizer  │  │
│  │                  │    │                  │  │
│  │ • Prédictions    │    │ • Décisions      │  │
│  │ • Coûts          │    │ • Activations    │  │
│  │ • Opportunités   │    │ • Priorités      │  │
│  │ • Fenêtrage      │    │ • Contraintes    │  │
│  └──────────────────┘    └──────────────────┘  │
│         │                         │             │
│         └─────────┬───────────────┘             │
│                   ▼                             │
│        ┌─────────────────────┐                  │
│        │ Appareils Contrôlés │                  │
│        └─────────────────────┘                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**SPVM devient le "cerveau prédictif et analytique"**
**Solar Optimizer reste le "cerveau décisionnel et exécutif"**

Ensemble, ils forment l'écosystème d'autoconsommation le plus puissant de Home Assistant.

---

**Document généré le 18 novembre 2025**
**Pour questions/suggestions :** [GitHub Issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)

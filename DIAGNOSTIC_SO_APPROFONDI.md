# 🔬 Diagnostic approfondi : Solar Optimizer n'active pas les consommateurs

**Situation confirmée :**
- ✅ Solar Optimizer utilise bien `sensor.spvm_expected_production`
- ❌ SO n'active toujours pas les consommateurs disponibles
- Production potentielle : 2.6kW
- Consommation actuelle : 1.5kW
- Surplus disponible : 1.1kW non exploité

---

## 📋 Checklist de diagnostic interactive

### Étape 1 : Vérifier que SO voit bien le surplus

**Activez les logs détaillés :**

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.solar_optimizer: debug
```

**Redémarrez HA**, puis forcez un refresh :
```yaml
# Outils développeur → Services
service: solar_optimizer.refresh
```

**Dans les logs (Outils développeur → Logs), cherchez :**
```
[custom_components.solar_optimizer] Production: XXXX W
[custom_components.solar_optimizer] Consumption: XXXX W
[custom_components.solar_optimizer] Available power: XXXX W
```

**Question cruciale :** SO voit-il bien **"Production: 2600W"** ou voit-il autre chose ?

---

### Étape 2 : Vérifier les états des appareils

**Pour chaque appareil géré par SO, vérifiez dans Outils développeur → États :**

#### 2.1 - Switches d'activation

```yaml
# Cherchez : switch.solar_optimizer_enable_
switch.solar_optimizer_enable_chauffe_eau: ???  # ON ou OFF ?
switch.solar_optimizer_enable_lave_linge: ???   # ON ou OFF ?
switch.solar_optimizer_enable_xxx: ???          # ON ou OFF ?
```

**Si OFF → L'appareil est exclu de l'optimisation**

---

#### 2.2 - Temps d'utilisation quotidien

```yaml
# Cherchez : sensor.solar_optimizer_*_on_time_today
sensor.solar_optimizer_chauffe_eau_on_time_today: ??? minutes
```

**Comparez avec votre configuration :**
```yaml
# Si vous avez configuré :
max_on_time_per_day_min: 180  # 3h max

# Et le sensor affiche : 175 minutes
# → Appareil presque bloqué, seulement 5 min restantes aujourd'hui
```

---

#### 2.3 - Attributs des appareils

**Cliquez sur un appareil dans États, regardez les attributs :**

```yaml
# Attributs importants
is_usable: true/false          # L'appareil peut-il être utilisé ?
is_active: true/false          # L'appareil est-il actuellement actif ?
is_waiting: true/false         # L'appareil est-il en attente (bloqué) ?
_next_date_available: XXX      # Prochaine action autorisée
current_power: XXX             # Puissance actuelle
```

**Si `is_usable: false` → Cherchez pourquoi :**
- Template de vérification ?
- Seuil batterie ?
- Switch enable désactivé ?

**Si `is_waiting: true` → L'appareil est bloqué temporellement**

---

### Étape 3 : Vérifier la configuration des appareils

**Pour chaque appareil, dans Paramètres → Solar Optimizer → Appareils :**

#### 3.1 - Durées minimales

```yaml
Durée minimale d'activation (duration_min): ??? secondes
Durée minimale d'arrêt (duration_stop_min): ??? secondes
Durée minimale entre changements de puissance: ??? secondes
```

**Problème potentiel :**
```yaml
# Si duration_min = 3600 (1 heure)
# Et que SO estime que le surplus de 1.1kW ne tiendra que 30 min
# → SO ne démarrera PAS l'appareil car il ne peut garantir 1h
```

**Test :** Réduire temporairement `duration_min` à 600 (10 min) et observer

---

#### 3.2 - Quotas quotidiens

```yaml
Temps maximum par jour (max_on_time_per_day_min): ??? minutes
Temps minimum par jour (min_on_time_per_day_min): ??? minutes
Heure heures creuses (offpeak_time): ??? (ex: 02:00)
```

**Problème potentiel :**
```yaml
# Si max_on_time_per_day_min = 120 (2h)
# Et l'appareil a déjà tourné 110 min aujourd'hui
# → Seulement 10 min restantes, SO peut juger ça inutile
```

---

#### 3.3 - Seuil batterie

```yaml
Seuil batterie minimum (battery_soc_threshold): ??? %
```

**Vérifiez l'état de votre batterie :**
```yaml
# Dans États
sensor.battery_soc: ??? %

# Si battery_soc = 45% et battery_soc_threshold = 50%
# → Appareil bloqué jusqu'à recharge batterie
```

---

#### 3.4 - Templates de vérification

```yaml
Template d'usabilité (check_usable_template): ???
Template d'état actif (active_template): ???
```

**Testez manuellement les templates dans Outils développeur → Modèle :**

```jinja
{# Exemple de template qui pourrait bloquer #}
{{ states('sensor.water_temperature') | float < 60 }}

{# Si température = 65°C → false → appareil non utilisable #}
```

**Problème fréquent :** Template mal écrit ou capteur indisponible → `false` → appareil bloqué

---

### Étape 4 : Vérifier configuration globale SO

#### 4.1 - Priority weight

**Dans Paramètres → Solar Optimizer → Configuration :**

```yaml
Priority weight: ??? %
```

**Problème potentiel :**
```yaml
# Si priority_weight = 80%
# SO privilégie FORTEMENT les priorités au détriment de l'autoconso

# Exemple :
Appareil A (priorité Haute) : 1000W, actuellement ON
Appareil B (priorité Basse) : 800W, actuellement OFF
Surplus disponible : 1100W

# SO préfère laisser appareil A seul (satisfait priorité)
# Plutôt qu'activer B (priorité basse, "pas important")
```

**Test :** Réduire `priority_weight` à 30% et observer

---

#### 4.2 - Coûts import/export

```yaml
Prix d'achat (buy_price): ??? €/kWh
Prix de vente (sell_price): ??? €/kWh
```

**Problème potentiel :**
```yaml
# Si buy_price = 0.20 et sell_price = 0.18
# Différence faible (0.02€/kWh) → 10% seulement

# SO peut calculer :
# - Activer appareil B (consomme 800W supplémentaires)
# - Ou exporter 800W (perte seulement 0.016€/h)
# → SO juge que l'export n'est "pas si grave"
```

**Test :** Augmenter artificiellement la différence :
```yaml
buy_price: 0.25
sell_price: 0.08  # Prix OA réel
```

---

#### 4.3 - Paramètres algorithme

```yaml
# Configuration avancée → Algorithme
initial_temp: ??? (défaut: 1000)
cooling_factor: ??? (défaut: 0.95)
max_iteration_number: ??? (défaut: 1000)
```

**Problème potentiel :**
```yaml
# Avec 5+ appareils et max_iteration_number = 1000
# Algorithme peut ne pas explorer toutes les combinaisons
# → Converge vers solution sous-optimale (1 appareil au lieu de 2)
```

**Test :** Augmenter temporairement :
```yaml
initial_temp: 1500
max_iteration_number: 2000
```

---

### Étape 5 : Analyser les logs d'optimisation

**Dans les logs, après `solar_optimizer.refresh`, cherchez :**

#### 5.1 - Solution trouvée

```
[solar_optimizer] Best solution found: {...}
[solar_optimizer] Best objective: XXX
```

**Analyse du "best objective" :**
```
Best objective: 0.05  # Proche de 0 = bon
Best objective: 2.30  # Élevé = solution très sous-optimale
```

**Si objective élevé avec un seul appareil activé → Problème de convergence**

---

#### 5.2 - Raisons de rejet

```
[solar_optimizer] Device XXX cannot change state: is_waiting
[solar_optimizer] Device XXX is not usable: battery_soc below threshold
[solar_optimizer] Device XXX is not usable: check_usable_template returned false
```

**Ces messages indiquent exactement pourquoi SO ignore l'appareil**

---

## 🎯 Scénarios probables (puisque capteur OK)

### Scénario A : Contraintes temporelles trop strictes (40%)

```yaml
# Vos appareils ont probablement :
duration_min: 1800-3600  # 30 min - 1h minimum

# SO calcule :
# "J'ai 1.1kW de surplus maintenant, mais dans 20 min le soleil baisse"
# "Je ne peux garantir 1h de surplus"
# → N'active pas l'appareil
```

**Solution :**
- Réduire `duration_min` à 600s (10 min)
- Ou augmenter `duration_power_min` pour permettre ajustements fréquents

---

### Scénario B : Priority weight trop élevé (30%)

```yaml
priority_weight: 70-90%

# SO privilégie satisfaction priorités
# Appareil prioritaire déjà ON → "Mission accomplie"
# Ignore appareils basse priorité même si surplus
```

**Solution :** Réduire à 30-40%

---

### Scénario C : Quotas quotidiens saturés (15%)

```yaml
# Un ou plusieurs appareils ont atteint leur max_on_time_per_day_min
# → Bloqués jusqu'à demain 05:00
```

**Solution :**
- Vérifier `sensor.solar_optimizer_*_on_time_today`
- Augmenter `max_on_time_per_day_min`

---

### Scénario D : Templates bloquants (10%)

```yaml
check_usable_template: "{{ states('sensor.xxx') | float < 60 }}"

# Si sensor.xxx = unavailable ou > 60
# → Template = false
# → Appareil non utilisable
```

**Solution :**
- Évaluer manuellement chaque template
- Ajouter gestion des états indisponibles :
  ```jinja
  {{ states('sensor.xxx') not in ['unavailable', 'unknown'] and states('sensor.xxx') | float < 60 }}
  ```

---

### Scénario E : Seuil batterie bloquant (5%)

```yaml
battery_soc_threshold: 50%
# Mais batterie à 45%
# → Tous appareils avec ce seuil bloqués
```

**Solution :** Réduire temporairement le seuil

---

## 🧪 Tests diagnostic à faire MAINTENANT

### Test 1 : Forcer refresh avec logs

```yaml
# 1. Activer logger debug (configuration.yaml)
logger:
  logs:
    custom_components.solar_optimizer: debug

# 2. Redémarrer HA

# 3. Forcer refresh
service: solar_optimizer.refresh

# 4. Copier TOUS les logs solar_optimizer et me les envoyer
```

---

### Test 2 : Vérifier états appareils

```yaml
# Dans Outils développeur → États
# Pour CHAQUE appareil solar_optimizer, noter :

Appareil 1 (ex: chauffe_eau) :
  - switch.solar_optimizer_enable_XXX: on/off ?
  - sensor.solar_optimizer_XXX_on_time_today: ??? min
  - is_usable: true/false ?
  - is_waiting: true/false ?
  - current_power: ??? W

Appareil 2 (ex: lave_linge) :
  - switch.solar_optimizer_enable_XXX: on/off ?
  - sensor.solar_optimizer_XXX_on_time_today: ??? min
  - is_usable: true/false ?
  - is_waiting: true/false ?
  - current_power: ??? W

# etc.
```

---

### Test 3 : Configuration appareil détaillée

```yaml
# Pour au moins 2 appareils, noter TOUTE la config :

Appareil : chauffe_eau
  - power_min: ??? W
  - power_max: ??? W
  - duration_min: ??? s
  - duration_stop_min: ??? s
  - max_on_time_per_day_min: ??? min
  - min_on_time_per_day_min: ??? min
  - battery_soc_threshold: ??? %
  - check_usable_template: ???
  - active_template: ???
  - priority: ??? (Very Low / Low / Medium / High / Very High)
```

---

### Test 4 : Configuration globale SO

```yaml
# Noter :
- priority_weight: ??? %
- buy_price: ??? €/kWh
- sell_price: ??? €/kWh
- refresh_period_sec: ??? s
- algorithm.initial_temp: ???
- algorithm.cooling_factor: ???
- algorithm.max_iteration_number: ???
```

---

### Test 5 : Test réduction contraintes

**Temporairement, pour 1 appareil :**
```yaml
# Modifier :
duration_min: 600  # 10 min au lieu de 1800+
duration_stop_min: 300  # 5 min
battery_soc_threshold: 20  # Au lieu de 50+
max_on_time_per_day_min: 360  # 6h au lieu de 180

# ET
priority_weight: 30  # Au lieu de 70+
```

**Forcer refresh et observer si l'appareil s'active**

---

## 📊 Informations à me fournir

Pour diagnostic précis, j'ai besoin de :

1. **Logs complets après refresh** (les 50 premières lignes contenant "solar_optimizer")

2. **États de 2-3 appareils** (copie complète des attributs depuis Outils développeur → États)

3. **Configuration d'au moins 1 appareil** (tous les paramètres)

4. **Configuration globale SO** (priority_weight, prix, algorithme)

5. **État batterie actuel** :
   ```yaml
   sensor.battery_soc: ??? %
   sensor.battery_power: ??? W
   ```

6. **Nombre total d'appareils gérés par SO** : ???

---

## 💡 Hypothèse la plus probable

Basé sur votre description (surplus de 1.1kW non utilisé), je suspecte **une combinaison de :**

1. **`duration_min` trop élevé** (1h+) → SO attend une garantie de surplus sur 1h
2. **`priority_weight` élevé** (70%+) → SO satisfait avec appareil prioritaire déjà ON
3. **Templates bloquants** → Appareils secondaires non utilisables pour raison cachée

**Test rapide à faire :**
- Réduire `priority_weight` à 25%
- Réduire `duration_min` à 600s pour un appareil
- Forcer refresh
- Observer si cet appareil s'active

---

Pouvez-vous me fournir les informations demandées (logs + états + config) pour qu'on identifie la cause exacte ?

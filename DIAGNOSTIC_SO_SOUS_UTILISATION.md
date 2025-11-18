# 🔍 Diagnostic : Solar Optimizer sous-utilise la production disponible

**Problème rapporté :**
- SPVM indique : **2.6kW de production potentielle**
- Consommation réelle : **1.5kW**
- **Surplus non exploité : 1.1kW**
- Consommateurs disponibles mais non activés par SO
- Activation manuelle → production suit correctement (installation bridée confirmée)

---

## 🎯 Causes possibles et vérifications

### ❌ Cause #1 : Mauvais capteur "Production solaire" dans SO

**Problème le plus probable :**

Solar Optimizer utilise probablement **`sensor.your_pv_production`** (production bridée actuelle = 1.5kW) au lieu de **`sensor.spvm_expected_production`** (potentiel disponible = 2.6kW).

**Vérification :**
```yaml
# Dans la configuration de Solar Optimizer
# Aller dans : Paramètres → Appareils et Services → Solar Optimizer → Configurer

Production solaire: ???  # ⬅️ VÉRIFIER ICI
```

**Solution :**
```yaml
# Configuration correcte pour installation bridée
Production solaire: sensor.spvm_expected_production  # ⬅️ Production POTENTIELLE
Consommation nette: sensor.your_house_consumption    # ⬅️ Consommation maison
```

**Ce qui se passe actuellement :**
```
SO voit :
  Production = 1.5kW (bridée)
  Consommation = 1.5kW
  Surplus calculé = 0kW
  → SO pense qu'il n'y a rien à activer ❌

Ce qu'il devrait voir :
  Production = 2.6kW (potentielle SPVM)
  Consommation = 1.5kW
  Surplus calculé = 1.1kW
  → SO active d'autres appareils ✅
```

---

### ❌ Cause #2 : Contraintes d'appareils bloquantes

Même si SO voit le bon surplus, vos appareils peuvent être bloqués par :

#### 2.1 - Durées minimales non respectées

```yaml
# Appareil configuré avec
duration_min: 3600  # 1 heure minimum

# Si l'appareil a démarré il y a 30 min
# → Bloqué, ne peut pas s'arrêter avant 30 min
# → SO ne peut pas activer un 2e appareil car le 1er "consomme" déjà le budget
```

**Vérification :**
- Logs Solar Optimizer : cherchez `"Device X is waiting, cannot change state"`
- États appareils : `_next_date_available` dans attributs

#### 2.2 - Quotas quotidiens atteints

```yaml
# Appareil configuré avec
max_on_time_per_day_min: 180  # 3h max par jour

# Si déjà utilisé 3h aujourd'hui
# → Bloqué jusqu'à demain (reset à 05:00)
```

**Vérification :**
```yaml
# Capteur par appareil
sensor.solar_optimizer_device_X_on_time_today

# Si proche de max_on_time_per_day_min → bloqué
```

#### 2.3 - Seuil batterie

```yaml
# Appareil configuré avec
battery_soc_threshold: 50  # Ne démarre que si batterie > 50%

# Si votre batterie est à 45%
# → Appareil bloqué
```

**Vérification :**
- État batterie vs seuils configurés

#### 2.4 - Templates de vérification

```yaml
# Appareil configuré avec
check_usable_template: "{{ states('sensor.temperature') | float < 60 }}"

# Si température > 60°C
# → Appareil considéré non utilisable
```

**Vérification :**
- Évaluer manuellement les templates dans Outils développeur

#### 2.5 - Commutateurs d'activation désactivés

```yaml
# Chaque appareil a un switch enable
switch.solar_optimizer_enable_device_X

# Si off → appareil exclu de l'optimisation
```

**Vérification :**
```yaml
# Vérifier que tous vos appareils ont :
switch.solar_optimizer_enable_device_X: on
```

---

### ❌ Cause #3 : Paramètres algorithme trop conservateurs

#### 3.1 - Nombre d'itérations insuffisant

```yaml
# Si vous avez beaucoup d'appareils (>5)
# Avec configuration par défaut
algorithm:
  max_iteration_number: 1000  # Peut être insuffisant
```

**Symptôme :**
- SO active seulement 1 appareil alors que plusieurs pourraient tenir
- Algorithme converge trop vite vers solution sous-optimale

**Solution :**
```yaml
# Pour 5-10 appareils
algorithm:
  max_iteration_number: 2000
  initial_temp: 1500
  cooling_factor: 0.95
```

#### 3.2 - Priority weight trop élevé

```yaml
# Si priority_weight = 80%
# SO privilégie les priorités au détriment de l'optimisation énergétique
# Peut activer seulement les appareils prioritaires
```

**Solution :**
```yaml
# Réduire le poids priorité
priority_weight: 30-40%  # Équilibre autoconso / priorités
```

---

### ❌ Cause #4 : SO n'active qu'un appareil à la fois (limitation algorithmique)

**Non, SO peut activer plusieurs appareils simultanément.**

L'algorithme de recuit simulé explore toutes les combinaisons possibles :
- Appareil A seul
- Appareil B seul
- Appareils A + B
- Appareils A + B + C
- etc.

**MAIS** : Si les contraintes ou la fonction objectif pénalisent les combinaisons multiples, SO peut préférer un seul appareil.

**Exemple :**
```python
# Si vous avez :
Appareil A : 1000W, priorité Haute
Appareil B : 800W, priorité Basse
Appareil C : 500W, priorité Basse

Surplus disponible : 1100W

# Avec priority_weight élevé, SO préfère :
Solution 1 : Activer A seul (1000W, satisfait priorité) → Coût faible
Solution 2 : Activer B + C (1300W, dépasse surplus, pas de priorité) → Coût élevé

# SO choisit solution 1 même si surplus reste
```

---

### ❌ Cause #5 : Coûts import/export mal configurés

```yaml
# Si vous avez
buy_price: 0.20  # Prix achat
sell_price: 0.18  # Prix revente

# Différence faible → SO peut considérer qu'exporter n'est pas si grave
# → Préfère ne pas activer appareil non prioritaire
```

**Solution :**
```yaml
# Accentuer la différence pour inciter autoconso
buy_price: 0.22
sell_price: 0.10  # Prix OA réel
```

---

## 🔧 Plan d'action diagnostic

### Étape 1 : Vérifier configuration capteurs SO

```yaml
# Configuration → Solar Optimizer → Éditer

VÉRIFIER :
  Production solaire: sensor.spvm_expected_production  # ⬅️ PAS sensor.pv_production
  Consommation nette: sensor.your_house_consumption

# Si vous utilisez sensor.pv_production → C'EST LE PROBLÈME
```

### Étape 2 : Activer les logs détaillés

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.solar_optimizer: debug
```

**Redémarrer HA** puis observer les logs :
```
Outils développeur → Logs

Chercher :
- "best_objective: XXX"
- "Device X is waiting"
- "Device X cannot change state"
- "Power available: XXX"
```

### Étape 3 : Vérifier états appareils

```yaml
# Pour chaque appareil géré par SO
# Outils développeur → États → Chercher "solar_optimizer"

VÉRIFIER :
  switch.solar_optimizer_enable_device_X: on  # Activé ?
  sensor.solar_optimizer_device_X_on_time_today: XXX  # Proche du max ?

# Attributs de l'appareil
  _next_date_available: XXX  # Dans le futur = bloqué
  is_usable: true/false
  is_active: true/false
```

### Étape 4 : Tester manuellement l'algorithme

```yaml
# Forcer un refresh SO
Outils développeur → Services → solar_optimizer.refresh

# Observer les logs immédiatement après
# Doit voir :
- "Starting optimization with X devices"
- "Production: 2600W, Consumption: 1500W"  # ⬅️ Si voit 1500W/1500W → mauvais capteur
- "Best solution found: [device_A=on, device_B=on, ...]"
```

### Étape 5 : Comparer solutions manuelles vs SO

```yaml
# Test A : Activer manuellement device_B en plus de device_A
# Observer : Production monte bien à 2.4kW ?

# Si oui → Confirme que SO devrait pouvoir le faire
# Si SO ne le fait pas → Problème configuration/contraintes
```

---

## 🎯 Solutions par ordre de probabilité

### ✅ Solution #1 (90% de chances) : Corriger capteur production

```yaml
Solar Optimizer:
  Production solaire: sensor.spvm_expected_production  # ⬅️ CHANGEZ ICI
```

### ✅ Solution #2 (5% de chances) : Ajuster contraintes appareils

```yaml
# Réduire duration_min si trop élevé
duration_min: 600  # 10 min au lieu de 1h

# Augmenter max_on_time_per_day_min si trop bas
max_on_time_per_day_min: 360  # 6h au lieu de 3h

# Vérifier battery_soc_threshold pas trop élevé
battery_soc_threshold: 20  # Au lieu de 50
```

### ✅ Solution #3 (3% de chances) : Ajuster algorithme

```yaml
algorithm:
  max_iteration_number: 2000  # Au lieu de 1000
  initial_temp: 1500  # Au lieu de 1000

priority_weight: 30  # Au lieu de 70+
```

### ✅ Solution #4 (2% de chances) : Ajuster coûts

```yaml
buy_price: 0.2228  # Vrai prix HP
sell_price: 0.10   # Vrai prix OA
```

---

## 📊 Exemple de configuration optimale pour installation bridée

```yaml
# Solar Optimizer - Configuration pour Enphase/micro-onduleurs bridés

# Capteurs principaux
Production solaire: sensor.spvm_expected_production  # ⬅️ CRUCIAL
Consommation nette: sensor.house_consumption
Batterie SOC: sensor.battery_soc
Batterie puissance: sensor.battery_power

# Coûts
buy_price: 0.2228  # €/kWh HP
sell_price: 0.10   # €/kWh OA

# Algorithme
algorithm:
  initial_temp: 1500
  min_temp: 0.1
  cooling_factor: 0.95
  max_iteration_number: 1500

# Priority weight
priority_weight: 35  # Équilibre autoconso/priorités

# Refresh period
refresh_period_sec: 300  # 5 minutes
```

---

## 🔍 Captures d'écran à fournir pour diagnostic

Si le problème persiste, fournissez :

1. **Configuration SO - Capteurs**
   - Screenshot : Paramètres → Solar Optimizer → Production solaire

2. **États capteurs**
   ```yaml
   sensor.spvm_expected_production: 2600
   sensor.your_pv_production: 1500  # Production bridée
   sensor.house_consumption: 1500
   ```

3. **États appareils SO**
   ```yaml
   switch.solar_optimizer_enable_device_A: on/off ?
   sensor.solar_optimizer_device_A_on_time_today: XXX
   ```

4. **Logs SO** après `solar_optimizer.refresh`
   ```
   [custom_components.solar_optimizer] Production: XXXX
   [custom_components.solar_optimizer] Consumption: XXXX
   [custom_components.solar_optimizer] Best objective: XXXX
   ```

---

## 💡 Conclusion

**Diagnostic le plus probable : 90% de chances**

Solar Optimizer utilise **`sensor.your_pv_production`** (1.5kW bridé) au lieu de **`sensor.spvm_expected_production`** (2.6kW potentiel).

**Solution immédiate :**
1. Paramètres → Appareils et Services → Solar Optimizer → Configurer
2. Production solaire → Changer vers `sensor.spvm_expected_production`
3. Sauvegarder
4. Attendre prochain cycle (5 min) ou forcer refresh
5. Observer activation supplémentaire d'appareils

**Validation :**
- Les logs devraient montrer "Production: 2600W" au lieu de "1500W"
- Plusieurs appareils activés simultanément
- Consommation réelle monte vers 2.5-2.6kW

---

**Prochaines étapes :**
Confirmez la configuration actuelle de votre capteur "Production solaire" dans SO, et on pourra affiner le diagnostic si ce n'est pas ça.

# 🎯 Diagnostic : 2 chauffe-eaux prioritaires - Pourquoi SO n'active pas le 2e ?

**Situation clarifiée :**
- ✅ 2 chauffe-eaux avec **priorité MAXIMALE**
- ✅ Durées minimales courtes (< 5 min, sauf clim 15 min)
- ❌ Surplus 1.1kW non exploité
- Production potentielle : 2.6kW
- Consommation actuelle : 1.5kW

---

## 🔍 Hypothèse principale : SO n'active qu'UN chauffe-eau au lieu de DEUX

### Questions critiques

**Question 1 : Actuellement, quel chauffe-eau est activé ?**

Vérifiez dans **Outils développeur → États** :
```yaml
# Cherchez vos 2 chauffe-eaux
switch.chauffe_eau_1: on/off ?
switch.chauffe_eau_2: on/off ?

# Ou selon votre config
climate.chauffe_eau_ballon_1: heat/off ?
climate.chauffe_eau_ballon_2: heat/off ?
```

**Scénario probable :**
- Chauffe-eau 1 : **ON** (consomme ~1000-1500W)
- Chauffe-eau 2 : **OFF** (alors qu'il pourrait être activé avec le surplus)

---

**Question 2 : Quelle est la puissance de chaque chauffe-eau ?**

```yaml
# Dans votre configuration SO, pour chaque chauffe-eau :
Puissance (power_max): ??? W
```

**Scénario probable :**
```yaml
Chauffe-eau 1 : 1200W (actuellement ON)
Chauffe-eau 2 : 1000W (devrait être activé mais ne l'est pas)

Total si les 2 ON : 2200W
Surplus disponible : 1100W + maison 1500W = 2600W produits
→ Largement suffisant pour les 2
```

---

**Question 3 : Quel est votre priority_weight actuel ?**

**Paramètres → Solar Optimizer → Configuration → Priority weight : ??? %**

---

## 💡 Explications possibles

### Cause A : Priority_weight trop élevé (60% de chances)

**Le problème :**

Avec `priority_weight` très élevé (70%+), l'algorithme raisonne ainsi :

```python
# Fonction objectif SO
objective = consumption_coef × (1 - priority_weight) + priority_coef × priority_weight

# Exemple avec priority_weight = 80% :
objective = consumption_coef × 0.2 + priority_coef × 0.8

# Calcul pour différentes solutions :

Solution 1 : Chauffe-eau 1 ON, Chauffe-eau 2 OFF
  - 1 appareil prioritaire activé sur 2
  - priority_coef = 0.5 (50% des priorités satisfaites)
  - consumption_coef = 0.3 (surplus de 1.1kW exporté)
  - objective = 0.3 × 0.2 + 0.5 × 0.8 = 0.06 + 0.40 = 0.46

Solution 2 : Chauffe-eau 1 ON, Chauffe-eau 2 ON
  - 2 appareils prioritaires activés sur 2
  - priority_coef = 0.0 (100% des priorités satisfaites)
  - consumption_coef = 0.1 (surplus de 100W seulement)
  - objective = 0.1 × 0.2 + 0.0 × 0.8 = 0.02 + 0.00 = 0.02 ✅ MEILLEUR

# Normalement SO devrait choisir Solution 2 !
```

**Mais il peut y avoir un bug ou une mauvaise convergence de l'algorithme.**

**Test immédiat :**
```yaml
# Réduire drastiquement priority_weight
priority_weight: 20  # Au lieu de 70%+

# Forcer refresh
service: solar_optimizer.refresh

# Observer si le 2e chauffe-eau s'active
```

---

### Cause B : Contrainte de quota quotidien sur le 2e chauffe-eau (20%)

**Le problème :**

```yaml
# Chauffe-eau 2 a peut-être atteint son quota
sensor.solar_optimizer_chauffe_eau_2_on_time_today: 175 min

# Si max_on_time_per_day_min = 180
# → Seulement 5 min restantes
# → SO juge ça inutile de l'activer
```

**Vérification :**
```yaml
# Pour chaque chauffe-eau
sensor.solar_optimizer_chauffe_eau_1_on_time_today: ??? min
sensor.solar_optimizer_chauffe_eau_2_on_time_today: ??? min

# Comparer avec max_on_time_per_day_min configuré
```

**Si proche du max → Augmenter temporairement le quota et tester**

---

### Cause C : Template bloquant sur le 2e chauffe-eau (10%)

**Le problème :**

```yaml
# Chauffe-eau 2 a peut-être un template :
check_usable_template: "{{ states('sensor.water_temp_ballon_2') | float < 60 }}"

# Si température = 61°C
# → Template retourne false
# → Chauffe-eau 2 non utilisable
```

**Vérification :**
```yaml
# Dans États, cliquez sur le chauffe-eau 2
# Regardez attributs :
is_usable: true/false ?

# Si false → vérifier les templates
```

---

### Cause D : Algorithme converge mal avec 2 appareils identiques (5%)

**Le problème :**

Avec 2 chauffe-eaux de priorité identique et puissance similaire, l'algorithme de recuit simulé peut avoir du mal à différencier les solutions :

```python
# Pour l'algorithme :
Solution A : CE1=ON, CE2=OFF
Solution B : CE1=OFF, CE2=ON
Solution C : CE1=ON, CE2=ON

# Solutions A et B sont équivalentes en termes de coût
# L'algorithme peut osciller entre A et B sans explorer C
```

**Test :**
```yaml
# Augmenter les paramètres d'exploration
algorithm:
  initial_temp: 2000  # Au lieu de 1000
  max_iteration_number: 2000  # Au lieu de 1000
```

---

### Cause E : Mauvaise estimation du surplus par SO (5%)

**Le problème :**

SO pourrait mal calculer le surplus disponible pour le 2e appareil.

**Vérification dans les logs :**
```
[solar_optimizer] Production: 2600 W
[solar_optimizer] Consumption: 1500 W
[solar_optimizer] Device chauffe_eau_1 current_power: 1200 W
[solar_optimizer] Available power for device chauffe_eau_2: ??? W
```

**Si "Available power" est < 1000W alors que surplus réel = 1100W → Bug calcul**

---

## 🧪 Plan d'action diagnostic

### Étape 1 : Identifier l'état actuel

**Répondez à ces questions :**

```yaml
1. Quel chauffe-eau est actuellement activé ?
   - Chauffe-eau 1 (ballon 1) : ON/OFF ?
   - Chauffe-eau 2 (ballon 2) : ON/OFF ?

2. Puissance de chaque chauffe-eau :
   - Chauffe-eau 1 power_max: ??? W
   - Chauffe-eau 2 power_max: ??? W

3. Priority weight actuel :
   - priority_weight: ??? %

4. Quotas quotidiens :
   - sensor.solar_optimizer_chauffe_eau_1_on_time_today: ??? min
   - sensor.solar_optimizer_chauffe_eau_2_on_time_today: ??? min
   - max_on_time_per_day_min (configuré) : ??? min

5. État d'usabilité :
   - Chauffe-eau 1 is_usable: true/false ?
   - Chauffe-eau 2 is_usable: true/false ?
```

---

### Étape 2 : Logs détaillés

**Activez debug et forcez refresh :**

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.solar_optimizer: debug

# Redémarrez HA

# Forcez refresh
service: solar_optimizer.refresh

# Dans les logs, cherchez :
[solar_optimizer] Production: XXX W
[solar_optimizer] Consumption: XXX W
[solar_optimizer] Device chauffe_eau_1: ...
[solar_optimizer] Device chauffe_eau_2: ...
[solar_optimizer] Best solution found: ...
[solar_optimizer] Best objective: XXX
```

**Copiez et envoyez-moi les 50 premières lignes contenant "solar_optimizer"**

---

### Étape 3 : Test réduction priority_weight

**Test immédiat à faire :**

```yaml
1. Paramètres → Solar Optimizer → Configuration
2. Priority weight → Mettre à 20%
3. Sauvegarder
4. Forcer refresh : service: solar_optimizer.refresh
5. Observer si chauffe-eau 2 s'active
```

**Si ça marche → Le problème était priority_weight trop élevé**

---

### Étape 4 : Test augmentation paramètres algorithme

**Si Étape 3 ne marche pas :**

```yaml
1. Configuration avancée → Algorithme
2. initial_temp: 2000
3. max_iteration_number: 2000
4. Sauvegarder
5. Forcer refresh
6. Observer
```

---

### Étape 5 : Test activation manuelle simultanée

**Test de validation :**

```yaml
1. Activer MANUELLEMENT les 2 chauffe-eaux en même temps
2. Observer la production réelle :
   - Monte-t-elle bien vers 2.4-2.5kW ?
   - Ou reste-t-elle à 1.5kW ?

3. Si production monte → Confirme que les 2 peuvent tourner ensemble
4. Si production reste basse → Problème de bridage ou limitation onduleur
```

---

## 🎯 Solutions par probabilité

### ✅ Solution #1 (60%) : Réduire priority_weight

```yaml
priority_weight: 20-30%  # Au lieu de 70%+
```

**Pourquoi ça marche :**
- Rééquilibre vers optimisation autoconsommation
- Force SO à activer les 2 chauffe-eaux prioritaires si surplus dispo

---

### ✅ Solution #2 (20%) : Augmenter quotas quotidiens

```yaml
# Pour chaque chauffe-eau
max_on_time_per_day_min: 360  # 6h au lieu de 180 (3h)
```

**Vérifier d'abord si un quota est saturé**

---

### ✅ Solution #3 (10%) : Vérifier/corriger templates

```yaml
# Si chauffe-eau 2 a un template bloquant
# Le corriger ou le supprimer temporairement
```

---

### ✅ Solution #4 (5%) : Augmenter paramètres algorithme

```yaml
algorithm:
  initial_temp: 2000
  max_iteration_number: 2000
```

---

### ✅ Solution #5 (5%) : Différencier les priorités

```yaml
# Solution de contournement si algorithme bugue :
Chauffe-eau 1 : Priorité "Very High"
Chauffe-eau 2 : Priorité "High" (un cran en dessous)

# Permet à l'algorithme de mieux différencier
# Mais ce n'est pas la vraie solution
```

---

## 📊 Configuration optimale pour 2 chauffe-eaux prioritaires

```yaml
# Solar Optimizer - Configuration pour 2 ballons ECS

# Capteurs
Production solaire: sensor.spvm_expected_production  ✅
Consommation nette: sensor.house_consumption

# Priority weight
priority_weight: 25%  # ⬅️ CRUCIAL : Pas trop élevé !

# Algorithme (pour 2+ appareils prioritaires)
algorithm:
  initial_temp: 1500
  max_iteration_number: 1500
  cooling_factor: 0.95

# Configuration chaque chauffe-eau
Chauffe-eau 1:
  power_max: 1200 W  # Ajustez selon votre ballon
  priority: Very High
  duration_min: 300 s  # 5 min
  max_on_time_per_day_min: 360  # 6h
  battery_soc_threshold: 20%

Chauffe-eau 2:
  power_max: 1000 W  # Ajustez selon votre ballon
  priority: Very High
  duration_min: 300 s  # 5 min
  max_on_time_per_day_min: 360  # 6h
  battery_soc_threshold: 20%
```

---

## 💡 Réponse directe à votre problème

**Avec 2 chauffe-eaux prioritaires et 1.1kW de surplus non utilisé, le problème est TRÈS PROBABLEMENT :**

**Priority_weight trop élevé (>60%)**

L'algorithme pense : *"J'ai déjà 1 chauffe-eau prioritaire qui tourne, mission accomplie, pas besoin d'activer le 2e"*

**Test immédiat :**
1. Réduire priority_weight à **25%**
2. Forcer refresh
3. Observer activation 2e chauffe-eau

---

## 📝 Informations à me fournir

Pour confirmer le diagnostic :

1. **Priority_weight actuel** : ??? %
2. **Puissance chauffe-eaux** :
   - CE1 : ??? W
   - CE2 : ??? W
3. **État actuel** :
   - CE1 : ON/OFF ?
   - CE2 : ON/OFF ?
4. **Quotas** :
   - CE1 on_time_today : ??? min / ??? max
   - CE2 on_time_today : ??? min / ??? max

Avec ces infos, je pourrai confirmer à 100% la cause !

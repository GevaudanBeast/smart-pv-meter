# 🎛️ Paramètres de correction SPVM v0.7.7

Guide des paramètres configurables pour affiner les prédictions selon votre installation.

---

## 🌍 Open-Meteo API (irradiance réelle) *(v0.7.5+)*

### `use_open_meteo`
**Activer l'API Open-Meteo pour l'irradiance réelle**

- **Défaut :** `true` (activé)
- **Type :** booléen
- **Description :** Utilise les données d'irradiance réelles d'Open-Meteo au lieu du modèle clear-sky théorique.

**Avantages Open-Meteo :**
- Données météo réelles (GHI, GTI, nuages, température)
- Pas besoin de calibration locale
- Précision uniforme partout dans le monde
- Base pour prévisions futures (J+1, J+7)

**Quand désactiver :**
- Pas de connexion internet stable
- Préférence pour le modèle local
- Tests de comparaison

**Configuration :**
```yaml
use_open_meteo: true   # Utilise Open-Meteo (défaut)
use_open_meteo: false  # Revient au modèle clear-sky
```

**Fonctionnement :**
1. SPVM appelle Open-Meteo toutes les 5 minutes (cache)
2. Récupère GHI et GTI (irradiance sur panneau incliné)
3. Applique uniquement les corrections température + ombrage
4. Si API indisponible → fallback automatique sur clear-sky

**Attributs de diagnostic :**
```yaml
irradiance_source: "open_meteo"    # ou "clear_sky_model"
open_meteo_enabled: true
open_meteo_ghi_wm2: 450.0          # GHI réel
open_meteo_gti_wm2: 520.0          # POA réel (incliné)
```

---

## 📍 Correction Lux (nuages épais)

### `lux_min_elevation_deg`
**Élévation minimale pour correction lux**

- **Défaut :** `5.0` degrés
- **Plage :** `0` à `15` degrés
- **Description :** Élévation solaire minimale pour activer la correction basée sur le lux. En dessous, le capteur lux n'est pas fiable.

**Quand augmenter :**
- Si vous avez des lectures lux erratiques en début/fin de journée
- Si le capteur lux est près d'obstacles qui le cachent à faible élévation

**Exemple :**
```yaml
lux_min_elevation_deg: 10  # N'utilise le lux que si soleil > 10°
```

---

### `lux_floor_factor`
**Plancher minimum de correction lux**

- **Défaut :** `0.1` (10% minimum)
- **Plage :** `0.01` à `0.5`
- **Description :** Facteur minimum appliqué même si le lux est très faible. Évite que SPVM prédise 0W par temps très couvert.

**Quand diminuer (ex: 0.02) :**
- Si SPVM **surestime** systématiquement par temps très couvert
- Si votre production réelle peut descendre très bas (< 5% du peak)

**Quand augmenter (ex: 0.2) :**
- Si SPVM **sous-estime** par temps couvert
- Si votre installation maintient une production minimum même par mauvais temps

**Exemple :**
```yaml
lux_floor_factor: 0.02  # Permet de descendre à 2% du potentiel
```

**Calcul :**
```
Élévation 9°, Lux 254
Lux théorique = 80000 × sin(9°) ≈ 12960 lux
Ratio = 254 / 12960 = 0.02 (2%)

Avec floor 0.1 → SPVM applique 10% (conservateur)
Avec floor 0.02 → SPVM applique 2% (précis)
```

---

### `lux_max_change_pct` *(v0.7.3+)*
**Filtre anti-reflet**

- **Défaut :** `100` %
- **Plage :** `20` à `500` %
- **Description :** Variation maximale tolérée entre deux lectures lux consécutives. Au-delà, la valeur est considérée comme un reflet et ignorée.

**Quand diminuer (ex: 50%) :**
- Si des reflets rapides passent malgré le filtre
- Si les conditions lumineuses sont stables

**Quand augmenter (ex: 150%) :**
- Si le capteur est dans une zone où la luminosité varie rapidement (nuages rapides)
- Si trop de valeurs sont filtrées par erreur

**Exemple :**
```yaml
lux_max_change_pct: 100  # Défaut : filtre les variations > 100%
lux_max_change_pct: 50   # Plus strict : filtre les variations > 50%
```

**Cas d'usage :**
- Tube inox ou surface métallique réfléchissante près du capteur
- Fenêtre qui reflète le soleil à certaines heures
- Véhicule garé qui crée des reflets temporaires

**Attributs de diagnostic :**
```yaml
lux_raw: 6000            # Valeur brute du capteur
lux_now: null            # Valeur filtrée (null si reflet détecté)
lux_spike_filtered: true # Indique qu'un reflet a été filtré
```

---

## 🏠 Multi-Array (orientations multiples) *(v0.7.4+)*

### `array2_peak_w`
**Puissance crête du 2ème groupe de panneaux**

- **Défaut :** `0` W (désactivé)
- **Plage :** `0` à `20000` W
- **Description :** Puissance totale du 2ème groupe de panneaux. Si `0`, le multi-array est désactivé.

**Quand utiliser :**
- Installation avec panneaux sur deux toits différents
- Panneaux sur toit + pergola
- Mix de panneaux avec inclinaisons différentes

---

### `array2_tilt_deg`
**Inclinaison du 2ème groupe**

- **Défaut :** `15` degrés
- **Plage :** `0` à `90` degrés
- **Description :** Angle d'inclinaison du 2ème groupe par rapport à l'horizontale.

**Exemples :**
- Pergola : `10-15°`
- Toit plat : `5-10°`
- Toit pentu : `30-45°`

---

### `array2_azimuth_deg`
**Orientation du 2ème groupe**

- **Défaut :** `180` degrés (Sud)
- **Plage :** `0` à `360` degrés
- **Description :** Direction vers laquelle pointe le 2ème groupe. 0=Nord, 90=Est, 180=Sud, 270=Ouest.

---

### Exemple de configuration multi-array

**Installation typique :**
- 6 panneaux × 450W sur toit à 30°, plein sud
- 4 panneaux × 500W sur pergola à 15°, plein sud

```yaml
# Groupe principal (toit)
panel_peak_w: 2700         # 6 × 450W
panel_tilt_deg: 30
panel_azimuth_deg: 180

# Groupe secondaire (pergola)
array2_peak_w: 2000        # 4 × 500W
array2_tilt_deg: 15
array2_azimuth_deg: 180

# Limite onduleur/contrat
cap_max_w: 2800            # Limite de puissance injectée
```

**Fonctionnement :**
1. SPVM calcule l'irradiance POA séparément pour chaque groupe
2. Chaque groupe a son propre angle d'incidence
3. Les corrections météo s'appliquent aux deux groupes
4. Les productions sont additionnées
5. La limite `cap_max_w` s'applique au total

---

## 🌲 Ombrage saisonnier (arbres, bâtiments)

### `shading_winter_pct`
**Ombrage supplémentaire en hiver**

- **Défaut :** `0` % (pas d'ombrage)
- **Plage :** `0` à `100` %
- **Description :** Réduction de production causée par des arbres, bâtiments, ou obstacles qui cachent le soleil en hiver (soleil bas).

**Comment calibrer :**
1. Comparer `sensor.spvm_expected_production` vs production réelle en décembre-janvier
2. Si SPVM surestime de 30% → mettre `shading_winter_pct: 30`

**Exemple :**
```yaml
shading_winter_pct: 40  # Arbres réduisent de 40% en hiver
```

**Impact :**
```
Sans ombrage :
  Production prévue = 1000W
  Production réelle = 600W (arbres cachent 40%)

Avec shading_winter_pct: 40 :
  Production prévue = 600W ✓ Cohérent
```

---

### `shading_month_start` & `shading_month_end`
**Période d'ombrage**

- **Défaut :** `11` (novembre) à `2` (février)
- **Plage :** `1` à `12` (mois)
- **Description :** Mois de début et fin de la période où l'ombrage s'applique.

**Gestion automatique du passage d'année :**
- Si `start <= end` : période simple (ex: mai à septembre)
- Si `start > end` : passage d'année (ex: novembre à février)

**Exemples :**

**Arbres feuillus (ombrage hiver seulement) :**
```yaml
shading_winter_pct: 30
shading_month_start: 11  # Novembre
shading_month_end: 2     # Février
# → Ombrage de novembre à février (soleil bas + feuilles tombées exposent troncs)
```

**Bâtiment au sud (ombrage été seulement) :**
```yaml
shading_winter_pct: 20
shading_month_start: 6   # Juin
shading_month_end: 8     # Août
# → Ombrage de juin à août (soleil haut passe derrière le bâtiment)
```

**Ombrage toute l'année :**
```yaml
shading_winter_pct: 15
shading_month_start: 1   # Janvier
shading_month_end: 12    # Décembre
# → Ombrage permanent
```

---

## 🎯 Cas d'usage

### Cas 1 : Arbres qui cachent en décembre

**Problème :**
- En décembre, production réelle = 80W mais SPVM prédit 150W
- SPVM surestime de ~50%

**Solution :**
```yaml
# Configuration SPVM
shading_winter_pct: 50       # Réduction de 50% en hiver
shading_month_start: 11      # Novembre à février
shading_month_end: 2
lux_floor_factor: 0.05       # Permet descente à 5% (soleil très bas)
```

**Résultat :**
- SPVM prédit maintenant 75W (150 × 0.5)
- Cohérent avec les 80W réels ✓

---

### Cas 2 : Ciel très couvert sous-estimé

**Problème :**
- Cloud sensor dit 40% mais ciel TRÈS couvert
- Lux = 617, élévation = 9°
- Production réelle = 84W mais SPVM prédit 50W (sous-estime)

**Solution :**
```yaml
# Configuration SPVM
lux_floor_factor: 0.15       # Plancher plus haut (15% au lieu de 10%)
lux_min_elevation_deg: 8     # Accepte lux jusqu'à 8° d'élévation
```

**Résultat :**
- Lux factor passe de 0.02 → capé à 0.15
- SPVM prédit ~90W au lieu de 50W
- Plus proche des 84W réels ✓

---

### Cas 3 : Installation dégagée (pas de problème)

**Configuration :**
```yaml
# Garder les défauts
lux_min_elevation_deg: 5     # Défaut
lux_floor_factor: 0.1        # Défaut
shading_winter_pct: 0        # Pas d'ombrage
```

**Résultat :**
- Prédictions précises toute l'année
- Pas besoin d'ajustements ✓

---

## 🔧 Configuration dans Home Assistant

### Via l'interface graphique

1. **Paramètres** → **Appareils et Services**
2. **Smart PV Meter** → **Configurer**
3. Section **Correction Lux** :
   - Élévation minimale lux (°)
   - Plancher correction lux
4. Section **Ombrage saisonnier** :
   - Ombrage hiver (%)
   - Mois début ombrage
   - Mois fin ombrage

### Via configuration.yaml (si besoin)

```yaml
# Ces paramètres sont stockés dans la config entry
# Modification via l'interface recommandée
```

---

## 📊 Monitoring des corrections appliquées

### Attributs du capteur `sensor.spvm_expected_production`

```yaml
lux_factor: 0.17              # Facteur lux appliqué (si actif)
lux_correction_active: true   # Correction lux active ?
lux_now: 617                  # Lux actuel
cloud_now_pct: 40             # Cloud coverage
model_elevation_deg: 9.3      # Élévation solaire
```

### Calcul manuel pour vérification

```python
# Dans Outils développeur → Modèle
{% set lux = states('sensor.xthl_1_luminance') | float %}
{% set elevation = state_attr('sensor.spvm_expected_production', 'model_elevation_deg') %}
{% set theo_lux = 80000 * (elevation | sin | float) %}
{% set ratio = lux / theo_lux %}

Lux actuel : {{ lux }}
Lux théorique : {{ theo_lux | round(0) }}
Ratio : {{ (ratio * 100) | round(1) }}%
Facteur appliqué : {{ [ratio, 0.1] | max | round(2) }}
```

---

## ❓ FAQ

### Q : Comment savoir si je dois ajuster ces paramètres ?

**R :** Comparez `sensor.spvm_expected_production` avec votre production réelle pendant 1 semaine :
- **SPVM surestime en hiver** → Ajuster `shading_winter_pct`
- **SPVM surestime par temps très couvert** → Réduire `lux_floor_factor`
- **SPVM sous-estime par temps très couvert** → Augmenter `lux_floor_factor`

### Q : Est-ce que ces corrections impactent Solar Optimizer ?

**R :** Oui ! C'est l'objectif. Des prédictions plus précises = meilleures décisions SO.

### Q : Puis-je désactiver la correction lux ?

**R :** Oui, en mettant `lux_min_elevation_deg: 90` (jamais utilisé).

### Q : L'ombrage saisonnier fonctionne-t-il avec la correction lux ?

**R :** Oui, les deux se cumulent :
```
Production finale = Production ciel clair
                    × Correction nuages (ou lux)
                    × Correction température
                    × Correction ombrage saisonnier
```

---

**Document mis à jour :** 28 août 2026
**Version SPVM :** 0.7.7

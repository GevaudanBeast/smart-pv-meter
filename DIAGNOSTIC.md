# 🔍 Diagnostic SPVM - Valeurs à 0W

Si vos capteurs SPVM affichent **0W** ou **"inconnu"**, voici comment diagnostiquer le problème.

## 📊 Comprendre les valeurs

### Production attendue (sensor.spvm_expected_production)
- **0W pendant la nuit** : **Normal** ✅
  - Le soleil est couché (élévation négative)
  - Le modèle solaire calcule correctement 0W

- **0W pendant la journée** : **Problème de configuration** ⚠️
  - Vérifiez vos paramètres solaires
  - Utilisez le script de diagnostic ci-dessous

### Rendement (sensor.spvm_yield_ratio)
- **"inconnu"** : **Normal la nuit** ✅
  - Le rendement ne peut pas être calculé quand production attendue < 1W
  - Valeur = (Production PV réelle / Production attendue) × 100%

### Surplus net (sensor.spvm_surplus_net)
- **0W** : **Normal dans plusieurs cas** ✅
  - Surplus = max(PV - Consommation - Réserve, 0)
  - Si vous consommez toute votre production, c'est normal
  - **Installation bridée en autoconsommation** : Toujours 0W car l'onduleur suit la consommation (voir Cas 4 ci-dessous)
  - **Nouveau (v0.6.3)** : Vérifiez les attributs debug pour comprendre le calcul
  - **Pour Solar Optimizer** : Utilisez `expected_production` si installation bridée (voir README)

---

## 🆕 Attributs de debug (v0.6.3+)

Le capteur `sensor.spvm_surplus_net` expose maintenant des attributs de debug pour diagnostiquer les problèmes :

### Vérifier les valeurs
1. **Outils de développement** → **États** → `sensor.spvm_surplus_net`
2. Regardez ces attributs :

```yaml
debug_pv_w: 966.0           # Production PV après conversion d'unité
debug_house_w: 920.0        # Consommation après conversion d'unité
debug_surplus_virtual: 58.3 # Surplus calculé avant réserve
reserve_w: 150              # Réserve configurée
```

### Diagnostic surplus_net = 0W

#### Cas 1 : Surplus < Réserve
```
debug_surplus_virtual: 58.3W
reserve_w: 150W
→ surplus_net = max(58.3 - 150, 0) = 0W ✅
```
**Solution** : Réduire la réserve ou attendre plus de production

#### Cas 2 : Pas de surplus
```
debug_pv_w: 800W
debug_house_w: 950W
debug_surplus_virtual: -150W (négatif)
→ surplus_net = 0W ✅
```
**Normal** : Vous consommez plus que vous ne produisez

#### Cas 3 : Problème d'unités
```
debug_pv_w: 2.6W   ← ⚠️ Très faible !
debug_house_w: 2.6W
```
**Problème** : Vos capteurs sont probablement en kW, pas en W
**Solution** : Configurez les unités par capteur (voir ci-dessous)

#### Cas 4 : Installation bridée en autoconsommation ⚡
```
debug_pv_w: 800W              # Production bridée actuelle
debug_house_w: 800W           # Consommation actuelle
debug_surplus_virtual: 0W
→ surplus_net = 0W ✅ NORMAL
```

**Explication** : Votre installation photovoltaïque est configurée pour **suivre la consommation** (mode autoconsommation bridé), couramment avec :
- Enphase micro-onduleurs
- Certaines configurations d'onduleurs hybrides
- Installations sans droit d'injection réseau

**C'est normal !** `surplus_net` montre le surplus **actuellement exporté**, qui est 0W car votre onduleur limite la production pour suivre la consommation.

**Pour Solar Optimizer** : Utilisez `sensor.spvm_expected_production` au lieu de `surplus_net` :
- `expected_production` indique le **potentiel théorique** disponible (ex: 3000W)
- Votre onduleur augmentera automatiquement la production quand Solar Optimizer activera des appareils
- Voir [README.md - Integration with Solar Optimizer](README.md#integration-with-solar-optimizer) pour la configuration complète

**Exemple concret** :
```
Situation actuelle:
  - Production PV: 800W (bridée)
  - Consommation: 800W
  - surplus_net: 0W ✅

Expected production: 3000W (conditions ensoleillées)

Solar Optimizer active 2kW de charge:
  → Onduleur augmente automatiquement à 2800W
  → Consommation totale: 2800W
  → Tout en solaire, 0 import réseau ! ☀️
```

---

## ⚙️ Configuration des unités (v0.6.3+)

### Problème : Capteurs en unités différentes

Si vous avez des capteurs de différents fabricants :
- **Enphase Envoy** : Envoie souvent en **kW**
- **Shelly** : Envoie en **W**
- **Zendure** : Envoie en **W**

### Solution : Unités par capteur

**Paramètres** → **Appareils et services** → **Smart PV Meter** → **CONFIGURER**

```
Capteur production PV
└─ Unité : kW  ← Pour Enphase

Capteur consommation maison
└─ Unité : kW  ← Pour Enphase

Capteur réseau
└─ Unité : W   ← Pour Shelly

Capteur batterie
└─ Unité : W   ← Pour Zendure
```

Après modification :
1. Sauvegardez
2. **⋮ (trois points)** → **Recharger**
3. Vérifiez que `debug_pv_w` affiche maintenant des valeurs cohérentes (centaines ou milliers de watts)

---

## 🔧 Script de diagnostic

**Nouveau (v0.6.3)** : Le script de diagnostic est maintenant inclus dans l'intégration !

### Étape 1 : Utilisez le script intégré

Le script est disponible dans `/config/custom_components/spvm/diagnostic.py`

Ou créez votre propre fichier `/config/spvm_diagnostic.py` avec ce contenu :

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/config/custom_components/spvm')

from datetime import datetime, timezone
from solar_model import SolarInputs, compute as solar_compute

# 📝 MODIFIEZ CES VALEURS AVEC VOTRE CONFIGURATION
now_utc = datetime.now(timezone.utc)

inputs = SolarInputs(
    dt_utc=now_utc,
    lat_deg=48.8566,      # ⬅️ VOTRE LATITUDE (degrés décimaux)
    lon_deg=2.3522,       # ⬅️ VOTRE LONGITUDE (degrés décimaux)
    altitude_m=35.0,      # ⬅️ VOTRE ALTITUDE (mètres)
    panel_tilt_deg=30.0,  # ⬅️ INCLINAISON PANNEAUX (0=horizontal, 90=vertical)
    panel_azimuth_deg=180.0,  # ⬅️ ORIENTATION (0=Nord, 90=Est, 180=Sud, 270=Ouest)
    panel_peak_w=2800.0,  # ⬅️ PUISSANCE CRÊTE (Watts)
    system_efficiency=0.85,  # ⬅️ EFFICACITÉ (0.75-0.95 typique)
    cloud_pct=None,
    temp_c=None,
)

print(f"=== SPVM Diagnostic ===")
print(f"Date/Heure UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nConfiguration:")
print(f"  GPS: {inputs.lat_deg}°, {inputs.lon_deg}° (alt: {inputs.altitude_m}m)")
print(f"  Panneaux: {inputs.panel_peak_w}W @ {inputs.panel_tilt_deg}° / {inputs.panel_azimuth_deg}°")

model = solar_compute(inputs)

print(f"\nPosition du soleil:")
print(f"  Élévation: {model.elevation_deg:.2f}° ({'☀️ JOUR' if model.elevation_deg > 0 else '🌙 NUIT'})")
print(f"  Azimut: {model.azimuth_deg:.2f}°")

print(f"\nProduction:")
print(f"  Attendue: {model.expected_corrected_w:.1f}W")

if model.elevation_deg <= 0:
    print(f"\n✅ Le soleil est couché → 0W est NORMAL")
elif model.expected_corrected_w < 10:
    print(f"\n⚠️  Production très faible, vérifiez la configuration")
else:
    print(f"\n✅ Le modèle fonctionne correctement")
```

### Étape 2 : Exécutez le script

Depuis Home Assistant (terminal SSH ou File Editor) :

```bash
# Avec le script intégré
python3 /config/custom_components/spvm/diagnostic.py

# Ou avec votre propre script
cd /config
python3 spvm_diagnostic.py
```

### Étape 3 : Interprétez les résultats

#### ✅ **NORMAL** : Soleil couché
```
Position du soleil:
  Élévation: -12.34° (🌙 NUIT)
Production:
  Attendue: 0.0W

✅ Le soleil est couché → 0W est NORMAL
```

#### ⚠️ **PROBLÈME** : Soleil levé mais 0W
```
Position du soleil:
  Élévation: 45.67° (☀️ JOUR)
Production:
  Attendue: 0.0W

⚠️  Production très faible, vérifiez la configuration
```

**→ Vérifiez vos paramètres dans Home Assistant** :
1. Allez dans **Paramètres** → **Appareils et services**
2. Cliquez sur **Smart PV Meter** → **Configurer**
3. Vérifiez :
   - ✅ Puissance crête des panneaux (en Watts, pas kW !)
   - ✅ Inclinaison (30° typique pour la France)
   - ✅ Orientation (180° pour Sud)
   - ✅ Coordonnées GPS correctes
   - ✅ Efficacité système (0.85 recommandé)

---

## 📍 Comment trouver vos coordonnées GPS

### Méthode 1 : Google Maps
1. Allez sur [Google Maps](https://maps.google.com)
2. Clic droit sur votre toit
3. Cliquez sur les coordonnées pour les copier
4. Format : `48.8566, 2.3522` (latitude, longitude)

### Méthode 2 : Home Assistant
Vos coordonnées sont dans **Configuration** → **Général** → **Localisation**

---

## 🔍 Attributs de diagnostic

### Attributs de expected_production

1. **Outils de développement** → **États** → `sensor.spvm_expected_production`
2. Regardez les **Attributs** :

```yaml
model_elevation_deg: 45.67  # Élévation du soleil
model_azimuth_deg: 180.23   # Azimut du soleil
ghi_clear_wm2: 823.4        # Irradiance globale (W/m²)
poa_clear_wm2: 956.2        # Irradiance sur les panneaux (W/m²)
site:
  lat: 48.8566
  lon: 2.3522
  alt_m: 35.0
panel:
  tilt_deg: 30.0
  azimuth_deg: 180.0
  peak_w: 2800.0
system_efficiency: 0.85
```

### Attributs de surplus_net (v0.6.3+)

1. **Outils de développement** → **États** → `sensor.spvm_surplus_net`
2. Regardez les **Attributs de debug** :

```yaml
debug_pv_w: 966.0           # Production PV en watts (après conversion)
debug_house_w: 920.0        # Consommation en watts (après conversion)
debug_surplus_virtual: 58.3 # Surplus calculé avant réserve
reserve_w: 150              # Réserve configurée
grid_now: -58.3            # Puissance réseau (négatif = export)
```

### ✅ Vérifications rapides

| Attribut | Valeur attendue | Si incorrect |
|----------|----------------|--------------|
| `model_elevation_deg` | > 0 pendant la journée | Le soleil est couché → 0W normal |
| `ghi_clear_wm2` | 100-1200 W/m² | Si 0 → vérifier latitude/longitude |
| `poa_clear_wm2` | > ghi si bien orienté | Si < ghi → vérifier orientation panneaux |
| `panel.peak_w` | Votre puissance crête | Si incorrect → reconfigurer |
| `debug_pv_w` | Centaines/milliers de watts | Si < 10W → problème d'unités (kW vs W) |
| `debug_house_w` | Centaines/milliers de watts | Si < 10W → problème d'unités (kW vs W) |

---

## 🆘 Support

Si après ces vérifications le problème persiste :

1. **Vérifiez les logs** Home Assistant : **Paramètres** → **Système** → **Journaux**
2. **Créez une issue** GitHub avec :
   - Votre configuration (masquez GPS si sensible)
   - Les attributs du capteur
   - L'heure locale et la sortie du script de diagnostic

---

## 📚 Paramètres typiques France

| Région | Latitude | Longitude | Inclinaison | Orientation |
|--------|----------|-----------|-------------|-------------|
| Paris | 48.86° | 2.35° | 30° | 180° (Sud) |
| Lyon | 45.75° | 4.85° | 32° | 180° (Sud) |
| Marseille | 43.30° | 5.37° | 35° | 180° (Sud) |
| Bordeaux | 44.84° | -0.58° | 34° | 180° (Sud) |
| Lille | 50.63° | 3.06° | 28° | 180° (Sud) |

**Règle générale** :
- **Inclinaison optimale** ≈ Latitude - 15° (pour maximiser production annuelle)
- **Orientation optimale** = 180° (plein Sud)
- **Efficacité système** = 0.80-0.90 (onduleur + câbles + poussière)

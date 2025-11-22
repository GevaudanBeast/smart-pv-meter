# Configuration recommandée pour votre installation

## 📋 Accès à la configuration

1. Home Assistant → **Paramètres**
2. **Appareils et Services**
3. Cherchez **Smart PV Meter**
4. Cliquez sur **Configurer** (⚙️)

## 🎛️ Nouveaux paramètres v0.6.9

Vous verrez maintenant 5 nouveaux champs dans l'interface :

### Correction Lux (pour temps nuageux épais)

**Lux : élévation min (°)**
```
Valeur recommandée : 8
```
Explique à SPVM de ne pas utiliser le capteur lux en dessous de 8° d'élévation solaire (car vos arbres rendent les lectures peu fiables).

**Lux : plancher (0.01-0.5)**
```
Valeur recommandée : 0.03
```
Permet à SPVM de descendre jusqu'à 3% de la production théorique (au lieu de 10% par défaut) par temps très couvert avec arbres.

### Ombrage saisonnier (pour vos arbres en hiver)

**Ombrage : réduction (%)**
```
Valeur recommandée : 35
```
Applique une réduction de 35% des prédictions pendant la période hivernale à cause de vos arbres.

**Ombrage : début (mois)**
```
Valeur recommandée : 11
```
Novembre - début de la période où les arbres bloquent significativement le soleil.

**Ombrage : fin (mois)**
```
Valeur recommandée : 2
```
Février - fin de la période d'ombrage important.

## 🔍 Vérification après configuration

Une fois configuré, vérifiez dans **Outils de développement** → **États** → `sensor.spvm_expected_production` :

Les attributs devraient montrer :
```yaml
lux_factor: 0.03              # Plancher actif en conditions très nuageuses
shading_factor: 0.65          # 35% de réduction appliquée (Nov-Fév)
lux_min_elevation_deg: 8.0    # Votre seuil personnalisé
```

## 📊 Calibration fine (optionnel)

Après quelques jours d'observation :

- **Si SPVM surestime encore** → Augmenter `Ombrage : réduction (%)` à 40-45%
- **Si SPVM sous-estime** → Réduire `Ombrage : réduction (%)` à 25-30%
- **Si temps très nuageux sous-estimé** → Réduire `Lux : plancher` à 0.02

## ⚠️ Important

Ces paramètres sont spécifiques à **votre installation** avec arbres bloquant en hiver. Les valeurs par défaut (5°, 0.1, 0%, 11, 2) conviennent aux installations sans obstacle.

---

**Configuration créée pour votre cas spécifique** : Arbres cachant le soleil en hiver (décembre particulièrement touché)

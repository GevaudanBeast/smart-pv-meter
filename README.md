# Guide de déploiement SPVM v0.5.8

## 🔥 Correctif critique : Erreur 500 du Config Flow

Cette version corrige l'erreur **500 Internal Server Error** qui empêchait la configuration de l'intégration SPVM dans Home Assistant.

---

## 📋 Prérequis

- Home Assistant 2024.1 ou supérieur
- Accès au répertoire `/config/custom_components/`
- Droits d'écriture sur les fichiers de configuration

---

## 🚀 Installation / Mise à jour

### Option 1 : Installation manuelle (recommandée pour ce correctif)

1. **Arrêter Home Assistant** (optionnel mais recommandé)
   ```bash
   ha core stop
   ```

2. **Naviguer vers le répertoire des custom components**
   ```bash
   cd /config/custom_components/spvm/
   ```

3. **Sauvegarder l'ancienne version** (au cas où)
   ```bash
   cp -r ../spvm ../spvm.backup.0.5.5
   ```

4. **Télécharger les fichiers corrigés depuis GitHub**
   ```bash
   # Si git est disponible
   git pull origin main
   
   # OU télécharger manuellement les fichiers suivants et les remplacer :
   # - config_flow.py
   # - const.py
   # - const_old.py
   # - en.json
   # - __init__.py
   # - manifest.json
   ```

5. **Vérifier la version**
   ```bash
   cat manifest.json | grep version
   # Doit afficher : "version": "0.5.8"
   ```

6. **Valider l'encodage** (optionnel)
   ```bash
   python3 validate_encoding.py
   # Doit afficher : ✅ Aucun problème d'encodage détecté!
   ```

7. **Redémarrer Home Assistant**
   ```bash
   ha core restart
   ```

### Option 2 : Via HACS (dès que la version sera publiée)

1. Ouvrir **HACS** dans Home Assistant
2. Aller dans **Intégrations**
3. Rechercher **SPVM - Smart PV Meter**
4. Cliquer sur **Mettre à jour**
5. Redémarrer Home Assistant

---

## ✅ Vérification post-installation

### 1. Vérifier les logs

Accéder aux logs Home Assistant :
```
Paramètres → Système → Journaux
```

Rechercher `spvm` - vous devriez voir :
```
2025-11-11 18:00:00.123 INFO (SyncWorker_1) [homeassistant.loader] Loaded spvm from custom_components.spvm
2025-11-11 18:00:00.456 INFO (MainThread) [custom_components.spvm] SPVM async_setup_entry (version=0.5.8, entry_id=...)
```

**Aucune erreur ne devrait apparaître.**

### 2. Tester l'interface de configuration

1. Aller dans **Paramètres** → **Appareils et services**
2. Chercher **SPVM - Smart PV Meter**
3. Cliquer sur **Configurer** (ou **Ajouter une intégration** si nouvelle installation)

**L'interface devrait s'afficher correctement sans erreur 500.**

### 3. Vérifier les entités créées

Les entités suivantes devraient être disponibles :

```
✅ sensor.spvm_grid_power_auto
✅ sensor.spvm_surplus_virtual
✅ sensor.spvm_surplus_net_raw
✅ sensor.spvm_surplus_net          ← À utiliser pour Solar Optimizer
✅ sensor.spvm_pv_effective_cap_now_w
✅ sensor.spvm_expected_similar
✅ sensor.spvm_expected_debug       ← Si debug activé
```

### 4. Vérifier le fonctionnement

Dans **Outils de développement** → **États**, chercher `sensor.spvm_surplus_net` :

```yaml
state: 1234.5  # Exemple de valeur en watts
attributes:
  source: "surplus_virtual - reserve_w (capped)"
  reserve_w: 150
  cap_max_w: 3000
  cap_limit_w: 3000
  smoothed: true
  window_s: 45
  note: "Zendure reserve applied; System cap applied; 3 kW hard limit applied"
```

---

## 🔧 Configuration recommandée

### Paramètres de base

```yaml
Configuration minimale :
- PV sensor: sensor.inverter_power
- House sensor: sensor.house_consumption
- Reserve W: 150  # Pour Zendure
- Cap max W: 3000  # Limite de l'installation
```

### Paramètres k-NN (prédiction)

Pour une prédiction optimale, configurer :

```yaml
Capteurs météo (optionnels mais recommandés) :
- Lux sensor: sensor.outdoor_lux
- Temperature sensor: sensor.outdoor_temp
- Humidity sensor: sensor.outdoor_humidity

Paramètres k-NN :
- k: 5 (nombre de voisins)
- Window min: 30 minutes
- Window max: 90 minutes
- Weight lux: 0.4
- Weight temp: 0.2
- Weight hum: 0.1
- Weight elevation: 0.3
```

### Intégration avec Solar Optimizer

Dans votre configuration Solar Optimizer, utiliser :

```yaml
surplus_sensor: sensor.spvm_surplus_net
```

**Important** : `sensor.spvm_surplus_net` inclut déjà :
- ✅ La réserve Zendure de 150W
- ✅ Le cap de 3kW
- ✅ Le lissage temporel

---

## 🐛 Dépannage

### Erreur "Config flow could not be loaded"

**Solution** : Vérifier que tous les fichiers sont bien encodés en UTF-8.

```bash
# Exécuter le script de validation
python3 validate_encoding.py /config/custom_components/spvm/

# Résultat attendu :
# ✅ Aucun problème d'encodage détecté!
```

### Les entités n'apparaissent pas

1. Vérifier que l'intégration est bien chargée :
   ```
   Paramètres → Appareils et services → SPVM
   ```

2. Recharger l'intégration :
   ```
   Dans SPVM → ⋮ → Recharger
   ```

3. Si ça ne fonctionne pas, supprimer et reconfigurer :
   ```
   SPVM → ⋮ → Supprimer l'intégration
   Puis : Ajouter une intégration → SPVM
   ```

### Valeurs incorrectes dans sensor.spvm_surplus_net

Vérifier que :
- Les capteurs sources (PV, house, grid, battery) sont bien configurés
- Les unités sont correctes (W ou kW)
- Le paramètre `reserve_w` est bien à 150W pour Zendure
- Le paramètre `cap_max_w` ne dépasse pas 3000W

### Prédiction k-NN non fonctionnelle

1. Vérifier qu'il y a des données historiques :
   ```yaml
   sensor.spvm_expected_similar:
     samples_total: 0  ← Problème !
   ```

2. Attendre quelques jours pour accumuler les données

3. Vérifier que les capteurs météo sont bien configurés

4. Forcer un recalcul :
   ```yaml
   service: spvm.recompute_expected_now
   ```

---

## 📞 Support

### Problèmes connus de cette version

✅ Erreur 500 du config flow → **CORRIGÉ**

### Rapporter un bug

Si vous rencontrez un problème :

1. **Activer le debug** dans `configuration.yaml` :
   ```yaml
   logger:
     default: info
     logs:
       custom_components.spvm: debug
   ```

2. **Collecter les diagnostics** :
   ```
   Paramètres → Appareils et services → SPVM
   → ⋮ → Télécharger les diagnostics
   ```

3. **Créer une issue sur GitHub** :
   https://github.com/GevaudanBeast/smart-pv-meter/issues

   Inclure :
   - Version de Home Assistant
   - Version de SPVM
   - Logs pertinents
   - Fichier de diagnostics

---

## 🎯 Prochaines étapes

Après validation du fonctionnement :

1. ✅ Intégrer avec Solar Optimizer
2. ✅ Surveiller les valeurs pendant 24-48h
3. ✅ Ajuster les paramètres si nécessaire
4. ✅ Activer les capteurs météo pour améliorer les prédictions

---

## 📚 Documentation complète

- **GitHub** : https://github.com/GevaudanBeast/smart-pv-meter
- **Wiki** : https://github.com/GevaudanBeast/smart-pv-meter/wiki
- **Issues** : https://github.com/GevaudanBeast/smart-pv-meter/issues

---

**Version** : 0.5.8  
**Date de sortie** : 11 novembre 2025  
**Urgence** : 🔴 CRITIQUE  
**Auteur** : GevaudanBeast

# SPVM Changelog - Version 0.5.8

## Corrections critiques (Bug fixes)

### Erreur 500 - Config Flow Fix
**Problème**: L'interface de configuration retournait une erreur 500 empêchant la configuration de l'intégration.

**Cause racine**: Problèmes d'encodage UTF-8 des caractères spéciaux dans plusieurs fichiers Python :
- `Â°C` et `Â°F` mal encodés dans les sélecteurs d'unités de température
- Caractères spéciaux (`→`, `•`) mal encodés dans les messages et commentaires

**Fichiers corrigés**:
1. **config_flow.py**
   - Ligne 282-283: Correction encodage `°C` et `°F` dans `SelectOptionDict`
   - Lignes 301-306: Correction caractères bullet points `•`

2. **const.py**
   - Ligne 49: `DEF_UNIT_TEMP` corrigé de `"Â°C"` vers `"°C"`
   - Lignes 92-93: `UNIT_C` et `UNIT_F` corrigés

3. **const_old.py** (pour cohérence)
   - Ligne 49: Correction similaire
   - Lignes 92-93: Correction similaire

4. **en.json**
   - Ligne 20: Correction de la description d'unité de température

5. **__init__.py**
   - Ligne 72: Message de log nettoyé (caractère flèche)

6. **manifest.json**
   - Version mise à jour de 0.5.5 → 0.5.8

## Impact utilisateur

### Avant la correction
```
Erreur: Le flux de configuration n'a pas pu être chargé: 500 Internal Server Error
Server got itself in trouble
```

### Après la correction
✅ L'interface de configuration charge correctement  
✅ Tous les sélecteurs d'options fonctionnent  
✅ Les unités de température s'affichent correctement (`°C` / `°F`)

## Instructions de mise à jour

### Pour Home Assistant

1. **Arrêter Home Assistant** (ou au moins l'intégration SPVM)

2. **Remplacer les fichiers** dans `/config/custom_components/spvm/`:
   - `config_flow.py`
   - `const.py`
   - `const_old.py`
   - `en.json`
   - `__init__.py`
   - `manifest.json`

3. **Redémarrer Home Assistant**

4. **Reconfigurer l'intégration** :
   - Aller dans Paramètres → Appareils et services
   - Cliquer sur "SPVM - Smart PV Meter"
   - Cliquer sur "Configurer"
   - L'interface devrait maintenant fonctionner correctement

### Via HACS

Si vous utilisez HACS, attendez que la version 0.5.8 soit publiée sur GitHub, puis :
1. HACS → Intégrations
2. SPVM - Smart PV Meter → Mettre à jour
3. Redémarrer Home Assistant

## Validation

Pour vérifier que la correction fonctionne :

```bash
# Vérifier l'encodage des fichiers
grep -r "Â°" /config/custom_components/spvm/
# Résultat attendu : aucune correspondance

# Vérifier la version
cat /config/custom_components/spvm/manifest.json | grep version
# Résultat attendu : "version": "0.5.8"
```

## Notes techniques

### Pourquoi ce problème ?

Les fichiers Python ont été créés ou édités avec un éditeur qui a mal interprété l'encodage UTF-8, transformant les caractères spéciaux en séquences multi-bytes incorrectes :
- `°` (U+00B0) → `Â°` (mauvaise interprétation ISO-8859-1)
- `→` (U+2192) → `Ã¢â€ â€™` (corruption multi-byte)

### Solution appliquée

Remplacement de tous les caractères mal encodés par leurs équivalents UTF-8 corrects, en utilisant un script Python pour garantir la cohérence.

## Compatibilité

- Home Assistant 2024.1+
- Python 3.11+
- Pas de changement dans la structure des données
- Pas de migration nécessaire depuis 0.5.x

## Prochaines étapes

Version 0.5.9 (planifiée) :
- [ ] Ajout de tests unitaires pour éviter les régressions d'encodage
- [ ] Validation automatique de l'encodage UTF-8 dans le pipeline CI/CD
- [ ] Documentation améliorée sur les standards d'encodage

---

**Date de sortie**: 11 novembre 2025  
**Urgence**: 🔴 CRITIQUE - Bloque la configuration de l'intégration  
**Auteur**: GevaudanBeast

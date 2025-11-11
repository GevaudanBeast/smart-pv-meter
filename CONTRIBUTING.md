# Contributing to Smart PV Meter

Merci de votre intérêt pour contribuer à Smart PV Meter ! 🎉

## 🐛 Signaler un bug

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/GevaudanBeast/smart-pv-meter/issues)
2. Créez une nouvelle issue avec :
   - **Version de Home Assistant**
   - **Version de SPVM** (voir manifest.json)
   - **Logs** (avec debug activé)
   - **Diagnostics** (téléchargés depuis l'intégration)
   - **Description détaillée** du problème
   - **Étapes pour reproduire**

## 💡 Proposer une fonctionnalité

1. Ouvrez une issue avec le tag `enhancement`
2. Décrivez :
   - Le problème que ça résout
   - Comment ça devrait fonctionner
   - Des exemples d'utilisation

## 🔧 Soumettre du code

### Prérequis

- Python 3.11+
- Home Assistant Core 2024.1+
- Git

### Setup développement

```bash
# Cloner le repo
git clone https://github.com/GevaudanBeast/smart-pv-meter.git
cd smart-pv-meter

# Créer une branche
git checkout -b feature/ma-nouvelle-fonctionnalite
```

### Standards de code

- **Style** : Suivre PEP 8
- **Imports** : Organisés et triés
- **Docstrings** : Pour toutes les fonctions publiques
- **Type hints** : Partout où c'est pertinent
- **Logging** : Utiliser `_LOGGER` avec niveaux appropriés

### Tests

Avant de soumettre :

1. **Tester localement** dans Home Assistant
2. **Vérifier les logs** (pas d'erreurs)
3. **Tester les cas limites** (capteurs indisponibles, etc.)

### Pull Request

1. **Commitez** vos changements
   ```bash
   git commit -m "feat: Description courte de la fonctionnalité"
   ```

2. **Poussez** votre branche
   ```bash
   git push origin feature/ma-nouvelle-fonctionnalite
   ```

3. **Créez une Pull Request** sur GitHub avec :
   - Description claire des changements
   - Pourquoi c'est nécessaire
   - Comment ça a été testé
   - Screenshots si pertinent

### Convention de commits

Utilisez [Conventional Commits](https://www.conventionalcommits.org/) :

- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation uniquement
- `style:` Formatage, espaces, etc.
- `refactor:` Refactoring sans changement de comportement
- `perf:` Amélioration de performance
- `test:` Ajout ou correction de tests
- `chore:` Maintenance (dépendances, build, etc.)

Exemples :
```
feat: add night filtering based on lux sensor
fix: prevent timeout on historical data fetch
docs: update README with new configuration options
perf: reduce data points by 90% with seasonal windows
```

## 🌐 Traductions

Les traductions sont dans `strings.json`, `en.json`, et `fr.json`.

Pour ajouter une langue :

1. Copier `en.json` vers `XX.json` (code langue ISO)
2. Traduire toutes les chaînes
3. Soumettre une PR

## 📝 Documentation

La documentation doit être mise à jour pour :

- Nouvelles fonctionnalités
- Changements de configuration
- Nouvelles entités créées
- Changements de comportement

Fichiers à mettre à jour :
- `README.md` - Vue d'ensemble
- `CHANGELOG.md` - Liste des changements
- Docstrings dans le code

## 🔍 Review process

1. **Code review** par les mainteneurs
2. **Tests** automatiques (si configurés)
3. **Tests manuels** sur Home Assistant
4. **Merge** une fois approuvé

## ❓ Questions

Pour toute question :
- Ouvrez une [Discussion](https://github.com/GevaudanBeast/smart-pv-meter/discussions)
- Contactez @GevaudanBeast

## 📄 Licence

En contribuant, vous acceptez que vos contributions soient sous licence MIT.

---

Merci de contribuer à rendre Smart PV Meter meilleur ! 🙏

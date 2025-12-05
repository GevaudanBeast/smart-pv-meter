# Guide: Soumettre SPVM au Home Assistant Brands Repository

## ✅ Assets Préparés

Les fichiers suivants ont été créés dans `/home/user/smart-pv-meter/brand_assets/`:

- ✅ `icon.png` - 256×256px, 73KB, interlaced, RGBA
- ✅ `icon@2x.png` - 512×512px, 247KB, interlaced, RGBA

Tous les fichiers respectent les exigences du brands repository:
- Format PNG avec transparence
- Optimisés avec optipng niveau 7
- Format interlaced (progressive)
- Dimensions conformes
- Métadonnées nettoyées

## 📋 Étapes pour Soumettre le PR

### 1. Cloner le Repository Brands

```bash
# Cloner le repo officiel
git clone https://github.com/home-assistant/brands.git
cd brands

# Créer une nouvelle branche
git checkout -b add-spvm-brand-assets
```

### 2. Créer la Structure de Dossiers

```bash
# Créer le dossier pour SPVM
mkdir -p custom_integrations/spvm

# Copier les assets préparés
cp /home/user/smart-pv-meter/brand_assets/icon.png custom_integrations/spvm/
cp /home/user/smart-pv-meter/brand_assets/icon@2x.png custom_integrations/spvm/
```

### 3. Vérifier la Structure

```bash
# Vérifier que tout est en place
tree custom_integrations/spvm/
# Devrait afficher:
# custom_integrations/spvm/
# ├── icon.png
# └── icon@2x.png

# Vérifier les propriétés des fichiers
file custom_integrations/spvm/*.png
# Devrait afficher "interlaced" pour chaque fichier
```

### 4. Créer le Commit

```bash
git add custom_integrations/spvm/
git commit -m "Add brand assets for Smart PV Meter (spvm) custom integration"
```

### 5. Push et Créer le PR

```bash
# Push vers votre fork (créez un fork d'abord sur GitHub)
git remote add myfork https://github.com/VOTRE-USERNAME/brands.git
git push -u myfork add-spvm-brand-assets
```

Ensuite, allez sur https://github.com/home-assistant/brands et créez un Pull Request.

## 📝 Template du Pull Request

**Titre:**
```
Add brand assets for Smart PV Meter (spvm)
```

**Description:**
```markdown
## Summary
This PR adds brand assets for the **Smart PV Meter** custom integration.

## Assets included
- ✅ `icon.png` (256×256px, interlaced, optimized)
- ✅ `icon@2x.png` (512×512px, interlaced, optimized)

## Integration Details
- **Domain**: `spvm`
- **Name**: Smart PV Meter
- **Type**: Custom Integration
- **Repository**: https://github.com/GevaudanBeast/smart-pv-meter
- **Description**: Physical solar production model for Home Assistant based on astronomical calculations

## Technical Details
All images meet the requirements:
- ✅ PNG format with RGBA transparency
- ✅ Properly compressed and optimized (lossless) with optipng -o7
- ✅ Interlaced/progressive format enabled
- ✅ Empty space and borders trimmed
- ✅ Domain folder name matches manifest.json
- ✅ File dimensions meet specifications:
  - icon.png: 256×256 pixels
  - icon@2x.png: 512×512 pixels
- ✅ Metadata stripped for web optimization

## Verification Commands
```bash
# Check interlacing
file custom_integrations/spvm/*.png

# Output:
# custom_integrations/spvm/icon.png:    PNG image data, 256 x 256, 8-bit/color RGBA, interlaced
# custom_integrations/spvm/icon@2x.png: PNG image data, 512 x 512, 8-bit/color RGBA, interlaced
```

## Checklist
- [x] PNG files are properly compressed and optimized (lossless)
- [x] Images are interlaced/progressive format
- [x] Images have transparency
- [x] Empty space and borders are trimmed
- [x] Domain folder name matches manifest.json (`spvm`)
- [x] File dimensions meet requirements
- [x] Standard and @2x versions provided
- [x] No symlinks used
- [x] Does not use Home Assistant branded images
```

## ⚠️ Points d'Attention

1. **Domain exact**: Le dossier DOIT s'appeler `spvm` (pas `smart-pv-meter`, pas `smart_pv_meter`)
2. **Interlaced obligatoire**: Le CI vérifie que les PNG sont interlacés
3. **Optimisation**: Les fichiers doivent être optimisés (nous avons utilisé optipng -o7)
4. **Pas de logos**: Nous ne soumettons que les icônes (logo optionnel, et notre logo est identique à l'icône)
5. **CI checks**: Attendez que tous les checks passent au vert avant de demander une review

## 🔍 Vérification CI

Après avoir créé le PR, le CI va vérifier:

- ✅ Structure des dossiers correcte
- ✅ Nommage des fichiers conforme
- ✅ Dimensions des images correctes
- ✅ Format PNG valide
- ✅ Optimisation des fichiers
- ✅ Interlacing activé

Si le CI échoue:
1. Lisez attentivement les messages d'erreur
2. Corrigez les problèmes localement
3. Force push sur votre branche: `git push -f myfork add-spvm-brand-assets`

## 📊 Comparaison avec la Tentative Précédente

### Avant (PR #8442 - Fermé):
- ❌ Fichiers @2x manquants
- ❌ icon.png était 512×512 au lieu de 256×256
- ❌ Non-interlaced
- ❌ Possiblement non-optimisé
- ❌ CI checks échoués

### Maintenant:
- ✅ Fichiers @2x inclus
- ✅ icon.png correctement dimensionné (256×256)
- ✅ Interlaced avec optipng
- ✅ Optimisé (optipng -o7)
- ✅ Toutes les exigences respectées

## 🎯 Résultat Attendu

Une fois le PR mergé, votre intégration SPVM aura:
- Un icône officiel dans l'interface Home Assistant
- Une meilleure visibilité dans HACS et le catalogue d'intégrations
- Un aspect professionnel cohérent avec les autres intégrations

## 📞 Support

Si le PR est rejeté ou nécessite des modifications:
1. Lisez attentivement les commentaires du reviewer
2. Apportez les corrections nécessaires
3. Re-testez localement avec `file` et `optipng`
4. Force push les corrections

Bonne chance avec votre PR! 🚀

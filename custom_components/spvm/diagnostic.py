#!/usr/bin/env python3
"""Script de diagnostic pour SPVM - à exécuter depuis Home Assistant"""

import sys
sys.path.insert(0, '/config/custom_components/spvm')

from datetime import datetime, timezone
from solar_model import SolarInputs, compute as solar_compute

# Pour tester avec les valeurs réelles de Home Assistant (optionnel)
try:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType
    HA_AVAILABLE = True
except ImportError:
    HA_AVAILABLE = False

# Exemple avec les paramètres par défaut - MODIFIEZ AVEC VOS VALEURS
now_utc = datetime.now(timezone.utc)

inputs = SolarInputs(
    dt_utc=now_utc,
    lat_deg=48.8566,  # Paris par défaut - MODIFIER
    lon_deg=2.3522,   # Paris par défaut - MODIFIER
    altitude_m=35.0,  # Paris par défaut - MODIFIER
    panel_tilt_deg=30.0,  # Inclinaison panneaux - MODIFIER
    panel_azimuth_deg=180.0,  # Sud - MODIFIER
    panel_peak_w=2800.0,  # Puissance crête - MODIFIER
    system_efficiency=0.85,  # Efficacité - MODIFIER
    cloud_pct=None,  # Pas de capteur nuage
    temp_c=None,  # Pas de capteur température
)

print(f"=== SPVM Diagnostic ===")
print(f"Date/Heure UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Heure locale: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nConfiguration:")
print(f"  Latitude: {inputs.lat_deg}°")
print(f"  Longitude: {inputs.lon_deg}°")
print(f"  Altitude: {inputs.altitude_m}m")
print(f"  Panneaux:")
print(f"    - Puissance crête: {inputs.panel_peak_w}W")
print(f"    - Inclinaison: {inputs.panel_tilt_deg}°")
print(f"    - Orientation: {inputs.panel_azimuth_deg}° (0=Nord, 180=Sud)")
print(f"  Efficacité système: {inputs.system_efficiency}")

print(f"\n=== Calcul du modèle solaire ===")
model = solar_compute(inputs)

print(f"\nPosition du soleil:")
print(f"  Élévation: {model.elevation_deg:.2f}° ({'JOUR' if model.elevation_deg > 0 else 'NUIT'})")
print(f"  Azimut: {model.azimuth_deg:.2f}°")
print(f"  Déclinaison: {model.declination_deg:.2f}°")
print(f"  Angle d'incidence: {model.incidence_deg:.2f}°")

print(f"\nIrradiance:")
print(f"  GHI clear-sky: {model.ghi_clear_wm2:.1f} W/m²")
print(f"  POA clear-sky: {model.poa_clear_wm2:.1f} W/m²")

print(f"\nProduction attendue:")
print(f"  Clear-sky (sans nuages/temp): {model.expected_clear_w:.1f}W")
print(f"  Corrigée (avec cloud/temp): {model.expected_corrected_w:.1f}W")

if model.elevation_deg <= 0:
    print(f"\n⚠️  Le soleil est couché (élévation négative)")
    print(f"   C'est normal que la production soit à 0W")
elif model.expected_corrected_w < 10:
    print(f"\n⚠️  Production très faible")
    print(f"   Vérifiez:")
    print(f"   - L'orientation des panneaux (azimut)")
    print(f"   - L'inclinaison des panneaux")
    print(f"   - La puissance crête configurée")
else:
    print(f"\n✅ Le modèle solaire fonctionne correctement")

print(f"\n=== Instructions ===")
print(f"Modifiez les valeurs au début du script avec votre configuration:")
print(f"  - Coordonnées GPS de votre installation")
print(f"  - Inclinaison et orientation de vos panneaux")
print(f"  - Puissance crête de votre installation")

# ==============================================================================
# SECTION DIAGNOSTIC SURPLUS_NET
# ==============================================================================
print(f"\n{'='*70}")
print(f"=== DIAGNOSTIC SURPLUS_NET ===")
print(f"{'='*70}")
print(f"\nSi sensor.spvm_surplus_net affiche 0W alors que vous avez de la production,")
print(f"renseignez vos valeurs actuelles ci-dessous pour simuler le calcul:\n")

# RENSEIGNEZ VOS VALEURS ICI (en Watts)
# ----------------------------------------------------------------------------
PV_CURRENT_W = None        # Production PV actuelle (ex: 1800.0)
HOUSE_CURRENT_W = None     # Consommation maison actuelle (ex: 1200.0)
GRID_CURRENT_W = None      # Puissance réseau (ex: -600.0 si export, +300.0 si import)
RESERVE_W = 150.0          # Réserve configurée dans l'intégration (défaut: 150W)
UNIT_POWER = "W"           # Unité de vos capteurs: "W" ou "kW"
# ----------------------------------------------------------------------------

if PV_CURRENT_W is not None and HOUSE_CURRENT_W is not None:
    print(f"Configuration:")
    print(f"  Unité des capteurs: {UNIT_POWER}")
    print(f"  Réserve configurée: {RESERVE_W}W")
    print(f"\nValeurs des capteurs:")

    # Conversion si nécessaire
    if UNIT_POWER == "kW":
        pv_w = PV_CURRENT_W * 1000.0
        house_w = HOUSE_CURRENT_W * 1000.0
        grid_w = GRID_CURRENT_W * 1000.0 if GRID_CURRENT_W is not None else None
        print(f"  ⚠️  ATTENTION: Vos capteurs sont en kW, conversion en W")
        print(f"  PV: {PV_CURRENT_W} kW → {pv_w:.1f}W")
        print(f"  House: {HOUSE_CURRENT_W} kW → {house_w:.1f}W")
        if grid_w is not None:
            print(f"  Grid: {GRID_CURRENT_W} kW → {grid_w:.1f}W")
    else:
        pv_w = PV_CURRENT_W
        house_w = HOUSE_CURRENT_W
        grid_w = GRID_CURRENT_W
        print(f"  PV: {pv_w:.1f}W")
        print(f"  House: {house_w:.1f}W")
        if grid_w is not None:
            print(f"  Grid: {grid_w:.1f}W")

    # Calcul du surplus (reproduit le code de coordinator.py)
    print(f"\n=== Calcul du surplus_net ===")
    surplus_virtual = pv_w - house_w
    print(f"Étape 1: surplus_virtual = PV - House")
    print(f"         surplus_virtual = {pv_w:.1f} - {house_w:.1f} = {surplus_virtual:.1f}W")

    if grid_w is not None:
        export_w = max(-grid_w, 0.0)
        print(f"\nÉtape 2: Ajustement avec capteur grid")
        print(f"         grid_w = {grid_w:.1f}W ({'IMPORT' if grid_w > 0 else 'EXPORT'})")
        print(f"         export_w = max(-grid_w, 0) = {export_w:.1f}W")
        surplus_virtual_before = surplus_virtual
        surplus_virtual = max(surplus_virtual, export_w)
        print(f"         surplus_virtual = max({surplus_virtual_before:.1f}, {export_w:.1f}) = {surplus_virtual:.1f}W")

    surplus_net_w = max(surplus_virtual - RESERVE_W, 0.0)
    print(f"\nÉtape finale: surplus_net_w = max(surplus_virtual - reserve, 0)")
    print(f"              surplus_net_w = max({surplus_virtual:.1f} - {RESERVE_W:.1f}, 0)")
    print(f"              surplus_net_w = {surplus_net_w:.1f}W")

    # Diagnostic
    print(f"\n=== DIAGNOSTIC ===")
    if surplus_net_w > 0:
        print(f"✅ Le calcul donne un surplus de {surplus_net_w:.1f}W")
        print(f"   Si sensor.spvm_surplus_net affiche 0W, vérifiez:")
        print(f"   1. Que l'intégration a bien été rechargée")
        print(f"   2. Les logs Home Assistant (cherchez 'SPVM surplus calculation')")
        print(f"   3. Les attributs debug_pv_w, debug_house_w dans le capteur")
    elif surplus_virtual > 0:
        print(f"⚠️  surplus_virtual = {surplus_virtual:.1f}W mais reserve = {RESERVE_W}W")
        print(f"   Résultat: surplus_net_w = 0W (pas assez de surplus après réserve)")
        print(f"   Solutions:")
        print(f"   - Réduire la réserve dans la configuration de l'intégration")
        print(f"   - Attendre que la production augmente")
    else:
        print(f"❌ Pas de surplus: PV ({pv_w:.1f}W) <= House ({house_w:.1f}W)")
        print(f"   C'est normal que surplus_net_w = 0W")
        print(f"   La maison consomme plus que ce que les panneaux produisent")

    # Vérification des unités
    if pv_w < 100 or house_w < 100:
        print(f"\n⚠️  ATTENTION: Les valeurs sont très faibles (< 100W)")
        print(f"   Vérifiez que vos capteurs envoient bien des valeurs en Watts")
        print(f"   Si vos capteurs sont en kW, changez UNIT_POWER = 'kW' ci-dessus")

else:
    print(f"❌ SURPLUS_NET non calculé")
    print(f"\nPour diagnostiquer le problème de surplus_net:")
    print(f"1. Ouvrez ce fichier dans un éditeur")
    print(f"2. Trouvez la section 'RENSEIGNEZ VOS VALEURS ICI'")
    print(f"3. Renseignez vos valeurs actuelles:")
    print(f"   PV_CURRENT_W = 1800.0        # Votre production actuelle")
    print(f"   HOUSE_CURRENT_W = 1200.0     # Votre consommation actuelle")
    print(f"   GRID_CURRENT_W = -600.0      # Si vous avez un capteur grid")
    print(f"   RESERVE_W = 150.0            # Votre réserve configurée")
    print(f"   UNIT_POWER = 'W'             # 'W' ou 'kW'")
    print(f"4. Relancez le script: python3 diagnostic.py")
    print(f"\nVous pouvez aussi vérifier les attributs du capteur dans Home Assistant:")
    print(f"  - Outils développeur → États → sensor.spvm_surplus_net")
    print(f"  - Regardez: debug_pv_w, debug_house_w, debug_surplus_virtual")

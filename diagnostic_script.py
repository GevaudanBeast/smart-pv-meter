#!/usr/bin/env python3
"""Script de diagnostic pour SPVM - à exécuter depuis Home Assistant"""

import sys
sys.path.insert(0, '/config/custom_components/spvm')

from datetime import datetime, timezone
from solar_model import SolarInputs, compute as solar_compute

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
print(f"  Théorique (sans correction): {model.expected_base_w:.1f}W")
print(f"  Corrigée (cloud/temp): {model.expected_corrected_w:.1f}W")

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

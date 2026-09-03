from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/02_traitees"
RES = ROOT / "data/03_resultats"

grid = gpd.read_file(OUT / "sites_candidats_phase8.gpkg", layer="grille_eligible").to_crs(4326)
env = pd.read_csv(OUT / "echantillons_environnement_phase9.csv")
data = grid.drop(columns=[c for c in env.columns if c in grid.columns and c != "candidate_id"] + ["geometry"], errors="ignore").merge(env, on="candidate_id")
data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.longitude, data.latitude), crs=4326).to_crs(6933)

data["score_pente"] = np.exp(-data.pente_locale_pct / 5)
data["score_final_environnemental"] = 0.80 * data.score_aptitude_preliminaire + 0.20 * data.score_pente
data["admissible_phase9"] = (
    data.occupation_compatible_preliminaire
    & data.relief_compatible_preliminaire.fillna(False)
    & data.pente_locale_pct.le(8)
)
eligible = data[data.admissible_phase9].sort_values("score_final_environnemental", ascending=False).copy()

# Un site par province, avec 75 km d'espacement lorsque possible.
chosen = []
for province in eligible.groupby("adm1_name")["score_final_environnemental"].max().sort_values(ascending=False).index:
    candidates = eligible[eligible.adm1_name.eq(province)]
    selected = None
    for idx, row in candidates.iterrows():
        if all(row.geometry.distance(eligible.loc[j].geometry) >= 75_000 for j in chosen):
            selected = idx
            break
    if selected is None and len(candidates):
        selected = candidates.index[0]
    if selected is not None:
        chosen.append(selected)

final = eligible.loc[chosen].sort_values("score_final_environnemental", ascending=False).copy()
final["rang_final"] = range(1, len(final) + 1)
final["distance_route_km"] = final.distance_route_m / 1000
final["distance_eau_km"] = final.distance_eau_m / 1000
final["distance_ville_km"] = final.distance_ville_m / 1000
final_wgs = final.to_crs(4326)
final_wgs["longitude"] = final_wgs.geometry.x
final_wgs["latitude"] = final_wgs.geometry.y

result_cols = [
    "rang_final", "candidate_id", "adm1_name", "localite_geonames_proche", "longitude", "latitude",
    "worldcover_classe", "elevation_m", "pente_locale_pct", "distance_route_km", "distance_eau_km",
    "distance_ville_km", "ville_existante_proche", "score_aptitude_preliminaire", "score_final_environnemental",
]
final_wgs[result_cols].to_csv(RES / "sites_nouveaux_filtres_phase9.csv", index=False, encoding="utf-8-sig")

gpkg = OUT / "sites_nouveaux_environnement_phase9.gpkg"
if gpkg.exists():
    gpkg.unlink()
eligible.to_crs(4326).to_file(gpkg, layer="candidats_admissibles_relief_sol", driver="GPKG")
final_wgs.to_file(gpkg, layer="selection_equilibree_finale", driver="GPKG")

classes = data.groupby("worldcover_classe", as_index=False).size().rename(columns={"size":"nombre_cellules"})
classes.to_csv(RES / "distribution_occupation_sol_phase9.csv", index=False, encoding="utf-8-sig")
summary = pd.DataFrame({
    "indicateur": ["Candidats phase 8", "Cellules forestières exclues", "Eau/zones humides/bâti exclus", "Candidats avec relief évalué", "Candidats finaux admissibles", "Provinces représentées"],
    "valeur": [len(data), int(data.worldcover_code.eq(10).sum()), int(data.worldcover_code.isin([50,80,90,95]).sum()), int(data.pente_locale_pct.notna().sum()), len(eligible), final.adm1_name.nunique()],
})
summary.to_csv(RES / "resume_filtre_environnemental_phase9.csv", index=False, encoding="utf-8-sig")

zone = gpd.read_file(ROOT / "restored/zone_etude.gpkg").to_crs(4326)
urban = gpd.read_file(OUT / "graphe_spatial_phase6.gpkg", layer="noeuds_centralites").to_crs(4326)
fig, ax = plt.subplots(figsize=(12, 13))
zone.plot(ax=ax, color="#edf2f7", edgecolor="#6b7280", linewidth=0.65)
data[data.worldcover_code.eq(10)].to_crs(4326).plot(ax=ax, color="#2f855a", markersize=4, alpha=0.22, label="Cellules forestières exclues")
eligible.to_crs(4326).plot(ax=ax, color="#f59e0b", markersize=13, alpha=0.65, label="Candidats admissibles")
urban.plot(ax=ax, color="#374151", markersize=11, label="Villes existantes")
final_wgs.plot(ax=ax, color="#c81e1e", marker="*", edgecolor="white", linewidth=0.6, markersize=120, label="Sélection équilibrée")
for _, row in final_wgs.iterrows():
    ax.annotate(f"{row.rang_final}. {row.localite_geonames_proche}", (row.geometry.x,row.geometry.y), xytext=(4,4), textcoords="offset points", fontsize=8)
ax.set_title("Sites nouveaux après filtres WorldCover et SRTM", fontsize=17, weight="bold")
ax.legend(loc="lower right", frameon=True)
ax.set_axis_off()
fig.tight_layout()
fig.savefig(RES / "sites_nouveaux_environnement_phase9.png", dpi=180, bbox_inches="tight")
plt.close(fig)

limits = pd.DataFrame({
    "contrainte": ["Aires protégées", "Inondation", "Foncier coutumier", "Qualité locale du sol"],
    "statut": ["non intégrée; téléchargement WDPA refusé", "non intégrée", "validation terrain requise", "validation géotechnique requise"],
})
limits.to_csv(RES / "contraintes_restantes_phase9.csv", index=False, encoding="utf-8-sig")

print(summary.to_string(index=False))
print("\nSélection finale préliminaire:\n", final_wgs[["rang_final","adm1_name","localite_geonames_proche","worldcover_classe","pente_locale_pct","score_final_environnemental"]].to_string(index=False))

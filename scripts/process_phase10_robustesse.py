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
geometry = grid[["candidate_id", "geometry"]]
data = env.merge(geometry, on="candidate_id", how="left")
data = gpd.GeoDataFrame(data, geometry="geometry", crs=4326)
data["score_pente"] = np.exp(-data.pente_locale_pct / 5)
data = data[
    data.occupation_compatible_preliminaire
    & data.relief_compatible_preliminaire.fillna(False)
    & data.pente_locale_pct.le(8)
].copy()

components = [
    "score_population", "score_route", "score_eau", "score_rail",
    "score_air", "score_lacune_territoriale", "score_pente",
]
base_weights = np.array([0.24, 0.20, 0.16, 0.08, 0.04, 0.08, 0.20])
X = data[components].to_numpy(float)

rng = np.random.default_rng(20260902)
n_simulations = 5000
weights = rng.dirichlet(base_weights * 60, size=n_simulations)
scores = X @ weights.T

selection_count = np.zeros(len(data), dtype=int)
for province in sorted(data.adm1_name.unique()):
    indices = np.flatnonzero(data.adm1_name.to_numpy() == province)
    winners = indices[np.argmax(scores[indices, :], axis=0)]
    selection_count += np.bincount(winners, minlength=len(data))

data["frequence_selection_pct"] = selection_count / n_simulations * 100
data["score_moyen_monte_carlo"] = scores.mean(axis=1)
data["score_ecart_type_monte_carlo"] = scores.std(axis=1)

def hydro_proxy(row):
    if row.distance_eau_m <= 5_000 and row.pente_locale_pct <= 2:
        return "élevée"
    if row.distance_eau_m <= 15_000 and row.pente_locale_pct <= 5:
        return "modérée"
    return "faible"

data["exposition_hydrologique_proxy"] = data.apply(hydro_proxy, axis=1)
robust = (
    data.sort_values(["adm1_name", "frequence_selection_pct", "score_moyen_monte_carlo"], ascending=[True, False, False])
    .groupby("adm1_name", group_keys=False).head(1).copy()
    .sort_values("frequence_selection_pct", ascending=False)
)
robust["rang_robustesse"] = range(1, len(robust) + 1)

data.to_file(OUT / "robustesse_sites_phase10.gpkg", layer="candidats_monte_carlo", driver="GPKG")
robust.to_file(OUT / "robustesse_sites_phase10.gpkg", layer="selection_robuste_provinciale", driver="GPKG")

cols = [
    "rang_robustesse", "candidate_id", "adm1_name", "localite_geonames_proche",
    "longitude", "latitude", "worldcover_classe", "elevation_m", "pente_locale_pct",
    "distance_eau_m", "exposition_hydrologique_proxy", "frequence_selection_pct",
    "score_moyen_monte_carlo", "score_ecart_type_monte_carlo",
]
robust[cols].to_csv(RES / "selection_robuste_sites_phase10.csv", index=False, encoding="utf-8-sig")
data.sort_values(["adm1_name", "frequence_selection_pct"], ascending=[True, False]).to_csv(
    RES / "sensibilite_complete_sites_phase10.csv", index=False, encoding="utf-8-sig"
)

weights_df = pd.DataFrame(weights, columns=components)
weight_summary = pd.DataFrame({
    "critere": components,
    "poids_reference": base_weights,
    "poids_moyen_simule": weights_df.mean().values,
    "poids_p05": weights_df.quantile(0.05).values,
    "poids_p95": weights_df.quantile(0.95).values,
})
weight_summary.to_csv(RES / "poids_monte_carlo_phase10.csv", index=False, encoding="utf-8-sig")

summary = pd.DataFrame({
    "indicateur": ["Simulations Monte-Carlo", "Candidats testés", "Provinces", "Sites robustes > 80 %", "Sites robustes > 50 %", "Exposition proxy élevée parmi les sites retenus"],
    "valeur": [n_simulations, len(data), robust.adm1_name.nunique(), int(robust.frequence_selection_pct.ge(80).sum()), int(robust.frequence_selection_pct.ge(50).sum()), int(robust.exposition_hydrologique_proxy.eq("élevée").sum())],
})
summary.to_csv(RES / "resume_robustesse_phase10.csv", index=False, encoding="utf-8-sig")

zone = gpd.read_file(ROOT / "restored/zone_etude.gpkg").to_crs(4326)
fig, ax = plt.subplots(figsize=(12, 13))
zone.plot(ax=ax, color="#eff3f8", edgecolor="#6b7280", linewidth=0.65)
data.plot(ax=ax, color="#d1a44b", markersize=11, alpha=0.45, label="75 candidats testés")
sizes = 50 + robust.frequence_selection_pct * 1.2
robust.plot(ax=ax, color="#b91c1c", marker="*", edgecolor="white", linewidth=0.6, markersize=sizes, label="Sites robustes")
for _, row in robust.iterrows():
    ax.annotate(f"{row.localite_geonames_proche} ({row.frequence_selection_pct:.0f} %)", (row.geometry.x, row.geometry.y), xytext=(4,4), textcoords="offset points", fontsize=8)
ax.set_title("Robustesse des sites sous variation des poids (5 000 simulations)", fontsize=16, weight="bold")
ax.legend(loc="lower right", frameon=True)
ax.set_axis_off()
fig.tight_layout()
fig.savefig(RES / "robustesse_sites_phase10.png", dpi=180, bbox_inches="tight")
plt.close(fig)

method = pd.DataFrame({
    "element": ["Distribution des poids", "Sélection", "Graine", "Exposition hydrologique"],
    "definition": [
        "Dirichlet centrée sur les poids de référence, concentration 60",
        "Meilleur candidat de chaque province à chacune des 5 000 simulations",
        "20260902, pour reproductibilité",
        "Proxy: élevée si eau <=5 km et pente <=2 %; modérée si eau <=15 km et pente <=5 %; ne remplace pas une carte d'inondation",
    ],
})
method.to_csv(RES / "methodologie_robustesse_phase10.csv", index=False, encoding="utf-8-sig")

print(summary.to_string(index=False))
print("\nSélection robuste:\n", robust[["adm1_name","localite_geonames_proche","frequence_selection_pct","exposition_hydrologique_proxy"]].to_string(index=False))

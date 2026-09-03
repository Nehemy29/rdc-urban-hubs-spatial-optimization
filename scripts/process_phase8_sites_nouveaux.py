from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/02_traitees"
RES = ROOT / "data/03_resultats"

zone = gpd.read_file(ROOT / "restored/zone_etude.gpkg").to_crs(6933)
roads = gpd.read_file(ROOT / "restored/reseau_routier_zone.gpkg", columns=["id", "highway", "geometry"]).to_crs(6933)
multi_path = OUT / "reseau_multimodal_phase5.gpkg"
water = gpd.read_file(multi_path, layer="voies_eau_principales_osm").to_crs(6933)
rail = gpd.read_file(multi_path, layer="lignes_ferroviaires_osm").to_crs(6933)
air = gpd.read_file(multi_path, layer="aerodromes_osm").to_crs(6933)
urban = gpd.read_file(OUT / "graphe_spatial_phase6.gpkg", layer="noeuds_centralites").to_crs(6933)

# Grille de 25 km; seuls les centres situés dans la zone sont conservés.
minx, miny, maxx, maxy = zone.total_bounds
step = 25_000
cells = []
cid = 1
for x in np.arange(minx, maxx, step):
    for y in np.arange(miny, maxy, step):
        geom = box(x, y, x + step, y + step)
        cells.append({"candidate_id": f"C{cid:04d}", "geometry": geom, "centre": geom.centroid})
        cid += 1
grid = gpd.GeoDataFrame(cells, crs=6933)
centres = gpd.GeoDataFrame(
    grid[["candidate_id"]], geometry=gpd.GeoSeries(grid.centre, crs=6933), crs=6933
)
centres = gpd.sjoin(centres, zone[["adm1_name", "geometry"]], how="inner", predicate="within").drop(columns="index_right")

def nearest(source, distance_col, fields):
    src = source[source.geometry.notna() & ~source.geometry.is_empty][fields + ["geometry"]]
    result = gpd.sjoin_nearest(centres[["candidate_id", "geometry"]], src, how="left", distance_col=distance_col)
    return result.sort_values(distance_col).drop_duplicates("candidate_id").drop(columns=["geometry", "index_right"], errors="ignore")

data = centres.copy()
data = data.merge(nearest(roads, "distance_route_m", ["highway"]), on="candidate_id", how="left")
data = data.merge(nearest(water, "distance_eau_m", ["waterway", "name"]), on="candidate_id", how="left", suffixes=("", "_eau"))
data = data.merge(nearest(rail, "distance_rail_m", ["railway"]), on="candidate_id", how="left")
data = data.merge(nearest(air, "distance_aerodrome_m", ["name"]), on="candidate_id", how="left", suffixes=("", "_aerodrome"))
data = data.merge(nearest(urban, "distance_ville_m", ["node_id", "name"]), on="candidate_id", how="left", suffixes=("", "_ville"))
data = data.rename(columns={"name": "voie_eau_proche", "name_aerodrome": "aerodrome_proche", "name_ville": "ville_existante_proche"})

# Accessibilité démographique gravitaire calculée à partir des 26 agglomérations.
urban_xy = np.array([[g.x, g.y] for g in urban.geometry])
urban_pop = urban.population_worldpop_5km_2025.to_numpy(dtype=float)
potential = []
for geom in data.geometry:
    d_km = np.sqrt((urban_xy[:, 0] - geom.x) ** 2 + (urban_xy[:, 1] - geom.y) ** 2) / 1000
    potential.append(np.sum(urban_pop / (1 + (d_km / 100) ** 2)))
data["potentiel_populationnel"] = potential

# Filtre de présélection : éloignement des villes existantes et accès route/eau.
data = data[
    (data.distance_ville_m >= 40_000)
    & ((data.distance_route_m <= 25_000) | (data.distance_eau_m <= 15_000))
].copy()

def minmax(series):
    span = series.max() - series.min()
    return (series - series.min()) / span if span else series * 0

data["score_population"] = minmax(np.log1p(data.potentiel_populationnel))
data["score_route"] = np.exp(-data.distance_route_m / 15_000)
data["score_eau"] = np.exp(-data.distance_eau_m / 15_000)
data["score_rail"] = np.exp(-data.distance_rail_m / 50_000)
data["score_air"] = np.exp(-data.distance_aerodrome_m / 100_000)
data["score_lacune_territoriale"] = np.clip((data.distance_ville_m - 40_000) / 110_000, 0, 1)
data["score_aptitude_preliminaire"] = (
    0.30 * data.score_population
    + 0.25 * data.score_route
    + 0.20 * data.score_eau
    + 0.10 * data.score_rail
    + 0.05 * data.score_air
    + 0.10 * data.score_lacune_territoriale
)

# Ajoute le nom de la localité GeoNames la plus proche.
cols = ["geonameid", "name", "asciiname", "alternatenames", "latitude", "longitude", "feature_class", "feature_code", "country_code", "cc2", "admin1_code", "admin2_code", "admin3_code", "admin4_code", "population", "elevation", "dem", "timezone", "modification_date"]
geo = pd.read_csv(ROOT / "data/01_brutes/localites/extracted/CD.txt", sep="\t", names=cols, header=None, low_memory=False)
geo = geo[geo.feature_class.eq("P")].copy()
geo = gpd.GeoDataFrame(geo, geometry=gpd.points_from_xy(geo.longitude, geo.latitude), crs=4326).to_crs(6933)
geo = gpd.sjoin(geo, zone[["geometry"]], how="inner", predicate="within").drop(columns="index_right")
near_places = gpd.sjoin_nearest(data[["candidate_id", "geometry"]], geo[["name", "geometry"]], how="left", distance_col="distance_localite_m")
near_places = near_places.sort_values("distance_localite_m").drop_duplicates("candidate_id")[["candidate_id", "name", "distance_localite_m"]]
data = data.merge(near_places, on="candidate_id", how="left").rename(columns={"name": "localite_geonames_proche"})

def select_spaced(frame, n=10, minimum_distance=100_000, max_per_province=None):
    chosen = []
    counts = {}
    for idx, row in frame.sort_values("score_aptitude_preliminaire", ascending=False).iterrows():
        province = row.adm1_name
        if max_per_province is not None and counts.get(province, 0) >= max_per_province:
            continue
        if all(row.geometry.distance(frame.loc[j].geometry) >= minimum_distance for j in chosen):
            chosen.append(idx)
            counts[province] = counts.get(province, 0) + 1
        if len(chosen) == n:
            break
    return frame.loc[chosen].copy()

unconstrained = select_spaced(data, n=10, minimum_distance=100_000)
equitable = select_spaced(data, n=10, minimum_distance=100_000, max_per_province=1)
unconstrained["scenario"] = "score_maximal_espace"
equitable["scenario"] = "equilibre_provincial"
selected = pd.concat([unconstrained, equitable], ignore_index=True)
selected["rang_scenario"] = selected.groupby("scenario")["score_aptitude_preliminaire"].rank(method="first", ascending=False).astype(int)

data_wgs = data.to_crs(4326)
selected_wgs = gpd.GeoDataFrame(selected, geometry="geometry", crs=6933).to_crs(4326)
data_wgs["longitude"] = data_wgs.geometry.x
data_wgs["latitude"] = data_wgs.geometry.y
selected_wgs["longitude"] = selected_wgs.geometry.x
selected_wgs["latitude"] = selected_wgs.geometry.y

all_path = OUT / "sites_candidats_phase8.gpkg"
if all_path.exists():
    all_path.unlink()
data_wgs.to_file(all_path, layer="grille_eligible", driver="GPKG")
selected_wgs[selected_wgs.scenario.eq("score_maximal_espace")].to_file(all_path, layer="top10_score_espace", driver="GPKG")
selected_wgs[selected_wgs.scenario.eq("equilibre_provincial")].to_file(all_path, layer="top10_equilibre_provincial", driver="GPKG")

columns = ["scenario", "rang_scenario", "candidate_id", "adm1_name", "localite_geonames_proche", "distance_localite_m", "longitude", "latitude", "distance_route_m", "distance_eau_m", "distance_rail_m", "distance_aerodrome_m", "distance_ville_m", "ville_existante_proche", "score_aptitude_preliminaire"]
selected_wgs[columns].sort_values(["scenario", "rang_scenario"]).to_csv(RES / "top_sites_nouveaux_phase8.csv", index=False, encoding="utf-8-sig")

summary = pd.DataFrame({
    "indicateur": ["Cellules initiales", "Candidats admissibles", "Taille de cellule (km)", "Distance minimale aux villes existantes (km)", "Espacement minimal entre sites retenus (km)"],
    "valeur": [len(centres), len(data), 25, 40, 100],
})
summary.to_csv(RES / "resume_sites_nouveaux_phase8.csv", index=False, encoding="utf-8-sig")

fig, axes = plt.subplots(1, 2, figsize=(15, 10), sharex=True, sharey=True)
zone_wgs = zone.to_crs(4326)
urban_wgs = urban.to_crs(4326)
for ax, scenario, title in zip(axes, ["score_maximal_espace", "equilibre_provincial"], ["Score maximal + espacement", "Maximum un site par province"]):
    zone_wgs.plot(ax=ax, color="#eff3f8", edgecolor="#707985", linewidth=0.6)
    data_wgs.plot(ax=ax, color="#a8b3c1", markersize=3, alpha=0.25)
    urban_wgs.plot(ax=ax, color="#374151", markersize=10)
    chosen = selected_wgs[selected_wgs.scenario.eq(scenario)]
    chosen.plot(ax=ax, color="#d11d1d", marker="*", edgecolor="white", linewidth=0.5, markersize=95)
    for _, row in chosen.iterrows():
        label = f"{row.rang_scenario}. {row.localite_geonames_proche}"
        ax.annotate(label, (row.geometry.x, row.geometry.y), xytext=(3, 3), textcoords="offset points", fontsize=7)
    ax.set_title(title, weight="bold")
    ax.set_axis_off()
fig.suptitle("Présélection préliminaire de sites nouveaux", fontsize=18, weight="bold")
fig.tight_layout()
fig.savefig(RES / "sites_nouveaux_phase8.png", dpi=180, bbox_inches="tight")
plt.close(fig)

method = pd.DataFrame({
    "critere": ["Potentiel populationnel", "Proximité route", "Proximité voie d'eau", "Proximité rail", "Proximité aérodrome", "Lacune territoriale"],
    "poids": [0.30, 0.25, 0.20, 0.10, 0.05, 0.10],
    "statut": ["réel/modélisé", "OSM", "OSM", "OSM", "OSM", "calculé"] * 1,
})
method.to_csv(RES / "methodologie_sites_nouveaux_phase8.csv", index=False, encoding="utf-8-sig")

print(summary.to_string(index=False))
for scenario in ["score_maximal_espace", "equilibre_provincial"]:
    print("\n", scenario)
    print(selected_wgs[selected_wgs.scenario.eq(scenario)][["rang_scenario", "adm1_name", "localite_geonames_proche", "score_aptitude_preliminaire"]].sort_values("rang_scenario").to_string(index=False))

from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
nodes_path = ROOT / "data/02_traitees/noeuds_urbains_phase3.gpkg"
roads_path = ROOT / "restored/reseau_routier_zone.gpkg"
out_dir = ROOT / "data/03_resultats"
out_dir.mkdir(parents=True, exist_ok=True)

nodes = gpd.read_file(nodes_path).to_crs(6933)
roads = gpd.read_file(roads_path, columns=["id", "highway", "geometry"]).to_crs(6933)
roads["segment_length_km"] = roads.length / 1000

nearest = gpd.sjoin_nearest(
    nodes,
    roads[["id", "highway", "geometry"]],
    how="left",
    distance_col="distance_route_m",
)
nearest = nearest.sort_values("distance_route_m").drop_duplicates("node_id")

rows = []
sindex = roads.sindex
for _, node in nearest.iterrows():
    zone = node.geometry.buffer(10_000)
    candidates = roads.iloc[list(sindex.intersection(zone.bounds))]
    clipped = candidates.geometry.intersection(zone)
    length_km = clipped.length.sum() / 1000
    rows.append(
        {
            "node_id": node.node_id,
            "nom": node["name"],
            "province": node.adm1_name,
            "population_worldpop_5km_2025": round(node.population_worldpop_5km_2025),
            "distance_route_plus_proche_m": round(node.distance_route_m, 1),
            "classe_route_plus_proche": node.highway,
            "longueur_routes_rayon_10km_km": round(length_km, 2),
        }
    )

df = pd.DataFrame(rows)
df["indice_accessibilite_routiere_initial"] = (
    df["longueur_routes_rayon_10km_km"] / (1 + df["distance_route_plus_proche_m"] / 1000)
).round(3)
df = df.sort_values("indice_accessibilite_routiere_initial", ascending=False)
df.to_csv(out_dir / "accessibilite_routiere_noeuds_phase4.csv", index=False, encoding="utf-8-sig")

summary = (
    df.groupby("province", as_index=False)
    .agg(
        nombre_noeuds=("node_id", "count"),
        distance_mediane_route_m=("distance_route_plus_proche_m", "median"),
        routes_moyennes_10km_km=("longueur_routes_rayon_10km_km", "mean"),
    )
    .sort_values("province")
)
summary.to_csv(out_dir / "resume_accessibilite_routiere_phase4.csv", index=False, encoding="utf-8-sig")

print(df.head(10).to_string(index=False))

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/01_brutes/osm_multimodal"
OUT = ROOT / "data/02_traitees"
RES = ROOT / "data/03_resultats"
OUT.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

zone = gpd.read_file(ROOT / "restored/zone_etude.gpkg")
codes = set(zone.adm1_pcode)
nodes = gpd.read_file(OUT / "noeuds_urbains_phase3.gpkg")

water_path = RAW / "waterways/waterways.gpkg"
fallback_water_paths = [
    RAW / "waterways/waterways.geojson",
    RAW / "waterways_geojson/waterways.geojson",
]
try:
    water = gpd.read_file(water_path)
except Exception as error:
    fallback_water_path = next((p for p in fallback_water_paths if p.exists()), None)
    if fallback_water_path is None:
        raise RuntimeError(
            "Le GeoPackage des voies d'eau est illisible et le repli GeoJSON manque."
        ) from error
    print(f"Avertissement: repli sur GeoJSON pour les voies d'eau ({error}).")
    water = gpd.read_file(fallback_water_path)
water = water[
    water.adm1_pcode.isin(codes)
    & water.waterway.isin(["river", "canal", "tidal_channel"])
    & water.geom_type.isin(["LineString", "MultiLineString"])
].copy()

rail = gpd.read_file(RAW / "railways/railways.gpkg")
rail_lines = rail[
    rail.adm1_pcode.isin(codes)
    & rail.railway.eq("rail")
    & rail.geom_type.isin(["LineString", "MultiLineString"])
].copy()
rail_stations = rail[
    rail.adm1_pcode.isin(codes) & rail.railway.eq("station")
].copy()

air = gpd.read_file(RAW / "airports/airports.gpkg")
aerodromes = air[air.adm1_pcode.isin(codes) & air.aeroway.eq("aerodrome")].copy()
aerodromes_m = aerodromes.to_crs(6933)
aerodromes["geometry"] = aerodromes_m.centroid.to_crs(4326)

out_gpkg = OUT / "reseau_multimodal_phase5.gpkg"
if out_gpkg.exists():
    out_gpkg.unlink()
for frame, layer in [
    (water, "voies_eau_principales_osm"),
    (rail_lines, "lignes_ferroviaires_osm"),
    (rail_stations, "gares_osm"),
    (aerodromes, "aerodromes_osm"),
    (nodes, "noeuds_urbains"),
]:
    frame.to_file(out_gpkg, layer=layer, driver="GPKG")

nodes_m = nodes.to_crs(6933)

def nearest_metrics(source, prefix, name_field="name"):
    source_m = source.to_crs(6933).copy()
    source_m = source_m[source_m.geometry.notna() & ~source_m.geometry.is_empty]
    nearest = gpd.sjoin_nearest(
        nodes_m[["node_id", "geometry"]],
        source_m[[name_field, "geometry"]],
        how="left",
        distance_col=f"distance_{prefix}_m",
    )
    nearest = nearest.sort_values(f"distance_{prefix}_m").drop_duplicates("node_id")
    return nearest[["node_id", name_field, f"distance_{prefix}_m"]].rename(
        columns={name_field: f"{prefix}_plus_proche"}
    )

metrics = nodes.drop(columns="geometry").copy()
metrics = metrics.merge(nearest_metrics(water, "voie_eau"), on="node_id", how="left")
metrics = metrics.merge(nearest_metrics(rail_lines, "rail"), on="node_id", how="left")
metrics = metrics.merge(nearest_metrics(aerodromes, "aerodrome"), on="node_id", how="left")
for col in ["distance_voie_eau_m", "distance_rail_m", "distance_aerodrome_m"]:
    metrics[col] = metrics[col].round(1)
metrics["connexion_fluviale_candidate_10km"] = metrics.distance_voie_eau_m.le(10_000)
metrics["connexion_ferroviaire_candidate_10km"] = metrics.distance_rail_m.le(10_000)
metrics["acces_aerien_30km"] = metrics.distance_aerodrome_m.le(30_000)
metrics["nombre_modes_accessibles"] = (
    1
    + metrics.connexion_fluviale_candidate_10km.astype(int)
    + metrics.connexion_ferroviaire_candidate_10km.astype(int)
    + metrics.acces_aerien_30km.astype(int)
)
metrics = metrics.sort_values(
    ["nombre_modes_accessibles", "population_worldpop_5km_2025"], ascending=False
)
metrics.to_csv(RES / "accessibilite_multimodale_noeuds_phase5.csv", index=False, encoding="utf-8-sig")

summary = pd.DataFrame(
    {
        "indicateur": [
            "Voies d'eau principales (segments)",
            "Lignes ferroviaires (segments)",
            "Gares OSM",
            "Aérodromes OSM",
            "Nœuds urbains",
            "Nœuds avec voie d'eau à 10 km",
            "Nœuds avec rail à 10 km",
            "Nœuds avec aérodrome à 30 km",
        ],
        "valeur": [
            len(water), len(rail_lines), len(rail_stations), len(aerodromes), len(nodes),
            metrics.connexion_fluviale_candidate_10km.sum(),
            metrics.connexion_ferroviaire_candidate_10km.sum(),
            metrics.acces_aerien_30km.sum(),
        ],
    }
)
summary.to_csv(RES / "resume_reseau_multimodal_phase5.csv", index=False, encoding="utf-8-sig")

fig, ax = plt.subplots(figsize=(12, 13))
zone.plot(ax=ax, color="#eef2f7", edgecolor="#67717e", linewidth=0.7)
water.plot(ax=ax, color="#3b82c4", linewidth=0.35, alpha=0.65, label="Rivières/canaux OSM")
rail_lines.plot(ax=ax, color="#222222", linewidth=1.0, label="Rail OSM")
aerodromes.plot(ax=ax, color="#f59e0b", marker="^", markersize=20, alpha=0.8, label="Aérodromes OSM")
nodes.plot(ax=ax, color="#b91c1c", markersize=12, label="28 nœuds urbains")
ax.set_title("Réseau multimodal cartographié dans la zone d'étude", fontsize=17, weight="bold")
ax.legend(loc="lower right", frameon=True)
ax.set_axis_off()
fig.tight_layout()
fig.savefig(RES / "reseau_multimodal_phase5.png", dpi=180, bbox_inches="tight")
plt.close(fig)

print(summary.to_string(index=False))
print("\nNœuds les plus multimodaux:\n", metrics[["name", "adm1_name", "nombre_modes_accessibles"]].head(12).to_string(index=False))

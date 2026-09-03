from pathlib import Path
from math import asin, cos, radians, sin, sqrt

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/03_resultats"
OUT = ROOT / "data/02_traitees"

nodes = gpd.read_file(OUT / "noeuds_urbains_phase3.gpkg")
multi = pd.read_csv(RES / "accessibilite_multimodale_noeuds_phase5.csv")
nodes = nodes.merge(
    multi[["node_id", "nombre_modes_accessibles"]], on="node_id", how="left"
)
# Évite le double comptage de localités appartenant à une même agglomération.
# Masina est agrégée à Kinshasa; Bolenge est agrégée à Mbandaka.
nodes = nodes[~nodes["name"].isin(["Masina", "Bolenge"])].copy().reset_index(drop=True)

def haversine(lon1, lat1, lon2, lat2):
    dlon, dlat = radians(lon2 - lon1), radians(lat2 - lat1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(a))

complete = nx.Graph()
for i, row in nodes.iterrows():
    complete.add_node(row.node_id)
for i, a in nodes.iterrows():
    for j in range(i + 1, len(nodes)):
        b = nodes.iloc[j]
        d = haversine(a.longitude, a.latitude, b.longitude, b.latitude)
        complete.add_edge(a.node_id, b.node_id, distance_km=d)

# Graphe spatial exploratoire : arbre couvrant minimal + trois voisins les plus proches.
G = nx.minimum_spanning_tree(complete, weight="distance_km")
for node in complete.nodes:
    nearest = sorted(complete[node].items(), key=lambda x: x[1]["distance_km"])[:3]
    for other, attrs in nearest:
        G.add_edge(node, other, **attrs)

degree = nx.degree_centrality(G)
between = nx.betweenness_centrality(G, weight="distance_km", normalized=True)
close = nx.closeness_centrality(G, distance="distance_km")

pop = dict(zip(nodes.node_id, nodes.population_worldpop_5km_2025))
access = {}
for origin in G.nodes:
    distances = nx.single_source_dijkstra_path_length(G, origin, weight="distance_km")
    access[origin] = sum(pop[d] / (1 + dist) for d, dist in distances.items() if d != origin)

df = nodes.drop(columns="geometry").copy()
df["centralite_degre"] = df.node_id.map(degree)
df["centralite_intermediarite"] = df.node_id.map(between)
df["centralite_proximite"] = df.node_id.map(close)
df["accessibilite_populationnelle"] = df.node_id.map(access)

def minmax(series):
    span = series.max() - series.min()
    return (series - series.min()) / span if span else series * 0

df["score_population"] = minmax(np.log1p(df.population_worldpop_5km_2025))
df["score_accessibilite"] = minmax(df.accessibilite_populationnelle)
df["score_intermediarite"] = minmax(df.centralite_intermediarite)
df["score_multimodalite"] = minmax(df.nombre_modes_accessibles)
df["score_strategique_exploratoire"] = (
    0.25 * df.score_population
    + 0.25 * df.score_accessibilite
    + 0.25 * df.score_intermediarite
    + 0.25 * df.score_multimodalite
)
df = df.sort_values("score_strategique_exploratoire", ascending=False)
df.insert(0, "rang", range(1, len(df) + 1))
df.to_csv(RES / "centralites_noeuds_phase6.csv", index=False, encoding="utf-8-sig")

lookup = nodes.set_index("node_id")
edge_rows = []
for a, b, attrs in G.edges(data=True):
    pa, pb = lookup.loc[a], lookup.loc[b]
    edge_rows.append(
        {
            "origine_id": a,
            "origine": pa["name"],
            "destination_id": b,
            "destination": pb["name"],
            "distance_geodesique_km": round(attrs["distance_km"], 2),
            "geometry": LineString([pa.geometry, pb.geometry]),
        }
    )
edges = gpd.GeoDataFrame(edge_rows, crs=4326)
graph_path = OUT / "graphe_spatial_phase6.gpkg"
if graph_path.exists():
    graph_path.unlink()
edges.to_file(graph_path, layer="aretes_modelees", driver="GPKG")
node_results = nodes.merge(
    df[["node_id", "rang", "centralite_degre", "centralite_intermediarite", "centralite_proximite", "accessibilite_populationnelle", "score_strategique_exploratoire"]],
    on="node_id",
)
node_results.to_file(graph_path, layer="noeuds_centralites", driver="GPKG")

zone = gpd.read_file(ROOT / "restored/zone_etude.gpkg")
fig, ax = plt.subplots(figsize=(12, 13))
zone.plot(ax=ax, color="#eff3f8", edgecolor="#79808a", linewidth=0.7)
edges.plot(ax=ax, color="#7c8da4", linewidth=0.7, alpha=0.65)
sizes = 30 + 450 * minmax(node_results.score_strategique_exploratoire)
node_results.plot(ax=ax, color="#b91c1c", edgecolor="white", linewidth=0.5, markersize=sizes)
top = node_results.nlargest(10, "score_strategique_exploratoire")
for _, row in top.iterrows():
    ax.annotate(row["name"], (row.geometry.x, row.geometry.y), xytext=(4, 4), textcoords="offset points", fontsize=8)
ax.set_title("Graphe spatial exploratoire et centralité stratégique", fontsize=17, weight="bold")
ax.set_axis_off()
fig.tight_layout()
fig.savefig(RES / "graphe_centralites_phase6.png", dpi=180, bbox_inches="tight")
plt.close(fig)

method = pd.DataFrame(
    {
        "element": ["Construction", "Arêtes", "Pondération du score", "Interprétation"],
        "definition": [
            "Arbre couvrant minimal complété par les trois voisins géographiques les plus proches de chaque nœud",
            f"{G.number_of_edges()} relations modélisées entre {G.number_of_nodes()} nœuds; poids = distance géodésique",
            "25 % population, 25 % accessibilité populationnelle, 25 % intermédiarité, 25 % multimodalité",
            "Diagnostic exploratoire; ne représente pas des flux de transport observés",
        ],
    }
)
method.to_csv(RES / "methodologie_graphe_phase6.csv", index=False, encoding="utf-8-sig")

print(f"Nœuds={G.number_of_nodes()} Arêtes={G.number_of_edges()} Connecté={nx.is_connected(G)}")
print(df[["rang", "name", "adm1_name", "centralite_intermediarite", "nombre_modes_accessibles", "score_strategique_exploratoire"]].head(12).to_string(index=False))

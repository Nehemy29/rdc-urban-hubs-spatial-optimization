from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/02_traitees"
RES = ROOT / "data/03_resultats"
GRAPH = OUT / "graphe_spatial_phase6.gpkg"

nodes = gpd.read_file(GRAPH, layer="noeuds_centralites")
edges = gpd.read_file(GRAPH, layer="aretes_modelees")

G = nx.Graph()
for _, row in nodes.iterrows():
    G.add_node(row.node_id)
for _, row in edges.iterrows():
    G.add_edge(row.origine_id, row.destination_id, weight=row.distance_geodesique_km)

ids = list(nodes.node_id)
weights = dict(zip(nodes.node_id, nodes.population_worldpop_5km_2025.astype(float)))
dist = dict(nx.all_pairs_dijkstra_path_length(G, weight="weight"))

def objective(facilities):
    return sum(weights[i] * min(dist[i][f] for f in facilities) for i in ids)

def solve_pmedian(p):
    selected = []
    remaining = set(ids)
    for _ in range(p):
        best = min(remaining, key=lambda c: objective(selected + [c]))
        selected.append(best)
        remaining.remove(best)

    improved = True
    while improved:
        improved = False
        current = objective(selected)
        best_swap = None
        for old in selected:
            for new in set(ids) - set(selected):
                proposal = [new if x == old else x for x in selected]
                value = objective(proposal)
                if value < current - 1e-6:
                    current, best_swap = value, (old, new)
        if best_swap:
            selected[selected.index(best_swap[0])] = best_swap[1]
            improved = True
    return selected, objective(selected)

baseline = [nodes.loc[nodes["name"].eq("Kinshasa"), "node_id"].iloc[0]]
baseline_obj = objective(baseline)
total_pop = sum(weights.values())
assignments = []
summaries = []
selections = []

for p in [5, 10, 15]:
    facilities, obj = solve_pmedian(p)
    for f in facilities:
        r = nodes.loc[nodes.node_id.eq(f)].iloc[0]
        selections.append({"scenario_p": p, "node_id": f, "pole": r["name"], "province": r.adm1_name})

    nearest_distances = []
    for i in ids:
        nearest = min(facilities, key=lambda f: dist[i][f])
        d = dist[i][nearest]
        nearest_distances.append(d)
        src, dst = nodes.loc[nodes.node_id.eq(i)].iloc[0], nodes.loc[nodes.node_id.eq(nearest)].iloc[0]
        assignments.append(
            {
                "scenario_p": p,
                "node_id": i,
                "noeud": src["name"],
                "province": src.adm1_name,
                "population_worldpop_5km_2025": round(weights[i]),
                "pole_affecte": dst["name"],
                "distance_reseau_modele_km": round(d, 2),
            }
        )
    weighted_mean = obj / total_pop
    summaries.append(
        {
            "scenario_p": p,
            "nombre_poles": p,
            "distance_moyenne_ponderee_km": round(weighted_mean, 2),
            "distance_maximale_km": round(max(nearest_distances), 2),
            "population_a_moins_100km_pct": round(100 * sum(weights[i] for i in ids if min(dist[i][f] for f in facilities) <= 100) / total_pop, 2),
            "population_a_moins_250km_pct": round(100 * sum(weights[i] for i in ids if min(dist[i][f] for f in facilities) <= 250) / total_pop, 2),
            "amelioration_vs_kinshasa_seule_pct": round(100 * (baseline_obj - obj) / baseline_obj, 2),
            "fonction_objectif_population_km": round(obj),
        }
    )

selection_df = pd.DataFrame(selections).sort_values(["scenario_p", "province", "pole"])
assignment_df = pd.DataFrame(assignments)
summary_df = pd.DataFrame(summaries)
selection_df.to_csv(RES / "poles_selectionnes_phase7.csv", index=False, encoding="utf-8-sig")
assignment_df.to_csv(RES / "affectations_pmedian_phase7.csv", index=False, encoding="utf-8-sig")
summary_df.to_csv(RES / "comparaison_scenarios_pmedian_phase7.csv", index=False, encoding="utf-8-sig")

selected_nodes = nodes.merge(selection_df, on="node_id", how="inner", suffixes=("", "_selection"))
scenario_gpkg = OUT / "scenarios_pmedian_phase7.gpkg"
if scenario_gpkg.exists():
    scenario_gpkg.unlink()
for p in [5, 10, 15]:
    selected_nodes[selected_nodes.scenario_p.eq(p)].to_file(
        scenario_gpkg, layer=f"poles_p{p}", driver="GPKG"
    )

zone = gpd.read_file(ROOT / "restored/zone_etude.gpkg")
fig, axes = plt.subplots(1, 3, figsize=(19, 9), sharex=True, sharey=True)
for ax, p in zip(axes, [5, 10, 15]):
    zone.plot(ax=ax, color="#eff3f8", edgecolor="#79808a", linewidth=0.55)
    edges.plot(ax=ax, color="#b5c0ce", linewidth=0.45)
    nodes.plot(ax=ax, color="#6b7280", markersize=9)
    chosen = selected_nodes[selected_nodes.scenario_p.eq(p)]
    chosen.plot(ax=ax, color="#c81e1e", edgecolor="white", linewidth=0.5, markersize=55)
    for _, row in chosen.iterrows():
        ax.annotate(row["name"], (row.geometry.x, row.geometry.y), xytext=(3, 3), textcoords="offset points", fontsize=7)
    metric = summary_df.loc[summary_df.scenario_p.eq(p)].iloc[0]
    ax.set_title(f"p = {p}\nDistance moyenne : {metric.distance_moyenne_ponderee_km:.0f} km", weight="bold")
    ax.set_axis_off()
fig.suptitle("Scénarios de localisation-allocation des pôles urbains", fontsize=18, weight="bold")
fig.tight_layout()
fig.savefig(RES / "scenarios_pmedian_phase7.png", dpi=180, bbox_inches="tight")
plt.close(fig)

method = pd.DataFrame(
    {
        "element": ["Demande", "Candidats", "Distance", "Algorithme", "Statut scientifique"],
        "definition": [
            "Population WorldPop 2025 estimée dans un rayon de 5 km autour de chaque agglomération",
            "26 agglomérations existantes après suppression des doubles comptages",
            "Plus court chemin dans le graphe spatial exploratoire de la phase 6",
            "Construction gloutonne suivie d'échanges locaux jusqu'à stabilisation",
            "Scénarios de renforcement de pôles existants; pas encore localisation de villes nouvelles sur une grille continue",
        ],
    }
)
method.to_csv(RES / "methodologie_pmedian_phase7.csv", index=False, encoding="utf-8-sig")

print(summary_df.to_string(index=False))
for p in [5, 10, 15]:
    print(f"\np={p}: " + ", ".join(selection_df.loc[selection_df.scenario_p.eq(p), "pole"]))

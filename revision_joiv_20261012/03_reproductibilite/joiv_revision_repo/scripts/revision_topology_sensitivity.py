"""Read-only sensitivity audit of the published 26-node spatial surrogate.

Outputs do not represent transport routes or observed flows. Run from any cwd.
"""
from pathlib import Path
from math import radians, sin, cos, asin, sqrt
import pandas as pd
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'revision_outputs'
OUT.mkdir(exist_ok=True)
nodes = pd.read_csv(ROOT / 'data/03_resultats/noeuds_urbains_phase3.csv')
nodes = nodes[~nodes['name'].isin(['Masina', 'Bolenge'])].copy()
assert len(nodes) == 26 and nodes.node_id.is_unique
full = nx.Graph()
full.add_nodes_from(nodes.node_id)
records = list(nodes.itertuples())
for i, a in enumerate(records):
    for b in records[i+1:]:
        dl = radians(b.longitude-a.longitude)
        dp = radians(b.latitude-a.latitude)
        h = sin(dp/2)**2 + cos(radians(a.latitude))*cos(radians(b.latitude))*sin(dl/2)**2
        full.add_edge(a.node_id, b.node_id, distance_km=12742.0176*asin(sqrt(min(1,h))))
graphs = {}
for k in [1, 2, 3, 4, 5, 8]:
    g = nx.minimum_spanning_tree(full, weight='distance_km')
    for u in full:
        for v, attrs in sorted(full[u].items(), key=lambda x:(x[1]['distance_km'],x[0]))[:k]:
            g.add_edge(u,v,**attrs)
    graphs[f'MST_knn_{k}'] = g
for threshold in [15,25,40,50,100]:
    g = nx.Graph()
    g.add_nodes_from(full)
    g.add_edges_from((u,v,a) for u,v,a in full.edges(data=True) if a['distance_km']<=threshold)
    graphs[f'radius_{threshold}km'] = g

summary, details = [], []
base = nx.betweenness_centrality(graphs['MST_knn_3'],weight='distance_km')
for label,g in graphs.items():
    bet = nx.betweenness_centrality(g,weight='distance_km',normalized=True)
    close = nx.closeness_centrality(g,distance='distance_km',wf_improved=True)
    rank = pd.Series(bet).rank(ascending=False,method='average')
    rho = pd.Series(bet).rank().corr(pd.Series(base).rank())
    summary.append(dict(topology=label,nodes=len(g),edges=g.number_of_edges(),components=nx.number_connected_components(g),isolates=len(list(nx.isolates(g))),betweenness_rank_correlation_to_baseline=rho))
    for a in records:
        reachable=len(nx.node_connected_component(g,a.node_id))-1
        details.append(dict(topology=label,node_id=a.node_id,name=a.name,betweenness=bet[a.node_id],betweenness_rank=rank[a.node_id],closeness_wf=close[a.node_id],reachable_other_nodes=reachable,reachability_fraction=reachable/(len(g)-1)))
assert graphs['MST_knn_3'].number_of_edges() == 49
pd.DataFrame(summary).to_csv(OUT/'topology_summary.csv',index=False)
pd.DataFrame(details).to_csv(OUT/'topology_node_metrics.csv',index=False)
print(pd.DataFrame(summary).to_string(index=False))
print(pd.DataFrame(details).query("name in ['Kenge','Bandundu']").to_string(index=False))

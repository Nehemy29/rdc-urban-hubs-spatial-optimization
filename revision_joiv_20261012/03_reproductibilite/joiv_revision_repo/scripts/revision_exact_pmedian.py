"""Exact MILP check of the released 26-node surrogate, not regional validation."""
from pathlib import Path
import sqlite3
import json
import numpy as np
import pandas as pd
import networkx as nx
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'revision_outputs'
OUT.mkdir(exist_ok=True)
with sqlite3.connect(ROOT/'data/02_traitees/graphe_spatial_phase6.gpkg') as con:
    nodes=pd.read_sql_query('SELECT node_id,name,population_worldpop_5km_2025 FROM noeuds_centralites',con)
    edges=pd.read_sql_query('SELECT origine_id,destination_id,distance_geodesique_km FROM aretes_modelees',con)
ids=list(nodes.node_id); n=len(ids)
assert n==26 and len(set(ids))==n
G=nx.Graph(); G.add_nodes_from(ids)
for e in edges.itertuples(): G.add_edge(e.origine_id,e.destination_id,weight=e.distance_geodesique_km)
assert nx.is_connected(G) and G.number_of_edges()==49
paths=dict(nx.all_pairs_dijkstra_path_length(G,weight='weight'))
D=np.array([[paths[i][j] for j in ids] for i in ids])
W=nodes.population_worldpop_5km_2025.to_numpy(float)
assert np.all(W>=0) and np.all(np.isfinite(D))
# y_j binary facility variables, x_ij continuous assignment variables.
# With fixed integral y, linear assignment constraints admit integral minima.
c=np.r_[np.zeros(n),(W[:,None]*D).ravel()]
A=lil_matrix((n+n*n+1,n+n*n))
lo=np.zeros(n+n*n+1); hi=np.zeros_like(lo)
for i in range(n):
    A[i,n+i*n:n+(i+1)*n]=1; lo[i]=hi[i]=1
for i in range(n):
    for j in range(n):
        r=n+i*n+j; A[r,n+i*n+j]=1; A[r,j]=-1
        lo[r]=-np.inf; hi[r]=0
A[-1,:n]=1
A=A.tocsr()
published=pd.read_csv(ROOT/'data/03_resultats/comparaison_scenarios_pmedian_phase7.csv').set_index('scenario_p')
out=[]; picks=[]
for p in range(2,21):
    lo[-1]=hi[-1]=p
    result=milp(c=c,integrality=np.r_[np.ones(n),np.zeros(n*n)],bounds=Bounds(0,1),constraints=LinearConstraint(A,lo,hi),options={'time_limit':45,'mip_rel_gap':1e-8})
    if result.x is None: raise RuntimeError(result.message)
    selected=np.flatnonzero(result.x[:n]>.5)
    independently_computed=float(np.sum(W*D[:,selected].min(axis=1)))
    assert len(selected)==p and np.isclose(result.fun,independently_computed,rtol=1e-7)
    initial=float(published.loc[p,'fonction_objectif_population_km']) if p in published.index else float('nan')
    row=dict(p=p,solver_status=int(result.status),solver_message=result.message,mip_gap=float(result.mip_gap),objective_population_km=independently_computed,mean_distance_km=independently_computed/W.sum(),released_heuristic_objective=initial,heuristic_excess_pct=100*(initial-independently_computed)/independently_computed)
    out.append(row)
    picks.extend(dict(p=p,node_id=ids[j],name=nodes.iloc[j]['name']) for j in selected)
    print(json.dumps(row),flush=True)
pd.DataFrame(out).to_csv(OUT/'exact_pmedian_check.csv',index=False)
pd.DataFrame(picks).to_csv(OUT/'exact_pmedian_facilities.csv',index=False)
curve=pd.DataFrame(out).set_index('p').mean_distance_km
gains=1-curve/curve.shift(1)
elbows={}
for threshold in [0.02,0.05,0.10]:
    eligible=[p for p in range(2,18) if all(gains.loc[p+j]<threshold for j in [1,2,3])]
    elbows[str(threshold)]=eligible[0] if eligible else None
(OUT/'elbow_rule_check.json').write_text(json.dumps({'rule':'first p with all next three relative improvements strictly below threshold; p tested 2..20, elbow eligible 2..17','threshold_results':elbows,'hypothesis':'5% rule elbow in [8,12]','supported':elbows['0.05'] is not None and 8<=elbows['0.05']<=12,'scope':'released 26-node surrogate only; not a regional empirical test'},indent=2))
(OUT/'exact_pmedian_metadata.json').write_text(json.dumps({'demand_total':float(W.sum()),'demand_definition':'sum of released 5-km node-buffer population estimates, not the regional population','nodes':n,'edges':G.number_of_edges(),'distance':'released rounded edge distances in km','solver':'scipy.optimize.milp / HiGHS'},indent=2))

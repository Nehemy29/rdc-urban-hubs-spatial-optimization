from pathlib import Path
import ast,json
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import Geod,Transformer
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,lil_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import milp,Bounds,LinearConstraint
B=Path(__file__).resolve().parent;P=B.parent;R=P/'joiv_revision_repo';geod=Geod(ellps='WGS84')
for filename,names in [('revision_road_accessibility.py',{'graph','xyz'}),('revision_joint_coverage.py',{'optimize'})]:
 s=ast.parse((R/'scripts'/filename).read_text());exec(compile(ast.Module(body=[v for v in s.body if isinstance(v,ast.FunctionDef) and v.name in names],type_ignores=[]),'reused_functions','exec'))
CODES=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45'];roads=gpd.read_file(next((P/'evidence_extension/sources/roads').rglob('*.gpkg')),where='adm1_pcode IN ('+','.join("'"+c+"'" for c in CODES)+')',columns=['id','highway','oneway','bridge','layer']);roads=roads[roads.geometry.notna()&~roads.geometry.is_empty]
BASE={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
hubs=pd.read_csv(R/'data/03_resultats/noeuds_urbains_phase3.csv');hubs=hubs[~hubs.name.isin(['Masina','Bolenge'])].reset_index(drop=True)
f=gpd.read_file(B/'results/bandundu_ferry_mapped.gpkg');f['oneway']='no';f['bridge']=None;f['layer']=0
frames=[]
for product,suf in [('WorldPop','geoboundaries'),('GHSPOP','ghspop')]:
 d=pd.read_csv(R/'revision_outputs'/f'population_demand_1km_{suf}.csv.gz');d['product']=product;frames.append(d)
a=pd.concat(frames,ignore_index=True);points=a[['x_center_m','y_center_m']].drop_duplicates().reset_index(drop=True);a['point_idx']=pd.MultiIndex.from_frame(points).get_indexer(pd.MultiIndex.from_frame(a[['x_center_m','y_center_m']]))
lon,lat=Transformer.from_crs(6933,4326,always_xy=True).transform(points.x_center_m,points.y_center_m)
previous=pd.read_csv(R/'revision_outputs/joint_maximal_coverage_results.csv');rows=[];selections=[]
for tracks in [False,True]:
 frame=gpd.GeoDataFrame(pd.concat([roads[roads.highway.isin(BASE|({'track'} if tracks else set()))],f],ignore_index=True),crs=4326);G,coords=graph(frame);tree=cKDTree(xyz(coords[:,0],coords[:,1]));_,di=tree.query(xyz(lon,lat));doff=geod.inv(lon,lat,coords[di,0],coords[di,1])[2]/1000;_,hi=tree.query(xyz(hubs.longitude.to_numpy(),hubs.latitude.to_numpy()));hoff=geod.inv(hubs.longitude.to_numpy(),hubs.latitude.to_numpy(),coords[hi,0],coords[hi,1])[2]/1000;matrix=np.empty((26,len(points)),dtype=np.float64);reverse=G.T.tocsr()
 for j,idx in enumerate(hi):
  dd=dijkstra(reverse,directed=True,indices=int(idx),limit=100);matrix[j]=dd[di]+doff+hoff[j]
 for prod,q in a.groupby('product'):
  ids=q.point_idx.to_numpy();w=q.population.to_numpy();cov=(matrix[:,ids]<=100)&(doff[ids][None,:]<=5)&(hoff[:,None]<=5)
  for p in [5,10,15]:
   value,sel,status,gap,patterns=optimize(cov,w,p);ref=previous[(previous.tracks==tracks)&previous.removal_fraction.eq(0)&previous.jitter_km.eq(0)&previous.resolution_km.eq(1)&previous.connector_km.eq(5)&previous['product'].eq(prod)&previous.p.eq(p)];assert len(ref)==1
   base=float(ref.iloc[0].coverage_pct);new=100*value/w.sum();row={'tracks':tracks,'product':prod,'resolution_km':1,'connector_km':5,'threshold_km':100,'p':p,'road_only_baseline_pct':base,'with_ferry_conditional_pct':new,'difference_pp':new-base,'solver_status':status,'mip_gap':gap,'covered_population':value,'population_total':w.sum()};rows.append(row);selections.extend({'tracks':tracks,'product':prod,'p':p,'name':hubs.iloc[k]['name'],'node_id':hubs.iloc[k].node_id} for k in sel);print(row,flush=True)
 pd.DataFrame(rows).to_csv(B/'results/ferry_coverage_results.csv',index=False);pd.DataFrame(selections).to_csv(B/'results/ferry_coverage_selections.csv',index=False)
 del G,coords,tree,frame,reverse,matrix
assert len(rows)==12 and all(x['solver_status']==0 and x['mip_gap']==0 for x in rows)
(B/'results/ferry_coverage_metadata.json').write_text(json.dumps({'new_optimization_runs':12,'only_changed_structure':'Three mapped Bandundu ferry ways added; exact-coordinate joins only','retained_assumptions':'Same hubs, complete 1-km population grids, 5-km connectors, 100-km threshold, no deletion or displacement','conditional_operation':'Ferry usable and bidirectional, no fare, waiting, capacity, season or security constraint','coverage_is_not_observed':True,'neither_nominal_failure_probability_nor_error_distribution_fitted':True},indent=2))

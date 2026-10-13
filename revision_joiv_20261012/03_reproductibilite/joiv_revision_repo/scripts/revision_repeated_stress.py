"""Repeated joint stresses, not confidence intervals or empirical flow validation."""
from pathlib import Path
import ast,json
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import Geod,Transformer
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,lil_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import milp,Bounds,LinearConstraint
R=Path(__file__).resolve().parents[1];S=R/'revision_sources';O=R/'revision_outputs';geod=Geod(ellps='WGS84')
for file,names in [('revision_road_accessibility.py',{'graph','xyz'}),('revision_joint_coverage.py',{'optimize'})]:
 tree=ast.parse((R/'scripts'/file).read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),file,'exec'))
codes=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45'];classes={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
roads=gpd.read_file(S/'roads/roads.gpkg',where='adm1_pcode IN ('+','.join("'"+x+"'" for x in codes)+')',columns=['id','highway','oneway','bridge','layer']);roads=roads[roads.highway.isin(classes)&roads.geometry.geom_type.isin(['LineString','MultiLineString'])].reset_index(drop=True)
h=pd.read_csv(R/'data/03_resultats/noeuds_urbains_phase3.csv');h=h[~h.name.isin(['Masina','Bolenge'])].reset_index(drop=True)
datasets={x:pd.read_csv(O/f'population_demand_5km_{y}.csv.gz') for x,y in [('WorldPop','geoboundaries'),('GHSPOP','ghspop')]}
u=pd.concat(list(datasets.values()))[['x_center_m','y_center_m']].drop_duplicates().reset_index(drop=True);idx=pd.MultiIndex.from_frame(u)
for d in datasets.values():d['point_idx']=idx.get_indexer(pd.MultiIndex.from_frame(d[['x_center_m','y_center_m']]))
lon,lat=Transformer.from_crs(6933,4326,always_xy=True).transform(u.x_center_m,u.y_center_m)
rows=[];selections=[]
for seed in [0,20261007,20261008,20261009,20261010,20261011]:
 if seed:
  rng=np.random.default_rng(seed);frame=roads.iloc[np.flatnonzero(rng.random(len(roads))>=.01)]
 else:frame=roads
 G,c=graph(frame);tree=cKDTree(xyz(c[:,0],c[:,1]));_,di=tree.query(xyz(lon,lat));doff=geod.inv(lon,lat,c[di,0],c[di,1])[2]/1000
 if seed:
  rng=np.random.default_rng(seed+100000);hlon,hlat,_=geod.fwd(h.longitude.to_numpy(),h.latitude.to_numpy(),rng.uniform(0,360,26),np.full(26,250.))
 else:hlon=h.longitude.to_numpy();hlat=h.latitude.to_numpy()
 _,hi=tree.query(xyz(hlon,hlat));hoff=geod.inv(hlon,hlat,c[hi,0],c[hi,1])[2]/1000
 reverse=G.transpose().tocsr();matrix=np.empty((26,len(u)),dtype=np.float32)
 for j,x in enumerate(hi):matrix[j]=dijkstra(reverse,directed=True,indices=int(x))[di]+doff+hoff[j]
 for product,d in datasets.items():
  ix=d.point_idx.to_numpy();w=d.population.to_numpy()
  for threshold in [50.,100.,150.]:
   cov=(matrix[:,ix]<=threshold)&(doff[ix][None,:]<=5)&(hoff[:,None]<=5)
   for p in [5,10,15]:
    value,sel,status,gap,patterns=optimize(cov,w,p);assert status==0 and gap<=1e-8
    tags=dict(seed=seed,product=product,grid_km=5,threshold_km=threshold,p=p)
    rows.append(dict(**tags,coverage_pct=100*value/w.sum(),covered_population=value,population_total=w.sum(),removed_features=len(roads)-len(frame),solver_status=status,mip_gap=gap))
    selections.extend(dict(**tags,node_id=h.iloc[j].node_id,name=h.iloc[j]['name']) for j in sel)
 pd.DataFrame(rows).to_csv(O/'repeated_joint_stress.csv',index=False);pd.DataFrame(selections).to_csv(O/'repeated_joint_stress_selections.csv',index=False)
 print('Completed seed',seed,'runs',len(rows),flush=True)
z=pd.DataFrame(rows);z[z.seed!=0].groupby(['product','threshold_km','p']).coverage_pct.agg(['min','max','mean','std']).to_csv(O/'repeated_joint_stress_summary.csv')
(O/'repeated_joint_stress_metadata.json').write_text(json.dumps({'total_runs':len(z),'five_stochastic_realizations':[20261007,20261008,20261009,20261010,20261011],'baseline_seed':0,'roads':'main classes','grid_km':5,'connector_km':5,'threshold_km':[50,100,150],'removal': 'independent 1% feature deletion in each realization','coordinates':'250 m fixed displacement with independently drawn azimuth; seed+100000','limits':['five realizations do not estimate tails','uncalibrated stress magnitudes','range/std are scenario descriptors, not statistical confidence','joint deletion+coordinate perturbation cannot separately attribute their effects','no empirical validation']},indent=2))

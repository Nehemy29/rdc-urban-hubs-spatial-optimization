"""Joint scenario sensitivity and exact maximal coverage on mapped roads.

Scenario ranges are assumed stress tests, not statistical confidence intervals.
"""
from pathlib import Path
import ast,json,time
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Geod,Transformer
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,lil_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import milp,Bounds,LinearConstraint

ROOT=Path(__file__).resolve().parents[1];S=ROOT/'revision_sources';O=ROOT/'revision_outputs'
geod=Geod(ellps='WGS84')
# Reuse the audited geometry functions without triggering its analysis workflow.
source=ast.parse((ROOT/'scripts/revision_road_accessibility.py').read_text())
functions=ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in {'graph','xyz'}],type_ignores=[])
exec(compile(functions,'road_geometry_functions','exec'))
codes=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
base={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
roads=gpd.read_file(S/'roads/roads.gpkg',engine='pyogrio',where='adm1_pcode IN ('+','.join("'"+c+"'" for c in codes)+')',columns=['id','highway','oneway','bridge','layer'])
roads=roads[roads.geometry.notna() & roads.geometry.geom_type.isin(['LineString','MultiLineString'])].copy()
hubs=pd.read_csv(ROOT/'data/03_resultats/noeuds_urbains_phase3.csv');hubs=hubs[~hubs['name'].isin(['Masina','Bolenge'])].reset_index(drop=True)
datasets=[]
for product,suffix in [('WorldPop','geoboundaries'),('GHSPOP','ghspop')]:
 for resolution in [1,5]:
  d=pd.read_csv(O/f'population_demand_{resolution}km_{suffix}.csv.gz')
  d['product']=product;d['resolution_km']=resolution;datasets.append(d)
all_d=pd.concat(datasets,ignore_index=True)
unique=all_d[['x_center_m','y_center_m']].drop_duplicates().reset_index(drop=True)
lookup=pd.MultiIndex.from_frame(unique)
all_d['point_idx']=lookup.get_indexer(pd.MultiIndex.from_frame(all_d[['x_center_m','y_center_m']]))
lon,lat=Transformer.from_crs(6933,4326,always_xy=True).transform(unique.x_center_m,unique.y_center_m)

def optimize(coverage,weights,p):
 bits=np.sum(coverage.astype(np.uint32)*(np.uint32(1)<<np.arange(26,dtype=np.uint32))[:,None],axis=0,dtype=np.uint32)
 patterns,inv=np.unique(bits,return_inverse=True)
 mass=np.bincount(inv,weights=weights);count=len(patterns)
 incidence=((patterns[:,None]>>np.arange(26,dtype=np.uint32))&1).astype(float)
 A=lil_matrix((count+1,26+count));A[:count,:26]=-incidence
 A[np.arange(count),26+np.arange(count)]=1;A[-1,:26]=1
 lo=np.r_[np.full(count,-np.inf),p];hi=np.r_[np.zeros(count),p]
 result=milp(c=np.r_[np.zeros(26),-mass],integrality=np.r_[np.ones(26),np.zeros(count)],bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),lo,hi),options={'time_limit':20,'mip_rel_gap':1e-8})
 if result.x is None:raise RuntimeError(result.message)
 sel=np.flatnonzero(result.x[:26]>.5)
 value=float(weights[coverage[sel].any(axis=0)].sum())
 assert len(sel)==p and np.isclose(value,-result.fun,rtol=1e-7)
 return value,sel,int(result.status),float(result.mip_gap),count

results=[];selections=[]
for tracks in [False,True]:
 frame=roads[roads.highway.isin(base|({'track'} if tracks else set()))].copy()
 for removal in [0.,.01]:
  rng=np.random.default_rng(20261006)
  current=frame.iloc[np.flatnonzero(rng.random(len(frame))>=removal)] if removal else frame
  G,coords=graph(current);tree=cKDTree(xyz(coords[:,0],coords[:,1]))
  _,di=tree.query(xyz(np.asarray(lon),np.asarray(lat)))
  doff=geod.inv(lon,lat,coords[di,0],coords[di,1])[2]/1000
  for jitter in [0.,.25]:
   if jitter:
    rng=np.random.default_rng(20261006)
    hlon,hlat,_=geod.fwd(hubs.longitude.to_numpy(),hubs.latitude.to_numpy(),rng.uniform(0,360,26),np.full(26,jitter*1000))
   else:hlon=hubs.longitude.to_numpy();hlat=hubs.latitude.to_numpy()
   _,hi=tree.query(xyz(hlon,hlat));hoff=geod.inv(hlon,hlat,coords[hi,0],coords[hi,1])[2]/1000
   matrix=np.empty((26,len(unique)),dtype=np.float32)
   reverse=G.transpose().tocsr()
   for j,idx in enumerate(hi):
    dd=dijkstra(reverse,directed=True,indices=int(idx));matrix[j]=dd[di]+doff+hoff[j]
   for (product,resolution),d in all_d.groupby(['product','resolution_km'],sort=True):
    idx=d.point_idx.to_numpy();w=d.population.to_numpy()
    for snap in [1.,2.5,5.]:
     coverage=(matrix[:,idx]<=100)&(doff[idx][None,:]<=snap)&(hoff[:,None]<=snap)
     for p in [5,10,15]:
      value,sel,status,gap,patterns=optimize(coverage,w,p)
      tag=dict(tracks=tracks,removal_fraction=removal,jitter_km=jitter,product=product,resolution_km=int(resolution),connector_km=snap,p=p)
      row=dict(**tag,population_total=float(w.sum()),covered_population=value,coverage_pct=100*value/w.sum(),coverage_with_all_26_pct=100*w[coverage.any(axis=0)].sum()/w.sum(),solver_status=status,mip_gap=gap,distinct_coverage_patterns=patterns)
      results.append(row)
      selections.extend(dict(**tag,node_id=hubs.iloc[j].node_id,name=hubs.iloc[j]['name']) for j in sel)
   print(f'completed tracks={tracks}, removal={removal}, jitter={jitter}',flush=True)
   pd.DataFrame(results).to_csv(O/'joint_maximal_coverage_results.csv',index=False)
   pd.DataFrame(selections).to_csv(O/'joint_maximal_coverage_selections.csv',index=False)
pd.DataFrame(results).groupby('p').coverage_pct.agg(['min','max','median']).to_csv(O/'joint_maximal_coverage_ranges.csv')
(O/'joint_coverage_metadata.json').write_text(json.dumps({'completed_scenarios_per_p':96,'total_optimization_runs':len(results),'objective':'maximize modelled population within 100 km road+assumed connector distance','candidate_set':'26 existing GeoNames urban nodes, not proposed new cities','factors':{'population':['WorldPop2025','GHSPOP2025'],'grid_km':[1,5],'tracks':[False,True],'connector_km':[1,2.5,5],'road_feature_removal_fraction':[0,.01],'hub_coordinate_displacement_km':[0,.25]},'perturbation_seed':20261006,'removal_method':'one independent uniform draw per selected road feature; fixed sample for each graph scenario; not calibrated OSM incompleteness','coordinate_method':'fixed 250 m displacement with independent random azimuth per hub; stress test not positional error distribution','limits':['scenario ranges are not confidence intervals','objective differs from legacy p-median','alternative population masks and products are modelled','equal-objective site sets may be nonunique; reported identities are one optimum','not a Sobol decomposition','no travel speeds because no travel-time claims','no observed-flow validation']},indent=2))

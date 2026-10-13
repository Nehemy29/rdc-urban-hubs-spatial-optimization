from pathlib import Path
import ast,json,hashlib
import numpy as np,pandas as pd,geopandas as gpd
from shapely.geometry import LineString
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from pyproj import Geod
B=Path(__file__).resolve().parent;P=B.parent;geod=Geod(ellps='WGS84')
source=ast.parse((P/'joiv_revision_repo/scripts/revision_road_accessibility.py').read_text());exec(compile(ast.Module(body=[v for v in source.body if isinstance(v,ast.FunctionDef) and v.name in ['graph','xyz']],type_ignores=[]),'graph_function','exec'))
CODES=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45'];roads=gpd.read_file(next((P/'evidence_extension/sources/roads').rglob('*.gpkg')),where='adm1_pcode IN ('+','.join("'"+c+"'" for c in CODES)+')',columns=['id','highway','oneway','bridge','layer','adm1_pcode'])
BASE={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
hubs=pd.read_csv(P/'joiv_revision_repo/data/03_resultats/noeuds_urbains_phase3.csv');h=hubs[hubs.name.isin(['Kinshasa','Bandundu Province'])].reset_index(drop=True)
ferries=json.loads((B/'sources/osm_ferries_20261008.json').read_text());frows=[]
for e in ferries['elements']:
 if e.get('tags',{}).get('name')!='Bac Bandundu':continue
 frows.append({'id':str(e['id']),'highway':'ferry_conditional','oneway':'no','bridge':None,'layer':0,'adm1_pcode':None,'geometry':LineString([(a['lon'],a['lat']) for a in e['geometry']])})
assert len(frows)==3
f=gpd.GeoDataFrame(frows,crs=4326);f.to_file(B/'results/bandundu_ferry_mapped.gpkg',driver='GPKG')
rows=[]
for label,classes in [('main',BASE),('main_plus_tracks',BASE|{'track'})]:
 frame=roads[roads.highway.isin(classes)&roads.geometry.notna()&~roads.geometry.is_empty].copy();frame=gpd.GeoDataFrame(pd.concat([frame,f],ignore_index=True),crs=4326)
 G,coords=graph(frame);tree=cKDTree(xyz(coords[:,0],coords[:,1]));_,idx=tree.query(xyz(h.longitude.to_numpy(),h.latitude.to_numpy()));offset=geod.inv(h.longitude.to_numpy(),h.latitude.to_numpy(),coords[idx,0],coords[idx,1])[2]/1000;i=int(h.index[h.name.eq('Kinshasa')][0]);j=int(h.index[h.name.eq('Bandundu Province')][0]);dist,pred=dijkstra(G,directed=True,indices=int(idx[i]),return_predecessors=True)
 path=[int(idx[j])]
 while path[-1]!=idx[i]:
  k=int(pred[path[-1]])
  if k<0:raise RuntimeError('No ferry scenario path')
  path.append(k)
 path=path[::-1];xy=coords[path,:2];gpd.GeoDataFrame([{'road_set':label,'distance_km':float(dist[idx[j]]+sum(offset)),'geometry':LineString(xy)}],crs=4326).to_file(B/'results'/f'Kinshasa_Bandundu_{label}_with_mapped_ferry.gpkg',driver='GPKG')
 ferry_used=any(np.array_equal(xy[k],np.array([17.3631662,-3.3107049])) for k in range(len(xy)))
 total=float(dist[idx[j]]+sum(offset));rows.append({'road_set':label,'scenario':'mapped_Bandundu_ferry_assumed_usable_bidirectional','model_distance_km':total,'reference_2018_km':490,'reference_2024_via_Mongata_km':405,'difference_vs_2024_pct':100*(total/405-1),'ferry_vertex_in_path':ferry_used,'added_ferry_ways':3,'added_synthetic_connections':0,'operational_status_validated':False})
 print(rows[-1],flush=True)
 del G,coords,dist,pred,frame,tree
pd.DataFrame(rows).to_csv(B/'results/ferry_route_scenario.csv',index=False)
(B/'results/ferry_scenario_metadata.json').write_text(json.dumps({'road_graph_source':'unchanged October 5 2026 HOT extract','ferry_source':'current OSM Overpass geometry retrieved Oct 8 2026','ferry_way_ids':[r['id'] for r in frows],'geometry_join':'exact shared coordinates only; no geometric gap repair','new_assumptions':['Bandundu ferry usable and bidirectional','Distance cost only; waiting, fares, vehicle capacity, security and seasonal operations omitted'],'independent_evidence':'Logistics Cluster April 18 2024 documents Bac Bandundu and RN17 access constraints; not current ferry verification','no_population_coverage_recalculation':True,'no_empirical_error_calibration':True},indent=2))

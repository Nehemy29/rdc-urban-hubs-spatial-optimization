from pathlib import Path
import ast,json,zipfile,hashlib
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import Geod
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
B=Path(__file__).resolve().parent; OUT=B/'results';OUT.mkdir(exist_ok=True)
assert hashlib.sha256((B/'sources/roads.zip').read_bytes()).hexdigest()=='e70623e58bc1f004ae143ca32d952421ffada78c302c2649b458ca183295c0b7'
with zipfile.ZipFile(B/'sources/roads.zip') as z:z.extractall(B/'sources/roads')
script=B.parent/'joiv_revision_repo/scripts/revision_road_accessibility.py'
s=ast.parse(script.read_text());geod=Geod(ellps='WGS84')
exec(compile(ast.Module(body=[v for v in s.body if isinstance(v,ast.FunctionDef) and v.name in ['graph','xyz']],type_ignores=[]),'existing_graph_functions','exec'))
CODES=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
roads=gpd.read_file(next((B/'sources/roads').rglob('*.gpkg')),where='adm1_pcode IN ('+','.join("'"+c+"'" for c in CODES)+')',columns=['id','highway','oneway','bridge','layer','adm1_pcode'])
BASE={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
hubs=pd.read_csv(B.parent/'joiv_revision_repo/data/03_resultats/noeuds_urbains_phase3.csv')
h=hubs[hubs.name.isin(['Kinshasa','Matadi','Bandundu Province','Mbandaka'])].reset_index(drop=True)
print(h[['name','longitude','latitude']].to_string(index=False),flush=True)
refs={frozenset(['Kinshasa','Matadi']):355,frozenset(['Kinshasa','Bandundu Province']):490,frozenset(['Matadi','Bandundu Province']):1051}
rows=[]
for label,classes in [('main',BASE),('main_plus_tracks',BASE|{'track'})]:
 frame=roads[roads.highway.isin(classes)&roads.geometry.notna() & ~roads.geometry.is_empty].copy()
 G,coords=graph(frame);tree=cKDTree(xyz(coords[:,0],coords[:,1]));_,idx=tree.query(xyz(h.longitude.to_numpy(),h.latitude.to_numpy()))
 offsets=geod.inv(h.longitude.to_numpy(),h.latitude.to_numpy(),coords[idx,0],coords[idx,1])[2]/1000
 dist=dijkstra(G,directed=True,indices=idx)
 print(label,G.shape,G.nnz,flush=True)
 for i in range(len(h)):
  for j in range(len(h)):
   key=frozenset([h.iloc[i]['name'],h.iloc[j]['name']])
   if i==j or key not in refs:continue
   network=float(dist[i,idx[j]]);total=network+offsets[i]+offsets[j]
   rows.append(dict(road_set=label,origin=h.iloc[i]['name'],destination=h.iloc[j]['name'],published_distance_km=refs[key],reference_date='2018-09-06',reference_type='published_logistics_catalogue_not_GPS',origin_offset_km=offsets[i],destination_offset_km=offsets[j],mapped_path_exists=np.isfinite(network),model_distance_km=total if np.isfinite(total) else None,signed_difference_km=total-refs[key] if np.isfinite(total) else None,relative_difference_pct=100*(total/refs[key]-1) if np.isfinite(total) else None,reference_triangle_violation=key==frozenset(['Matadi','Bandundu Province']),included_in_empirical_calibration=False))
 pd.DataFrame(rows).to_csv(OUT/'published_route_benchmark.csv',index=False)
 del G,coords,dist,frame,tree
print(pd.DataFrame(rows).to_string(index=False),flush=True)
(OUT/'route_benchmark_metadata.json').write_text(json.dumps({'source_url':'https://logcluster.org/sites/default/files/public/maps/coddistcapittomajortown4l_20180906.pdf','reference_date':'2018-09-06','snapshot':'2026-10-05','triangle_check':'1051 > 355 + 490; excess 206 km','endpoint_definition':'released GeoNames hub points, not specified catalogue terminals','reference_mode':'published road distances, not GPS or observed use','no_calibrated_error_distribution':True,'no_validation_of_population_coverage':True},indent=2))

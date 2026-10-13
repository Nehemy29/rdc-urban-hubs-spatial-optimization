from pathlib import Path
import ast,json
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import Geod
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import LineString
B=Path(__file__).resolve().parent;P=B.parent; geod=Geod(ellps='WGS84')
source=ast.parse((P/'joiv_revision_repo/scripts/revision_road_accessibility.py').read_text());exec(compile(ast.Module(body=[v for v in source.body if isinstance(v,ast.FunctionDef) and v.name in ['graph','xyz']],type_ignores=[]),'oldgraph','exec'))
CODES=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45'];roads=gpd.read_file(next((P/'evidence_extension/sources/roads').rglob('*.gpkg')),where='adm1_pcode IN ('+','.join("'"+c+"'" for c in CODES)+')',columns=['id','highway','oneway','bridge','layer','adm1_pcode'])
BASE={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
hubs=pd.read_csv(P/'joiv_revision_repo/data/03_resultats/noeuds_urbains_phase3.csv');h=hubs[hubs.name.isin(['Kinshasa','Bandundu Province'])].reset_index(drop=True);result=[]
for label,classes in [('main',BASE),('main_plus_tracks',BASE|{'track'})]:
 frame=roads[roads.highway.isin(classes)&roads.geometry.notna()&~roads.geometry.is_empty].copy();G,coords=graph(frame);tree=cKDTree(xyz(coords[:,0],coords[:,1]));_,idx=tree.query(xyz(h.longitude.to_numpy(),h.latitude.to_numpy()));i=int(h.index[h.name.eq('Kinshasa')][0]);j=int(h.index[h.name.eq('Bandundu Province')][0]);dist,pred=dijkstra(G,directed=True,indices=int(idx[i]),return_predecessors=True);path=[int(idx[j])]
 while path[-1]!=idx[i]:
  k=int(pred[path[-1]])
  if k<0:raise RuntimeError('Missing path')
  path.append(k)
 path=path[::-1];xy=coords[path,:2];gpd.GeoDataFrame([{'road_set':label,'mapped_distance_km':dist[idx[j]],'geometry':LineString(xy)}],crs=4326).to_file(B/'results'/f'Kinshasa_Bandundu_{label}.gpkg',driver='GPKG')
 # Export geometry as OSM-derived diagnostic, not as an observed journey.
 result.append({'road_set':label,'distance_without_offsets_km':float(dist[idx[j]]),'path_vertices':len(path),'bounds_lon_lat':list(LineString(xy).bounds)})
 print(result[-1],flush=True)
 del G,coords,dist,pred,frame,tree
(B/'results/path_trace_metadata.json').write_text(json.dumps(result,indent=2))

"""Compare supplied OSRM distances to the unchanged published graph rules.
This is a routing comparison, not independent empirical household validation.
"""
from pathlib import Path
import ast,json,hashlib,argparse,gc,time
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import Geod
from shapely.geometry import LineString
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
B=Path(__file__).resolve().parent;O=B/'results';O.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--roads',type=Path,required=True);parser.add_argument('--road-archive',type=Path,required=True);parser.add_argument('--graph-script',type=Path,required=True);parser.add_argument('--ferry-json',type=Path,required=True);args=parser.parse_args()
assert hashlib.sha256(args.road_archive.read_bytes()).hexdigest()=='e70623e58bc1f004ae143ca32d952421ffada78c302c2649b458ca183295c0b7'
geod=Geod(ellps='WGS84');treecode=ast.parse(args.graph_script.read_text())
exec(compile(ast.Module(body=[x for x in treecode.body if isinstance(x,ast.FunctionDef) and x.name in ['graph','xyz']],type_ignores=[]),'original_graph','exec'))
a=pd.read_csv(B/'input/40_trajets_distances_osrm.csv');docs=pd.read_csv(B/'input/comparaison_documentaire_40_trajets.csv')
assert len(a)==40 and a.id_trajet.is_unique
for r in docs.itertuples(index=False):assert r[1]==a.loc[a.id_trajet.eq(r[0]),'origine'].iloc[0]
assert np.isfinite(a.distance_osrm_km).all() and a.distance_osrm_km.gt(0).all()
CODES=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
roads=gpd.read_file(args.roads,where='adm1_pcode IN ('+','.join("'"+x+"'" for x in CODES)+')',columns=['id','highway','oneway','bridge','layer'])
roads=roads[roads.geometry.notna()&~roads.geometry.is_empty]
base={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
ferrydata=json.loads(args.ferry_json.read_text());frows=[]
for e in ferrydata['elements']:
 if e.get('tags',{}).get('name')=='Bac Bandundu':frows.append({'id':str(e['id']),'highway':'ferry_conditional','oneway':'no','bridge':None,'layer':0,'geometry':LineString([(v['lon'],v['lat']) for v in e['geometry']])})
assert len(frows)==3
f=gpd.GeoDataFrame(frows,crs=4326)
rows=[];graphs=[]
for tracks in [False,True]:
 for ferry in [False,True]:
  started=time.time();tag=('main_tracks' if tracks else 'main')+('_conditional_Bandundu_ferry' if ferry else '_road_only')
  frame=roads[roads.highway.isin(base|({'track'} if tracks else set()))].copy()
  if ferry:frame=gpd.GeoDataFrame(pd.concat([frame,f],ignore_index=True),crs=4326)
  G,xy=graph(frame);print(tag,'graph',G.shape,G.nnz,flush=True)
  points=pd.concat([a[['longitude_origine','latitude_origine']].rename(columns={'longitude_origine':'lon','latitude_origine':'lat'}),a[['longitude_destination','latitude_destination']].rename(columns={'longitude_destination':'lon','latitude_destination':'lat'})],ignore_index=True)
  tree=cKDTree(xyz(xy[:,0],xy[:,1]));_,idx=tree.query(xyz(points.lon.to_numpy(),points.lat.to_numpy()))
  off=geod.inv(points.lon.to_numpy(),points.lat.to_numpy(),xy[idx,0],xy[idx,1])[2]/1000
  for origin in np.unique(idx[:40]):
   distance=dijkstra(G,directed=True,indices=int(origin))
   for k in np.flatnonzero(idx[:40]==origin):
    r=a.iloc[k];network=float(distance[idx[40+k]]);attach=bool(off[k]<=5 and off[40+k]<=5);finite=attach and np.isfinite(network)
    total=network+off[k]+off[40+k] if finite else np.nan;ref=float(r.distance_osrm_km)
    rec={'id_trajet':r.id_trajet,'origine':r.origine,'destination':r.destination,'scenario':tag,'tracks':tracks,'conditional_Bandundu_ferry':ferry,'distance_osrm_reference_km':ref,'distance_model_km':total,'origin_connector_km':off[k],'destination_connector_km':off[40+k],'endpoints_attached':attach,'directed_path_exists':bool(np.isfinite(network)),'comparison_available':bool(finite),'status':'finite_comparison' if finite else ('connector_exceeds_5km' if not attach else 'no_directed_path'),'signed_difference_km':total-ref if finite else np.nan,'absolute_difference_km':abs(total-ref) if finite else np.nan,'absolute_relative_difference_pct':100*abs(total-ref)/ref if finite else np.nan,'osrm_within_100km':ref<=100,'model_within_100km':total<=100 if finite else np.nan,'threshold_disagreement':bool((total<=100)!=(ref<=100)) if finite else np.nan,'reference_type':'OSRM fastest driving route, supplied CSV; OSM-based, not field observation','reference_date':r.date_verification,'reference_query_url':r.url_requete_osrm}
    if finite:
     straight=geod.inv(r.longitude_origine,r.latitude_origine,r.longitude_destination,r.latitude_destination)[2]/1000
     assert total>=straight-1e-5
    rows.append(rec)
  pd.DataFrame(rows).sort_values(['scenario','id_trajet']).to_csv(O/'model_vs_osrm_160_comparisons.csv',index=False)
  graphs.append({'scenario':tag,'features':len(frame),'vertices':G.shape[0],'arcs':G.nnz,'seconds':time.time()-started})
  del G,xy,tree,frame,distance;gc.collect()
long=pd.DataFrame(rows);s=[]
for name,g in long.groupby('scenario'):
 valid=g[g.comparison_available];s.append({'scenario':name,'routes_supplied':len(g),'finite_comparisons':len(valid),'unavailable':len(g)-len(valid),'mean_absolute_relative_difference_pct':valid.absolute_relative_difference_pct.mean(),'median_absolute_relative_difference_pct':valid.absolute_relative_difference_pct.median(),'mean_signed_difference_km':valid.signed_difference_km.mean(),'mean_absolute_difference_km':valid.absolute_difference_km.mean(),'root_mean_square_difference_km':np.sqrt(np.mean(valid.signed_difference_km**2)),'threshold_disagreements_100km':int(valid.threshold_disagreement.sum()),'model_within_osrm_outside_100km':int(((valid.distance_model_km<=100)&(valid.distance_osrm_reference_km>100)).sum()),'model_outside_osrm_within_100km':int(((valid.distance_model_km>100)&(valid.distance_osrm_reference_km<=100)).sum())})
pd.DataFrame(s).to_csv(O/'routing_comparison_summary.csv',index=False)
# Complete the supplied documentary rows while preserving provenance and missingness.
main=long[long.scenario.eq('main_road_only')].set_index('id_trajet')
all40=docs.copy();all40['Distance modèle (km)']=all40.ID.map(main.distance_model_km);all40['Statut modèle']=all40.ID.map(main.status)
all40['Écart modèle moins référence documentaire km']=all40['Distance modèle (km)']-all40['Distance documentaire (km)']
all40['Écart absolu relatif modèle documentaire pourcent']=100*abs(all40['Écart modèle moins référence documentaire km'])/all40['Distance documentaire (km)']
all40['Référence documentaire vérifiée en ligne']=all40.ID.isin(['TR-001','TR-018'])
all40['Portée documentaire']=np.where(all40.ID.isin(['TR-001','TR-018']),'Commercial advertised distance; original measurement method, terminals and date unverified',np.where(all40.ID.eq('TR-032'),'Secondary reproduction; original provenance not verified, excluded from confirmed documentary checks','No documentary benchmark supplied'))
all40.to_csv(O/'comparaison_documentaire_40_trajets_completee.csv',index=False,encoding='utf-8-sig')
meta={'date':'2026-10-12','runs':4,'route_pairs':40,'comparison_rows':160,'road_archive_sha256':hashlib.sha256(args.road_archive.read_bytes()).hexdigest(),'graph_function_sha256':hashlib.sha256(args.graph_script.read_bytes()).hexdigest(),'input_osrm_sha256':hashlib.sha256((B/'input/40_trajets_distances_osrm.csv').read_bytes()).hexdigest(),'ferry_source_sha256':hashlib.sha256(args.ferry_json.read_bytes()).hexdigest(),'source_epoch':'HOT/OSM snapshot 5 Oct 2026; ferry geometry retrieved 8 Oct 2026','same_original_graph_rules':True,'distance_objective':'directed minimum geodesic road length + assumed connectors <=5km at both ends','osrm_objective':'fastest driving route distance; not minimum length','graph':graphs,'osrm_limitations':['Shared OSM provenance; no independent field validation','Supplied CSV, no raw response/waypoint snap distances or server data epoch','Different profile, cost function, extraction and potentially mode rules'],'documentary_sources':[{'ids':['TR-001','TR-018'],'url':'https://kayou.app/trajets','web_checked':'2026-10-12','status':'advertised commercial distances, measurement method and independence unverified'},{'ids':['TR-032'],'url':'https://fr.scribd.com/document/704533262/PROJET-TRANSPORT','status':'original provenance unverified; excluded from confirmed checks'}],'no_population_coverage_validation':True,'no_error_distribution_calibration':True,'no_simulated_observed_distance_used':True,'no_optimizations_or_hub_locations_changed':True}
(O/'route_comparison_metadata.json').write_text(json.dumps(meta,indent=2))
print(pd.DataFrame(s).to_string(index=False),flush=True)
print(all40[all40['Distance documentaire (km)'].notna()][['ID','Origine','Destination','Distance documentaire (km)','Distance modèle (km)','Écart absolu relatif modèle documentaire pourcent']].to_string(index=False),flush=True)

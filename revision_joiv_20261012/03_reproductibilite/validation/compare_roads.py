from pathlib import Path
import zipfile,json,hashlib,argparse
import geopandas as gpd,numpy as np,pandas as pd,shapely
parser=argparse.ArgumentParser();parser.add_argument('--step-m',type=int,choices=[25,50],default=25);STEP=parser.parse_args().step_m
ROOT=Path(__file__).resolve().parent
OUT=ROOT/f'results_{STEP}m';OUT.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT/'sources/hot_roads.zip') as z:z.extractall(ROOT/'sources/hot')
p=next((ROOT/'sources/hot').rglob('*.gpkg'))
codes=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
b=gpd.read_file(ROOT/'sources/geoBoundaries-COD-ADM1.geojson')
print(b.columns.tolist(),flush=True)
names=['Kinshasa','Kongo-Central','Kwango','Kwilu','Mai-Ndombe','Équateur','Mongala','Nord-Ubangi','Sud-Ubangi','Tshuapa']
print(b.shapeName.tolist(),flush=True)
sel=b[b.shapeName.str.normalize('NFKD').str.encode('ascii',errors='ignore').str.decode('ascii').str.lower().str.replace('-','').str.replace(' ','').isin(['kinshasa','kongocentral','kwango','kwilu','maindombe','equateur','mongala','nordubangi','sudubangi','tshuapa'])]
assert len(sel)==10,len(sel)
region=sel.to_crs(4326).geometry.union_all()
roads=gpd.read_file(p,where="adm1_pcode IN ("+','.join("'"+c+"'" for c in codes)+")")
roads=roads[roads.geometry.notna() & ~roads.geometry.is_empty]
proj='+proj=aeqd +lat_0=-1 +lon_0=19 +datum=WGS84 +units=m +no_defs'
r=roads.to_crs(proj)
base=['trunk','primary','secondary','tertiary','trunk_link','primary_link','secondary_link','tertiary_link','unclassified','residential','service','living_street','road']
trees={'main':shapely.STRtree(r[r.highway.isin(base)].geometry.values),'main_plus_tracks':shapely.STRtree(r[r.highway.isin(base+['track'])].geometry.values),'all_mapped':shapely.STRtree(r.geometry.values)}
f=gpd.read_file(next((ROOT/'sources/forest').glob('*.shp'))).to_crs(4326)
f=gpd.clip(f,region).to_crs(proj)
f=f.explode(index_parts=False).reset_index(drop=True)
f=f[f.geometry.geom_type=='LineString']
print('region',len(roads),'forest',len(f),flush=True)
f['projected_clipped_length_m']=f.geometry.length
f.drop(columns='geometry').to_csv(OUT/'forest_reference_inventory.csv',index=False)
a=gpd.read_file(next((ROOT/'sources/aicd').glob('*.shp')))
a=a[(a.OBJECTID>0)&(a.AADT_VALUE>=0)]
a.drop(columns='geometry').to_csv(OUT/'historical_traffic_inventory.csv',index=False)
stats=[]
for label,frame in [('forest_2019_2025',f),('aicd_2004_traffic_segments',a.to_crs(proj))]:
 pts=[];weights=[]
 for line in frame.geometry:
  for geom in ([line] if line.geom_type=='LineString' else list(line.geoms)):
   n=max(1,int(np.ceil(geom.length/STEP)))
   pts.extend(shapely.line_interpolate_point(geom,(np.arange(n)+.5)/n,normalized=True));weights.extend([geom.length/n]*n)
 pts=np.array(pts,dtype=object);w=np.array(weights)
 print(label,len(pts),sum(w)/1000,flush=True)
 for name,tree in trees.items():
  idx,d=tree.query_nearest(pts,return_distance=True,all_matches=False)
  order=np.argsort(idx[0]);d=d[order]
  assert len(d)==len(w)
  pd.DataFrame({'distance_m':d,'length_weight_m':w}).to_csv(OUT/f'{label}_{name}_sample_distances.csv',index=False)
  for tol in [25,50,100,250]:stats.append({'reference':label,'road_set':name,'tolerance_m':tol,'reference_features':len(frame),'reference_length_km':sum(w)/1000,'sample_count':len(w),'matched_length_pct':100*sum(w[d<=tol])/sum(w)})
pd.DataFrame(stats).to_csv(OUT/'road_reference_agreement.csv',index=False)
manifest={str(p.name):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (ROOT/'sources').glob('*') if p.is_file()}
(OUT/'source_checksums.json').write_text(json.dumps(manifest,indent=2))
print(pd.DataFrame(stats).to_string(index=False),flush=True)

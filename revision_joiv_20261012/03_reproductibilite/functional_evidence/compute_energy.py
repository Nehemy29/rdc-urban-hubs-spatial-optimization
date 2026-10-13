"""Distances to historical HV linework; not operational electricity access."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import CRS,Transformer
from shapely.ops import transform,unary_union,nearest_points
from shapely import Point,segmentize
B=Path(__file__).resolve().parent
S=B/'sources';O=B/'results';O.mkdir(exist_ok=True)
z=S/'cod_hv_network_2018.zip'
with zipfile.ZipFile(z) as f:f.extractall(S/'hv')
lines=gpd.read_file(next((S/'hv').glob('*.shp'))).to_crs(4326)
assert len(lines)==46 and lines.geometry.notna().all()
g=unary_union([segmentize(x,0.01) for x in lines.geometry])
sel=pd.read_csv(B.parent/'new_hubs/results/all_new_hub_selections.csv')
u=sel.drop_duplicates('candidate_id')[['candidate_id','province','longitude','latitude']].copy()
dist=[];names=[]
for r in u.itertuples():
 crs=CRS.from_proj4(f'+proj=aeqd +lat_0={r.latitude} +lon_0={r.longitude} +datum=WGS84 +units=m')
 tr=Transformer.from_crs(4326,crs,always_xy=True)
 local=transform(tr.transform,g); d=Point(0,0).distance(local)/1000
 dist.append(d)
 # Identify nearest source feature in the same local projection.
 dl=[Point(0,0).distance(transform(tr.transform,x)) for x in lines.geometry]
 names.append(lines.iloc[int(np.argmin(dl))]['Name'])
u['distance_historical_hv_km']=dist;u['nearest_historical_line']=names
u.to_csv(O/'unique_selected_sites_hv_distance.csv',index=False)
x=sel.merge(u[['candidate_id','distance_historical_hv_km','nearest_historical_line']],on='candidate_id',validate='many_to_one')
x.to_csv(O/'all_selected_sites_hv_distance.csv',index=False)
example=x[x.grid_km.eq(10)&~x.tracks&x['product'].eq('WorldPop')&x.condition.eq('screened')&x.new_hubs.eq(5)].copy()
example.to_csv(O/'five_site_example_hv_distance.csv',index=False)
summary=x.groupby(['grid_km','tracks','product','condition','new_hubs']).agg(sites=('candidate_id','count'),min_hv_km=('distance_historical_hv_km','min'),max_hv_km=('distance_historical_hv_km','max'),median_hv_km=('distance_historical_hv_km','median')).reset_index()
assert len(summary)==24 and (summary.sites==summary.new_hubs).all()
summary.to_csv(O/'scenario_hv_distance_summary.csv',index=False)
meta={'retrieved_date':'2026-10-09','source_url':'https://datacatalogfiles.worldbank.org/ddh-published/0038470/1/DR0046995/cod_hv_network_2018.zip','catalog_url':'https://energydata.info/en/dataset/democratic-republic-congo-cod-transmission-network-2018','source_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'source_features':len(lines),'unique_selected_candidates':len(u),'scenario_count':24,'method':'Densify source linework at maximum 0.01-degree segment length, per-site WGS84 azimuthal equidistant projection, shortest planar point-to-line distance; approximate geometric proximity, not routed connection length.','epoch_note':'Dataset title refers to 2018; catalog release year 2021 and metadata update 2025 do not establish current operational status.','independence_note':'Catalogue describes DRC EASE mapping revised with SNEL specialists; it is an infrastructure context, not an independent validation of road coverage or energy reliability.','license':'CC BY 4.0','exclusions':'No inference of energization, connection, voltage compatibility, spare capacity, reliability, tariff or economic sovereignty.'}
(O/'energy_distance_metadata.json').write_text(json.dumps(meta,indent=2))
print(example[['candidate_id','province','distance_historical_hv_km','nearest_historical_line']].to_string(index=False))
print('unique',len(u),'scenario rows',len(summary))

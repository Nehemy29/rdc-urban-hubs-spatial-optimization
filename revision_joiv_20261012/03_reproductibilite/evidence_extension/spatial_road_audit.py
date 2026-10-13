from pathlib import Path
import zipfile,json
import geopandas as gpd,numpy as np,pandas as pd,shapely
B=Path(__file__).resolve().parent;O=B/'results';O.mkdir(exist_ok=True)
with zipfile.ZipFile(B/'sources/forest_roads.zip') as z:z.extractall(B/'sources/forest')
mask=gpd.read_file(B/'sources/geoBoundaries-COD-ADM1.geojson');names={'Kinshasa','Kongo-Central','Kwango','Kwilu','Mai-Ndombe','Équateur','Mongala','Nord-Ubangi','Sud-Ubangi','Tshuapa'};mask=mask[mask.shapeName.isin(names)].to_crs(4326);assert len(mask)==10
proj='+proj=aeqd +lat_0=-1 +lon_0=19 +datum=WGS84 +units=m +no_defs'
f=gpd.read_file(next((B/'sources/forest').glob('*.shp'))).to_crs(4326)
codes=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
r=gpd.read_file(next((B/'sources/roads').rglob('*.gpkg')),where='adm1_pcode IN ('+','.join("'"+c+"'" for c in codes)+')',columns=['highway']).to_crs(proj)
base={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
trees={n:shapely.STRtree(r[r.highway.isin(c)].geometry.values) for n,c in [('main',base),('main_plus_tracks',base|{'track'})]}
all_rows=[];summary=[]
for m in mask.itertuples():
 a=gpd.clip(f,m.geometry).to_crs(proj).explode(index_parts=False);a=a[a.geometry.geom_type=='LineString'];pts=[];w=[];years=[]
 for row in a.itertuples():
  n=max(1,int(np.ceil(row.geometry.length/25)))
  pts.extend(shapely.line_interpolate_point(row.geometry,(np.arange(n)+.5)/n,normalized=True));w.extend([row.geometry.length/n]*n);years.extend([row.Year]*n)
 if not pts:
  summary.append({'province':m.shapeName,'road_set':'main','tolerance_m':100,'reference_km':0,'matched_pct':None});continue
 p=np.array(pts,dtype=object);w=np.array(w);x=shapely.get_x(p);y=shapely.get_y(p)
 for label,tree in trees.items():
  idx,d=tree.query_nearest(p,all_matches=False,return_distance=True);d=d[np.argsort(idx[0])]
  q=pd.DataFrame({'province':m.shapeName,'road_set':label,'x_m':x,'y_m':y,'year':years,'weight_m':w,'distance_m':d});all_rows.append(q)
  for tol in [25,50,100,250]:summary.append({'province':m.shapeName,'road_set':label,'tolerance_m':tol,'reference_km':sum(w)/1000,'matched_pct':100*sum(w[d<=tol])/sum(w)})
 print(m.shapeName,len(p),sum(w)/1000,flush=True)
s=pd.DataFrame(summary);s.to_csv(O/'province_road_agreement.csv',index=False)
a=pd.concat(all_rows,ignore_index=True);a['period']=np.where(a.year<=2022,'2019_2022','2023_2025');age=[]
for (road,period),q in a.groupby(['road_set','period']):
 age.append({'road_set':road,'period':period,'reference_km':q.weight_m.sum()/1000,'agreement_100m_pct':100*q.loc[q.distance_m<=100,'weight_m'].sum()/q.weight_m.sum()})
pd.DataFrame(age).to_csv(O/'road_agreement_by_detection_period.csv',index=False)
res=[]
for road in ['main','main_plus_tracks']:
 q=a[a.road_set==road].copy();q['matched_m']=np.where(q.distance_m<=100,q.weight_m,0)
 for size in [25000,50000]:
  q['bx']=np.floor(q.x_m/size).astype(int);q['by']=np.floor(q.y_m/size).astype(int)
  blocks=q.groupby(['bx','by'])[['weight_m','matched_m']].sum().reset_index();weights=blocks.weight_m.to_numpy();matches=blocks.matched_m.to_numpy();rng=np.random.default_rng(20261008);rep=[]
  for i in range(1000):
   ids=rng.integers(0,len(blocks),len(blocks));rep.append(100*matches[ids].sum()/weights[ids].sum())
  res.append({'road_set':road,'block_km':size/1000,'nonempty_blocks':len(blocks),'replicates':1000,'agreement_pct':100*matches.sum()/weights.sum(),'spatial_resampling_p025_pct':np.quantile(rep,.025),'spatial_resampling_p975_pct':np.quantile(rep,.975),'range_type':'conditional_spatial_resampling_not_total_error_confidence_interval'})
  blocks[['weight_m','matched_m']].to_csv(O/f'block_sufficient_statistics_{road}_{size//1000}km.csv',index=False)
pd.DataFrame(res).to_csv(O/'spatial_resampling_ranges.csv',index=False)
# Do not export EO road coordinates or raw line attributes under unresolved producer terms.
print(pd.DataFrame(res).to_string(index=False),flush=True)
print(s[(s.road_set=='main_plus_tracks')&(s.tolerance_m==100)].to_string(index=False),flush=True)

"""10/25 km candidate screening sensitivity; no constructability claim.
WDPCA raw polygons and attributes are private inputs, not redistributed outputs.
"""
from pathlib import Path
import json,math,os,concurrent.futures,hashlib,urllib.request,shutil
import numpy as np,pandas as pd,geopandas as gpd,rasterio
from shapely.geometry import Point,box
from shapely import make_valid,union_all
from scipy.spatial.distance import cdist
R=Path(__file__).resolve().parents[1];S=R/'revision_sources';O=R/'revision_outputs'
NAMES={'Kinshasa','Kongo-Central','Kwango','Kwilu','Mai-Ndombe','Équateur','Mongala','Nord-Ubangi','Sud-Ubangi','Tshuapa'}
z=gpd.read_file(S/'geoBoundaries-COD-ADM1.geojson');z=z[z.shapeName.isin(NAMES)].to_crs(6933).rename(columns={'shapeName':'province'});assert len(z)==10
zone=union_all([make_valid(x) for x in z.geometry]);bounds=zone.bounds
# Constant feature sources across the two candidate grids.
codes=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45'];road=gpd.read_file(S/'roads/roads.gpkg',where='adm1_pcode IN ('+','.join("'"+x+"'" for x in codes)+')',columns=['highway']);road=road[road.geometry.geom_type.isin(['LineString','MultiLineString'])].to_crs(6933)
multi=R/'data/02_traitees/reseau_multimodal_phase5.gpkg'
water=gpd.read_file(multi,layer='voies_eau_principales_osm').to_crs(6933);rail=gpd.read_file(multi,layer='lignes_ferroviaires_osm').to_crs(6933);air=gpd.read_file(multi,layer='aerodromes_osm').to_crs(6933)
h=gpd.read_file(R/'data/02_traitees/noeuds_urbains_phase3.gpkg');h=h[~h.name.isin(['Masina','Bolenge'])].to_crs(6933)
pa=gpd.read_file(S/'wdpca_cod_layer1.json');pa['geometry']=pa.geometry.map(make_valid);pa=pa[pa.status.isin(['Designated','Inscribed','Established'])].to_crs(6933);pa_union=union_all(pa.geometry)
pt=gpd.read_file(S/'wdpca_cod_layer0.json').to_crs(6933)
# Reported area buffers for point-only records are a screening assumption, not boundaries.
pointbuffers=[]
for row in pt.itertuples():
 if row.status in {'Designated','Inscribed','Established'} and np.isfinite(row.rep_area) and row.rep_area>0:pointbuffers.append(row.geometry.buffer(np.sqrt(row.rep_area*1e6/np.pi)))
point_union=union_all(pointbuffers) if pointbuffers else None
frames=[];counts=[]
for step in [10000,25000]:
 xs=np.arange(math.floor(bounds[0]/step),math.ceil(bounds[2]/step));ys=np.arange(math.floor(bounds[1]/step),math.ceil(bounds[3]/step));rows=[]
 for ix in xs:
  for iy in ys:
   centre=Point((ix+.5)*step,(iy+.5)*step)
   if zone.contains(centre):rows.append(dict(candidate_id=f'G{step//1000}_{ix}_{iy}',grid_km=step//1000,ix=ix,iy=iy,geometry=centre))
 g=gpd.GeoDataFrame(rows,crs=6933);g=gpd.sjoin(g,z[['province','geometry']],how='inner',predicate='within').drop(columns='index_right').drop_duplicates('candidate_id').reset_index(drop=True)
 n0=len(g)
 for label,source in [('road',road),('water',water),('rail',rail),('air',air),('hub',h)]:
  near=gpd.sjoin_nearest(g[['candidate_id','geometry']],source[['geometry']],distance_col='distance',how='left');near=near.groupby('candidate_id').distance.min();g[f'd_{label}_m']=g.candidate_id.map(near)
 g=g[(g.d_hub_m>=40000)&((g.d_road_m<=25000)|(g.d_water_m<=15000))].copy().reset_index(drop=True)
 g['protected_centre']=g.geometry.intersects(pa_union)
 cells=[box(x.geometry.x-step/2,x.geometry.y-step/2,x.geometry.x+step/2,x.geometry.y+step/2) for x in g.itertuples()]
 g['protected_cell_intersection']=[x.intersects(pa_union) for x in cells]
 g['point_buffer_cell_intersection']=[x.intersects(point_union) for x in cells] if point_union is not None else False
 counts.append(dict(grid_km=step//1000,centres_in_zone=n0,access_remoteness_eligible=len(g),protected_centre=int(g.protected_centre.sum()),protected_cell_intersection=int(g.protected_cell_intersection.sum()),point_buffer_cell_intersection=int(g.point_buffer_cell_intersection.sum())))
 frames.append(g);print('Grid',step,'eligible',len(g),'PA intersections',g.protected_cell_intersection.sum(),flush=True)
g=gpd.GeoDataFrame(pd.concat(frames,ignore_index=True),crs=6933)
# Same regional population demand and same kernel at both resolutions.
d=pd.read_csv(O/'population_demand_5km_geoboundaries.csv.gz');coords=d[['x_center_m','y_center_m']].to_numpy();mass=d.population.to_numpy();pot=[]
for i in range(0,len(g),128):
 xy=np.column_stack([g.geometry.x.iloc[i:i+128],g.geometry.y.iloc[i:i+128]]);dist=cdist(xy,coords)/1000;pot.extend((1/(1+(dist/100)**2))@mass)
g['population_potential']=pot;lo=np.log1p(g.population_potential).min();hi=np.log1p(g.population_potential).max();g['score_population']=(np.log1p(g.population_potential)-lo)/(hi-lo)
for name,scale in [('road',15000),('water',15000),('rail',50000),('air',100000)]:g['score_'+name]=np.exp(-g['d_'+name+'_m']/scale)
g['score_gap']=np.clip((g.d_hub_m-40000)/110000,0,1);cols=['score_population','score_road','score_water','score_rail','score_air','score_gap'];g['score_reference']=g[cols].to_numpy()@np.array([.3,.25,.2,.1,.05,.1]);g['score_uniform']=g[cols].mean(axis=1)
g.to_pickle(O/'candidate_grid_prepared.pkl')
wgs=g.to_crs(4326);g['longitude']=wgs.geometry.x;g['latitude']=wgs.geometry.y
# WorldCover nearest native pixel at each candidate centre, not parcel composition.
def tile(lat,lon):
 a=math.floor(lat/3)*3;b=math.floor(lon/3)*3;return ('N' if a>=0 else 'S')+f'{abs(a):02d}'+('E' if b>=0 else 'W')+f'{abs(b):03d}'
g['tile']=[tile(y,x) for x,y in zip(g.longitude,g.latitude)]
# Read verified local tiles; HTTPS byte downloads use the system certificate context.
(S/'worldcover').mkdir(exist_ok=True)
tile_manifest={x['tile']:x for x in json.loads((S/'worldcover_tile_manifest.json').read_text())}
cache=O/'candidate_grid_worldcover_samples.csv'
known=pd.read_csv(cache).set_index('candidate_id').worldcover_code.to_dict() if cache.exists() else {}
def sample(item):
 t,group=item;url='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_'+t+'_Map.tif'
 try:
  local=S/'worldcover'/(t+'.tif')
  if not local.exists():
   temp=local.with_suffix('.download')
   with urllib.request.urlopen(url,timeout=120) as response,temp.open('wb') as target:shutil.copyfileobj(response,target)
   temp.replace(local)
  if hashlib.sha256(local.read_bytes()).hexdigest()!=tile_manifest[t]['sha256']:raise RuntimeError('WorldCover source snapshot mismatch: '+t)
  with rasterio.open(local) as ds:
   return t,dict(zip(group.candidate_id,[int(x[0]) for x in ds.sample(zip(group.longitude,group.latitude))])),None
 except Exception as e:return t,{},str(e)
missing=g[~g.candidate_id.isin(known)];errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 fut=[pool.submit(sample,item) for item in missing.groupby('tile')]
 for f in concurrent.futures.as_completed(fut):
  t,values,error=f.result();known.update(values)
  if error:errors.append(dict(tile=t,error=error))
  pd.DataFrame(list(known.items()),columns=['candidate_id','worldcover_code']).to_csv(cache,index=False);print('Sampled tile',t,len(values),'error',error,flush=True)
g['worldcover_code']=g.candidate_id.map(known)
# Extreme alternative allows mapped tree cover only to expose effect of the hard rule.
summary=[];selected=[]
for res in [10,25]:
 a=g[g.grid_km==res]
 for forest,allowed in [('strict_tree_exclusion',{20,30,40,60}),('tree_allowed_sensitivity_only',{10,20,30,40,60})]:
  for protection in ['centre','cell_intersection']:
   flag=a.protected_centre if protection=='centre' else a.protected_cell_intersection|a.point_buffer_cell_intersection
   b=a[a.worldcover_code.isin(allowed)&~flag].copy()
   summary.append(dict(grid_km=res,forest_rule=forest,protection_rule=protection,eligible_before_environment=len(a),unclassified_landcover=int(a.worldcover_code.isna().sum()),after_landcover=int(a.worldcover_code.isin(allowed).sum()),after_protected_mask=len(b),provinces_with_candidates=b.province.nunique()))
   for weight in ['reference','uniform']:
    winners=b.sort_values('score_'+weight,ascending=False).groupby('province',sort=True).head(1)
    for row in winners.itertuples():selected.append(dict(grid_km=res,forest_rule=forest,protection_rule=protection,weight=weight,province=row.province,candidate_id=row.candidate_id,longitude=row.longitude,latitude=row.latitude,score=getattr(row,'score_'+weight),worldcover_code=row.worldcover_code))
g.drop(columns='geometry').to_csv(O/'candidate_grid_comparison.csv',index=False);pd.DataFrame(counts).to_csv(O/'candidate_grid_protection_counts.csv',index=False);pd.DataFrame(summary).to_csv(O/'candidate_grid_environment_summary.csv',index=False);pd.DataFrame(selected).to_csv(O/'candidate_grid_environment_winners.csv',index=False)
meta={'boundary':'geoBoundaries common ten-province mask','grid_origin':'EPSG6933 global zero; centres=(index+0.5)*step','grid_km':[10,25],'protected_database':'UNEP-WCMC and IUCN WDPCA October 2026 protected-area view, site_type PA','polygon_records_cod':59,'point_records_cod':1,'included_status':['Designated','Inscribed','Established'],'proposed_records':'not included','masked_modes':['candidate centre within polygon','full square cell intersects polygon or reported-area point buffer'],'forest_modes':['strict exclude WorldCover10','allow WorldCover10 solely as upper-bound sensitivity; no inference of forest degradation'],'worldcover':'ESA WorldCover2021v200 native point samples','weights':'assumed six-variable reference vs uniform; no expert elicitation','unknown_landcover':int(g.worldcover_code.isna().sum()),'errors':errors,'limits':['no slope/parcel audit for new grid','no forest integrity class','tree-allowed candidates are not recommendations','point buffers approximate reported area; not legal boundary','population potential is a kernel, not observed flows','no tenure or capacity validation','protected polygon coordinates and attributes excluded from public package']}
(O/'candidate_grid_environment_metadata.json').write_text(json.dumps(meta,indent=2));print(pd.DataFrame(summary).to_string(index=False),flush=True)

# Geodesic comparison of top centres under strict full-cell screening.
from pyproj import Geod
w=pd.DataFrame(selected);shifts=[]
for weight in ['reference','uniform']:
 a=w[(w.forest_rule=='strict_tree_exclusion')&(w.protection_rule=='cell_intersection')&(w.weight==weight)]
 b=a[a.grid_km==10].merge(a[a.grid_km==25],on='province',suffixes=('_10','_25'))
 for row in b.itertuples():
  distance=Geod(ellps='WGS84').inv(row.longitude_10,row.latitude_10,row.longitude_25,row.latitude_25)[2]/1000
  shifts.append(dict(weight=weight,province=row.province,winner_10km=row.candidate_id_10,winner_25km=row.candidate_id_25,geodesic_shift_km=distance))
sh=pd.DataFrame(shifts);sh.to_csv(O/'candidate_grid_winner_shifts.csv',index=False)
(O/'candidate_grid_winner_shifts_metadata.json').write_text(json.dumps({'strict_fullcell_common_provinces':int(sh[sh.weight=='reference'].province.nunique()),'comparison':sh.groupby('weight').geodesic_shift_km.agg(['count','median','max']).to_dict('index')},indent=2))

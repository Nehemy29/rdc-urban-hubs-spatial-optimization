from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.features import shapes
from scipy.ndimage import label,find_objects
from shapely import make_valid,union_all,contains_xy
from shapely.geometry import shape,Point
from pyproj import Transformer
B=Path(__file__).resolve().parent;S=B/'sources';O=B/'results';O.mkdir(exist_ok=True)
fs=json.loads((S/'geoBoundaries-COD-ADM1.geojson').read_text())['features']
names={'Kinshasa','Kongo-Central','Kwango','Kwilu','Mai-Ndombe','Équateur','Mongala','Nord-Ubangi','Sud-Ubangi','Tshuapa'}
country=union_all([make_valid(shape(f['geometry'])) for f in fs]);zone=union_all([make_valid(shape(f['geometry'])) for f in fs if f['properties']['shapeName'] in names])
smod=next(S.glob('GHS_SMOD*.tif'));pop=next(S.glob('GHS_POP*.tif'))
with rasterio.open(smod) as src:
 bounds=transform_bounds(4326,src.crs,*country.bounds,densify_pts=41)
 win=from_bounds(*bounds,transform=src.transform).round_offsets().round_lengths();win=win.intersection(rasterio.windows.Window(0,0,src.width,src.height));a=src.read(1,window=win);t=src.window_transform(win);crs=src.crs
with rasterio.open(pop) as src:
 assert src.crs==crs
 pw=from_bounds(*rasterio.windows.bounds(win,transform=rasterio.open(smod).transform),transform=src.transform).round_offsets().round_lengths()
 assert src.window_transform(pw).almost_equals(t), "Native grids are not aligned"
 population=src.read(1,window=pw,masked=True).filled(0);assert population.shape==a.shape
 population=np.where(np.isfinite(population)&(population>0),population,0)
rr,cc=np.indices(a.shape);x,y=rasterio.transform.xy(t,rr.ravel(),cc.ravel());tx=Transformer.from_crs(crs,4326,always_xy=True);lon,lat=tx.transform(x,y)
country_mask=contains_xy(country,np.asarray(lon),np.asarray(lat)).reshape(a.shape)
region_mask=contains_xy(zone,np.asarray(lon),np.asarray(lat)).reshape(a.shape)
print('native window',a.shape,flush=True)
all_polys=[];all_rows=[]
for code,kind in [(30,'urban_centre'),(23,'dense_urban_cluster'),(22,'semi_dense_urban_cluster')]:
 cells=(a==code)&country_mask
 labs,n=label(cells,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
 ids=np.unique(labs[region_mask & (labs>0)])
 # No region clipping before component labelling; country clipped by cell-centre rule.
 keep=np.isin(labs,ids)&(labs>0)
 comp_pops=np.bincount(labs.ravel(),weights=population.ravel(),minlength=n+1)
 comp_cells=np.bincount(labs.ravel(),minlength=n+1)
 region_pops=np.bincount(labs.ravel(),weights=(population*region_mask).ravel(),minlength=n+1)
 geoms={int(value):make_valid(shape(geom)) for geom,value in shapes(labs.astype('int32'),mask=keep,transform=t,connectivity=4)}
 for idx in ids:
  key=f'{kind}_{int(idx):05d}';geom=geoms[int(idx)]
  row={'cluster_id':key,'smod_code':code,'type':kind,'native_cells':int(comp_cells[idx]),'native_area_km2':float(comp_cells[idx]),'ghspop_2025_cluster':float(comp_pops[idx]),'ghspop_2025_in_study_centres':float(region_pops[idx])}
  all_rows.append(row);all_polys.append(dict(row,geometry=geom))
 labs8,n8=label(cells,structure=np.ones((3,3),dtype=int));id8=np.unique(labs8[region_mask&(labs8>0)])
 print(kind,'4connected',len(ids),'8connected',len(id8),flush=True)
g=gpd.GeoDataFrame(all_polys,crs=crs);g.to_file(O/'ghsl_morphological_clusters.gpkg',layer='classified_cell_components',driver='GPKG')
pd.DataFrame(all_rows).to_csv(O/'ghsl_cluster_inventory.csv',index=False)
hubs=pd.read_csv(B.parent/'joiv_revision_repo/data/03_resultats/noeuds_urbains_phase3.csv');hubs=hubs[~hubs.name.isin(['Masina','Bolenge'])]
ht=Transformer.from_crs(4326,crs,always_xy=True);hp=[]
for h in hubs.itertuples():
 px,py=ht.transform(h.longitude,h.latitude);pt=Point(px,py);matches=g[g.geometry.covers(pt)]
 row={'node_id':h.node_id,'name':h.name,'cluster_id':'','ghspop_2025_cluster':np.nan,'morphological_area_km2':np.nan,'point_inside_mapped_component':False}
 if len(matches):
  m=matches.iloc[0];row.update(cluster_id=m.cluster_id,ghspop_2025_cluster=m.ghspop_2025_cluster,morphological_area_km2=m.native_area_km2,point_inside_mapped_component=True)
 hp.append(row)
pd.DataFrame(hp).to_csv(O/'existing_hubs_cluster_membership.csv',index=False)
metadata={'sources':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [smod,pop,S/'geoBoundaries-COD-ADM1.geojson']], 'epoch':2025,'crs':str(crs),'native_resolution_m':1000,'method':'Four-connected components of published native SMOD class 30, 23 and 22, labelled separately after COD cell-centre masking, before selecting components intersecting study-region cell centres. No arbitrary hub radius. Population sum of aligned native GHS-POP cells, including entire country-masked component.','components_by_class':pd.DataFrame(all_rows).groupby('smod_code').size().to_dict(),'hubs_inside':sum(r['point_inside_mapped_component'] for r in hp),'hubs_total':len(hp),'limits':['Derived morphological classified-cell components; not official UCDB identifiers or functional urban areas','No commuter or institutional boundaries inferred','Country cell-centre masking and four-connectivity explicit; class22 and23 kept separate, not merged into a combined agglomeration','Class30 producer smoothing already encoded; no new smoothing applied','2025 population projections are modelled estimates, not validation observations','Rural hub points remain unmatched; no nearest-cluster forced assignment']}
(O/'ghsl_metadata.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2))

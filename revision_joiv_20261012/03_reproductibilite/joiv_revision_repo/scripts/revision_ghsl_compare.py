"""Independent population-product comparison, not census/flow validation."""
from pathlib import Path
import json
import gzip
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from pyproj import Transformer
from shapely.geometry import shape
from shapely import make_valid,union_all,contains_xy
ROOT=Path(__file__).resolve().parents[1];S=ROOT/'revision_sources';O=ROOT/'revision_outputs'
NAMES={'Kinshasa','Kongo-Central','Kwango','Kwilu','Mai-Ndombe','Équateur','Mongala','Nord-Ubangi','Sud-Ubangi','Tshuapa'}
fs=json.loads((S/'geoBoundaries-COD-ADM1.geojson').read_text())['features']
zone=union_all([make_valid(shape(f['geometry'])) for f in fs if f['properties']['shapeName'] in NAMES])
parts=[]
ghs_path=next((S/'GHSL').glob('GHS_POP*.tif'))
with rasterio.open(ghs_path) as src:
 b=transform_bounds('EPSG:4326',src.crs,*zone.bounds,densify_pts=41)
 w=from_bounds(*b,transform=src.transform).round_offsets().round_lengths()
 a=src.read(1,window=w,masked=True)
 rr,cc=np.nonzero((~np.ma.getmaskarray(a))&np.isfinite(a.data)&(a.data>0))
 x,y=rasterio.transform.xy(src.window_transform(w),rr,cc)
 lon,lat=Transformer.from_crs(src.crs,4326,always_xy=True).transform(x,y)
 use=contains_xy(zone,np.asarray(lon),np.asarray(lat))
 xx,yy=Transformer.from_crs(4326,6933,always_xy=True).transform(np.asarray(lon)[use],np.asarray(lat)[use])
 values=a.data[rr[use],cc[use]].astype(float)
 g=pd.DataFrame({'ix':np.floor(np.asarray(xx)/1000).astype(int),'iy':np.floor(np.asarray(yy)/1000).astype(int),'population':values}).groupby(['ix','iy'],as_index=False).population.sum()
 g['x_center_m']=(g.ix+.5)*1000;g['y_center_m']=(g.iy+.5)*1000
 assert np.isclose(g.population.sum(),values.sum())
 with gzip.open(O/'population_demand_1km_ghspop.csv.gz','wt',encoding='utf-8') as file:
  g.to_csv(file,index=False)
 g5=g.assign(ix=g.ix//5,iy=g.iy//5).groupby(['ix','iy'],as_index=False).population.sum()
 g5['x_center_m']=(g5.ix+.5)*5000;g5['y_center_m']=(g5.iy+.5)*5000
 with gzip.open(O/'population_demand_5km_ghspop.csv.gz','wt',encoding='utf-8') as file:
  g5.to_csv(file,index=False)
wp5=pd.read_csv(O/'population_demand_5km_geoboundaries.csv.gz')
compare=wp5[['ix','iy','population']].rename(columns={'population':'worldpop'}).merge(g5[['ix','iy','population']].rename(columns={'population':'ghspop'}),on=['ix','iy'],how='outer').fillna(0)
with gzip.open(O/'population_product_comparison_5km.csv.gz','wt',encoding='utf-8') as file:
 compare.to_csv(file,index=False)
wp=pd.read_csv(O/'population_demand_1km_geoboundaries.csv.gz')
smod_path=next((S/'GHSL').glob('GHS_SMOD*.tif'))
with rasterio.open(smod_path) as src:
 tr=Transformer.from_crs(6933,src.crs,always_xy=True)
 x,y=tr.transform(wp.x_center_m,wp.y_center_m)
 # Read one region window; vectorized indices avoid per-pixel disk reads.
 b=transform_bounds(4326,src.crs,*zone.bounds,densify_pts=41)
 w=from_bounds(*b,transform=src.transform).round_offsets().round_lengths()
 a=src.read(1,window=w,masked=True)
 rr,cc=rasterio.transform.rowcol(src.window_transform(w),x,y)
 rr=np.asarray(rr);cc=np.asarray(cc);good=(rr>=0)&(rr<a.shape[0])&(cc>=0)&(cc<a.shape[1])
 codes=np.full(len(wp),-999,int);codes[good]=a.filled(-999)[rr[good],cc[good]]
 wp['ghsl_smod_code']=codes
 nodes=pd.read_csv(ROOT/'data/03_resultats/noeuds_urbains_phase3.csv');nodes=nodes[~nodes['name'].isin(['Masina','Bolenge'])].copy()
 x,y=Transformer.from_crs(4326,src.crs,always_xy=True).transform(nodes.longitude,nodes.latitude)
 nodes['ghsl_smod_code']=[int(v[0]) for v in src.sample(zip(x,y))]
 nodes[['node_id','name','ghsl_smod_code']].to_csv(O/'existing_hubs_ghsl_classification.csv',index=False)
wp.groupby('ghsl_smod_code',as_index=False).population.sum().to_csv(O/'worldpop_population_by_ghsl_class.csv',index=False)
meta={'worldpop_total':float(wp.population.sum()),'ghspop_total':float(g.population.sum()),'ghspop_vs_worldpop_pct':float(100*(g.population.sum()/wp.population.sum()-1)),'positive_ghspop_cells_1km':len(g),'positive_ghspop_cells_5km':len(g5),'cell_5km_pearson':float(compare.worldpop.corr(compare.ghspop)),'cell_5km_spearman':float(compare.worldpop.rank().corr(compare.ghspop.rank())),'sum_absolute_cell_difference':float((compare.worldpop-compare.ghspop).abs().sum()),'limits':['both are modelled 2025 population products, not observations','native GHS pixel centres allocated to EPSG6933 bins; grid alignment affects local comparisons','same alternative regional boundary mask with pixel-centre inclusion','GHS SMOD is modelled settlement classification; no functional autonomy inferred']}
(O/'population_product_comparison_metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))

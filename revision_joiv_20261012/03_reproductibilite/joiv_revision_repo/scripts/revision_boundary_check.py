"""Mass-conserving aggregation of WorldPop pixel counts to equal-area grids.

Boundary sensitivity dataset: geoBoundaries ADM1, not original COD-AB.
Pixel-centre inclusion; grids nest at 1 km / 5 km in EPSG:6933.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds, Window
from shapely.geometry import shape
from shapely import union_all, contains_xy, make_valid
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'revision_sources'; OUT=ROOT/'revision_outputs'/'boundary_check';OUT.mkdir(exist_ok=True)
NAMES={'Kinshasa','Kongo-Central','Kwango','Kwilu','Mai-Ndombe','Équateur','Mongala','Nord-Ubangi','Sud-Ubangi','Tshuapa'}
import geopandas as gpd
adm=gpd.read_file(SRC/'COD_AB/cod_admin1.shp')
features=adm[adm.adm1_pcode.isin(['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45'])]
assert len(features)==10
zone=union_all([make_valid(g) for g in features.geometry])
transformer=Transformer.from_crs(4326,6933,always_xy=True)
parts=[]; original=0.; count=0
path=SRC/'cod_pop_2025_CN_100m_R2025A_v1.tif'
with rasterio.open(path) as src:
    assert src.crs.to_epsg()==4326
    win=from_bounds(*zone.bounds,transform=src.transform).round_offsets().round_lengths()
    # Include the boundary margin before exact pixel-centre selection.
    left=max(0,int(win.col_off)-1); top=max(0,int(win.row_off)-1)
    right=min(src.width,int(win.col_off+win.width)+2); bottom=min(src.height,int(win.row_off+win.height)+2)
    for row in range(top,bottom,128):
        w=Window(left,row,right-left,min(128,bottom-row))
        a=src.read(1,window=w,masked=True)
        valid=(~np.ma.getmaskarray(a)) & np.isfinite(a.data) & (a.data>0)
        rr,cc=np.nonzero(valid)
        xs=src.transform.c+(cc+left+.5)*src.transform.a
        ys=src.transform.f+(rr+row+.5)*src.transform.e
        inside=contains_xy(zone,xs,ys)
        values=a.data[rr[inside],cc[inside]].astype(float)
        x,y=transformer.transform(xs[inside],ys[inside])
        frame=pd.DataFrame({'ix':np.floor(np.asarray(x)/1000).astype(int),'iy':np.floor(np.asarray(y)/1000).astype(int),'population':values})
        parts.append(frame.groupby(['ix','iy'],as_index=False).population.sum())
        original+=float(values.sum()); count+=len(values)
grid=pd.concat(parts,ignore_index=True).groupby(['ix','iy'],as_index=False).population.sum()
assert np.isclose(grid.population.sum(),original,rtol=1e-10)
grid['x_center_m']=(grid.ix+.5)*1000; grid['y_center_m']=(grid.iy+.5)*1000
grid.to_csv(OUT/'population_demand_1km_geoboundaries.csv.gz',index=False)
coarse=grid.assign(ix=grid.ix//5,iy=grid.iy//5).groupby(['ix','iy'],as_index=False).population.sum()
assert np.isclose(coarse.population.sum(),original,rtol=1e-10)
coarse['x_center_m']=(coarse.ix+.5)*5000; coarse['y_center_m']=(coarse.iy+.5)*5000
coarse.to_csv(OUT/'population_demand_5km_geoboundaries.csv.gz',index=False)
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
meta={'status':'computed','population_product':'WorldPop 2025 R2025A v1 constrained, alpha','boundary_product':'COD-AB ADM1 v01, valid_on 2019-09-11','boundary_note':'COD-AB boundary sensitivity comparison; not used in road coverage optimization','provinces':sorted(NAMES),'crs':'EPSG:6933','pixel_inclusion':'centre inside union of ten provinces; positive finite pixel counts only','original_selected_pixel_sum':original,'positive_source_pixels':count,'positive_cells_1km':len(grid),'positive_cells_5km':len(coarse),'mass_conservation_relative_error':float(abs(grid.population.sum()-original)/original),'worldpop_sha256':digest(path),'boundary_sha256':digest(SRC/'cod_admin_boundaries.shp.zip')}
(OUT/'population_grid_metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False))
print(json.dumps(meta,indent=2,ensure_ascii=False))

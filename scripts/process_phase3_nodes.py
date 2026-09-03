from pathlib import Path
import pandas as pd, numpy as np, geopandas as gpd
import rasterio
from rasterio.mask import mask
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
cols=['geonameid','name','asciiname','alternatenames','latitude','longitude','feature_class','feature_code','country_code','cc2','admin1_code','admin2_code','admin3_code','admin4_code','population','elevation','dem','timezone','modification_date']
d=pd.read_csv(ROOT/'data/01_brutes/localites/extracted/CD.txt',sep='\t',names=cols,low_memory=False)
pts=gpd.GeoDataFrame(d[d.feature_class.eq('P')].copy(),geometry=gpd.points_from_xy(d[d.feature_class.eq('P')].longitude,d[d.feature_class.eq('P')].latitude),crs=4326)
zone=gpd.read_file(ROOT/'restored/zone_etude.gpkg',layer='provinces')[['adm1_pcode','adm1_name','geometry']]
pts=gpd.sjoin(pts,zone,predicate='within',how='inner').drop(columns='index_right')

# Nœuds initiaux: chefs-lieux administratifs et localités ayant une population GeoNames >= 50 000.
admin_codes={'PPLC','PPLA','PPLA2','PPLA3','PPLA4'}
nodes=pts[pts.feature_code.isin(admin_codes) | (pts.population>=50000)].copy()
capitals={'CD10':'Kinshasa','CD20':'Matadi','CD31':'Kenge','CD32':'Bandundu','CD33':'Inongo','CD41':'Mbandaka','CD42':'Gemena','CD43':'Gbadolite','CD44':'Lisala','CD45':'Boende'}
# Retirer les homonymes qui portent le nom d'un chef-lieu mais se trouvent dans une autre province.
for pc,name in capitals.items(): nodes=nodes[~((nodes.name.str.casefold()==name.casefold())&(nodes.adm1_pcode!=pc))]
extra=[]
for pc,name in capitals.items():
 cand=pts[(pts.adm1_pcode==pc)&(pts.name.str.casefold().str.startswith(name.casefold()))].copy()
 if len(cand):
  cand['p_priority']=cand.feature_code.map({'PPLC':5,'PPLA':4,'PPLA2':3,'PPLA3':2,'PPL':1}).fillna(0)
  extra.append(cand.sort_values(['p_priority','population'],ascending=False).head(1).drop(columns='p_priority'))
if extra: nodes=pd.concat([nodes,*extra],ignore_index=True)
nodes=nodes.sort_values(['adm1_name','population'],ascending=[True,False]).drop_duplicates(subset=['name','adm1_pcode'])

# Estimation comparable: somme WorldPop 2025 dans un rayon de 5 km autour du point.
aea='+proj=aea +lat_1=-18 +lat_2=21 +lat_0=0 +lon_0=25 +datum=WGS84 +units=m +no_defs'
buffers=nodes.to_crs(aea); buffers.geometry=buffers.geometry.buffer(5000); buffers=buffers.to_crs(4326)
vals=[]
with rasterio.open(ROOT/'restored/cod_pop_2025_CN_100m_R2025A_v1.tif') as src:
 for geom in buffers.geometry:
  arr,_=mask(src,[geom],crop=True,filled=False,indexes=1)
  a=arr.compressed(); a=a[np.isfinite(a)&(a>=0)]; vals.append(float(a.sum(dtype=np.float64)))
nodes['population_worldpop_5km_2025']=vals
nodes['population_worldpop_5km_arrondie']=nodes.population_worldpop_5km_2025.round().astype('int64')
nodes['node_id']=['GN'+str(x) for x in nodes.geonameid]
nodes['source']='GeoNames 2026-09-02 + WorldPop 2025 R2025A v1'
keep=['node_id','geonameid','name','feature_code','adm1_pcode','adm1_name','latitude','longitude','population','population_worldpop_5km_2025','population_worldpop_5km_arrondie','modification_date','source','geometry']
nodes[keep].to_file(ROOT/'data/02_traitees/noeuds_urbains_phase3.gpkg',layer='noeuds_urbains',driver='GPKG')
nodes.drop(columns='geometry')[keep[:-1]].to_csv(ROOT/'data/03_resultats/noeuds_urbains_phase3.csv',index=False,encoding='utf-8-sig')

summary=(nodes.groupby('adm1_name').agg(nombre_noeuds=('node_id','count'),population_worldpop_5km=('population_worldpop_5km_2025','sum')).reset_index())
summary.to_csv(ROOT/'data/03_resultats/resume_noeuds_par_province.csv',index=False,encoding='utf-8-sig')

fig,ax=plt.subplots(figsize=(10,10)); zone.plot(ax=ax,color='#E8EEF5',edgecolor='#555',linewidth=.7)
sizes=np.clip(np.sqrt(nodes.population_worldpop_5km_2025.clip(lower=1))/3,8,220)
nodes.plot(ax=ax,color='#B32025',edgecolor='white',linewidth=.4,markersize=sizes,alpha=.78)
top=nodes.sort_values('population_worldpop_5km_2025',ascending=False).head(25)
for _,r in top.iterrows(): ax.annotate(r['name'],(r.geometry.x,r.geometry.y),xytext=(3,3),textcoords='offset points',fontsize=6)
ax.set_title(f'Nœuds urbains initiaux ({len(nodes)}) et population WorldPop à 5 km',fontsize=14,fontweight='bold'); ax.set_axis_off(); fig.tight_layout(); fig.savefig(ROOT/'data/03_resultats/noeuds_urbains_phase3.png',dpi=220,bbox_inches='tight'); plt.close(fig)
print(f'localites_zone={len(pts)} noeuds_retenus={len(nodes)}')
print(nodes[['name','adm1_name','feature_code','population','population_worldpop_5km_arrondie']].sort_values('population_worldpop_5km_arrondie',ascending=False).head(40).to_string(index=False))

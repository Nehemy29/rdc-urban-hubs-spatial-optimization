from pathlib import Path
import geopandas as gpd,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent;P=B.parent
roads=gpd.read_file(next((P/'evidence_extension/sources/roads').rglob('*.gpkg')),bbox=(15,-5.3,19.3,-3.0));roads=roads[roads.highway.isin(['trunk','primary','secondary','tertiary'])]
fig,ax=plt.subplots(figsize=(3.36,3.1));roads.plot(ax=ax,color='#bbbbbb',linewidth=.5)
for label,c in [('main','#b5352c'),('main_with_mapped_ferry','#164775')]:
 p=gpd.read_file(B/'results'/f'Kinshasa_Bandundu_{label}.gpkg');p.plot(ax=ax,color=c,linewidth=1.5,label='Roads only' if label=='main' else 'With ferry (assumed usable)')
h=pd.read_csv(P/'joiv_revision_repo/data/03_resultats/noeuds_urbains_phase3.csv')
for name in ['Kinshasa','Bandundu Province','Kenge','Kikwit']:
 x=h[h.name==name].iloc[0];ax.scatter(x.longitude,x.latitude,s=20,color='black');ax.annotate('Bandundu' if name=='Bandundu Province' else name,(x.longitude,x.latitude),xytext=(4,4),textcoords='offset points',fontsize=6)
ax.set_xlabel('Longitude (degrees)',fontsize=7);ax.set_ylabel('Latitude (degrees)',fontsize=7);ax.set_xlim(15,19.3);ax.set_ylim(-5.3,-3);ax.legend(frameon=False,fontsize=6,loc='upper left');ax.tick_params(labelsize=6);ax.grid(alpha=.15);fig.tight_layout();fig.savefig(B/'results/calculated_paths_bandundu.png',dpi=300)

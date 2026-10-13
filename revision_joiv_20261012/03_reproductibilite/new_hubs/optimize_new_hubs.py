"""Conditional new-centre location allocation with all existing hubs retained.

No preference weights or expert answers are invented. Exact optimality is
conditional on a coarse, screened candidate set and a geometric network.
"""
from pathlib import Path
import ast,json,time,hashlib,argparse
import numpy as np,pandas as pd,geopandas as gpd
from pyproj import Geod,Transformer
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,hstack,vstack,eye
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import milp,Bounds,LinearConstraint

parser=argparse.ArgumentParser();parser.add_argument('--grid-km',type=int,choices=[10,25],default=25);args=parser.parse_args();grid=args.grid_km
B=Path(__file__).resolve().parent; P=B.parent; R=P/'joiv_revision_repo'; O=B/('results' if grid==25 else 'results/grid10'); O.mkdir(exist_ok=True,parents=True)
geod=Geod(ellps='WGS84')
s=ast.parse((R/'scripts/revision_road_accessibility.py').read_text())
exec(compile(ast.Module(body=[x for x in s.body if isinstance(x,ast.FunctionDef) and x.name in ['graph','xyz']],type_ignores=[]),'audited_geometry','exec'))
c=pd.read_csv(R/'revision_outputs/candidate_grid_comparison.csv')
c=c[c.grid_km.eq(grid)&c.worldcover_code.isin([20,30,40,60])&~c.protected_cell_intersection&~c.point_buffer_cell_intersection].copy().reset_index(drop=True)
assert len(c)==(241 if grid==25 else 1583) and c.d_hub_m.min()>=40000
h=pd.read_csv(R/'data/03_resultats/noeuds_urbains_phase3.csv'); h=h[~h.name.isin(['Masina','Bolenge'])].reset_index(drop=True)
datasets=[]
for product,suffix in [('WorldPop','geoboundaries'),('GHSPOP','ghspop')]:
    z=pd.read_csv(R/'revision_outputs'/f'population_demand_5km_{suffix}.csv.gz'); z['product']=product; datasets.append(z)
a=pd.concat(datasets,ignore_index=True); u=a[['x_center_m','y_center_m']].drop_duplicates().reset_index(drop=True)
# Province labels are diagnostic centre assignments, not source-pixel totals.
adm=gpd.read_file(P/'evidence_extension/sources/geoBoundaries-COD-ADM1.geojson').to_crs(6933)
pts=gpd.GeoDataFrame(u.copy(),geometry=gpd.points_from_xy(u.x_center_m,u.y_center_m),crs=6933)
joins=gpd.sjoin(pts,adm[['shapeName','geometry']],predicate='within',how='left')
assert joins.index.is_unique
u['province']=joins.shapeName.reindex(u.index).fillna('Unassigned cell centre')
a['idx']=pd.MultiIndex.from_frame(u[['x_center_m','y_center_m']]).get_indexer(pd.MultiIndex.from_frame(a[['x_center_m','y_center_m']]))
a['province']=u.province.to_numpy()[a.idx.to_numpy()]
dlon,dlat=Transformer.from_crs(6933,4326,always_xy=True).transform(u.x_center_m,u.y_center_m)
codes=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
roads=gpd.read_file(next((P/'evidence_extension/sources/roads').rglob('*.gpkg')),where='adm1_pcode IN ('+','.join("'"+x+"'" for x in codes)+')',columns=['id','highway','oneway','bridge','layer'])
roads=roads[roads.geometry.notna()&~roads.geometry.is_empty]
base={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}

def solve(cov,w,q):
    # Collapse demand with identical full candidate incidence; no 26-bit limit.
    bits=np.packbits(cov.T,axis=1,bitorder='little')
    pat,inv=np.unique(bits,axis=0,return_inverse=True)
    mass=np.bincount(inv,weights=w)
    inc=csr_matrix(np.unpackbits(pat,axis=1,bitorder='little')[:,:cov.shape[0]],dtype=float)
    k=cov.shape[0]; n=len(mass)
    A=vstack([hstack([-inc,eye(n,format='csr')]),hstack([csr_matrix(np.ones((1,k))),csr_matrix((1,n))])],format='csr')
    res=milp(c=np.r_[np.zeros(k),-mass],integrality=np.r_[np.ones(k),np.zeros(n)],bounds=Bounds(0,1),constraints=LinearConstraint(A,np.r_[np.full(n,-np.inf),q],np.r_[np.zeros(n),q]),options={'time_limit':180,'mip_rel_gap':1e-8})
    if res.x is None: raise RuntimeError(res.message)
    sel=np.flatnonzero(res.x[:k]>.5); value=float(w[cov[sel].any(axis=0)].sum())
    assert len(sel)==q and np.isclose(value,-res.fun,rtol=1e-7)
    return value,sel,int(res.status),float(res.mip_gap),len(mass)

rows=[]; selected=[]; provinces=[]; attachments=[]
for tracks in [False,True]:
    started=time.time(); G,xy=graph(roads[roads.highway.isin(base|({'track'} if tracks else set()))]); rev=G.T.tocsr(); tree=cKDTree(xyz(xy[:,0],xy[:,1]))
    _,di=tree.query(xyz(dlon,dlat)); doff=geod.inv(dlon,dlat,xy[di,0],xy[di,1])[2]/1000
    centres=pd.concat([h[['longitude','latitude']],c[['longitude','latitude']]],ignore_index=True)
    _,si=tree.query(xyz(centres.longitude.to_numpy(),centres.latitude.to_numpy()))
    soff=geod.inv(centres.longitude.to_numpy(),centres.latitude.to_numpy(),xy[si,0],xy[si,1])[2]/1000
    cov=np.zeros((len(centres),len(u)),dtype=bool)
    for j,idx in enumerate(si):
        if soff[j]<=5:
            dist=dijkstra(rev,directed=True,indices=int(idx),limit=100)
            cov[j]=(dist[di]+doff+soff[j]<=100)&(doff<=5)
        if j%40==0: print('routing',tracks,j,len(centres),'seconds',round(time.time()-started),flush=True)
    attach=c.copy();attach['tracks']=tracks;attach['network_connector_km']=soff[26:];attach['connector_eligible']=soff[26:]<=5;attachments.append(attach)
    np.savez_compressed(O/f'coverage_tracks_{tracks}.npz',coverage=cov,demand_x=u.x_center_m.to_numpy(),demand_y=u.y_center_m.to_numpy(),site_connector_km=soff,demand_connector_km=doff)
    for prod,d in a.groupby('product'):
        ids=d.idx.to_numpy();w=d.population.to_numpy();old=cov[:26,ids].any(axis=0); baseline=float(w[old].sum());total=float(w.sum())
        for condition in ['screened','water_proximity_15km']:
            eligible=(soff[26:]<=5)&(c.d_water_m.to_numpy()<=15000 if condition!='screened' else True)
            candidates=np.flatnonzero(eligible)
            for q in ([3,5,10] if condition=='screened' and grid==25 else [5]):
                cc=cov[26+candidates][:,ids][:,~old];ww=w[~old]
                value,sel,status,gap,patterns=solve(cc,ww,q);chosen=candidates[sel];new=old|cov[26+chosen][:,ids].any(axis=0)
                covered=float(w[new].sum());assert np.isclose(covered,baseline+value)
                tag={'grid_km':grid,'tracks':tracks,'product':prod,'condition':condition,'new_hubs':q}
                row={**tag,'candidate_count':len(candidates),'population_total':total,'baseline_26_existing_pct':100*baseline/total,'with_new_hubs_pct':100*covered/total,'gain_pp':100*value/total,'additional_population':value,'solver_status':status,'mip_gap':gap,'patterns':patterns};rows.append(row);print(row,flush=True)
                for k in chosen:
                    rec=c.iloc[k].to_dict();rec.update(tag);rec['network_connector_km']=soff[26+k];selected.append(rec)
                for prov,g in d.groupby('province'):
                    positions=d.index.get_indexer(g.index); pop=g.population.to_numpy();pvtotal=pop.sum()
                    provinces.append({**tag,'province':prov,'population_total':pvtotal,'baseline_pct':100*pop[old[positions]].sum()/pvtotal,'with_new_pct':100*pop[new[positions]].sum()/pvtotal})
                pd.DataFrame(rows).to_csv(O/'new_hub_scenarios.csv',index=False);pd.DataFrame(selected).to_csv(O/'new_hub_selections.csv',index=False);pd.DataFrame(provinces).to_csv(O/'new_hub_province_coverage.csv',index=False)
    del G,rev,xy,tree,cov
pd.concat(attachments).to_csv(O/'candidate_attachments.csv',index=False)
assert len(rows)==(16 if grid==25 else 8) and all(x['solver_status']==0 and x['mip_gap']<=1e-8 for x in rows)
(O/'metadata.json').write_text(json.dumps({'runs':len(rows),'candidate_grid_km':grid,'initial_candidates':len(c),'demand_grid_km':5,'threshold_km':100,'connectors_km':5,'existing_hubs_fixed':26,'mode':'roads only with or without tracks; ferry omitted in this design for matched baseline','objective':'maximise additional modelled population covered beyond all 26 existing hubs','assumptions':['all 26 mapped existing hubs treated as available services','new centre assumed to offer same service without capacity limits','straight connector is an assumed off-network distance, not an observed road','no new roads designed','candidate centres >=40km from mapped existing hubs','strict full-cell protected-area mask and point-sampled land-cover exclusion','one optimum only; location identity may not be unique'],'autonomy':'water proximity is one necessary-resource proxy only; not water quality, energy, local transformation, jobs or measured independence','limits':['no empirical household access validation','no cadastral, slope, finance, hazard or displacement clearance','25km sampling omits Equateur and either grid may miss useful sites','WorldPop and GHSL are modelled population products','no inference that selected centres are buildable sovereign cities'],'candidate_source_sha256':hashlib.sha256((R/'revision_outputs/candidate_grid_comparison.csv').read_bytes()).hexdigest()},indent=2))

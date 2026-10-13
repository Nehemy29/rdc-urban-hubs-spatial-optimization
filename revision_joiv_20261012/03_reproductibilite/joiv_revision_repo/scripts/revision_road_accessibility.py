"""Geometry-based road access audit; no synthetic links between road components.

Uses a new HOT/OSM snapshot, the alternative regional population grid, and
released urban nodes. It is NOT an operational routing/traffic model.
"""
from pathlib import Path
import json, hashlib, gzip, os
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Geod, Transformer
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'revision_sources'; OUT=ROOT/'revision_outputs'
CODES=['CD10','CD20','CD31','CD32','CD33','CD41','CD42','CD43','CD44','CD45']
BASE={'trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street','road'}
roads=gpd.read_file(SRC/'roads/roads.gpkg',engine='pyogrio',where='adm1_pcode IN ('+','.join("'"+c+"'" for c in CODES)+')',columns=['id','highway','oneway','bridge','layer','adm1_pcode'])
roads=roads[roads.geometry.notna() & ~roads.geometry.is_empty].copy()
inventory=roads.groupby(['adm1_pcode','highway']).size().reset_index(name='feature_count')
inventory.to_csv(OUT/'road_class_inventory_20261005.csv',index=False)
nodes=pd.read_csv(ROOT/'data/03_resultats/noeuds_urbains_phase3.csv')
nodes=nodes[~nodes['name'].isin(['Masina','Bolenge'])].reset_index(drop=True)
demand=pd.read_csv(OUT/'population_demand_1km_geoboundaries.csv.gz')
lon,lat=Transformer.from_crs(6933,4326,always_xy=True).transform(demand.x_center_m,demand.y_center_m)
geod=Geod(ellps='WGS84')
def xyz(lon,lat):
    a,b=np.deg2rad(lon),np.deg2rad(lat)
    return np.column_stack([np.cos(b)*np.cos(a),np.cos(b)*np.sin(a),np.sin(b)])
def graph(frame):
    # Each original OSM vertex is used. Only exactly equal coordinates connect.
    # Interior layer keys protect tagged crossings; endpoints permit transitions.
    coords=[]; us=[]; vs=[]; modes=[]; offset=0
    for row in frame.itertuples():
        if row.geometry.geom_type=='LineString': lines=[row.geometry]
        elif row.geometry.geom_type=='MultiLineString': lines=list(row.geometry.geoms)
        else: continue
        try: level=float(row.layer) if pd.notna(row.layer) else (1. if str(row.bridge).lower() in {'yes','true','1'} else 0.)
        except (ValueError,TypeError): level=0.
        if not np.isfinite(level):level=0.
        for line in lines:
            a=np.asarray(line.coords)[:,:2]; n=len(a)
            if n<2:continue
            l=np.full(n,level);l[0]=l[-1]=0
            coords.append(np.column_stack([a,l]));us.extend(range(offset,offset+n-1));vs.extend(range(offset+1,offset+n))
            modes.extend([str(row.oneway).lower()]*(n-1));offset+=n
    allcoords=np.concatenate(coords)
    unique,inverse=np.unique(allcoords,axis=0,return_inverse=True)
    u=inverse[np.asarray(us)]; v=inverse[np.asarray(vs)]
    length=geod.inv(unique[u,0],unique[u,1],unique[v,0],unique[v,1])[2]/1000
    mode=np.asarray(modes); positive=(length>0)&(u!=v)
    forward=positive&(mode!='-1');reverse=positive&~np.isin(mode,['yes','true','1'])
    rows=np.r_[u[forward],v[reverse]];cols=np.r_[v[forward],u[reverse]];weights=np.r_[length[forward],length[reverse]]
    n=len(unique); keys=rows.astype(np.int64)*n+cols
    order=np.argsort(keys);keys=keys[order];weights=weights[order]
    start=np.r_[0,np.flatnonzero(keys[1:]!=keys[:-1])+1]
    keys=keys[start];weights=np.minimum.reduceat(weights,start)
    G=csr_matrix((weights,(keys//n,keys%n)),shape=(n,n))
    return G,unique

summary=[];meta=[]
for label,classes in [('road_classes',BASE),('including_tracks',BASE|{'track'})]:
    frame=roads[roads.highway.isin(classes)].copy()
    G,coords=graph(frame);n=len(coords)
    component_count,components=connected_components(G,directed=True,connection='weak')
    tree=cKDTree(xyz(coords[:,0],coords[:,1]))
    _,hub_idx=tree.query(xyz(nodes.longitude.to_numpy(),nodes.latitude.to_numpy()))
    hub_offsets=geod.inv(nodes.longitude.to_numpy(),nodes.latitude.to_numpy(),coords[hub_idx,0],coords[hub_idx,1])[2]/1000
    _,demand_idx=tree.query(xyz(np.asarray(lon),np.asarray(lat)))
    demand_offsets=geod.inv(lon,lat,coords[demand_idx,0],coords[demand_idx,1])[2]/1000
    for max_snap in [1.,2.5,5.]:
        eligible=hub_offsets<=max_snap
        # Reverse edges: distance from an origin TO a hub. Virtual source gives
        # terminal offset costs, avoiding biases from different hub offsets.
        rg=G.transpose().tocoo()
        augmented=csr_matrix((np.r_[rg.data,hub_offsets[eligible]],(np.r_[rg.row,np.full(eligible.sum(),n)],np.r_[rg.col,hub_idx[eligible]])),shape=(n+1,n+1))
        distances=dijkstra(augmented,directed=True,indices=n)
        attached=demand_offsets<=max_snap
        reachable=attached & np.isfinite(distances[demand_idx])
        total=distances[demand_idx]+demand_offsets
        w=demand.population.to_numpy(); denominator=w.sum()
        row=dict(scenario=label,max_connector_km=max_snap,road_features=len(frame),graph_vertices=n,directed_arcs=G.nnz,weak_components=component_count,eligible_hubs=int(eligible.sum()),population_total=denominator,population_attached_pct=100*w[attached].sum()/denominator,population_reachable_pct=100*w[reachable].sum()/denominator,population_attached_no_hub_path_pct=100*w[attached & ~reachable].sum()/denominator,population_unattached_pct=100*w[~attached].sum()/denominator,reachable_population_mean_distance_km=float(np.average(total[reachable],weights=w[reachable])) if reachable.any() else None,population_within100km_pct=100*w[reachable & (total<=100)].sum()/denominator)
        assert abs(row['population_reachable_pct']+row['population_attached_no_hub_path_pct']+row['population_unattached_pct']-100)<1e-6
        summary.append(row); print(json.dumps(row),flush=True)
        detail=demand[['ix','iy','population']].copy();detail['connector_to_vertex_km']=demand_offsets;detail['attached']=attached;detail['hub_path_exists']=reachable;detail['model_distance_to_any_existing_hub_km']=np.where(reachable,total,np.nan)
        export_bytes=gzip.compress(detail.to_csv(index=False).encode(),mtime=0)
        with (OUT/f'road_demand_{label}_snap{max_snap:g}km.csv.gz').open('wb') as output_file:
            output_file.write(export_bytes);output_file.flush();os.fsync(output_file.fileno())
    hub_table=nodes[['node_id','name']].copy();hub_table['nearest_vertex_offset_km']=hub_offsets;hub_table['weak_component']=components[hub_idx];hub_table.to_csv(OUT/f'road_hub_attachment_{label}.csv',index=False)
    meta.append({'scenario':label,'classes':sorted(classes),'oneway_nonempty_features':int(frame.oneway.notna().sum()),'oneway_yes_features':int(frame.oneway.eq('yes').sum()),'layer_nonempty_features':int(frame.layer.notna().sum()),'bridge_nonempty_features':int(frame.bridge.notna().sum()),'weak_component_sizes_top10':np.sort(np.bincount(components))[-10:][::-1].tolist()})
pd.DataFrame(summary).to_csv(OUT/'road_accessibility_summary.csv',index=False)
(OUT/'road_accessibility_metadata.json').write_text(json.dumps({'snapshot':'2026-10-05','source':'HOT/OSM HDX roads.gpkg','population_mask':'geoBoundaries alternative','lengths':'WGS84 ellipsoidal geodesic, km','junctions':'exact shared source coordinates; interior layer key; endpoints level 0; no spatial snapping between roads','direction':'oneway yes/true/1 forward, -1 reverse; all other values assumed bidirectional, including missing/reversible','limits':['no turn restrictions or access tags','vertex attachment rather than nearest segment','off-network straight connectors are hypothetical, not observed traversability','missing layer/bridge tags may cause incorrect junctions','roads selected by ten provincial pcodes; outside-province detours omitted','no rail/fluvial routing or navigability validation','26 hubs are existing urban nodes; this is not a new-hub optimization'], 'scenarios':meta},indent=2))

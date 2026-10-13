"""Recover 2.5-km detail from the verified 5-km run with identical 26 hub eligibility.
No routing values are imputed; only the tighter connector mask is applied.
"""
from pathlib import Path
import pandas as pd,numpy as np,gzip,os
R=Path(__file__).resolve().parents[1];O=R/'revision_outputs'
hubs=pd.read_csv(O/'road_hub_attachment_road_classes.csv')
assert (hubs.nearest_vertex_offset_km<=2.5).all(), 'Identical eligible hub set is required'
a=pd.read_csv(O/'road_demand_road_classes_snap5km.csv.gz')
a['attached']=a.connector_to_vertex_km<=2.5
a['hub_path_exists']=a.attached&a.hub_path_exists
a.loc[~a.hub_path_exists,'model_distance_to_any_existing_hub_km']=np.nan
s=pd.read_csv(O/'road_accessibility_summary.csv');s=s[(s.scenario=='road_classes')&(s.max_connector_km==2.5)].iloc[0]
w=a.population;reachable=a.hub_path_exists
assert np.isclose(100*w[reachable].sum()/w.sum(),s.population_reachable_pct)
assert np.isclose(100*w[reachable&a.model_distance_to_any_existing_hub_km.le(100)].sum()/w.sum(),s.population_within100km_pct)
assert np.isclose(np.average(a.loc[reachable,'model_distance_to_any_existing_hub_km'],weights=w[reachable]),s.reachable_population_mean_distance_km)
b=gzip.compress(a.to_csv(index=False).encode(),mtime=0)
p=O/'road_demand_road_classes_snap2.5km.csv.gz'
with p.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
assert len(pd.read_csv(p))==219279
print('Re-export verified against computed summary; no route imputation',len(b),'bytes')

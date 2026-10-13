from pathlib import Path
import json
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'revision_outputs'
d=pd.read_csv(R/'data/02_traitees/echantillons_environnement_phase9.csv')
d=d[d.occupation_compatible_preliminaire & d.relief_compatible_preliminaire.fillna(False) & d.pente_locale_pct.le(8)].copy().reset_index(drop=True)
d['score_pente']=np.exp(-d.pente_locale_pct/5)
cols=['score_population','score_route','score_eau','score_rail','score_air','score_lacune_territoriale','score_pente']
X=d[cols].to_numpy();assert np.isfinite(X).all() and len(d)==75
rows=[]
for name,weights in [('reference',np.array([.24,.20,.16,.08,.04,.08,.20])),('uniform',np.ones(7)/7)]:
 rng=np.random.default_rng(20260902);mc=rng.dirichlet(weights*60,size=5000)
 scores=X@mc.T;nominal=X@weights
 for province in sorted(d.adm1_name.unique()):
  idx=np.flatnonzero(d.adm1_name.eq(province));wins=idx[np.argmax(scores[idx],axis=0)]
  counts=np.bincount(wins,minlength=len(d));dominant=idx[np.argmax(counts[idx])];best=idx[np.argmax(nominal[idx])]
  rows.append(dict(province=province,weights=name,nominal_candidate=d.iloc[best].candidate_id,nominal_locality=d.iloc[best].localite_geonames_proche,dominant_candidate=d.iloc[dominant].candidate_id,dominant_locality=d.iloc[dominant].localite_geonames_proche,dominant_frequency_pct=counts[dominant]/50,candidate_count=len(idx)))
pd.DataFrame(rows).to_csv(O/'candidate_reference_uniform_weights.csv',index=False)
meta={'candidate_count':len(d),'models':['reference seven criteria','uniform seven criteria'],'dirichlet_concentration':60,'simulations_per_model':5000,'seed':20260902,'limits':['only 75 previously sampled and filtered sites, not all eligible regional land','one winner per province; no across-province separation constraint','weights are assumed, not elicited expert judgments','weight-only frequencies are conditional, not probabilities of feasibility','protected areas, tenure and infrastructure capacity unverified']}
(O/'candidate_weight_audit_metadata.json').write_text(json.dumps(meta,indent=2))
print(pd.DataFrame(rows).to_string(index=False))

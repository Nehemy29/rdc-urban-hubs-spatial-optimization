from pathlib import Path
import tempfile,importlib.util
import pandas as pd,numpy as np
b=Path(__file__).parent;s=importlib.util.spec_from_file_location('expert',b/'expert_kit/analyser_consultation.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as t:
 p=Path(t);source=b/'expert_kit/candidats_10_25km.csv'
 # Explicitly synthetic software verification only; temporary inputs are not consultation records.
 columns=['expert_id','date','profil','consentement','definitions_acceptees']+m.CRITERES
 d=pd.DataFrame([['TEST_A','2026-10-08','TEST','oui','oui',100,0,0,0,0,0],['TEST_B','2026-10-08','TEST','oui','oui',0,100,0,0,0,0]],columns=columns);d.to_csv(p/'test.csv',index=False)
 m.analyser(p/'test.csv',source,p/'ok');v=pd.read_csv(p/'ok/poids_experts.csv');assert np.allclose(v.moyenne,[.5,.5,0,0,0,0]);r=pd.read_csv(p/'ok/classements_conditionnels.csv');assert r.ponderation.nunique()==8
 for variant in ['bad_sum','duplicate','missing','no_consent']:
  z=d.copy()
  if variant=='bad_sum':z.loc[0,'population']=99
  if variant=='duplicate':z.loc[1,'expert_id']='TEST_A'
  if variant=='missing':z.loc[0,'route']=np.nan
  if variant=='no_consent':z.loc[0,'consentement']='non'
  z.to_csv(p/'test.csv',index=False)
  try:m.analyser(p/'test.csv',source,p/variant)
  except ValueError:pass
  else:raise AssertionError(variant)
print('Temporary synthetic software checks passed; no test consultation data retained.')

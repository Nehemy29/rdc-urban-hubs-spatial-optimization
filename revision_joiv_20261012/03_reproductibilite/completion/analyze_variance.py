from pathlib import Path
import itertools,json,hashlib
import numpy as np,pandas as pd
out=Path(__file__).resolve().parent/'results';out.mkdir(exist_ok=True)
source=Path(__file__).resolve().parents[1]/'joiv_revision_repo/revision_outputs/joint_maximal_coverage_results.csv'
d=pd.read_csv(source)
factors=['product','resolution_km','tracks','connector_km','removal_fraction','jitter_km']
rows=[];checks=[]
for p,g in d.groupby('p'):
 g=g.copy(); y=g.coverage_pct; total=float(np.var(y,ddof=0));components={frozenset():0.0}
 assert len(g)==96 and not g.duplicated(factors).any()
 assert len(g)==np.prod([g[x].nunique() for x in factors])
 for size in range(1,len(factors)+1):
  for sub in itertools.combinations(factors,size):
   key=frozenset(sub)
   conditional=g.groupby(list(sub),observed=True).coverage_pct.mean()
   v=float(np.var(conditional,ddof=0))-sum(val for k,val in components.items() if k<key)
   assert v>=-1e-9
   v=max(0.0,v);components[key]=v
 for f in factors:
  rows.append({'p':int(p),'factor':f,'first_order_share_pct':100*components[frozenset([f])]/total,'total_effect_share_pct':100*sum(v for k,v in components.items() if f in k)/total,'variance_coverage_pp2':total})
 checks.append({'p':int(p),'n':len(g),'total_variance_pp2':total,'component_sum_pp2':sum(components.values()),'main_effect_share_pct':100*sum(v for k,v in components.items() if len(k)==1)/total,'interaction_share_pct':100*sum(v for k,v in components.items() if len(k)>1)/total})
 assert np.isclose(sum(components.values()),total)
 pd.DataFrame([{'factors':' × '.join(sorted(k)),'order':len(k),'variance_pp2':v,'share_pct':100*v/total} for k,v in components.items() if k]).to_csv(out/f'variance_components_p{p}.csv',index=False)
pd.DataFrame(rows).to_csv(out/'variance_factor_indices.csv',index=False)
(out/'variance_metadata.json').write_text(json.dumps({'method':'Exact functional ANOVA of complete categorical factorial table; independent uniform mass on the enumerated levels, separately for p=5,10,15','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'factors':factors,'checks':checks,'limits':['Scenario variance, not calibrated uncertainty or confidence intervals','Deletion and displacement each have one fixed realization per factorial level','Not a continuous-parameter Monte Carlo Sobol estimator','Speed uncertainty, road additions and environmental grid factors are outside this covering experiment','Total-effect shares overlap through interactions and must not be summed']},indent=2))
print(pd.DataFrame(rows).query('p==10').to_string(index=False));print(checks)

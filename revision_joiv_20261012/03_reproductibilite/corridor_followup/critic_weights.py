from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
B=Path(__file__).resolve().parent;source=B.parent/'joiv_revision_repo/revision_outputs/candidate_grid_comparison.csv';d=pd.read_csv(source)
cols=['score_population','score_road','score_water','score_rail','score_air','score_gap'];weights=[];ranks=[];compare=[]
for res in [10,25]:
 q=d[d.grid_km.eq(res)&d.worldcover_code.isin([20,30,40,60])&~d.protected_cell_intersection&~d.point_buffer_cell_intersection].copy();x=q[cols].to_numpy(float);assert np.isfinite(x).all()
 std=x.std(axis=0,ddof=0);corr=np.corrcoef(x,rowvar=False);assert np.isfinite(corr).all();info=std*np.sum(1-corr,axis=1);w=info/info.sum();assert np.all(w>=0) and np.isclose(w.sum(),1)
 for c,s,v,a in zip(cols,std,info,w):weights.append({'grid_km':res,'candidate_count':len(q),'criterion':c,'std':s,'information':v,'critic_weight':a})
 pd.DataFrame(corr,index=cols,columns=cols).to_csv(B/'results'/f'critic_correlations_{res}km.csv')
 frames=[]
 for label,v in [('CRITIC',w),('reference_assumed',np.array([.3,.25,.2,.1,.05,.1])),('uniform',np.ones(6)/6)]:
  z=q[['candidate_id','province','longitude','latitude']].copy();z['score']=x@v;z['rank_province']=z.groupby('province').score.rank(ascending=False,method='min');z['method']=label;z['grid_km']=res;frames.append(z);ranks.append(z)
 for name,g in pd.concat(frames).groupby('province'):
  winners={m:sorted(z[z.rank_province==1].candidate_id.tolist()) for m,z in g.groupby('method')};compare.append({'grid_km':res,'province':name,'critic_winners':';'.join(winners['CRITIC']),'reference_winners':';'.join(winners['reference_assumed']),'uniform_winners':';'.join(winners['uniform']),'same_as_reference':winners['CRITIC']==winners['reference_assumed'],'same_as_uniform':winners['CRITIC']==winners['uniform']})
pd.DataFrame(weights).to_csv(B/'results/critic_weights.csv',index=False);pd.concat(ranks).to_csv(B/'results/critic_candidate_rankings.csv',index=False);pd.DataFrame(compare).to_csv(B/'results/critic_winner_comparison.csv',index=False)
(B/'results/critic_metadata.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'definition':'c_j=sigma_j sum_k(1-r_jk); w_j=c_j/sum_l c_l','score_scaling':'Retain existing common 0–1 transformations and limits; no grid-specific rescaling','std_ddof':0,'candidate_sampling':'Equal weight per admitted candidate centre, separately at 10/25 km','limitations':['Data-driven contrast/correlation weights, not expert judgments or normative priorities','Candidate density and masks influence weights','Original 30/25/20/10/5/10 vector remains unelicited','No empirical mobility validation or greenfield recommendation','Does not alter main population-covering objective']},indent=2))
print(pd.DataFrame(weights)[['grid_km','criterion','critic_weight']].to_string(index=False));print(pd.DataFrame(compare).groupby('grid_km')[['same_as_reference','same_as_uniform']].agg(['sum','count']).to_string())

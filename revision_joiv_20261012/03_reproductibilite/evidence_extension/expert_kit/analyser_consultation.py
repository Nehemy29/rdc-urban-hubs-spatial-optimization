"""Analyse des réponses réelles au formulaire de pondération, sans données simulées."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
CRITERES=['population','route','eau','rail','air','lacune']
SCORES=['score_population','score_road','score_water','score_rail','score_air','score_gap']
def analyser(reponses,candidats,out):
 out.mkdir(parents=True,exist_ok=True)
 d=pd.read_csv(reponses,dtype={'expert_id':str,'consentement':str,'definitions_acceptees':str}).dropna(how='all')
 requis=['expert_id','date','profil','consentement','definitions_acceptees']+CRITERES
 if any(c not in d for c in requis):raise ValueError('Colonnes requises : '+', '.join(requis))
 if d.empty:
  (out/'statut.json').write_text(json.dumps({'statut':'en_attente_de_reponses_reelles','nombre_experts':0},ensure_ascii=False,indent=2),encoding='utf-8');print('Aucune réponse. Aucun poids ni classement expert produit.');return
 if d[requis].isna().any().any() or d[requis].astype(str).apply(lambda c:c.str.strip().eq('')).any().any():raise ValueError('Réponse incomplète. Compléter ou retirer la ligne, sans inventer de valeur.')
 if d.expert_id.duplicated().any():raise ValueError('Un identifiant doit représenter une seule personne pour cette ronde.')
 pd.to_datetime(d.date,format='%Y-%m-%d',errors='raise')
 for c in ['consentement','definitions_acceptees']:
  if not d[c].str.strip().str.lower().eq('oui').all():raise ValueError('Consentement et acceptation des définitions requis. Conserver les exclusions dans un journal séparé.')
 x=d[CRITERES].apply(pd.to_numeric,errors='raise').to_numpy(float)
 if not np.isfinite(x).all() or (x<0).any() or (x>100).any() or not np.allclose(x.sum(axis=1),100,atol=1e-6,rtol=0):raise ValueError('Attribuer 100 points exactement, valeurs finies entre 0 et 100.')
 w=x/100;mean=w.mean(axis=0);median=np.median(w,axis=0);median_defined=median.sum()>0;median=median/median.sum() if median_defined else np.full(6,np.nan)
 stats=pd.DataFrame({'critere':CRITERES,'moyenne':mean,'mediane_normalisee':median,'q25':np.quantile(w,.25,axis=0),'q75':np.quantile(w,.75,axis=0),'ecart_type':np.std(w,axis=0,ddof=1) if len(w)>1 else np.nan})
 stats.to_csv(out/'poids_experts.csv',index=False,encoding='utf-8-sig')
 c=pd.read_csv(candidats);keep=c.grid_km.eq(10)&c.worldcover_code.isin([20,30,40,60])
 for col in ['protected_cell_intersection','point_buffer_cell_intersection']:
  protected=c[col].astype(str).str.lower().map({'true':True,'false':False,'1':True,'0':False})
  if protected.isna().any():raise ValueError('Masque de protection indéterminé.')
  keep &= ~protected
 c=c[keep].copy();a=c[SCORES].to_numpy(float)
 if not np.isfinite(a).all() or c.candidate_id.duplicated().any():raise ValueError('Scores non finis ou candidats dupliqués.')
 rows=[]
 vectors=[('moyenne_panel',mean),('reference_non_elicitee',np.array([.30,.25,.20,.10,.05,.10])),('uniforme',np.ones(6)/6)]
 if median_defined:vectors.append(('mediane_panel',median))
 vectors.extend((str(i),v) for i,v in zip(d.expert_id,w))
 if len(w)>1:vectors.extend((f'sans_expert_{eid}',np.delete(w,k,axis=0).mean(axis=0)) for k,eid in enumerate(d.expert_id))
 for label,v in vectors:
  z=c[['candidate_id','province','longitude','latitude']].copy();z['score']=a@v;z['rang_province']=z.groupby('province').score.rank(ascending=False,method='min');z['ponderation']=label;rows.append(z)
 pd.concat(rows,ignore_index=True).to_csv(out/'classements_conditionnels.csv',index=False,encoding='utf-8-sig')
 (out/'statut.json').write_text(json.dumps({'statut':'reponses_analysees','nombre_experts':len(d),'mediane_normalisee_definie':bool(median_defined),'candidats':len(c),'agregation':'moyenne de points normalisés; médiane normalisée en sensibilité','limites':['Panel raisonné non représentatif statistiquement','Poids de préférence, pas mesure de validité empirique','Scores et masques restent conditionnels','Aucun contrôle de cohérence AHP car pas de matrice de comparaisons par paires','Pondération limitée aux six critères de la grille supplémentaire sans pente','Ne modifie pas le modèle principal de couverture']},ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'{len(d)} réponses analysées. Résultats dans {out}')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reponses',type=Path,default=Path(__file__).with_name('reponses_experts.csv'));p.add_argument('--candidats',type=Path,default=Path(__file__).with_name('candidats_10_25km.csv'));p.add_argument('--sortie',type=Path,default=Path(__file__).with_name('resultats_experts'));args=p.parse_args();analyser(args.reponses,args.candidats,args.sortie)

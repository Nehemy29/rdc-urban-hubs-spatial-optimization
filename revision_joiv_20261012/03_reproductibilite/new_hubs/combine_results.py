from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent/'results'
for stem in ['new_hub_scenarios','new_hub_selections']:
 parts=[]
 for grid,folder in [(25,B),(10,B/'grid10')]:
  x=pd.read_csv(folder/(stem+'.csv'));x['grid_km']=grid;parts.append(x)
 result=pd.concat(parts,ignore_index=True)
 if stem=='new_hub_scenarios':
  assert len(result)==24 and result.solver_status.eq(0).all() and result.mip_gap.eq(0).all()
 result.to_csv(B/('all_'+stem+'.csv'),index=False)
print('24 executed scenarios combined and solver status checked.')

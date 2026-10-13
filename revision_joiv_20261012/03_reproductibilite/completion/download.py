from pathlib import Path
import json,urllib.request,hashlib,zipfile
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parents[1]/'joiv_revision_repo'; dest=Path(__file__).resolve().parent/'sources';dest.mkdir(exist_ok=True)
m=json.loads((root/'revision_sources/source_manifest.json').read_text())
items=[x for x in m if x['file'] in ['GHS_SMOD_2025_1km.zip','GHS_POP_2025_1km.zip','geoBoundaries-COD-ADM1.geojson']]
def get(x):
 p=dest/x['file'];tmp=p.with_suffix('.download')
 if not p.exists():
  with urllib.request.urlopen(x['url'],timeout=180) as response,tmp.open('wb') as f:
   while block:=response.read(1024*1024):f.write(block)
  assert hashlib.sha256(tmp.read_bytes()).hexdigest()==x['sha256'],x['file'];tmp.rename(p)
 if p.suffix=='.zip':
  with zipfile.ZipFile(p) as z:z.extractall(dest)
 print(x['file'],p.stat().st_size,flush=True)
with ThreadPoolExecutor(3) as pool:list(pool.map(get,items))

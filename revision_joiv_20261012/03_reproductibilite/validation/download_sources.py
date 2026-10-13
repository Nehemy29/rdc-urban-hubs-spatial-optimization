from pathlib import Path
import urllib.request,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
S=ROOT/'sources';S.mkdir(exist_ok=True)
for item in json.loads((ROOT/'source_manifest.json').read_text()):
 p=S/item['file']
 if not p.exists():
  temp=p.with_suffix('.download')
  with urllib.request.urlopen(item['url'],timeout=180) as r,temp.open('wb') as out:
   while block:=r.read(1024*1024):out.write(block)
  assert hashlib.sha256(temp.read_bytes()).hexdigest()==item['sha256'],item['file']
  temp.rename(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['file']
 if p.suffix=='.zip':
  folder={'aicd.zip':'aicd','forest_roads.zip':'forest','hot_roads.zip':'hot'}[p.name]
  with zipfile.ZipFile(p) as z:z.extractall(S/folder)
 print(item['file'],'verified',flush=True)

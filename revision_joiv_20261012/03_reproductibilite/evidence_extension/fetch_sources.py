from pathlib import Path
import json,hashlib,urllib.request,zipfile
B=Path(__file__).resolve().parent;D=B/'sources';D.mkdir(exist_ok=True)
for item in json.loads((B/'source_manifest.json').read_text()):
 p=D/item['file'];tmp=p.with_suffix('.download')
 if not p.exists():
  with urllib.request.urlopen(item['url'],timeout=180) as response,tmp.open('wb') as f:
   while chunk:=response.read(1024*1024):f.write(chunk)
  if hashlib.sha256(tmp.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Source changed or incomplete: '+item['file'])
  tmp.rename(p)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Checksum mismatch: '+item['file'])
 if p.name=='roads.zip':
  with zipfile.ZipFile(p) as z:z.extractall(D/'roads')
 print(item['file'],p.stat().st_size)

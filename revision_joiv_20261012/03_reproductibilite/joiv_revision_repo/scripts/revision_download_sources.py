"""Retrieve only documented real sources; verify hashes; never substitute simulations."""
from pathlib import Path
import urllib.request,hashlib,json,zipfile,shutil,os
R=Path(__file__).resolve().parents[1];S=R/'revision_sources';S.mkdir(exist_ok=True);(R/'revision_outputs').mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
for item in json.loads((S/'source_manifest.json').read_text()):
 p=S/item['file']
 if not p.exists() or sha(p)!=item['sha256']:
  target=p.with_name(p.name+'.download')
  print('Downloading',item['file'],flush=True)
  with urllib.request.urlopen(item['url'],timeout=120) as r,target.open('wb') as w:
   shutil.copyfileobj(r,w);w.flush();os.fsync(w.fileno())
  if sha(target)!=item['sha256']:raise RuntimeError('Source checksum mismatch: '+item['file']+'; preserve the new download and obtain the correct snapshot. Do not silently replace data.')
  target.replace(p)
 print('Verified',item['file'],flush=True)
 if zipfile.is_zipfile(p):
  folder='roads' if 'roads' in p.name else 'COD_AB' if p.name.startswith('cod_admin') else 'GHSL'
  out=S/folder;out.mkdir(exist_ok=True)
  with zipfile.ZipFile(p) as z:
   bad=z.testzip()
   if bad:raise RuntimeError('ZIP CRC error: '+bad)
   for info in z.infolist():
    if info.is_dir():continue
    dest=out/Path(info.filename).name
    with z.open(info) as r,dest.open('wb') as w:shutil.copyfileobj(r,w)
print('All downloaded sources verified. No field observations were generated.')

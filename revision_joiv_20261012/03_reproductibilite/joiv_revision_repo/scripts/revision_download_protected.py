"""Reacquire producer data privately under Protected Planet terms; do not redistribute."""
from pathlib import Path
import urllib.request,urllib.parse,json,hashlib
S=Path(__file__).resolve().parents[1]/'revision_sources';S.mkdir(exist_ok=True);base='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/FeatureServer'
for layer in [0,1]:
 params={'where':"iso3 LIKE '%COD%'",'outFields':'*','returnGeometry':'true','outSR':4326,'f':'json'}
 url=base+'/'+str(layer)+'/query?'+urllib.parse.urlencode(params)
 with urllib.request.urlopen(url,timeout=90) as r:b=r.read()
 j=json.loads(b)
 if 'error' in j:raise RuntimeError(j['error'])
 assert not j.get('exceededTransferLimit',False)
 expected={0:'3435b3c82dd5f341fa1be38a9044bc20ec8e5e6a221f010725409795b3142f3e',1:'d7a8b8ef6b45e01117ab4693a3b5dccdf00f0982f1076ef3c815ef70dfa7a1ac'}
 if hashlib.sha256(b).hexdigest()!=expected[layer]:raise RuntimeError('Protected-area source differs from the documented October 2026 response. Obtain its archived snapshot or disclose and rerun using the new version.')
 (S/f'wdpca_cod_layer{layer}.json').write_bytes(b)
 print('layer',layer,'features',len(j['features']),'SHA256',hashlib.sha256(b).hexdigest(),flush=True)
 print('statuses',sorted(set(x['attributes']['status'] for x in j['features'])),flush=True)

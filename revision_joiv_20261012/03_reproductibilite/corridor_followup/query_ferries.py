from pathlib import Path
import urllib.request,urllib.parse,json,time
B=Path(__file__).resolve().parent
q='[out:json][timeout:25];way[route=ferry](-3.7,17.0,-2.9,18.5);out geom;'
url='https://overpass.kumi.systems/api/interpreter?'+urllib.parse.urlencode({'data':q})
try:
 with urllib.request.urlopen(url,timeout=60) as r:data=r.read()
 # A live query may change. Preserve the frozen extract used for the article.
 d=json.loads(data);(B/'sources/osm_ferries_live.json').write_bytes(data)
 print('elements',len(d.get('elements',[])))
 for e in d.get('elements',[]):print(e['type'],e['id'],e.get('tags'),len(e.get('geometry',[])))
except Exception as e:print(type(e).__name__,str(e))

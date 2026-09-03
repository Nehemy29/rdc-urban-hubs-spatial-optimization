from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json, math, os, ssl, time, urllib.parse, urllib.request

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/02_traitees/sites_candidats_phase8.gpkg"
OUT = ROOT / "data/02_traitees/echantillons_environnement_phase9.csv"
sites = gpd.read_file(SRC, layer="grille_eligible").to_crs(4326)
sites["longitude"], sites["latitude"] = sites.geometry.x, sites.geometry.y

def tile_code(lat, lon):
    south, west = math.floor(lat / 3) * 3, math.floor(lon / 3) * 3
    ns = f"N{south:02d}" if south >= 0 else f"S{abs(south):02d}"
    ew = f"E{west:03d}" if west >= 0 else f"W{abs(west):03d}"
    return ns + ew

sites["tile"] = [tile_code(y, x) for y, x in zip(sites.latitude, sites.longitude)]
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["GDAL_HTTP_UNSAFESSL"] = "YES"

def sample_tile(item):
    tile, group = item
    url = f"/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    with rasterio.open(url) as ds:
        values = [int(v[0]) for v in ds.sample(zip(group.longitude, group.latitude))]
    return tile, dict(zip(group.candidate_id, values))

landcover = {}
groups = list(sites.groupby("tile"))
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = [pool.submit(sample_tile, item) for item in groups]
    for number, future in enumerate(as_completed(futures), start=1):
        tile, values = future.result()
        landcover.update(values)
        print(f"WorldCover {number}/{len(groups)} {tile}", flush=True)

labels = {10:"arbres",20:"arbustes",30:"herbace",40:"agriculture",50:"bati",60:"sol_nu",70:"neige_glace",80:"eau",90:"zone_humide_herbacee",95:"mangrove",100:"mousse_lichen"}
sites["worldcover_code"] = sites.candidate_id.map(landcover)
sites["worldcover_classe"] = sites.worldcover_code.map(labels)
sites["occupation_compatible_preliminaire"] = sites.worldcover_code.isin([20, 30, 40, 60])

shortlist = (sites[sites.occupation_compatible_preliminaire]
             .sort_values("score_aptitude_preliminaire", ascending=False)
             .groupby("adm1_name", group_keys=False).head(10).copy())
queries = []
for _, row in shortlist.iterrows():
    lat, lon = row.latitude, row.longitude
    dlat, dlon = 0.009, 0.009 / max(math.cos(math.radians(lat)), 0.2)
    for pos, y, x in [("centre",lat,lon),("nord",lat+dlat,lon),("sud",lat-dlat,lon),("est",lat,lon+dlon),("ouest",lat,lon-dlon)]:
        queries.append((row.candidate_id, pos, y, x))

context = ssl._create_unverified_context()
rows = []
for start in range(0, len(queries), 100):
    batch = queries[start:start+100]
    locations = "|".join(f"{lat:.6f},{lon:.6f}" for _,_,lat,lon in batch)
    url = "https://api.opentopodata.org/v1/srtm90m?" + urllib.parse.urlencode({"locations":locations,"interpolation":"bilinear"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90, context=context) as response: payload=json.load(response)
            if payload.get("status") != "OK": raise RuntimeError(str(payload))
            for meta, result in zip(batch, payload["results"]): rows.append({"candidate_id":meta[0],"position":meta[1],"elevation_m":result["elevation"]})
            break
        except Exception:
            if attempt == 2: raise
            time.sleep(4)
    print(f"SRTM {min(start+100,len(queries))}/{len(queries)}", flush=True)
    time.sleep(1.1)

pivot = pd.DataFrame(rows).pivot(index="candidate_id",columns="position",values="elevation_m")
pivot["elevation_m"] = pivot.centre
pivot["pente_locale_pct"] = np.maximum((pivot.nord-pivot.sud).abs()/2000*100,(pivot.est-pivot.ouest).abs()/2000*100)
result = sites.drop(columns="geometry").merge(pivot[["elevation_m","pente_locale_pct"]],on="candidate_id",how="left")
result["relief_compatible_preliminaire"] = result.pente_locale_pct.le(8)
result.to_csv(OUT,index=False,encoding="utf-8-sig")
print(f"Saved {len(result)} sites; SRTM evaluated on {len(shortlist)} shortlisted cells",flush=True)

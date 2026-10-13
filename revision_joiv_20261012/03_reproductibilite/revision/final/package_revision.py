from pathlib import Path
import json,hashlib,zipfile,importlib.metadata,os,shutil
B=Path(__file__).resolve().parent;R=B.parents[1]/'joiv_revision_repo';S=R/'revision_sources';O=R/'revision_outputs'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(4*1024*1024),b''):h.update(x)
 return h.hexdigest()
man=json.loads((S/'source_manifest.json').read_text())
for file,url,version in [
('GHS_POP_2025_1km.zip','https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_1000/V1-0/GHS_POP_E2025_GLOBE_R2023A_54009_1000_V1_0.zip','GHS-POP R2023A 2025, 1 km, V1.0'),
('GHS_SMOD_2025_1km.zip','https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_SMOD_GLOBE_R2023A/GHS_SMOD_E2025_GLOBE_R2023A_54009_1000/V2-0/GHS_SMOD_E2025_GLOBE_R2023A_54009_1000_V2_0.zip','GHS-SMOD R2023A 2025, 1 km, V2.0'),
('cod_admin_boundaries.shp.zip','https://data.humdata.org/dataset/f42132b9-8cc6-4201-b020-9259c56e8868/resource/7514482b-f7af-4654-8ea2-e8a34a6acb6a/download/cod_admin_boundaries.shp.zip','COD-AB ADM1 v01 valid_on 2019-09-11')]:
 f=S/file;man.append(dict(file=file,url=url,version=version,bytes=f.stat().st_size,sha256=sha(f),access_date='2026-10-06'))
man=list({x['file']:x for x in man}.values())
(S/'source_manifest.json').write_text(json.dumps(man,indent=2))
mods=['numpy','pandas','scipy','networkx','geopandas','pyogrio','pyproj','rasterio','shapely','matplotlib','python-docx','Pillow']
req='\n'.join(m+'=='+importlib.metadata.version(m) for m in mods)+'\n'
(B/'requirements_revision.txt').write_text(req)
readme='''# JOIV revision — submission 6222
Prepared 6 October 2026 for PAMBOLO MAYAMBO Néhémie.

## Evidence boundary
This is a revision of a geospatial sensitivity study. There is no completed regional empirical flow validation or field survey. The revised main analysis selects EXISTING hubs by maximal population coverage on mapped roads; it does not recommend construction of new towns. The original v1.0.0 Zenodo archive does not contain this revision. Do not cite that DOI as if it did.

## Files
- revision/final/: revised English manuscript, response to reviewers, supplement, figures, build script, and artifact audit.
- joiv_revision_repo/scripts/revision_*.py: analyses actually executed for this revision.
- joiv_revision_repo/revision_outputs/: computed CSV/JSON outputs, gridded demand, and road-coverage details.
- joiv_revision_repo/data/: specific original derived inputs required for the audits, preserved without modification.
- joiv_revision_repo/revision_sources/source_manifest.json: exact source URLs, downloaded hashes, versions, and dates. Raw heavy third-party datasets are not included.

## Setup
Use Python 3.12 or an environment compatible with the pinned packages. From the unpacked root:

    python -m pip install -r revision/final/requirements_revision.txt
    python joiv_revision_repo/scripts/revision_download_sources.py

The downloader verifies exact hashes before using a file and stops if the producer has changed its content. It extracts the road GPKG to revision_sources/roads, GHSL files to revision_sources/GHSL, and COD-AB to revision_sources/COD_AB. The .part road archive name is the historical local name of a FULL verified archive, not a partial source.

## Run analyses sequentially

    python joiv_revision_repo/scripts/revision_population_grid.py
    python joiv_revision_repo/scripts/revision_ghsl_compare.py
    python joiv_revision_repo/scripts/revision_topology_sensitivity.py
    python joiv_revision_repo/scripts/revision_exact_pmedian.py
    python joiv_revision_repo/scripts/revision_candidate_weights.py
    python joiv_revision_repo/scripts/revision_road_accessibility.py
    python joiv_revision_repo/scripts/revision_joint_coverage.py
    python joiv_revision_repo/scripts/revision_boundary_check.py
    python revision/final/build_final.py

Graph construction and repeated routing use millions of vertices and can require substantial memory and execution time. A new complete independent-machine run has not been executed. The preserved CSVs are the actual revision outputs; checksums allow comparison. The publisher's live HOT URL may later return a different snapshot: a mismatch must not be silently accepted. Obtain the matching archived snapshot or explicitly rerun and disclose the changed data.

## Model details
96 complete factor configurations are solved for each of p=5,10,15, giving 288 runs. Factors: two population products; 1/5 km demand grids; main roads/plus tracks; 1/2.5/5 km assumed connectors; no/fixed 1% feature removal; no/fixed 250 m hub displacement. Coverage threshold is 100 km. Scenario envelopes are not confidence intervals. Removal and displacement are stress tests, not calibrated error probabilities. No Sobol indices are computed.

The legacy p-median audit covers p=2 through 20, and the elbow rule finds none. Candidate-weight frequencies are conditional on 75 cached points. Tshuapa has only one candidate, making Yanganga's frequency automatically 100%. These audits must not be used as regional mobility validation.

## Licensing and attribution
The existing repository's LICENSE is included for its software. Raw and derived datasets retain producer conditions independently of the software license. WorldPop: CC BY 4.0 with producer attribution; GHSL: European Commission/JRC attribution and applicable reuse terms; geoBoundaries/OSM-derived geography: ODbL 1.0 with source attribution. Preserve all included metadata and do not apply a software license to third-party databases. JICA report is referenced; it is not redistributed. Source metadata and original archive establish the provenance of older derived inputs.

## Publication
Before resubmission, review the changed title/scope and response, confirm author declarations, and deposit the revision code/results as a new release on GitHub/Zenodo. Then update the manuscript's release citation with the actual newly assigned DOI. Do not invent or reuse the old DOI for a new revision. The editor may still require empirical validation despite the reduced scope.
'''
(B/'README_REVISION.md').write_text(readme)
download='''"""Retrieve only documented real sources; verify hashes; never substitute simulations."""
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
'''
(R/'scripts/revision_download_sources.py').write_text(download)
files=[]
for p in (R/'scripts').glob('revision_*.py'):files.append((p,'joiv_revision_repo/scripts/'+p.name))
for p in O.rglob('*'):
 if p.is_file() and p.suffix in ['.csv','.json','.gz','.png']:files.append((p,'joiv_revision_repo/revision_outputs/'+str(p.relative_to(O))))
for name in ['data/02_traitees/graphe_spatial_phase6.gpkg','data/02_traitees/noeuds_urbains_phase3.gpkg','data/02_traitees/echantillons_environnement_phase9.csv','data/03_resultats/noeuds_urbains_phase3.csv','LICENSE','CITATION.cff']:
 files.append((R/name,'joiv_revision_repo/'+name))
for p in S.glob('*metadata.json'):files.append((p,'joiv_revision_repo/revision_sources/'+p.name))
files.append((S/'source_manifest.json','joiv_revision_repo/revision_sources/source_manifest.json'))
for p in B.glob('*'):
 if p.is_file() and p.suffix in ['.docx','.pdf','.json','.py','.md','.txt'] and not p.name.startswith('manuscript_pdf'):files.append((p,'revision/final/'+p.name))
for p in (B/'figures').glob('*.png'):files.append((p,'revision/final/figures/'+p.name))
for name in ['crossref.json','new_reference_metadata.json']:files.append((B.parent/name,'revision/'+name))
checks={arc:sha(p) for p,arc in files}
with zipfile.ZipFile(B/'JOIV_revision_complete.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.writestr('README.md',readme);z.writestr('CHECKSUMS_SHA256.json',json.dumps(checks,indent=2))
 for p,arc in files:z.write(p,arc)
with zipfile.ZipFile(B/'JOIV_revision_complete.zip') as z:assert z.testzip() is None
print('Zip verified:',(B/'JOIV_revision_complete.zip').stat().st_size,'bytes; files',len(files))

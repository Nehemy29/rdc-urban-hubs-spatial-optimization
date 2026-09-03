# Données du pipeline

## Téléchargement automatisé

`scripts/phase1_download_data.py` récupère GeoNames et interroge l'API HDX pour
les limites administratives et les couches OSM (routes, voies d'eau, rails et
aéroports). Le raster WorldPop est téléchargé lorsque son URL officielle est
fournie avec `--worldpop-url`. Les empreintes sont inscrites dans
`data/provenance_manifest.json`. Le paramètre `--skip-hdx` conserve les archives
HDX déjà présentes.

## Entrées non redistribuées

| Fichier attendu | Source/rôle | Statut |
|---|---|---|
| `data/01_brutes/localites/extracted/CD.txt` | GeoNames, localités de la RDC | téléchargé localement |
| `restored/zone_etude.gpkg` | limites des dix provinces | dérivé à documenter |
| `restored/cod_pop_2025_CN_100m_R2025A_v1.tif` | WorldPop 2025 | fichier lourd |
| `restored/reseau_routier_zone.gpkg` | réseau routier découpé | dérivé à documenter |
| `data/01_brutes/osm_multimodal/...` | voies d'eau, rail et aérodromes HOT/OSM | téléchargés localement |

## Données dérivées

- `data/02_traitees` : GeoPackages et cache environnemental ;
- `data/03_resultats` : tableaux CSV et figures utilisés dans l'article.

Chaque source devra recevoir avant publication : URL officielle, version, date
d'accès, licence, empreinte SHA-256 et script de téléchargement ou d'extraction.

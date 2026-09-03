# Prélocalisation de pôles urbains en RDC

Code de réplication de l'étude exploratoire consacrée au système territorial
interconnecté Grand Bandundu–Grand Équateur–Kinshasa–Kongo Central.

## Statut scientifique

Le pipeline produit des scénarios de prélocalisation à partir de données ouvertes.
Les distances du graphe, les temps de parcours, les flux potentiels et les sites
candidats ne constituent pas des observations de terrain ni des décisions de
construction. Les limites sont détaillées dans l'article.

## Résultats reproduits

- sélection de 26 nœuds analytiques et agrégation WorldPop à 5 km ;
- accessibilité routière et multimodale ;
- graphe spatial exploratoire et centralités ;
- scénarios p-médiane pour `p = 5`, `10` et `15` ;
- grille de candidats de 25 km ;
- filtrage WorldCover/SRTM ;
- 5 000 simulations Monte Carlo avec la graine `20260902`.

## Installation

Python 3.12 est recommandé.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Sous Windows PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Données nécessaires

Les fichiers tiers lourds ne sont pas redistribués dans le dépôt. Ils doivent être
placés aux emplacements décrits dans `data/README.md`. Les résultats dérivés légers
peuvent être conservés sous `data/03_resultats`.

## Exécution

Reconstruction depuis les sources (utiliser l'URL affichée sur la fiche officielle
du produit WorldPop retenu) :

```bash
python run_pipeline.py --from-scratch --worldpop-url "URL_DU_GEOTIFF"
```

Avec le cache environnemental fourni :

```bash
python run_pipeline.py
```

Pour interroger à nouveau ESA WorldCover et OpenTopoData :

```bash
python run_pipeline.py --refresh-environment
```

## Provenance et état de reproductibilité

La phase 1 télécharge GeoNames et recherche les ressources courantes dans le
catalogue HDX; elle consigne URL, taille et SHA-256 dans
`data/provenance_manifest.json`. La phase 2 sélectionne les dix provinces par code
administratif et extrait les routes. Les phases 3 à 10 produisent les résultats.

Le pipeline a été exécuté intégralement avec Python 3.12.13 dans un environnement
virtuel neuf. `scripts/verify_results.py` contrôle automatiquement les principaux
résultats annoncés dans l'article. Les services externes peuvent néanmoins changer
ou être indisponibles; le manifeste identifie alors les fichiers utilisés.

## Limite à signaler

Le GeoPackage HOT/OSM des voies d'eau daté du 1er septembre 2026 échoue au contrôle
SQLite malgré une archive ZIP valide. Le pipeline utilise donc automatiquement la
ressource GeoJSON équivalente du même catalogue et du même snapshot. Ce choix est
tracé et ne modifie pas les 5 277 segments retenus dans la zone d'étude.

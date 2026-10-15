# Localisation conditionnelle de nouveaux pôles urbains en RDC

Code, données dérivées et documents de la révision JOIV n° 6222 préparée le 12 octobre 2026 pour le système interconnecté Grand Bandundu–Grand Équateur–Kinshasa–Kongo Central.

## Version actuelle et portée scientifique

La révision ajoute un modèle de couverture de population fondé sur les routes cartographiées. Les 26 pôles existants sont conservés et des centres supplémentaires sont optimisés sur des grilles de candidats de 10 et 25 km. Les 24 optimisations de nouveaux centres complètent 408 expériences antérieures de couverture. La p-médiane et le graphe MST antérieurs sont conservés comme audits, pas comme résultats principaux validés.

Les nouveaux secteurs sont des localisations conditionnelles pour étude, pas des parcelles constructibles ou des villes dont la souveraineté serait démontrée. L’héritage colonial demeure un contexte historique; aucun effet causal colonial n’est estimé.

Le complément des 40 trajets fournit 160 comparaisons sur quatre variantes du graphe. Le réseau principal fournit 29 distances comparables et 11 trajets sans chemin dirigé. L’écart absolu relatif moyen avec OSRM est 24,72 %, la médiane 3,30 %. Deux distances commerciales sont vérifiées sur la page citée, mais leur méthode de mesure et leur indépendance ne sont pas établies. Les références OSRM partagent la provenance OSM : il ne s’agit pas d’une validation indépendante de terrain. Les valeurs manquantes et écarts défavorables sont conservés.

La validation empirique de la couverture régionale, l’opérationnalité des transports, les distributions d’erreur calibrées et les fonctions économiques et énergétiques locales restent partielles ou absentes. Aucun entretien d’expert ou flux observé n’est inventé. La réponse aux reviewers distingue explicitement les demandes traitées et les preuves encore manquantes.

## Où trouver les fichiers actuels

Tout le dossier finalisé est dans [revision_joiv_20261012](revision_joiv_20261012/).

- [Article révisé](revision_joiv_20261012/01_manuscrit/JOIV_revised_manuscript.docx) et son PDF : 17 pages, 24 tableaux, 6 figures, 47 références.
- [Réponse aux neuf remarques](revision_joiv_20261012/02_reponse/JOIV_response_to_reviewers.docx).
- [Code et données dérivées](revision_joiv_20261012/03_reproductibilite/).
- [Comparaison finale des 40 trajets](revision_joiv_20261012/03_reproductibilite/route_comparison_40/results/comparaison_routes_40_finale.csv).
- [Guide de renvoi et compléments](revision_joiv_20261012/04_sources_et_notes/).
- [Instructions actualisées](revision_joiv_20261012/03_reproductibilite/LATEST_README.md) et [statut des réponses](revision_joiv_20261012/03_reproductibilite/STATUS_REVIEWERS.md).

Les anciennes entrées document_inputs et finalization/inputs sont conservées pour reconstruire les amendements. Les anciens scripts à la racine et README_VERSION_1.md décrivent la version initiale; ils ne reconstruisent pas seuls l’article révisé.

## Installation sous Windows

Depuis la racine du dépôt, dans CMD ou PowerShell :

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r revision_joiv_20261012/03_reproductibilite/route_comparison_40/requirements.txt
```

Pour les 40 trajets, suivre [le protocole détaillé](revision_joiv_20261012/03_reproductibilite/route_comparison_40/README_FR.md). Il documente le téléchargement de l’archive routière exacte, son SHA256, le GeoPackage, les règles du graphe et les commandes. Les couches brutes lourdes ne sont pas toutes incluses. L’archive routière originale fait environ 193 Mo; sa version doit respecter l’empreinte enregistrée.

Pour exporter à nouveau le tableau final à partir des calculs fournis :

```powershell
cd revision_joiv_20261012/03_reproductibilite
..\..\.venv\Scripts\python.exe route_comparison_40/export_final_csv.py
```

Les graphes complets atteignent 1,7 à 2,5 millions de sommets. Prévoir suffisamment de mémoire. Les autres modules documentent leurs propres dépendances et données.

## Citation et archivage

**v2.0.0 est publiée et archivée : [10.5281/zenodo.23389655](https://doi.org/10.5281/zenodo.23389655), 15 octobre 2026, commit `8a4a186`.** Les documents courants ajoutent cette citation après publication; le tag et les calculs archivés sont inchangés.

Citer les métadonnées de CITATION.cff et préciser le commit utilisé. L’archive Zenodo historique [v1.0.0](https://doi.org/10.5281/zenodo.22287395) précède ces révisions et ne contient pas les nouveaux calculs. Le DOI [10.5281/zenodo.22287394](https://doi.org/10.5281/zenodo.22287394) regroupe toutes les versions. Pour citer précisément les calculs de cette révision, utiliser le DOI de v2.0.0 ci-dessus. La note antérieure annonçant l’ajout futur du DOI est conservée dans l’archive figée; les métadonnées courantes sont actualisées ici.

## Licences et provenance

Le code original est sous MIT. Les données tierces gardent leurs licences et conditions : notamment OpenStreetMap/HOT sous ODbL, les sources Banque mondiale selon les métadonnées fournies et les protections institutionnelles selon leurs conditions. Ne pas interpréter MIT comme une licence générale de toutes les données. Les limites de redistribution sont précisées dans les modules; les sources restreintes ne sont pas ajoutées automatiquement.

SHA256SUMS.txt dans le dossier de révision couvre ses fichiers distribués. Les sous-modules conservent aussi les empreintes des sources et états historiques. Les tests numériques sont des vérifications de calcul, pas une preuve d’accessibilité observée.

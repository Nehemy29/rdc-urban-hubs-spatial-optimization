# Complément exécuté le 8 octobre 2026

## Résultats et limites

Le rapport Logistics Cluster du 18 avril 2024 décrit une route Kinshasa–Bandundu via Mongata et bac, longue de 405 km. L'ajout des trois géométries OSM de Bac Bandundu, uniquement par coordonnées communes exactes, réduit le trajet du graphe principal de 922,62 à 398,99 km. Les voies sont supposées utilisables dans les deux sens; leur exploitation actuelle, les attentes et les conditions saisonnières ne sont pas vérifiées. Le rapport est un benchmark publié, pas une trace GPS actuelle.

Douze optimisations exactes nouvelles croisent deux réseaux, deux populations et p=5/10/15. Toutes ont un gap nul et une couverture recomputée concordante. Les couvertures optimales sont inchangées à p=5 et p=10; à p=15 les gains sont de 0,049 à 0,079 point de pourcentage. Ce diagnostic ne valide pas l'accès des ménages.

La pondération CRITIC-style utilise les six scores 0–1 existants, avec leur normalisation commune conservée, sans recalage min–max par grille. C_j=sigma_j*sum_k(1-r_jk), w_j=C_j/sum_l(C_l), sigma population ddof=0 et corrélation Pearson. Chaque candidat compte également. Les grilles strictes de 10/25 km comptent 1 583/241 centres. Les poids sont dérivés de la dispersion/corrélation de cette matrice; ils ne sont ni une consultation ni une mesure de priorité sociale. Aucun entretien n'a été effectué.

Les 288 optimisations factorielles, 108 tests antérieurs et 12 tests ferry totalisent 408 optimisations. Les 4 000 rééchantillonnages spatiaux antérieurs sont distincts et ne sont pas ajoutés à ce total. Les distributions d'erreur empiriquement calibrées et les observations d'accès appariées restent manquantes.

## Reproduction sous Windows depuis la racine de l'archive

```
py -m pip install numpy pandas scipy geopandas pyproj shapely pyogrio matplotlib python-docx
py evidence_extension/fetch_sources.py
py corridor_followup/trace_road_path.py
py corridor_followup/ferry_scenario.py
py corridor_followup/ferry_coverage.py
py corridor_followup/critic_weights.py
py corridor_followup/plot_paths.py
```

Le fichier OSM daté utilisé dans l'étude est inclus; il ne faut pas le remplacer par une requête actuelle. query_ferries.py écrit une extraction live séparée. Les sources lourdes sont réacquises avec les empreintes du manifeste antérieur; si elles changent, retrouver le snapshot approprié. source_manifest.json décrit aussi le rapport 2024 et son empreinte, sans redistribuer son PDF. Les fichiers document_inputs conservent exactement les entrées avant ce complément. update_documents.py reproduit les documents courants dans completion/final.

## Attribution et licences

L'extraction ferry et les chemins dérivés utilisent les données © OpenStreetMap contributors, https://www.openstreetmap.org/copyright, licence ODbL 1.0 https://opendatacommons.org/licenses/odbl/1-0/. Les géométries sont incluses pour la reproduction de ce diagnostic. Les sources tierces brutes non incluses restent soumises aux conditions de leurs producteurs. Le DOI original ne couvre pas ce nouveau complément; une nouvelle release publique est nécessaire.

# Extension nouveaux pôles — 9 octobre 2026

24 nouvelles optimisations exécutées, en complément des 408 expériences antérieures de couverture. Les 26 pôles existants restent fixes. Le modèle sélectionne des centres nouveaux sur une grille; leur caractère inhabité et leur faisabilité ne sont pas établis. L’autonomie fonctionnelle est un cadre d’évaluation, pas une observation. Aucune consultation d’experts n’a été inventée.

Depuis la racine du dossier extrait, sous Windows :

```
py -m pip install -r new_hubs/requirements.txt
py evidence_extension/fetch_sources.py
py new_hubs/optimize_new_hubs.py --grid-km 25
py new_hubs/optimize_new_hubs.py --grid-km 10
py new_hubs/combine_results.py
py new_hubs/build_documents.py
```

Les demandes de téléchargement peuvent dépendre des disponibilités des serveurs. Les données dérivées, matrices de couverture, résultats et versions sources des documents sont inclus. Les grands fichiers routiers originaux restent externes. Les coordonnées ne sont pas des recommandations de construction. L’accès effectif, les transports opérationnels, le foncier, les investissements et les fonctions productives/énergétiques restent à valider. Le scénario eau ≤15 km est un choix explicite et ne garantit ni navigabilité ni alimentation fiable.

Les grilles de candidats 10/25 km ne remplacent pas la grille de demande 5 km de cette extension. Les baselines à 1 km de l’audit antérieur ne servent pas de baseline aux nouveaux centres. Les poids multicritères anciens restent un audit, sans servir d’objectif au nouveau modèle.

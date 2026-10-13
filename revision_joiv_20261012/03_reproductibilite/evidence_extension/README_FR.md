> État historique avant le complément ferry/CRITIC. Consulter corridor_followup/README_FR.md et completion/final pour la version actuelle.

# Extension du 8 octobre 2026

Les fichiers à lire sont dans completion/final. Le manuscrit comporte 12 pages, 16 tableaux et 4 figures. La réponse aux reviewers et le guide de consultation ont été actualisés. Les versions plus anciennes restent des entrées et ne sont pas les documents à soumettre.

## Travail effectué

Comparaison exécutée des distances publiées du Logistics Cluster 2018 avec le graphe dirigé utilisé dans l’étude. Deux jeux de routes et deux directions sont exportés. Kinshasa–Bandundu présente un écart important; aucun ajout fictif n’a été effectué pour le réduire. L’entrée Matadi–Bandundu du catalogue ne respecte pas l’inégalité triangulaire avec les deux autres entrées. Aucune distribution d’erreur n’a été ajustée à ce petit échantillon non homogène.

Comparaison satellitaire par province et période, puis 1 000 rééchantillonnages de blocs pour chacun des deux jeux de routes et deux tailles de blocs. Les plages obtenues sont conditionnelles à cette référence de routes forestières récentes. Elles ne sont pas des intervalles de confiance de la couverture de population. Les 4 000 tirages ne sont pas des optimisations de couverture supplémentaires.

## Reproduire

Sous CMD ou PowerShell, depuis la racine du dossier décompressé :

```
py -m pip install numpy pandas scipy geopandas pyproj shapely pyogrio python-docx
py evidence_extension/fetch_sources.py
py evidence_extension/route_benchmark.py
py evidence_extension/spatial_road_audit.py
```

Le téléchargement vérifie les empreintes; le lien HOT est mutable. Si sa version a changé, le script s’arrête et il faut retrouver le snapshot exact auprès du producteur ou du détenteur autorisé. Ne pas remplacer silencieusement un fichier ni sa somme de contrôle. Les données tierces brutes ne sont pas incluses; respecter leurs conditions d’utilisation. Les scripts d’analyse n’utilisent pas l’annexe JICA comme observation appariée.

## Consultation

Le dossier expert_kit contient les formulaires CSV vides, les scores de la grille supplémentaire et le script. Lire le guide dans completion/final, effectuer les entretiens puis saisir les réponses. Depuis expert_kit :

```
py -m pip install numpy pandas
py analyser_consultation.py
```

Sans réponse, aucun poids d’expert n’est produit. Les critères doivent être acceptés tels que définis. Une médiane dont les six composantes sont nulles est indéfinie et n’est pas convertie artificiellement en poids. Le panel ne valide pas les déplacements des ménages. Les identifiants personnels et les consentements signés restent hors du dépôt public.

## Éléments encore requis

Observations d’accès appariées au modèle, explication ou correction étayée des anomalies de routage, distributions d’erreur empiriquement défendables et réponses d’experts si le classement multicritère est conservé. Cette archive ne déclare pas les demandes des reviewers entièrement satisfaites. Le DOI de la version originale ne couvre pas cette révision; une nouvelle release reste nécessaire.

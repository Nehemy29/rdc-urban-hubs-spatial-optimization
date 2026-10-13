# Comparaison des quarante trajets du 12 octobre 2026

Les deux CSV d’entrée sont conservés tels que reçus. Les valeurs OSRM sont cartographiques, pas des mesures GPS. Les trois références documentaires sont conservées avec leur statut : deux distances commerciales vérifiées sur la page citée, méthode et indépendance inconnues; une reproduction Scribd non vérifiée exclue des contrôles confirmés. Aucun nombre SIM n’est utilisé.

Quatre variantes donnent 160 lignes calculées. Le graphe principal donne 29 distances et 11 cas sans chemin dirigé. Moyenne et médiane des écarts absolus relatifs aux références OSRM : 24,72 % et 3,30 %. Les distances manquantes restent manquantes. Aucun flux, accès réel des ménages ou poids d’expert n’a été observé par cette analyse.

## Reproduction sous Windows
Depuis 03_reproductibilite :

```
py -m pip install -r route_comparison_40/requirements.txt
py route_comparison_40/calculate_routes.py --roads evidence_extension/sources/roads/roads.gpkg --road-archive evidence_extension/sources/roads.zip --graph-script joiv_revision_repo/scripts/revision_road_accessibility.py --ferry-json corridor_followup/sources/osm_ferries_20261008.json
py route_comparison_40/export_final_csv.py
py route_comparison_40/update_article.py
```

Télécharger avant la première commande le ZIP routier depuis https://production-raw-data-api.s3.amazonaws.com/ISO3/COD/roads/hotosm_cod_roads_osm_gpkg.zip et extraire son GeoPackage aux chemins indiqués. Le code impose le SHA256 original e70623e58bc1f004ae143ca32d952421ffada78c302c2649b458ca183295c0b7. Si le producteur remplace ce fichier, retrouver le même instantané; ne pas retirer silencieusement le contrôle. L’archive brute de 193 Mo n’est pas redistribuée ici. Les OSM sont sous ODbL, attribution OpenStreetMap contributors et Humanitarian OpenStreetMap Team. Les métadonnées enregistrent aussi l’empreinte du script original et du petit extrait de bac.

Prévoir une machine avec suffisamment de mémoire pour les graphes de 1,7 à 2,5 millions de sommets. Le calcul utilise les fonctions originales graph et xyz; leurs règles, les sens uniques et les coordonnées exactes ne sont pas modifiés pour ajuster les références. Le bac est une hypothèse d’usage conditionnel, pas un service confirmé.

Les fichiers document_inputs sont les deux versions antérieures nécessaires à l’amendement déterministe. update_article.py produit le manuscrit et la réponse consolidés dans completion/final. Le PDF est une conversion Word/LibreOffice à contrôler visuellement. Le guide français est livré séparément et n’est pas reconstruit par ce script.

OSRM cherche une route rapide; notre graphe minimise la longueur. Les deux partagent la provenance OSM, avec profils, périodes et extrémités potentiellement différents. Ne pas renommer ces écarts « erreur empirique validée ». Trois seulement des quarante routes OSRM sont dans le seuil de 100 km : l’accord de classement est peu informatif sur ce seuil. Aucun modèle d’erreur régional ni intervalle de confiance n’est calibré.

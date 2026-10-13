from pathlib import Path
import pandas as pd
B=Path(__file__).resolve().parent
x=pd.read_csv(B/'results/comparaison_documentaire_40_trajets_completee.csv')
x=x.rename(columns={'Distance OSRM (km)':'distance_reference_OSRM_km','Distance documentaire (km)':'distance_documentaire_km','Distance modèle (km)':'distance_modele_routes_principales_km'})
a=pd.read_csv(B/'input/40_trajets_distances_osrm.csv')
m=pd.read_csv(B/'results/model_vs_osrm_160_comparisons.csv');m=m[m.scenario.eq('main_road_only')]
x=x.merge(m[['id_trajet','signed_difference_km','absolute_difference_km','absolute_relative_difference_pct','threshold_disagreement','origin_connector_km','destination_connector_km']],left_on='ID',right_on='id_trajet').drop(columns='id_trajet')
x=x.merge(a[['id_trajet','longitude_origine','latitude_origine','longitude_destination','latitude_destination','date_verification','url_requete_osrm']],left_on='ID',right_on='id_trajet').drop(columns='id_trajet')
x['independance_empirique_etablie']=False;x['mesure_terrain_GPS_disponible']=False
x=x[['ID', 'Origine', 'Destination', 'distance_reference_OSRM_km', 'distance_documentaire_km', 'Lien source', 'Nature de la référence', 'distance_modele_routes_principales_km', 'Statut modèle', 'Écart modèle moins référence documentaire km', 'Écart absolu relatif modèle documentaire pourcent', 'Référence documentaire vérifiée en ligne', 'Portée documentaire', 'signed_difference_km', 'absolute_difference_km', 'absolute_relative_difference_pct', 'threshold_disagreement', 'origin_connector_km', 'destination_connector_km', 'longitude_origine', 'latitude_origine', 'longitude_destination', 'latitude_destination', 'date_verification', 'url_requete_osrm', 'independance_empirique_etablie', 'mesure_terrain_GPS_disponible']]
x.to_csv(B/'results/comparaison_routes_40_finale.csv',index=False,encoding='utf-8-sig')

from pathlib import Path
import json,hashlib,zipfile
import pandas as pd
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
B=Path(__file__).resolve().parent;O=B/'results';D=B/'deliverables';D.mkdir(exist_ok=True)
x=pd.read_csv(O/'five_site_example_hv_distance.csv');m=json.loads((O/'energy_distance_metadata.json').read_text())
# Published weighted country-profile indicators, not unweighted microdata counts.
context=pd.DataFrame([
 ['firms_experiencing_outages_pct',77.4,'percent','Eligible formal non-agricultural private establishments, national'],
 ['outages_typical_month',11.6,'number','Eligible formal non-agricultural private establishments, national'],
 ['direct_exporters_at_least_10pct_sales_pct',1.7,'percent','Eligible formal non-agricultural private establishments, national'],
 ['manufacturing_foreign_inputs_pct',27.2,'percent','Manufacturing establishments only, national']
],columns=['indicator','published_value','unit','universe'])
context['survey_year']=2024;context['source_page']=11;context['source_url']='https://www.enterprisesurveys.org/content/dam/enterprisesurveys/documents/country/Congo-Dem-Rep-2024.pdf';context['retrieval_route']='Official published profile retrieved by web reader; original PDF download returned HTTP403 locally';context['valid_for_candidate_site_estimate']=False
context.to_csv(O/'WBES_2024_national_context.csv',index=False)
# Maintain exact source metadata and failure record rather than inventing local data.
(O/'source_access.json').write_text(json.dumps({'hv_archive_download':'succeeded','energydata_ckan_api':'HTTP403','enterprise_profile_local_pdf':'HTTP403','enterprise_profile_web_reader':'succeeded; pages inspected as published text','microdata':'not downloaded or analysed','date':'2026-10-09'},indent=2))
d=Document();s=d.sections[0];s.page_width=Inches(8.5);s.page_height=Inches(11);s.top_margin=s.bottom_margin=Inches(.7);s.left_margin=s.right_margin=Inches(.8)
normal=d.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10);normal.paragraph_format.space_after=Pt(6)
for name in ['Title','Heading 1','Heading 2']:
 d.styles[name].font.color.rgb=RGBColor(0,0,0)
 for e in list(d.styles[name].element.iter(qn('w:pBdr'))):e.getparent().remove(e)
d.styles['Title'].font.size=Pt(22)
def p(t):d.add_paragraph(t)
def heading(t):d.add_paragraph(t,'Heading 1')
def table(headers,rows):
 t=d.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER
 for c,v in zip(t.rows[0].cells,headers):c.text=v
 for vals in rows:
  for c,v in zip(t.add_row().cells,vals):c.text=str(v)
 for i,row in enumerate(t.rows):
  trPr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trPr.append(cant)
  for c in row.cells:
   c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b)
   if i==0:
    e=OxmlElement('w:shd');e.set(qn('w:fill'),'E7EDF2');pr.append(e)
   for para in c.paragraphs:
    para.paragraph_format.space_after=Pt(4);para.paragraph_format.space_before=Pt(4)
    for r in para.runs:r.font.size=Pt(9);r.bold=i==0
 return t
d.add_paragraph('Énergie et activité économique des secteurs candidats','Title')
p('Complément à la révision JOIV 6222 — PAMBOLO MAYAMBO Néhémie — 9 octobre 2026')
p('Une couche historique indépendante du calcul routier permet désormais de mesurer la proximité des secteurs retenus à des lignes électriques à haute tension cartographiées. Cette mesure révèle des contraintes d’implantation à examiner. Elle ne mesure pas leur alimentation actuelle. Des indicateurs économiques observés existent au niveau national; leur échelle ne permet pas de les attribuer aux cinq sites.')
heading('Résultats géographiques calculés')
p('Le fichier COD_HV_Network_2018 contient 46 entités linéaires nationales. La Banque mondiale décrit des travaux cartographiques du projet DRC EASE, révisés avec la SNEL et des spécialistes de l’énergie. Le titre renvoie à 2018; la page indique une année de publication 2021 et une mise à jour de métadonnées en 2025. Ces dates ne prouvent pas une actualisation des lignes ou de leur état opérationnel [1].')
rows=[]
for i,r in enumerate(x.itertuples()):rows.append([f'N{i+1}',r.province,f'{r.longitude:.3f}',f'{r.latitude:.3f}',f'{r.distance_historical_hv_km:.1f}'])
table(['Site','Province','Longitude','Latitude','Distance HT km'],rows)
p('N1 à N5 sont le jeu optimal WorldPop, routes principales, cinq nouveaux centres, grille de candidats 10 km, sans contrainte eau. Les distances sont géométriques, pas des longueurs de raccordement. Elles sont arrondies à 0,1 km pour le tableau, sans présumer cette précision pour la cartographie source.')
p('N4 est à environ 8,1 km d’une ligne historique cartographiée; N2, N3 et N5 sont à plus de 100 km. N1 est à 48,2 km. La proximité ne garantit ni branchement, ni capacité, ni continuité de fourniture. L’absence de proximité dans cette couche ne démontre pas l’absence de mini-réseau, de distribution locale ou de projet récent.')
heading('Méthode reproductible')
p('Les 38 centres distincts sélectionnés dans les 24 scénarios sont analysés. Les lignes WGS84 sont densifiées à un pas maximal de 0,01 degré. Pour chaque centre, une projection azimutale équidistante WGS84 centrée sur ce point est utilisée; la distance minimale point–ligne est calculée en mètres et convertie en kilomètres. Les résultats par site et par scénario, l’empreinte SHA256 du fichier original et le script sont fournis. Aucune optimisation de localisation n’est refaite à partir de cette proximité historique.')
heading('Ce que mesure réellement l’enquête entreprises')
p('Le profil WBES RDC 2024 publie une proportion de 77,4 % d’établissements ayant connu des coupures et une moyenne de 11,6 coupures dans un mois typique. Il rapporte 1,7 % d’exportateurs directs réalisant au moins 10 % de leurs ventes à l’exportation et, pour les entreprises manufacturières, 27,2 % utilisant des intrants d’origine étrangère [2]. Ce sont des résultats publiés de l’enquête, pas des estimations calculées ici à partir des microdonnées.')
p('L’univers est constitué d’établissements formels privés non agricoles d’au moins cinq employés, dans les secteurs éligibles. Les interviews ont eu lieu entre avril et décembre 2024. La documentation exige l’utilisation des poids de sondage pour les inférences [3]. Ces données ne décrivent pas tous les ménages, les fermes, l’économie informelle ou les nouveaux sites. La dépendance aux intrants étrangers n’est pas une mesure de dépendance à Kinshasa.')
heading('Portée de la calibration')
p('La nouvelle mesure électrique ajoute une variable géographique documentée; elle ne calibre pas les erreurs routières ou démographiques. Les contrôles externes antérieurs restent des diagnostics avec différences de dates, d’itinéraires et de couverture. La proximité à une ligne n’est pas une observation indépendante d’accès effectif à l’électricité. Le seuil de couverture routière de 100 km demeure une hypothèse de service.')
table(['Facteur','Ce qui est disponible','Ce qui reste nécessaire'],[
 ['Routes','Comparaisons spatiales et itinéraires publiés','Référence contemporaine représentative et état opérationnel'],
 ['Population','Deux produits modélisés comparés','Comptages indépendants à une échelle compatible'],
 ['Électricité','Proximité à des lignes historiques','Capacité disponible, raccordements, horaires et coupures locaux'],
 ['Économie','Indicateurs nationaux observés WBES','Production, emplois, services et échanges des secteurs candidats']])
p('Une calibration exigerait des paires mesure indépendante–prédiction comparables, une estimation des erreurs par territoire et une validation sur observations non utilisées pour ajuster le modèle. Les perturbations actuelles restent des scénarios de sensibilité; aucune distribution d’erreur validée ou probabilité de souveraineté n’est ajoutée.')
heading('Texte anglais proposé pour le manuscrit')
p('Historical electricity infrastructure was examined as an additional context variable, without changing the population-coverage objective. A World Bank DRC EASE high-voltage line dataset containing 46 mapped features was downloaded and analysed. For the fine-grid WorldPop five-centre example, distances to mapped historical linework are approximately 48.2, 107.2, 278.8, 8.1 and 158.5 km for N1–N5, respectively. Distances use per-site WGS84 azimuthal equidistant projections after line densification. They quantify historical geometric proximity, not feasible connection lengths, spare capacity or current power reliability. National WBES 2024 findings provide observed enterprise context but cannot be spatially assigned to candidate centres. These additions refine the functional-autonomy evidence framework without validating the regional coverage outcome or establishing economic independence.')
heading('Sources')
p('[1] World Bank Group. Democratic Republic Congo (COD) — Transmission Network (2018). CC BY 4.0. https://energydata.info/en/dataset/democratic-republic-congo-cod-transmission-network-2018. Fichier COD_HV_Network_2018 téléchargé le 9 octobre 2026.')
p('[2] World Bank Group. Enterprise Surveys — Congo, Dem. Rep. 2024 country profile, appendix, page PDF 11. https://www.enterprisesurveys.org/content/dam/enterprisesurveys/documents/country/Congo-Dem-Rep-2024.pdf. Profil vérifié en ligne; téléchargement local du PDF refusé HTTP 403.')
p('[3] World Bank Group. COD_2024_WBES_v01_M, study description and sampling documentation. https://microdata.worldbank.org/index.php/catalog/6681/study-description. Consulté le 9 octobre 2026; microdonnées non téléchargées.')
for para in d.paragraphs:
 if para.text.startswith(('[1]', '[2]', '[3]')):
  for run in para.runs:run.font.size=Pt(9)
d.save(D/'Complement_energie_economie_JOIV.docx')
(B/'README_FR.md').write_text('''# Complément énergie et économie\nExécution : py compute_energy.py puis py build_supplement.py\nDépendances : pandas, numpy, geopandas, pyproj, shapely, python-docx.\nLe fichier routier n’est pas nécessaire : conserver new_hubs/results/all_new_hub_selections.csv dans le dossier parent.\nLes distances ajoutent du contexte historique, sans reclasser les sites ni prétendre à un raccordement disponible. La couche Banque mondiale est sous CC BY 4.0. Les données nationales WBES sont transcrites du profil officiel et ne sont pas extrapolées aux sites. Les sources actuelles insuffisantes ne sont pas remplacées par des valeurs inventées.\n''')
print('Supplement built; five-site distances verified; national context explicitly scoped.')

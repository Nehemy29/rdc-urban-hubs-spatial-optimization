from pathlib import Path
from copy import deepcopy
import ast,json,shutil,re
import pandas as pd
from docx import Document
from docx.text.paragraph import Paragraph
from docx.shared import Pt,Inches,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
B=Path(__file__).resolve().parent;P=B.parent;D=B/'deliverables';D.mkdir(exist_ok=True)
E=B.parent/'functional_evidence'
energy=pd.read_csv(E/'results/five_site_example_hv_distance.csv')
assert len(energy)==5 and energy.candidate_id.tolist()==['G10_173_-69','G10_179_-53','G10_184_33','G10_187_-73','G10_206_36']
def inserted(anchor,text,template):
 el=deepcopy(template._p)
 for node in list(el):
  if node.tag!=qn('w:pPr'):el.remove(node)
 anchor.addprevious(el);p=Paragraph(el,template._parent);p.add_run(text)
 if template.runs:
  old=template.runs[0];new=p.runs[0];new.font.name=old.font.name;new.font.size=old.font.size;new.bold=old.bold;new.italic=old.italic
 return p

d=Document(B/'inputs/JOIV_revised_manuscript.docx');normal=d.paragraphs[82];sub=d.paragraphs[81];refs=d.paragraphs[-1]
for p in d.paragraphs:
 if p.text.startswith('The maximal covering model selects exactly p facilities'):p.text=p.text.replace('The maximal covering model','The baseline existing-hub maximal covering model',1)
anchor=next(p for p in d.paragraphs if p.text=='III. RESULTS AND DISCUSSION')._p
inserted(anchor,'N. Historical Electricity Infrastructure and Enterprise Context',sub)
inserted(anchor,'A World Bank DRC EASE high-voltage network file titled COD_HV_Network_2018 is used as a separate infrastructure-context layer [43]. The download contains 46 line features in WGS84. The catalogue describes mapping revised with SNEL and energy specialists; its release year 2021 and metadata update 2025 do not establish current operational conditions. The layer is historical linework, not a census of present distribution, mini-grids or reliable electricity access.',normal)
inserted(anchor,'For the 38 distinct new centres selected across the 24 scenarios, source linework is densified at a maximum segment length of 0.01 degree and transformed into a WGS84 azimuthal equidistant projection centred on each candidate. Shortest point-to-line distance is computed in metres and converted to kilometres. A numerical check at 0.001-degree densification changes the five example distances by less than 0.001 km; this checks discretization, not source positional accuracy. Historical geometric proximity is not a feasible connection length or an operating-capacity measure. This diagnostic does not change candidate selection or the coverage objective.',normal)
inserted(anchor,'Published indicators from the World Bank Enterprise Survey (WBES) RDC 2024 provide observed national enterprise context [44]. Its universe covers eligible registered non-agricultural private establishments with at least five employees; interviews were conducted between April and December 2024, and population inference requires survey weights [45]. Published profile indicators are transcribed with their universe and source page. Microdata are not downloaded or analysed here, and national indicators are not assigned to candidate locations or used to calibrate road-access errors.',normal)
anchor=next(p for p in d.paragraphs if p.text=='IV. CONCLUSION')._p
inserted(anchor,'N. Energy Proximity and Economic Evidence Boundary',sub)
inserted(anchor,'Table XXII adds historical high-voltage proximity for the fine-grid WorldPop five-centre example. N4 is approximately 8.1 km from mapped linework, N1 is 48.2 km away, and N2, N3 and N5 exceed 100 km. These distances identify energy-supply questions for site feasibility. They cannot establish energization, spare capacity, compatible voltage, reliability, connection rights or investment cost. Large distances in this layer do not establish absence of present mini-grids, local distribution or later projects.',normal)
cap=inserted(anchor,'TABLE XXII\nHISTORICAL HIGH VOLTAGE PROXIMITY OF FIVE NEW CENTRES',d.paragraphs[184]);cap.paragraph_format.keep_with_next=True;cap.alignment=WD_ALIGN_PARAGRAPH.CENTER;cap.paragraph_format.first_line_indent=Inches(0)
for run in cap.runs:run.font.name='Times New Roman';run.font.size=Pt(8);run.bold=False
# Reuse the existing aligned single-column numeric table dimensions.
t=deepcopy(d.tables[-1]._tbl);anchor.addprevious(t)
from docx.table import Table
table=Table(t,d._body)
headers=['Site','Province','Water km','HT km','Layer title']
for c,v in zip(table.rows[0].cells,headers):c.text=v
for i,r in enumerate(energy.itertuples()):
 for c,v in zip(table.rows[i+1].cells,[f'N{i+1}',r.province,f'{r.d_water_m/1000:.2f}',f'{r.distance_historical_hv_km:.1f}','2018']):c.text=str(v)
for row_index,row in enumerate(table.rows):
 for c in row.cells:
  for p in c.paragraphs:
   p.paragraph_format.space_after=Pt(2);p.paragraph_format.first_line_indent=Inches(0);p.paragraph_format.left_indent=Inches(0);p.paragraph_format.right_indent=Inches(0);p.alignment=WD_ALIGN_PARAGRAPH.LEFT
   for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(8);run.bold=row_index==0
inserted(anchor,'HT denotes mapped historical high-voltage linework; Water repeats the mapped-water proximity in Table XXI. The 2018 layer title is not confirmation of the date when each feature was surveyed or last operated. Distances are geometric, not construction or routing costs.',normal)
inserted(anchor,'The published national WBES profile reports 77.4% of eligible firms experiencing electrical outages and 11.6 outages in a typical month. It also reports 1.7% direct exporters with at least 10% of sales exported and, among manufacturing firms only, 27.2% using inputs of foreign origin [44]. These observations document an economic and energy context, not the functions of N1–N5. Foreign-input dependence is not dependence on Kinshasa. Neither current reliable power nor local output transformation, employment or essential-service capacity is measured at the new sites.',normal)
inserted(anchor,'The additional layer strengthens the explicit evidence framework for functional autonomy without fulfilling empirical validation of the regional coverage outcome. Coverage scenarios remain conditional on assumed services and distances; calibrated error distributions require representative independent observations matched in place, epoch and measurement target. Historical energy proximity is not such an observation of household access.',normal)
for p in d.paragraphs:
 if p.text.startswith('New urban hubs remain the planning objective'):
  p.text=p.text.replace('The model locates sectors with conditional marginal service benefits and evaluates one explicit water-proximity constraint.','The model locates sectors with conditional marginal service benefits, evaluates an explicit water-proximity constraint, and documents historical high-voltage proximity as a separate feasibility diagnostic.')
 if p.text.startswith('The replication package provides scripts'):
  p.text=p.text.replace('Revised files accompany resubmission and require a new public release with its own archive citation.','The consolidated 12 October 2026 package contains the revised documents and the historical-energy diagnostic. A new public repository release and archive citation remain required; no new DOI is claimed here.')
for text in [
 '[43] World Bank Group, “Democratic Republic Congo (COD)—Transmission Network (2018),” DRC EASE high-voltage mapping, catalogue release year 2021, CC BY 4.0. [Online]. Available: https://energydata.info/en/dataset/democratic-republic-congo-cod-transmission-network-2018. File COD_HV_Network_2018 downloaded: 9 Oct. 2026.',
 '[44] World Bank Group, Enterprise Surveys: Congo, Dem. Rep. 2024, country profile, appendix, PDF p. 11. [Online]. Available: https://www.enterprisesurveys.org/content/dam/enterprisesurveys/documents/country/Congo-Dem-Rep-2024.pdf. Verified online: 9 Oct. 2026.',
 '[45] World Bank Group, “Congo, Dem. Rep.—World Bank Enterprise Survey 2024,” Ref. COD_2024_WBES_v01_M, study description and sampling documentation. [Online]. Available: https://microdata.worldbank.org/index.php/catalog/6681/study-description. Accessed: 9 Oct. 2026.'
]:
 p=d.add_paragraph(text);p.paragraph_format.space_after=Pt(3)
 for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(8)
d.core_properties.author='PAMBOLO MAYAMBO Néhémie';d.save(D/'JOIV_revised_manuscript.docx')

reply=Document(B/'inputs/JOIV_response_to_reviewers.docx')
section=0
locations={
1:'Sections I, III.F and IV; revised title.',
2:'Sections II.C and II.F, III.B and III.D; Fig. 3; Table VII; topology_node_metrics.csv and topology_summary.csv.',
3:'Sections II.L–N and III.L–N; Fig. 6; Tables XIX–XXII; all_new_hub_scenarios.csv, all_new_hub_selections.csv and functional_evidence/results/.',
4:'Section II.F; candidate_weight_audit_metadata.json; legacy environment script.',
5:'Sections II.G and II.J–K, III.I–K and IV; Figs. 5; Tables XIV–XVII; references [32]–[39]; route and satellite-road diagnostic CSVs.',
6:'Sections II.E, II.H–K and II.L, III.C and III.G–L; Tables II, VI, IX, XII, XVI–XVII and XIX–XX; joint_maximal_coverage_results.csv, repeated_joint_stress.csv and all_new_hub_scenarios.csv.',
7:'Sections II.F, II.J–L and III.E, III.K–L; Tables VIII and XVIII; criterion audit outputs. The principal new-centre objective contains no preference-weight vector.',
8:'Sections II.B, II.E–F, II.H–I and II.L, III.G–H and III.L; Tables II, IX–XII and XIX–XX; complete supplementary scenario and candidate-screen tables.',
9:'Sections II.B, II.D, II.F and II.I–L, III.A, III.C–D and III.H, III.L; Tables III, V, XIII and XIX–XX; Figs. 2 and 4; elbow_rule_check.json.'}
for p in list(reply.paragraphs):
 if p.text.startswith('Author:'):p.text='Author: PAMBOLO MAYAMBO Néhémie. Consolidated revision: 12 October 2026.'
 match=re.match(r'^([1-9])\. ',p.text)
 if match:section=int(match.group(1))
 if p.text.startswith('Location and evidence:') and section in locations:p.text='Location and evidence: '+locations[section]
 if p.text.startswith('Response: New Sections II.L–M'):
  p.text+=' The consolidated revision now adds Sections II.N and III.N with historical high-voltage proximity for all 38 distinct selected centres and Table XXII. In the five-centre example distances range from 8.1 to 278.8 km. Published WBES 2024 national enterprise indicators are documented with their sampling universe. These additions do not establish local reliable power, economic independence or observed service coverage.'
 if p.text.startswith('Dear Editor and Reviewers,'):
  p.text+=' Historical electricity infrastructure and published national enterprise observations are now integrated into the manuscript and the consolidated package, with their epoch and scale limitations explicit.'
# Consolidate historical appended sections into one current evidence summary.
for p in list(reply.paragraphs)[45:]:p._element.getparent().remove(p._element)
for p in reply.paragraphs:
 if p.style.name.startswith('Heading'):p.paragraph_format.keep_with_next=True
reply.core_properties.author='PAMBOLO MAYAMBO Néhémie';reply.save(D/'JOIV_response_to_reviewers.docx')

n=Document();s=n.sections[0];s.page_width=Inches(8.5);s.page_height=Inches(11);s.top_margin=s.bottom_margin=Inches(.7);s.left_margin=s.right_margin=Inches(.8)
n.styles['Normal'].font.name='Calibri';n.styles['Normal'].font.size=Pt(11)
for st in ['Title','Heading 1','Heading 2']:
 n.styles[st].font.color.rgb=RGBColor(0,0,0)
 for e in list(n.styles[st].element.iter(qn('w:pBdr'))):e.getparent().remove(e)
n.add_paragraph('Dossier de renvoi de la révision JOIV 6222','Title')
n.add_paragraph('PAMBOLO MAYAMBO Néhémie — 12 octobre 2026')
n.add_paragraph('Les documents sont consolidés pour préparer le renvoi à la revue. Le manuscrit intègre maintenant les méthodes et résultats du complément énergie–économie. La réponse traite les neuf remarques et indique les réponses partielles. La finalisation documentaire ne signifie pas que toutes les preuves empiriques demandées sont acquises.')
for title,text in [
('Fichiers à utiliser','Dans 01_manuscrit, utiliser JOIV_revised_manuscript.docx comme version révisée; le PDF permet de vérifier la présentation. Dans 02_reponse, utiliser JOIV_response_to_reviewers.docx pour la réponse point par point. Dans 03_reproductibilite se trouvent le code, les tableaux et les données dérivées. Le dossier 04_sources_et_notes contient le complément documenté et cette notice. Ne pas reprendre les anciennes versions incluses dans les entrées historiques des scripts.'),
('Ce qui est intégré','Le modèle conserve les 26 pôles existants et optimise des centres supplémentaires. Le manuscrit comporte 22 tableaux, six figures et 45 références. Les sections II.N et III.N décrivent la proximité des sites à des lignes haute tension historiques et les observations nationales de l’enquête entreprises RDC 2024. Elles ne transforment pas ces informations en preuve d’autonomie locale.'),
('Limites à défendre auprès de la revue','La validation empirique de la couverture régionale reste partielle. Les différences entre produits démographiques et les perturbations de routes sont des tests de sensibilité; leurs probabilités ne sont pas entièrement calibrées. La proximité électrique ne garantit pas un raccordement ou une fourniture fiable. Les fonctions économiques locales, les coûts, le foncier et la constructabilité des secteurs demeurent à vérifier. La consultation d’experts n’est pas présentée comme réalisée; l’objectif principal ne dépend pas de poids issus d’un panel fictif.'),
('Avant le dépôt sur JOIV','Ouvrir les deux fichiers Word et leur PDF, vérifier les coordonnées de l’auteur et conserver le même numéro de soumission 6222. Déposer la révision dans le dossier existant en suivant les indications de la revue; ne pas créer une nouvelle soumission pour le même article. Joindre la réponse point par point et, si l’interface le permet, les pièces de reproductibilité. Le dossier n’a pas été envoyé à la revue par cet assistant.'),
('Actualiser GitHub et Zenodo','Publier les nouveaux scripts et tableaux sur le dépôt du projet puis créer une nouvelle version publique. Le DOI de l’ancienne version v1.0.0 ne couvre pas les révisions récentes. Après création de la nouvelle archive Zenodo, remplacer la mention de version dans le manuscrit et la réponse par le DOI effectivement attribué. Aucun DOI nouveau n’est inventé dans ce dossier. Vérifier les droits de diffusion des données brutes; les grandes couches et sources restreintes ne sont pas toutes incluses.'),
('Reproduire le complément énergétique sous Windows','Depuis la racine du dossier 03_reproductibilite, utiliser la même installation Python que pour le projet. Exécuter : py functional_evidence/compute_energy.py. Le script analyse l’archive historique incluse et les sélections new_hubs/results/. Les distances CSV doivent correspondre aux résultats fournis. Les réexécutions complètes du réseau requièrent les sources lourdes décrites dans les README. La construction historique des documents du 9 octobre reste conservée; le script finalization/finalize_documents.py applique la consolidation du 12 octobre aux entrées archivées.'),
]:
 n.add_paragraph(title,'Heading 1');n.add_paragraph(text)
n.save(D/'Mode_emploi_renvoi_JOIV_FR.docx')
assert len(d.tables)==22 and len(d.inline_shapes)==6
assert len([p for p in d.paragraphs if re.match(r'^\[\d+\]',p.text)])==45
print('3 documents consolidated; 22 tables, 6 figures, 45 references; reviewer cross-references updated.')

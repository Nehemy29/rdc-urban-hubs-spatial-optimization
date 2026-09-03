from pathlib import Path
import csv

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path('/workspace/scratch/17bef4d8569c')
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
DOCX = OUT / 'article_amenagement_rdc_V8_format_JOIV_francais.docx'

NAVY = '17365D'; BLUE = '2E74B5'; LIGHT = 'E8EEF5'; GRAY = '5B6573'; GOLD = 'B8860B'; WHITE = 'FFFFFF'

def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def set_cell_width(cell, dxa):
    tcPr = cell._tc.get_or_add_tcPr(); tcW = tcPr.find(qn('w:tcW'))
    if tcW is None: tcW = OxmlElement('w:tcW'); tcPr.append(tcW)
    tcW.set(qn('w:w'), str(dxa)); tcW.set(qn('w:type'), 'dxa')

def set_table_geometry(table, widths):
    table.autofit = False; table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn('w:tblW'))
    if tblW is None: tblW = OxmlElement('w:tblW'); tblPr.append(tblW)
    tblW.set(qn('w:w'), str(sum(widths))); tblW.set(qn('w:type'), 'dxa')
    tblInd = OxmlElement('w:tblInd'); tblInd.set(qn('w:w'), '120'); tblInd.set(qn('w:type'), 'dxa'); tblPr.append(tblInd)
    grid = table._tbl.tblGrid
    for child in list(grid): grid.remove(child)
    for width in widths:
        col = OxmlElement('w:gridCol'); col.set(qn('w:w'), str(width)); grid.append(col)
    for row in table.rows:
        for cell, width in zip(row.cells, widths): set_cell_width(cell, width)

def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr(); tblHeader = OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'), 'true'); trPr.append(tblHeader)

def set_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr(); cant = OxmlElement('w:cantSplit'); trPr.append(cant)

def set_columns(section, count=2, space=360):
    sectPr = section._sectPr
    cols = sectPr.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols'); sectPr.append(cols)
    cols.set(qn('w:num'), str(count)); cols.set(qn('w:space'), str(space))

def begin_wide(doc):
    set_columns(doc.add_section(WD_SECTION.CONTINUOUS), 1)

def add_table(doc, headers, rows, widths):
    begin_wide(doc)
    table = doc.add_table(rows=1, cols=len(headers)); table.style = 'Table Grid'
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]; cell.text = str(h); set_cell_shading(cell, NAVY)
        for run in cell.paragraphs[0].runs: run.font.color.rgb = RGBColor(255,255,255); run.bold = True; run.font.size = Pt(8.5)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_repeat_table_header(table.rows[0])
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(2)
                for run in p.runs: run.font.size = Pt(8.5); run.font.name = 'Times New Roman'
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_table_geometry(table, widths)
    for row in table.rows: set_row_cant_split(row)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table

def add_caption(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(8)
    r = p.add_run(text); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = RGBColor(80,80,80)
    set_columns(doc.add_section(WD_SECTION.CONTINUOUS), 2)

def add_figure(doc, path, caption, width=6.25):
    begin_wide(doc)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    add_caption(doc, caption)

def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run('Page '); run.font.size = Pt(9); run.font.color.rgb = RGBColor(100,100,100)
    fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1); run._r.append(instrText); run._r.append(fldChar2)

def add_body(doc, text, bold_lead=None):
    p = doc.add_paragraph(); p.style = doc.styles['Normal']
    if bold_lead and text.startswith(bold_lead):
        p.add_run(bold_lead).bold = True; p.add_run(text[len(bold_lead):])
    else: p.add_run(text)
    return p

def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style='List Bullet'); p.add_run(item)

def add_numbers(doc, items):
    numbering = doc.part.numbering_part.element
    abstract_ids = [int(x.get(qn('w:abstractNumId'))) for x in numbering.findall(qn('w:abstractNum'))]
    num_ids = [int(x.get(qn('w:numId'))) for x in numbering.findall(qn('w:num'))]
    abstract_id = max(abstract_ids, default=0) + 1
    num_id = max(num_ids, default=0) + 1
    abstract = OxmlElement('w:abstractNum'); abstract.set(qn('w:abstractNumId'), str(abstract_id))
    multi = OxmlElement('w:multiLevelType'); multi.set(qn('w:val'), 'singleLevel'); abstract.append(multi)
    lvl = OxmlElement('w:lvl'); lvl.set(qn('w:ilvl'), '0')
    start = OxmlElement('w:start'); start.set(qn('w:val'), '1'); lvl.append(start)
    numfmt = OxmlElement('w:numFmt'); numfmt.set(qn('w:val'), 'decimal'); lvl.append(numfmt)
    lvltext = OxmlElement('w:lvlText'); lvltext.set(qn('w:val'), '%1.'); lvl.append(lvltext)
    suff = OxmlElement('w:suff'); suff.set(qn('w:val'), 'tab'); lvl.append(suff)
    ppr = OxmlElement('w:pPr')
    tabs = OxmlElement('w:tabs'); tab = OxmlElement('w:tab'); tab.set(qn('w:val'), 'num'); tab.set(qn('w:pos'), '420'); tabs.append(tab); ppr.append(tabs)
    ind = OxmlElement('w:ind'); ind.set(qn('w:left'), '420'); ind.set(qn('w:hanging'), '300'); ppr.append(ind); lvl.append(ppr)
    abstract.append(lvl); numbering.append(abstract)
    num = OxmlElement('w:num'); num.set(qn('w:numId'), str(num_id))
    absid = OxmlElement('w:abstractNumId'); absid.set(qn('w:val'), str(abstract_id)); num.append(absid); numbering.append(num)
    for item in items:
        p = doc.add_paragraph(); p.style = doc.styles['Normal']
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.5)
        numpr = OxmlElement('w:numPr')
        ilvl = OxmlElement('w:ilvl'); ilvl.set(qn('w:val'), '0'); numpr.append(ilvl)
        numid = OxmlElement('w:numId'); numid.set(qn('w:val'), str(num_id)); numpr.append(numid)
        p._p.get_or_add_pPr().append(numpr); p.add_run(item)

doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21); sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2.0); sec.left_margin = Cm(1.9); sec.right_margin = Cm(1.9)
sec.header_distance = Cm(0.8); sec.footer_distance = Cm(0.8)

styles = doc.styles
normal = styles['Normal']; normal.font.name = 'Times New Roman'; normal.font.size = Pt(10)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; normal.paragraph_format.space_after = Pt(3); normal.paragraph_format.line_spacing = 1.0
for style_name, size, color, before, after in [('Heading 1',10,NAVY,10,4),('Heading 2',10,NAVY,8,3),('Heading 3',10,NAVY,6,3)]:
    s=styles[style_name]; s.font.name='Times New Roman'; s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color)
    s.paragraph_format.space_before=Pt(before); s.paragraph_format.space_after=Pt(after); s.paragraph_format.keep_with_next=True
for style_name in ['List Bullet','List Number']:
    s=styles[style_name]; s.font.name='Times New Roman'; s.font.size=Pt(10); s.paragraph_format.space_after=Pt(3); s.paragraph_format.line_spacing=1.0

header = sec.header.paragraphs[0]; header.text = ''
sec.footer.paragraphs[0].text = ''

# Bloc de tête conforme au gabarit JOIV (traduction anglaise différée)
p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(42); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run("De la structure coloniale à l'aménagement souverain : modélisation des réseaux multimodaux et localisation optimale de nouveaux pôles urbains en RDC par la data science spatiale"); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(18)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('Nehemy Rehoboth¹*'); r.font.name='Times New Roman'; r.font.size=Pt(11); r.bold=True
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('¹ [Affiliation institutionnelle, ville et pays à compléter]'); r.font.name='Times New Roman'; r.font.size=Pt(9); r.italic=True
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(8)
r=p.add_run('* Auteur correspondant : [adresse électronique à compléter]'); r.font.name='Times New Roman'; r.font.size=Pt(9)

p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(4)
r=p.add_run('Résumé—'); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(10)
add_body(doc, "Cet article propose un cadre reproductible de prélocalisation polycentrique multimodale sous rareté des données, appliqué à dix provinces interconnectées de l'Ouest et du Nord-Ouest de la République Démocratique du Congo. La base empirique combine les limites COD-AB, WorldPop 2025, GeoNames, OpenStreetMap/HOT, ESA WorldCover 2021 et SRTM90. Le traitement identifie 14 000 localités habitées, 26 agglomérations analytiques, 175 308 segments routiers, 5 277 segments fluviaux principaux, 198 segments ferroviaires, 30 gares et 142 aérodromes cartographiés. Un graphe spatial, une p-médiane pondérée, une grille multicritère de 25 km et 5 000 simulations Monte-Carlo sont mobilisés. Le scénario à dix pôles réduit la distance moyenne pondérée modélisée à 28,36 km, contre 80,44 km pour cinq pôles. Sous des hypothèses explicites de vitesse effective, le temps moyen correspondant est estimé à 1,06 heure en saison sèche et 1,53 heure en saison humide. Après filtrage environnemental, 75 candidats sont testés et neuf sites provinciaux sont sélectionnés dans plus de 50 % des simulations. Faute de matrice origine-destination, les interactions représentent une demande potentielle et la validation est indirecte, par cohérence intersources et récupération de pôles et corridors connus. La contribution réside dans l'intégration de l'accessibilité, de l'équité territoriale, de l'aptitude environnementale et de l'incertitude dans un contexte de données incomplètes. Les estimations ne sont jamais assimilées à des observations et les résultats constituent un outil de dépistage territorial, non une décision d'implantation.")
add_body(doc, "Mots-clés—aménagement du territoire; réseau multimodal; localisation-allocation; p-médiane; analyse multicritère; Monte Carlo; villes nouvelles; RDC.")

add_body(doc, "Note de préparation : le titre, le résumé, les mots-clés et le corps du manuscrit devront être traduits en anglais avant le dépôt sur la plateforme JOIV.")
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(6)
r=p.add_run('Dates éditoriales : reçue, révisée, acceptée et publiée - réservées à la revue.'); r.italic=True; r.font.size=Pt(8)
set_columns(doc.add_section(WD_SECTION.CONTINUOUS), 2)

doc.add_heading('1. Introduction', level=1)
add_body(doc, "L'organisation territoriale congolaise conserve la trace d'une trajectoire historique dans laquelle de nombreux axes ont été développés pour relier des zones de production à des points d'exportation. Cette trajectoire ne suffit pas, à elle seule, à expliquer la structure actuelle : la croissance démographique, les investissements postérieurs à 1960, les conflits, l'urbanisation informelle et les politiques publiques ont également transformé le réseau. L'héritage colonial est donc traité ici comme une hypothèse historique et spatiale à documenter, et non comme une explication exclusive.")
add_body(doc, "Le problème scientifique est formulé ainsi : comment optimiser conjointement la localisation de pôles urbains et la configuration d'un réseau multimodal afin de réduire la fragmentation spatiale et la dépendance excessive à Kinshasa dans l'Ouest et le Nord-Ouest de la RDC? L'article apporte une première réponse empirique à l'échelle d'un système territorial continu réunissant Grand Bandundu, Grand Équateur, Kinshasa et Kongo Central.")
add_body(doc, "La contribution est quadruple : constitution d'une base géospatiale reproductible; diagnostic du réseau par la théorie des graphes; comparaison de scénarios de localisation-allocation; et présélection environnementale assortie d'une analyse de sensibilité. Le modèle sert à produire des scénarios soumis à la décision publique. Il ne désigne pas automatiquement une « meilleure ville » indépendamment des réalités sociales et institutionnelles.")
add_body(doc, "La nouveauté transférable au-delà du cas congolais est un protocole d'aide à la décision conçu pour les territoires à données rares. Il articule quatre dimensions rarement traitées ensemble : performance d'accessibilité, équilibre provincial, compatibilité environnementale et robustesse aux poids. Les résultats sont comparés à la référence d'un système centré uniquement sur Kinshasa et aux scénarios p = 5, 10 et 15. Trois hypothèses sont testées : H1, l'augmentation du nombre de pôles réduit fortement la distance pondérée; H2, le gain marginal diminue au-delà de dix pôles; H3, certains sites restent sélectionnés malgré l'incertitude des pondérations.")
add_body(doc, "Le positionnement scientifique est celui d'une étude exploratoire de prélocalisation. L'article n'estime pas des flux effectivement réalisés et ne certifie pas la constructibilité des sites. Il examine si des données ouvertes hétérogènes permettent de produire des scénarios transparents, comparables et réfutables avant une validation institutionnelle et de terrain. Cette délimitation évite de confondre plausibilité spatiale, demande potentielle et mobilité observée.")

doc.add_heading('2. Cadre théorique', level=1)
doc.add_heading('2.1 Trajectoire historique et dépendance spatiale', level=2)
add_body(doc, "Les travaux de Taaffe, Morrill et Gould (1963) décrivent l'extension de lignes de pénétration depuis les interfaces d'exportation vers l'intérieur des économies dites sous-développées. Appliquée à la RDC, cette perspective permet d'interroger la persistance de réseaux linéaires et discontinus. Toutefois, l'attribution causale exige une comparaison diachronique des infrastructures coloniales et post-indépendance, qui dépasse le périmètre empirique de la présente application.")
doc.add_heading('2.2 Polycentrisme et villes nouvelles', level=2)
add_body(doc, "Le polycentrisme vise un réseau de villes complémentaires plutôt qu'une hiérarchie entièrement dominée par une métropole. Une ville nouvelle n'est viable que si son site physique, sa connexion aux flux, ses fonctions économiques et la séquence des investissements sont cohérents. Le concept de « ville souveraine » est ici opérationnalisé comme un pôle capable de combiner connectivité, services, transformation locale, résilience et insertion dans plusieurs bassins de population.")
doc.add_heading('2.3 Réseaux complexes et localisation-allocation', level=2)
add_body(doc, "La théorie des graphes décrit les villes et infrastructures comme des nœuds et des arêtes. La centralité d'intermédiarité mesure la fonction de passage; la proximité pondérée mesure l'accès aux autres nœuds; la p-médiane choisit p implantations minimisant la somme des distances entre demandes et équipements. L'analyse multicritère complète cette optimisation en imposant des conditions physiques et environnementales.")

doc.add_heading("3. Zone d'étude et données", level=1)
add_body(doc, "La zone comprend dix provinces : Kinshasa, Kongo Central, Kwango, Kwilu, Maï-Ndombe, Équateur, Mongala, Nord-Ubangi, Sud-Ubangi et Tshuapa. Elles sont analysées comme un seul système territorial, et non comme dix études indépendantes. Cette configuration permet d'observer la transition entre le corridor atlantique, la métropole de Kinshasa, les espaces du Grand Bandundu et la dorsale fluviale du Grand Équateur.")
data_rows = [
    ('Limites administratives','COD-AB / OCHA','Vecteur','Découpage des 10 provinces'),
    ('Population','WorldPop 2025 R2025A','100 m','Population provinciale et autour des nœuds'),
    ('Localités','GeoNames, extraction COD','Points','14 000 localités dans la zone'),
    ('Routes','HOT/OpenStreetMap','Vecteur','175 308 segments filtrés'),
    ('Hydrographie','HOT/OpenStreetMap','Vecteur','Rivières, canaux et chenaux'),
    ('Rail et gares','HOT/OpenStreetMap','Vecteur','Lignes et stations cartographiées'),
    ('Aérodromes','HOT/OpenStreetMap','Vecteur','Aérodromes et pistes cartographiés'),
    ('Occupation du sol','ESA WorldCover 2021','10 m','Exclusions et compatibilité préliminaire'),
    ('Altitude et pente','SRTM90 via OpenTopoData','~90 m','Pente locale sur sites présélectionnés'),
]
add_table(doc,['Bloc','Source','Résolution/type','Usage'],data_rows,[1750,2400,1250,3960])
add_caption(doc,"Tableau 1. Architecture des données utilisées. Les dates correspondent aux versions accessibles lors du traitement de septembre 2026.")
add_body(doc, "La population WorldPop est une estimation modélisée et non un recensement. La population autour des villes est calculée dans un rayon de 5 km; elle ne doit pas être interprétée comme la population administrative officielle de chaque ville. La complétude d'OpenStreetMap varie également selon les provinces et peut avantager les espaces mieux cartographiés.")

doc.add_heading('4. Méthodologie', level=1)
doc.add_heading('4.1 Construction des nœuds et du réseau multimodal', level=2)
add_body(doc, "L'extraction nationale GeoNames contient 66 785 entités, dont 37 236 lieux habités. Après intersection spatiale, 14 000 localités appartiennent à la zone d'étude. Un premier seuil combinant statut administratif et population déclarée a produit 28 nœuds. Masina a ensuite été agrégée à Kinshasa et Bolenge à Mbandaka afin d'éviter le double comptage d'une même agglomération, laissant 26 nœuds analytiques.")
add_body(doc, "Les réseaux routier, fluvial, ferroviaire et aérien sont découpés aux limites des dix provinces. L'accessibilité multimodale est mesurée par la proximité aux infrastructures cartographiées. Une proximité ne prouve ni la navigabilité d'un cours d'eau, ni l'état d'une voie ferrée, ni l'activité d'un aérodrome.")
add_figure(doc, RES := ROOT/'data/03_resultats/reseau_multimodal_phase5_v7.png', 'Figure 1. Infrastructures multimodales cartographiées dans la zone d’étude.')

doc.add_heading('4.2 Graphe spatial exploratoire', level=2)
add_body(doc, "Le réseau routier OSM présente de nombreuses composantes déconnectées, en partie à cause de ruptures de numérisation. Calculer directement les centralités sur ce graphe incomplet aurait produit des résultats instables. Un graphe spatial exploratoire connecté a donc été construit à partir d'un arbre couvrant minimal complété par les trois voisins géographiques les plus proches de chaque nœud. Il comprend 26 nœuds et 49 arêtes pondérées par la distance géodésique. Les centralités qui en résultent décrivent la structure du modèle spatial, non des itinéraires observés.")
add_figure(doc, ROOT/'data/03_resultats/graphe_centralites_phase6.png', 'Figure 2. Graphe spatial exploratoire et score de centralité stratégique.')

doc.add_heading('\u00a04.3 Localisation-allocation des pôles existants', level=2)
add_body(doc, "Pour un ensemble de pôles F de cardinal p, la fonction objectif est Z(F) = Σᵢ Pᵢ minⱼ∈F(dᵢⱼ), où Pᵢ représente la population WorldPop dans un rayon de 5 km et dᵢⱼ le plus court chemin du graphe spatial. Une construction gloutonne est suivie d'échanges locaux jusqu'à stabilisation. Trois valeurs de p sont testées : 5, 10 et 15.")

doc.add_heading('4.4 Grille des sites nouveaux et analyse multicritère', level=2)
add_body(doc, "Une grille de 25 km est générée sur la zone. Les centres situés à moins de 40 km des villes existantes sont écartés. Un candidat doit se trouver à moins de 25 km d'une route ou de 15 km d'une voie d'eau. Le score préliminaire combine potentiel populationnel (30 %), route (25 %), eau (20 %), rail (10 %), aérodrome (5 %) et lacune territoriale (10 %). Les sites retenus sont espacés d'au moins 100 km.")
add_body(doc, "WorldCover exclut, à ce stade, les cellules classées comme eau, zones humides, bâti ou couverture arborée. La pente est estimée par cinq requêtes SRTM90 autour de chaque site présélectionné; le seuil exploratoire est fixé à 8 %. L'exclusion de toute cellule arborée est volontairement conservatrice afin de limiter le risque de déforestation et d'artificialisation. Elle ne distingue toutefois pas les forêts primaires intactes des forêts secondaires dégradées, plantations, jachères arborées ou mosaïques agroforestières. Une analyse ultérieure devra combiner intégrité forestière, perte de couvert et valeur de conservation afin d'appliquer des restrictions différenciées sans compromettre les écosystèmes prioritaires.")

doc.add_heading('4.5 Analyse de sensibilité', level=2)
add_body(doc, "Cinq mille vecteurs de poids sont tirés dans une distribution de Dirichlet centrée sur les poids de référence. À chaque simulation, le meilleur candidat de chaque province est enregistré. La fréquence de sélection mesure la robustesse du site à la variation des préférences. La graine aléatoire 20260902 rend l'expérience reproductible.")

doc.add_heading('4.6 Estimation des temps sous données manquantes', level=2)
add_body(doc, "Faute de vitesses observées homogènes, les distances du graphe sont converties en temps indicatifs par scénarios. Le scénario sec suppose une vitesse effective moyenne de 35 km/h et 15 minutes de pénalité multimodale; le scénario humide, 24 km/h et 21 minutes. L'intervalle exploratoire combine une borne favorable de 45 km/h avec 9 minutes de pénalité et une borne défavorable de 18 km/h avec 30 minutes. Ces paramètres sont des hypothèses de travail inspirées de conditions contrastées; ils ne sont ni des mesures de trafic ni des horaires garantis. La formule est T = d/v + tau, avec d la distance modélisée, v la vitesse effective et tau la rupture de charge.")

doc.add_heading('4.7 Validation spatiale indirecte', level=2)
add_body(doc, "En l'absence de matrice origine-destination, la plausibilité est évaluée par quatre contrôles : cohérence des sources; récupération de pôles majeurs; concordance avec les corridors cartographiés; et stabilité sous 5 000 variations des poids. Cette validation indirecte du dispositif de prélocalisation ne valide ni les volumes de trafic, ni les temps réels, ni la faisabilité foncière.")
validation_rows=[
    ('Cohérence intersources','Convergence population-localités-réseaux','Contrôle de plausibilité'),
    ('Récupération des pôles','Émergence de centres majeurs connus','Validité apparente'),
    ('Corridors structurants','Axes terrestre et fluviaux retrouvés','Concordance qualitative'),
    ('Robustesse','Fréquences de sélection sous 5 000 pondérations','Sensibilité aux préférences'),
]
add_table(doc,['Axe','Test réalisé','Portée'],validation_rows,[2200,4700,2460])
add_caption(doc,"Tableau 2. Cadre de validation spatiale indirecte. Aucun de ces contrôles ne remplace une validation primaire des flux et des sites.")
assumption_rows=[
    ('Saison sèche','35 km/h','0,25 h','Estimation centrale'),
    ('Saison humide','24 km/h','0,35 h','Estimation prudente'),
    ('Borne favorable','45 km/h','0,15 h','Analyse d’incertitude'),
    ('Borne défavorable','18 km/h','0,50 h','Analyse d’incertitude'),
]
doc.add_page_break()
add_table(doc,['Hypothèse','Vitesse effective','Pénalité','Statut'],assumption_rows,[2100,2100,1900,3260])
add_caption(doc,"Tableau 3. Hypothèses explicites de conversion distance-temps. Toutes les valeurs sont estimées et remplaçables lors de la calibration.")

doc.add_heading('5. Résultats', level=1)
doc.add_heading('5.1 Diagnostic démographique et multimodal', level=2)
pop_rows=[('Kinshasa','9,56'),('Kwilu','7,87'),('Kongo Central','7,18'),('Sud-Ubangi','3,68'),('Kwango','3,07'),('Maï-Ndombe','2,66'),('Mongala','2,62'),('Tshuapa','2,38'),('Équateur','2,31'),('Nord-Ubangi','1,91')]
add_table(doc,['Province','Population modélisée 2025 (millions)'],pop_rows,[4200,5160])
add_caption(doc,'Tableau 4. Estimations WorldPop agrégées aux limites provinciales; total du système : environ 43,23 millions.')
add_body(doc, "Le sous-réseau extrait comprend 5 277 segments fluviaux principaux, 198 segments ferroviaires, 30 gares et 142 aérodromes. Vingt-sept des 28 nœuds initiaux sont situés à moins de 10 km d'une voie d'eau, six à moins de 10 km du rail et vingt-six à moins de 30 km d'un aérodrome cartographié. Kinshasa, Matadi, Kimpese et Mbanza-Ngungu présentent l'accessibilité aux quatre modes selon ces seuils.")

doc.add_heading('5.2 Centralités territoriales', level=2)
central_rows=[('Kinshasa','Kinshasa','0,732'),('Matadi','Kongo Central','0,678'),('Kimpese','Kongo Central','0,670'),('Mbanza-Ngungu','Kongo Central','0,624'),('Kenge','Kwango','0,585'),('Bandundu','Kwilu','0,540'),('Inkisi','Kongo Central','0,510'),('Boma','Kongo Central','0,485'),('Mbandaka','Équateur','0,459'),('Inongo','Maï-Ndombe','0,411')]
add_table(doc,['Rang/nœud','Province','Score stratégique'],[(f'{i+1}. {r[0]}',r[1],r[2]) for i,r in enumerate(central_rows)],[3300,3300,2760])
add_caption(doc,'Tableau 5. Dix premiers nœuds selon le score stratégique exploratoire.')
add_body(doc, "Kenge obtient la plus forte centralité d'intermédiarité, suivie de Bandundu, Kinshasa, Inongo et Mbandaka. Cette configuration suggère une fonction de charnière de Kenge entre Kinshasa, le Kongo Central et le Grand Bandundu. Elle reste conditionnée par la topologie du graphe exploratoire.")

doc.add_heading('5.3 Scénarios de p-médiane', level=2)
pmed_rows=[('5','80,44','279,62','57,41 %','98,21 %','81,92 %'),('10','28,36','184,47','87,20 %','100,00 %','93,63 %'),('15','12,58','115,89','96,97 %','100,00 %','97,17 %')]
add_table(doc,['p','Distance moyenne (km)','Distance max. (km)','Pop. <=100 km','Pop. <=250 km','Gain vs Kinshasa seule'],pmed_rows,[600,1700,1500,1500,1500,2560])
add_caption(doc,'Tableau 6. Comparaison des scénarios de localisation-allocation.')
add_body(doc, "Le scénario à dix pôles constitue le compromis le plus lisible entre réduction de distance et nombre d'investissements. Il sélectionne Mbandaka, Kinshasa, Matadi, Mbanza-Ngungu, Moanda, Bandundu, Kikwit, Bumba, Gemena et Boende. Kenge, pourtant très intermédiaire, n'est pas retenue dans ce scénario parce que la p-médiane minimise la distance population-pôle et n'intègre pas directement un objectif de fonction de corridor. Cette divergence justifie une optimisation multi-objectifs.")
time_rows=[
    ('5','2,55 h','3,70 h','1,94-4,97 h'),
    ('10','1,06 h','1,53 h','0,78-2,08 h'),
    ('15','0,61 h','0,87 h','0,43-1,20 h'),
]
add_table(doc,['p','Temps sec estimé','Temps humide estimé','Intervalle exploratoire'],time_rows,[1200,2600,2600,2960])
add_caption(doc,"Tableau 7. Temps moyens indicatifs dérivés des distances pondérées; il ne s'agit pas de temps observés.")
add_body(doc, "Le passage de cinq à dix pôles produit la réduction la plus importante : -52,08 km de distance moyenne, soit -64,7 %. Le passage de dix à quinze pôles apporte encore -15,78 km, soit -55,6 % relativement au scénario p = 10, mais mobilise cinq pôles supplémentaires. Par rapport à Kinshasa seule, les gains modélisés sont respectivement de 81,92 %, 93,63 % et 97,17 %. H1 est donc soutenue. H2 est soutenue en termes de gain absolu et de besoin d'investissement, mais pas au sens d'un seuil économique définitif, puisque les coûts de construction ne sont pas encore observés.")
add_figure(doc, ROOT/'data/03_resultats/scenarios_pmedian_phase7.png', 'Figure 3. Scénarios p = 5, p = 10 et p = 15.')

doc.add_heading('5.4 Présélection des sites nouveaux', level=2)
add_body(doc, "La grille initiale comprend 1 220 centres; 1 031 satisfont les critères d'éloignement et d'accès. Sans contrainte provinciale, la moitié des dix premiers candidats se concentre au Kongo Central, ce qui traduit à la fois sa position, sa population accessible et une meilleure densité de cartographie OSM. Un scénario d'équilibre limite donc la sélection à un site par province.")
add_figure(doc, ROOT/'data/03_resultats/sites_nouveaux_phase8.png', 'Figure 4. Présélection des sites nouveaux avant filtre environnemental.')

doc.add_heading('5.5 Filtrage environnemental', level=2)
add_body(doc, "WorldCover classe 740 des 1 031 centres en couverture arborée, 228 en végétation herbacée, 48 en arbustes, 10 en eau, 3 en zone humide herbacée, 1 en bâti et 1 en agriculture. Le filtre conservateur exclut les 740 cellules arborées et 14 cellules d'eau, de zone humide ou bâties. Parmi les 76 meilleurs candidats provinciaux compatibles soumis à SRTM, 75 ont une pente inférieure ou égale à 8 %. Cette exclusion forestière maximise la précaution mais peut produire des faux négatifs dans des mosaïques dégradées ou agroforestières; aucun site forestier exclu ne doit être réintroduit sans données plus fines sur l'intégrité écologique et la perte de couvert.")
env_rows=[('Kimpika','Kongo Central','Herbacée','0,75 %'),('Komo','Kinshasa','Herbacée','0,45 %'),('Pana','Kwilu','Herbacée','0,85 %'),('Fumu-Mashi','Kwango','Arbustes','0,55 %'),('Kintswe','Maï-Ndombe','Herbacée','0,90 %'),('Bwamandema','Sud-Ubangi','Herbacée','0,15 %'),('Yanganga','Tshuapa','Herbacée','0,55 %'),('Buanza','Équateur','Herbacée','0,40 %'),('Bale Deuxième','Nord-Ubangi','Herbacée','2,75 %'),('Amamba','Mongala','Herbacée','2,45 %')]
add_table(doc,['Localité de référence','Province','Couverture','Pente'],env_rows,[2500,2500,2200,2160])
add_caption(doc,"Tableau 8. Sélection provinciale après filtres WorldCover et SRTM. Le nom est celui de la localité GeoNames la plus proche du centre de cellule.")
add_figure(doc, ROOT/'data/03_resultats/sites_nouveaux_environnement_phase9.png', 'Figure 5. Sites après filtres d’occupation du sol et de pente.', width=4.7)

doc.add_heading('\u00a05.6 Robustesse des sites', level=2)
robust_rows=[('Yanganga','Tshuapa','100,00 %','Élevée'),('Ebale','Maï-Ndombe','98,18 %','Modérée'),('Fumu-Mashi','Kwango','95,46 %','Élevée'),('Bwamandema','Sud-Ubangi','94,08 %','Élevée'),('Amamba','Mongala','86,90 %','Modérée'),('Bale Deuxième','Nord-Ubangi','81,68 %','Modérée'),('Pana','Kwilu','74,10 %','Élevée'),('Komo','Kinshasa','72,14 %','Élevée'),('Kimpika','Kongo Central','59,98 %','Modérée'),('Buanza','Équateur','49,40 %','Élevée')]
add_table(doc,['Localité de référence','Province','Fréquence','Exposition hydrologique proxy'],robust_rows,[2400,2300,1400,3260])
add_caption(doc,'Tableau 9. Robustesse sous 5 000 pondérations plausibles.')
add_body(doc, "Six sites sont sélectionnés dans au moins 80 % des simulations et neuf dans plus de 50 %. Le proxy hydrologique signale néanmoins six sites proches de l'eau sur terrain très plat. Il ne constitue pas une carte d'inondation; ces sites doivent être suspendus à une analyse hydrologique dédiée. Buanza est le résultat le moins stable (49,40 %) et nécessite une comparaison approfondie avec Nkondi et Inganda.")
add_body(doc, "La stabilité de six sites au seuil de 80 % soutient H3. Cette robustesse concerne toutefois la variation des poids du modèle, pas l'incertitude de toutes les données d'entrée. Une analyse complète devra perturber simultanément la population, la complétude du réseau, les vitesses, les seuils environnementaux et les coordonnées candidates.")
add_figure(doc, ROOT/'data/03_resultats/robustesse_sites_phase10.png', 'Figure 6. Fréquence de sélection des sites dans 5 000 simulations Monte-Carlo.', width=4.7)

doc.add_heading('6. Discussion', level=1)
doc.add_heading('6.1 Ce que démontrent les résultats', level=2)
add_body(doc, "L'application démontre qu'il est techniquement possible de construire une chaîne reproductible allant des données ouvertes à des scénarios territoriaux quantifiés. Elle met en évidence trois structures : la persistance du poids de Kinshasa et du corridor du Kongo Central; le rôle de charnière de Kenge et Bandundu; et l'importance d'un ensemble de pôles septentrionaux autour de Mbandaka, Bumba, Lisala, Gemena et Boende.")
add_body(doc, "La différence entre centralité et p-médiane est substantielle. Une ville peut être essentielle comme pont territorial sans minimiser la distance totale à la population. Une politique d'aménagement souverain doit donc combiner accessibilité, équilibre spatial, résilience et coûts, au lieu d'optimiser une seule fonction.")
doc.add_heading('6.2 Interprétation des sites nouveaux', level=2)
add_body(doc, "Les coordonnées proposées correspondent au centre de cellules de 25 km et les noms associés désignent seulement la localité connue la plus proche. Un centre de cellule ne peut être assimilé à une parcelle disponible. La résolution doit être affinée à 1-5 km après consultation locale, puis à l'échelle cadastrale et géotechnique avant toute décision.")
doc.add_heading('6.3 Héritage colonial et transformations postérieures', level=2)
add_body(doc, "Les résultats montrent une concentration fonctionnelle le long du corridor Kinshasa-Kongo Central et une faible continuité ferroviaire vers le Nord-Ouest. Ils sont compatibles avec l'hypothèse d'une trajectoire historique extravertie, mais ne l'identifient pas causalement. Une démonstration historique complète requerrait la numérisation des réseaux à plusieurs dates, l'inventaire des investissements depuis 1960 et une décomposition de la structure actuelle entre héritage, croissance urbaine et politiques post-indépendance.")
doc.add_heading('6.4 Portée internationale et comparaison méthodologique', level=2)
add_body(doc, "La valeur générale du cadre tient moins au classement particulier des sites qu'à la séparation explicite entre données observées, calculs reproductibles, paramètres estimés et validations manquantes. La p-médiane fournit une référence d'efficience, la contrainte d'un site par province introduit l'équité, WorldCover et SRTM apportent une compatibilité physique préliminaire, et Monte-Carlo teste la dépendance aux préférences. Cette architecture est transposable à d'autres grands territoires où l'information fonctionnelle sur les réseaux reste fragmentaire.")
add_body(doc, "La comparaison avec Kinshasa comme pôle unique joue le rôle de scénario naïf de référence. Elle montre la valeur ajoutée de configurations polycentriques, tandis que la divergence entre centralité de réseau et solution p-médiane révèle la dépendance au critère choisi. Une comparaison future avec k-médoïdes contraint, couverture maximale et optimisation multi-objectifs sera nécessaire pour établir la supériorité relative d'un algorithme plutôt que la seule cohérence du cadre.")

doc.add_heading('7. Limites et conditions de validation', level=1)
add_numbers(doc,[
    "Les flux de voyageurs et de marchandises ne sont pas observés; le modèle gravitationnel n'est donc pas encore calibré.",
    "Le graphe spatial garantit la connexité analytique mais ne reproduit pas tous les itinéraires réellement praticables.",
    "La population WorldPop est modélisée; ses incertitudes doivent être reportées, notamment dans les provinces faiblement documentées.",
    "La densité OSM varie selon les territoires et peut favoriser le Kongo Central et Kinshasa.",
    "La navigabilité des cours d'eau, l'état des rails, gares et aérodromes doivent être vérifiés par inventaire technique.",
    "Les aires protégées ne sont pas encore intégrées aux résultats numériques. La source WDPA de l'UNEP-WCMC a été identifiée, mais son extraction doit être effectuée dans un environnement authentifié, versionnée et documentée conformément aux conditions d'utilisation.",
    "Le proxy hydrologique ne remplace pas une carte probabiliste d'inondation.",
    "Les droits fonciers coutumiers, conflits, déplacements et acceptabilité sociale ne sont pas observables dans les couches utilisées.",
])
add_body(doc, "En conséquence, les sorties doivent être lues comme une présélection scientifique destinée à organiser des investigations, non comme un acte de classement foncier ou une recommandation immédiate de construction.")

doc.add_heading('8. Protocole de validation et mise en œuvre', level=1)
add_numbers(doc,[
    "Valider les dix sites avec les services provinciaux, les autorités coutumières et les communautés concernées.",
    "Exporter les polygones et points WDPA pour ISO3 = COD, conserver la date de version et l'attribution UNEP-WCMC/IUCN, appliquer le masque aux 1 031 cellules, puis recalculer et publier le nombre de candidats exclus. Ajouter ensuite concessions, titres fonciers et zones inondables officielles.",
    "Réaliser un audit de terrain de la route, du rail, de la navigabilité, des ports et aérodromes dans un rayon de 50 km.",
    "Collecter des flux observés : comptages routiers, trafic portuaire, fret ferroviaire, mobilité téléphonique agrégée et enquêtes origine-destination.",
    "Calibrer les temps et coûts par mode, puis remplacer les distances géodésiques par des coûts généralisés observés.",
    "Retenir deux ou trois sites pilotes et conduire les études hydrologiques, géotechniques, environnementales et sociales réglementaires.",
    "Comparer après validation les scénarios p = 5, 10 et 15 dans un modèle multi-objectifs incluant budget, équité et résilience.",
])

doc.add_heading('8.1 Critères de remplacement des estimations', level=2)
add_body(doc, "Chaque hypothèse approximative possède une règle de remplacement. Les vitesses seront remplacées dès que des relevés GPS ou des temps d'itinéraire seront disponibles; les pénalités de transfert par des observations portuaires et ferroviaires; le proxy hydrologique par des cartes de fréquence et de profondeur des crues; les exclusions foncières par les données cadastrales et coutumières. Une estimation ne devient une observation qu'après documentation de sa source, de sa date, de son unité et de sa méthode de contrôle.")

doc.add_heading('8.2 Données, code et reproductibilité', level=2)
add_body(doc, "Le paquet de réplication doit comprendre les scripts de traitement, les tableaux dérivés, les paramètres, la graine aléatoire, un dictionnaire des variables et un fichier de provenance. Les données redistribuables peuvent être déposées avec le code; les couches soumises à licence doivent être remplacées par leurs liens, versions et instructions de téléchargement. Le manuscrit devra indiquer l'adresse pérenne du dépôt avant soumission. Aucun renseignement individuel n'est utilisé; les enjeux éthiques concernent surtout l'interprétation territoriale et la consultation des populations potentiellement affectées.")

doc.add_heading('8.3 Déclaration de disponibilité et niveau de preuve', level=2)
add_body(doc, "Les résultats dérivés, paramètres et scripts devront être déposés dans une archive pérenne avant l'envoi définitif. Les données sources non redistribuables seront référencées par producteur, version, date d'accès, licence et procédure d'extraction. Le niveau de preuve revendiqué est celui d'une prélocalisation exploratoire validée indirectement. Toute formulation laissant entendre des comptages de trafic, des enquêtes de terrain ou une validation foncière primaire doit être exclue tant que ces opérations n'ont pas été réalisées et archivées.")

doc.add_heading('9. Conclusion', level=1)
add_body(doc, "Cette version transforme un cadre conceptuel en une application exploratoire renforcée sur un système territorial de dix provinces. Elle fournit des données, des scripts reproductibles, des cartes, des centralités, des scénarios de p-médiane, une grille de sites nouveaux, des filtres environnementaux, des temps indicatifs et une analyse de robustesse. Le résultat principal n'est ni l'observation des flux effectifs ni l'annonce définitive de dix villes nouvelles, mais la démonstration qu'une décision territoriale sous rareté des données peut être structurée, testée et contestée à partir d'indicateurs explicites.")
add_body(doc, "Le scénario à dix pôles existants apparaît comme un compromis opérationnel pour la structuration régionale. Pour les sites nouveaux, Yanganga, Ebale, Fumu-Mashi, Bwamandema, Amamba et Bale Deuxième présentent les meilleures fréquences de sélection, tandis que les signaux hydrologiques imposent une prudence forte. L'étape suivante n'est plus une optimisation supplémentaire sur les mêmes données : elle consiste à confronter les résultats aux couches officielles et au terrain.")

doc.add_heading('Déclarations', level=1)
add_body(doc, "Contribution de l'auteur—Conception, méthodologie, analyse, visualisation et rédaction : Nehemy Rehoboth. Cette mention devra être ajustée si d'autres auteurs remplissent les critères d'attribution.")
add_body(doc, "Financement—[À compléter : indiquer la source de financement ou déclarer l'absence de financement externe].")
add_body(doc, "Conflits d'intérêts—L'auteur déclare [à confirmer] ne connaître aucun conflit d'intérêts susceptible d'influencer ce travail.")
add_body(doc, "Disponibilité des données et du code—Les liens pérennes vers les scripts, paramètres et résultats dérivés seront ajoutés avant la soumission. Les données tierces seront référencées selon leurs licences respectives.")

doc.add_heading('Références', level=1)
refs=[
"[1] E. J. Taaffe, R. L. Morrill, and P. R. Gould, “Transport expansion in underdeveloped countries,” Geographical Review, vol. 53, no. 4, pp. 503-529, 1963.",
"[2] J.-P. Rodrigue, The Geography of Transport Systems, 5th ed. New York, NY, USA: Routledge, 2020.",
"[3] M. Batty, The New Science of Cities. Cambridge, MA, USA: MIT Press, 2013.",
"[4] World Bank, World Development Report 2009: Reshaping Economic Geography. Washington, DC, USA: World Bank, 2009.",
"[5] S. Davoudi, “Polycentricity in European spatial planning,” European Planning Studies, vol. 11, no. 8, pp. 979-999, 2003.",
"[6] M. Burger and E. Meijers, “Form follows function? Linking morphological and functional polycentricity,” Urban Studies, vol. 49, no. 5, pp. 1127-1149, 2012.",
"[7] M. Barthélemy, “Spatial networks,” Physics Reports, vol. 499, nos. 1-3, pp. 1-101, 2011.",
"[8] M. E. J. Newman, Networks: An Introduction. Oxford, UK: Oxford University Press, 2010.",
"[9] S. Boccaletti, V. Latora, Y. Moreno, M. Chavez, and D.-U. Hwang, “Complex networks: Structure and dynamics,” Physics Reports, vol. 424, nos. 4-5, pp. 175-308, 2006.",
"[10] S. L. Hakimi, “Optimum distribution of switching centers and the absolute centers and medians of a graph,” Operations Research, vol. 12, no. 3, pp. 450-459, 1964.",
"[11] C. S. ReVelle and R. W. Swain, “Central facilities location,” Geographical Analysis, vol. 2, no. 1, pp. 30-42, 1970.",
"[12] M. B. Teitz and P. Bart, “Heuristic methods for estimating the generalized vertex median of a weighted graph,” Operations Research, vol. 16, no. 5, pp. 955-961, 1968.",
"[13] R. Church and C. ReVelle, “The maximal covering location problem,” Papers of the Regional Science Association, vol. 32, pp. 101-118, 1974.",
"[14] M. S. Daskin, Network and Discrete Location: Models, Algorithms, and Applications, 2nd ed. Hoboken, NJ, USA: Wiley, 2013.",
"[15] J. Malczewski, “GIS-based multicriteria decision analysis: A survey of the literature,” International Journal of Geographical Information Science, vol. 20, no. 7, pp. 703-726, 2006.",
"[16] T. L. Saaty, The Analytic Hierarchy Process. New York, NY, USA: McGraw-Hill, 1980.",
"[17] J. Current, M. Daskin, and D. Schilling, “Discrete network location models,” in Facility Location: Applications and Theory, Z. Drezner and H. W. Hamacher, Eds. Berlin, Germany: Springer, 2002, pp. 81-118.",
"[18] M. E. O’Kelly, “A quadratic integer program for the location of interacting hub facilities,” European Journal of Operational Research, vol. 32, no. 3, pp. 393-404, 1987.",
"[19] A. Saltelli, M. Ratto, T. Andres, F. Campolongo, J. Cariboni, D. Gatelli, M. Saisana, and S. Tarantola, Global Sensitivity Analysis: The Primer. Chichester, UK: Wiley, 2008.",
"[20] I. M. Sobol’, “Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates,” Mathematics and Computers in Simulation, vol. 55, nos. 1-3, pp. 271-280, 2001.",
"[21] F. V. Louveaux, “Discrete stochastic location models,” Annals of Operations Research, vol. 6, pp. 23-34, 1986.",
"[22] A. Sen and A. G. Wilson, “The entropy maximising approach to trip distribution modelling,” Transportation Research, vol. 4, no. 4, pp. 367-382, 1970.",
"[23] WorldPop, “Democratic Republic of the Congo population raster, R2025A,” University of Southampton, Southampton, UK, 2025.",
"[24] A. J. Tatem, “WorldPop, open data for spatial demography,” Scientific Data, vol. 4, Art. no. 170004, 2017.",
"[25] GeoNames, “GeoNames geographical database: Democratic Republic of the Congo dump,” 2026. [Online]. Available: https://download.geonames.org/export/dump/",
"[26] OpenStreetMap contributors, “Roads, waterways, railways and airports of the Democratic Republic of the Congo,” Humanitarian Data Exchange, 2026.",
"[27] M. Haklay and P. Weber, “OpenStreetMap: User-generated street maps,” IEEE Pervasive Computing, vol. 7, no. 4, pp. 12-18, 2008.",
"[28] C. Barrington-Leigh and A. Millard-Ball, “The world’s user-generated road map is more than 80% complete,” PLOS ONE, vol. 12, no. 8, Art. no. e0180698, 2017.",
"[29] ESA WorldCover Consortium, “ESA WorldCover 10 m 2021 v200,” European Space Agency, 2021. [Online]. Available: https://esa-worldcover.org/en/data-access",
"[30] D. Zanaga et al., “ESA WorldCover 10 m 2021 v200,” Zenodo, 2022, doi: 10.5281/zenodo.7254221.",
"[31] T. G. Farr et al., “The Shuttle Radar Topography Mission,” Reviews of Geophysics, vol. 45, no. 2, Art. no. RG2004, 2007.",
"[32] B. Lehner and G. Grill, “Global river hydrography and network routing: Baseline data and new approaches to study the world’s large river systems,” Hydrological Processes, vol. 27, no. 15, pp. 2171-2186, 2013.",
"[33] OpenTopoData, “SRTM 90 m elevation API documentation,” 2026. [Online]. Available: https://www.opentopodata.org/datasets/srtm/",
"[34] UNEP-WCMC and IUCN, “Protected Planet: The World Database on Protected Areas, September 2026 version,” Cambridge, UK, 2026. [Online]. Available: https://www.protectedplanet.net/",
"[35] UN-Habitat, World Cities Report 2022: Envisaging the Future of Cities. Nairobi, Kenya: United Nations Human Settlements Programme, 2022.",
"[36] K. T. Geurs and B. van Wee, “Accessibility evaluation of land-use and transport strategies: Review and research directions,” Journal of Transport Geography, vol. 12, no. 2, pp. 127-140, 2004.",
]
for ref in refs:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.LEFT; p.paragraph_format.left_indent=Cm(0.45); p.paragraph_format.first_line_indent=Cm(-0.45); p.paragraph_format.space_after=Pt(2)
    r=p.add_run(ref); r.font.name='Times New Roman'; r.font.size=Pt(8)

doc.add_heading('Annexe - Statut des résultats', level=1)
status_rows=[
('Observé/téléchargé','Limites, localités, routes, hydrographie, rail, gares, aérodromes, WorldCover, SRTM'),
('Calculé sur données réelles','Population agrégée, proximités, centralités, p-médiane, scores, Monte-Carlo'),
('Estimé par hypothèse','Vitesses effectives, pénalités de transfert, temps sec/humide et intervalles'),
('Modélisé/exploratoire','Arêtes du graphe spatial, distances de scénario, poids multicritères, proxy hydrologique'),
('Validation indirecte','Cohérence intersources, récupération de pôles connus, concordance qualitative des corridors, robustesse aux poids'),
('Non encore validé','Flux effectifs, état fonctionnel, navigabilité, inondation officielle, masque WDPA appliqué, foncier, acceptabilité'),
]
add_table(doc,['Statut','Éléments'],status_rows,[2400,6960])

heading_map = {
    '1. Introduction':'I. INTRODUCTION',
    '2. Cadre théorique':'II. CADRE THÉORIQUE',
    '2.1 Trajectoire historique et dépendance spatiale':'A. Trajectoire historique et dépendance spatiale',
    '2.2 Polycentrisme et villes nouvelles':'B. Polycentrisme et villes nouvelles',
    '2.3 Réseaux complexes et localisation-allocation':'C. Réseaux complexes et localisation-allocation',
    "3. Zone d'étude et données":"III. ZONE D'ÉTUDE ET DONNÉES",
    '4. Méthodologie':'IV. MÉTHODOLOGIE',
    '4.1 Construction des nœuds et du réseau multimodal':'A. Construction des nœuds et du réseau multimodal',
    '4.2 Graphe spatial exploratoire':'B. Graphe spatial exploratoire',
    '\u00a04.3 Localisation-allocation des pôles existants':'C. Localisation-allocation des pôles existants',
    '4.4 Grille des sites nouveaux et analyse multicritère':'D. Grille des sites nouveaux et analyse multicritère',
    '4.5 Analyse de sensibilité':'E. Analyse de sensibilité',
    '4.6 Estimation des temps sous données manquantes':'F. Estimation des temps sous données manquantes',
    '4.7 Validation spatiale indirecte':'G. Validation spatiale indirecte',
    '5. Résultats':'V. RÉSULTATS',
    '5.1 Diagnostic démographique et multimodal':'A. Diagnostic démographique et multimodal',
    '5.2 Centralités territoriales':'B. Centralités territoriales',
    '5.3 Scénarios de p-médiane':'C. Scénarios de p-médiane',
    '5.4 Présélection des sites nouveaux':'D. Présélection des sites nouveaux',
    '5.5 Filtrage environnemental':'E. Filtrage environnemental',
    '\u00a05.6 Robustesse des sites':'F. Robustesse des sites',
    '6. Discussion':'VI. DISCUSSION',
    '6.1 Ce que démontrent les résultats':'A. Ce que démontrent les résultats',
    '6.2 Interprétation des sites nouveaux':'B. Interprétation des sites nouveaux',
    '6.3 Héritage colonial et transformations postérieures':'C. Héritage colonial et transformations postérieures',
    '6.4 Portée internationale et comparaison méthodologique':'D. Portée internationale et comparaison méthodologique',
    '7. Limites et conditions de validation':'VII. LIMITES ET CONDITIONS DE VALIDATION',
    '8. Protocole de validation et mise en œuvre':'VIII. PROTOCOLE DE VALIDATION ET MISE EN ŒUVRE',
    '8.1 Critères de remplacement des estimations':'A. Critères de remplacement des estimations',
    '8.2 Données, code et reproductibilité':'B. Données, code et reproductibilité',
    '8.3 Déclaration de disponibilité et niveau de preuve':'C. Déclaration de disponibilité et niveau de preuve',
    '9. Conclusion':'IX. CONCLUSION',
    'Déclarations':'DÉCLARATIONS', 'Références':'RÉFÉRENCES',
    'Annexe - Statut des résultats':'ANNEXE A - STATUT DES RÉSULTATS',
}
# Le gabarit JOIV présente l'étiquette Abstract et son contenu dans un seul paragraphe.
paragraphs_snapshot = list(doc.paragraphs)
for i, para in enumerate(paragraphs_snapshot[:-1]):
    if para.text == 'Résumé—':
        following = paragraphs_snapshot[i+1]
        para.add_run(' ' + following.text)
        following._element.getparent().remove(following._element)
        break
citation_map = {
    "L'organisation territoriale congolaise":" [1]-[4]",
    'Le polycentrisme vise':' [5], [6], [35]',
    'La théorie des graphes décrit':' [7]-[18], [36]',
    'La zone comprend dix provinces':' [23]-[34]',
    "L'extraction nationale GeoNames":" [23]-[28]",
    'WorldCover exclut':' [29]-[34]',
    'Cinq mille vecteurs de poids':' [19]-[21]',
    "En l'absence de matrice origine-destination":" [22]",
}
for p in doc.paragraphs:
    if p.text in heading_map:
        p.text = heading_map[p.text]
    for start, cite in citation_map.items():
        if p.text.startswith(start) and cite not in p.text:
            p.add_run(cite)
    if p.text.startswith('Tableau '):
        n = int(p.text.split()[1].rstrip('.'))
        roman = ['I','II','III','IV','V','VI','VII','VIII','IX'][n-1]
        p.text = 'TABLEAU ' + roman + p.text[p.text.find('.'):]
    elif p.text.startswith('Figure '):
        p.text = 'Fig. ' + p.text[len('Figure '):]

doc.core_properties.title = "De la structure coloniale à l'aménagement souverain - V8 format JOIV"
doc.core_properties.subject = "Réseaux multimodaux et localisation de pôles urbains en RDC"
doc.core_properties.keywords = "RDC, aménagement, data science spatiale, p-médiane, réseaux"
doc.save(DOCX)
print(DOCX)

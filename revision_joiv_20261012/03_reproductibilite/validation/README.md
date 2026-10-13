# External road checks added to the JOIV revision

Latest manuscript and reviewer response: completion/final. External supplement: validation/final/JOIV_external_road_checks.docx. This extension performs a restricted road-input check, not validation of regional population coverage or observed mobility. The selected reference describes recently developed forest roads; it is not a complete public-road inventory or field ground truth. Expert consultation and calibrated uncertainty are not claimed.

From the unpacked archive root in Windows Command Prompt or PowerShell:

    python -m pip install -r completion/requirements.txt
    python validation/download_sources.py
    python validation/compare_roads.py --step-m 25
    python validation/compare_roads.py --step-m 50

Downloads total about 242 MB. SHA256 checks stop the pipeline if a live source changes. The mask is the same geoBoundaries ten-province union used in the revised model. Projection is local azimuthal equidistant, central longitude 19°E, latitude 1°S. Output shares weight each midpoint by represented line length. The two quadrature resolutions were executed; their maximum difference across all results is 0.112253 percentage points. Main forest-road agreement at 100 m is 4.907821%; including tracks 20.928087%. References are clipped to 12,798 fragments totalling 2,062.533133 km. Samples are not independent observations and no confidence interval is assigned.

The historical AICD file has 859 records, 852 missing AADT sentinels, two dummy zero-ID records, and five positive segments with two distinct 2004 values. They are not five independent count stations. There is no modelled AADT prediction to validate against them. Shared source cartography is possible.

Raw downloaded archives are excluded. The forest inventory licence is not explicit in the retrieved record; do not redistribute it without resolving producer terms. Detailed reference attributes are excluded from this package. Derived nearest-line distance and represented-length samples do not contain reference coordinates. AICD records are CC BY 4.0 per World Bank catalogue. Attribute World Bank/Tecsult/Office des Routes, Slagter et al. and their dataset DOI 10.5281/zenodo.20201702, OpenStreetMap contributors/HOT (ODbL), and geoBoundaries according to each producer's terms.

Latest external-road tables are validation/results_25m. The 50-m comparison is validation/results_50m. This does not convert the assumed 1% deletion stress into a calibrated error distribution. The existing Zenodo v1.0.0 predates this revision.

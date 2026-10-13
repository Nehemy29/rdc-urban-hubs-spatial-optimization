# Latest completion of the JOIV revision
Current deliverables are in completion/final. Earlier revision and revision2 folders are retained as historical build inputs, not latest submission files.

New results: exact categorical functional ANOVA of the preserved complete factorial table (no additional covering optimization); native 2025 SMOD morphological component polygons and aligned GHS-POP population sums. Scenario variance uses independent uniform probabilities over listed factor levels and is not empirically calibrated uncertainty. A prospective French face-to-face expert guide is included. No expert or empirical flow validation is claimed.

From the unpacked root, run:
python -m pip install -r completion/requirements.txt
python completion/download.py
python completion/analyze_variance.py
python completion/delineate_ghsl.py

These three scripts were executed; the entire historical pipeline has not been rerun on an independent machine. Downloaded raw source rasters are omitted from this package. The downloader verifies exact archive hashes. GHS outputs require European Commission/JRC attribution; geographic masking uses geoBoundaries with its separate producer terms. No protected-area raw geometry or JICA reports are added. Consult prior README files for original source conditions. Existing Zenodo v1.0.0 does not contain these revisions.

The substantive outstanding items remain compatible empirical validation and actual expert responses, alongside calibrated uncertainty and operational/tenure information for stronger planning claims.

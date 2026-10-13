# JOIV revision — submission 6222
Prepared 6 October 2026 for PAMBOLO MAYAMBO Néhémie.

## Evidence boundary
This is a revision of a geospatial sensitivity study. There is no completed regional empirical flow validation or field survey. The revised main analysis selects EXISTING hubs by maximal population coverage on mapped roads; it does not recommend construction of new towns. The original v1.0.0 Zenodo archive does not contain this revision. Do not cite that DOI as if it did.

## Files
- revision/final/: revised English manuscript, response to reviewers, supplement, figures, build script, and artifact audit.
- joiv_revision_repo/scripts/revision_*.py: analyses actually executed for this revision.
- joiv_revision_repo/revision_outputs/: computed CSV/JSON outputs, gridded demand, and road-coverage details.
- joiv_revision_repo/data/: specific original derived inputs required for the audits, preserved without modification.
- joiv_revision_repo/revision_sources/source_manifest.json: exact source URLs, downloaded hashes, versions, and dates. Raw heavy third-party datasets are not included.

## Setup
Use Python 3.12 or an environment compatible with the pinned packages. From the unpacked root:

    python -m pip install -r revision/final/requirements_revision.txt
    python joiv_revision_repo/scripts/revision_download_sources.py

The downloader verifies exact hashes before using a file and stops if the producer has changed its content. It extracts the road GPKG to revision_sources/roads, GHSL files to revision_sources/GHSL, and COD-AB to revision_sources/COD_AB. The .part road archive name is the historical local name of a FULL verified archive, not a partial source.

## Run analyses sequentially

    python joiv_revision_repo/scripts/revision_population_grid.py
    python joiv_revision_repo/scripts/revision_ghsl_compare.py
    python joiv_revision_repo/scripts/revision_topology_sensitivity.py
    python joiv_revision_repo/scripts/revision_exact_pmedian.py
    python joiv_revision_repo/scripts/revision_candidate_weights.py
    python joiv_revision_repo/scripts/revision_road_accessibility.py
    python joiv_revision_repo/scripts/revision_joint_coverage.py
    python joiv_revision_repo/scripts/revision_boundary_check.py
    python revision/final/build_final.py

Graph construction and repeated routing use millions of vertices and can require substantial memory and execution time. A new complete independent-machine run has not been executed. The preserved CSVs are the actual revision outputs; checksums allow comparison. The publisher's live HOT URL may later return a different snapshot: a mismatch must not be silently accepted. Obtain the matching archived snapshot or explicitly rerun and disclose the changed data.

## Model details
96 complete factor configurations are solved for each of p=5,10,15, giving 288 runs. Factors: two population products; 1/5 km demand grids; main roads/plus tracks; 1/2.5/5 km assumed connectors; no/fixed 1% feature removal; no/fixed 250 m hub displacement. Coverage threshold is 100 km. Scenario envelopes are not confidence intervals. Removal and displacement are stress tests, not calibrated error probabilities. No Sobol indices are computed.

The legacy p-median audit covers p=2 through 20, and the elbow rule finds none. Candidate-weight frequencies are conditional on 75 cached points. Tshuapa has only one candidate, making Yanganga's frequency automatically 100%. These audits must not be used as regional mobility validation.

## Licensing and attribution
The existing repository's LICENSE is included for its software. Raw and derived datasets retain producer conditions independently of the software license. WorldPop: CC BY 4.0 with producer attribution; GHSL: European Commission/JRC attribution and applicable reuse terms; geoBoundaries/OSM-derived geography: ODbL 1.0 with source attribution. Preserve all included metadata and do not apply a software license to third-party databases. JICA report is referenced; it is not redistributed. Source metadata and original archive establish the provenance of older derived inputs.

## Publication
Before resubmission, review the changed title/scope and response, confirm author declarations, and deposit the revision code/results as a new release on GitHub/Zenodo. Then update the manuscript's release citation with the actual newly assigned DOI. Do not invent or reuse the old DOI for a new revision. The editor may still require empirical validation despite the reduced scope.

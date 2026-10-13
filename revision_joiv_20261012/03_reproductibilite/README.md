# JOIV revision — submission 6222
Extended 7 October 2026 for PAMBOLO MAYAMBO Néhémie.

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

## Extension of 7 October 2026 — current submission files
The CURRENT manuscript, response, supplement and prospective expert questionnaire are in revision2/final. Files in revision/final are retained as prior inputs to the amendment script, not the current submission versions.

Added results: 108 exact runs (two population products, three hub counts, 50/100/150 km thresholds, five independent combined deletion/displacement draws plus a baseline), for 396 covering optimizations including the original factorial design. These are scenario stresses, not calibrated probability or Sobol sensitivity indices.

The 10/25 km candidate screens use one boundary mask and grid origin, the same mapped access inventory, recomputed full-grid population potential, native WorldCover2021v200 centre samples, and centre versus full-cell protected-area masks. The strict full-cell screens retain 1,583 candidates at 10 km and 241 at 25 km. Équateur has no retained candidate at 25 km. Province-specific winners change substantially; these results do not certify new-city locations. Tree admission is solely an extreme sensitivity test, not a forest-conversion recommendation.

JICA Table2.3.18 observations (311,333 and 335,747 PCU/day) are retained as real secondary evidence. This study does not predict PCU/day: JICA's own calibrated estimates are not validation of our population coverage model. Empirical validation remains unresolved. The expert questionnaire is a prospective collection instrument; no consultation is claimed to have occurred.

Run the extension after the preceding analyses:

    python joiv_revision_repo/scripts/revision_repeated_stress.py
    python joiv_revision_repo/scripts/revision_download_protected.py
    python joiv_revision_repo/scripts/revision_candidate_grid_environment.py
    python revision2/amend_final.py

Protected Planet WDPCA October2026 data are private producer inputs. Raw polygons and source attributes are NOT in this archive. The query script checks the recorded response hashes and stops on changed data; obtain the documented archived snapshot or explicitly disclose and rerun on a newer release. Native WorldCover tiles are acquired on demand by the candidate script and verified against worldcover_tile_manifest.json; the preserved derived sampling cache avoids needless repeated source retrieval. Do not redistribute WDPCA input files in a public release. Cite UNEP-WCMC and IUCN, Protected Planet WDPCA, October2026, and observe producer terms.

The current extension was executed and checked in this environment. A complete clean-machine rerun of all earlier phases has not been performed. The amendment script uses the retained original DOCX inputs; Word rendering is an additional verification step described in the accompanying document workflow. A new GitHub/Zenodo release must archive this revision before it can receive its own release DOI.

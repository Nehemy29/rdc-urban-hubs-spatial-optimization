# Prospective JOIV 6222 travel-time protocol

This optional module is separate from the completed distance-based analysis.
No observed travel-time dataset, trained model or performance result is included.

Install in Windows CMD: `py -m pip install catboost numpy pandas scipy scikit-learn`.
Fill a copy of observations_template.csv and run:
`py travel_time.py observations.csv results`.

Each row must be an independently timed, georeferenced road trip. Keep the
date, endpoints, direction, route geometry and timing protocol in a separate
controlled provenance file; source_ref links to that record. Keep only
comparable elapsed durations. source_type must be gps_observed or
operator_observed. Do not relabel router output, traffic counts or simulations.
Ensure road-class lengths are disjoint and exhaustive, and ferry_count is
the number of crossings. Group overlapping segments, repeated and reversed
journeys before splitting so they cannot cross train/test boundaries.
Three groups is a software minimum, not evidence of adequate coverage.
Review corridor geography, timing definitions, missing road classes and
conditions outside the training range before interpreting results.

The script reports out-of-corridor predictions, compares a fixed CatBoost
specification to nonnegative minutes-per-km coefficients by road class and
a ferry delay fitted inside each training split, and reports bias, MAE and
threshold errors overall and within 30 minutes of the threshold.
The 120-minute default is illustrative. Test performance is not proof of
regional household coverage. The script does not rerun the hub optimizer;
only after defensible independent evaluation should estimated itinerary
durations be used to build a separate coverage matrix.

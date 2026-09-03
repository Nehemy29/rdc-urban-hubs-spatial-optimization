"""Vérifie les invariants publiés après une exécution complète."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/03_resultats"

scenarios = pd.read_csv(RES / "comparaison_scenarios_pmedian_phase7.csv")
expected = {5: 80.44, 10: 28.36, 15: 12.58}
observed = dict(zip(scenarios.scenario_p, scenarios.distance_moyenne_ponderee_km))
for p, value in expected.items():
    assert abs(float(observed[p]) - value) <= 0.01, (p, observed[p], value)

robustness = pd.read_csv(RES / "resume_robustesse_phase10.csv")
metrics = dict(zip(robustness.indicateur, robustness.valeur))
assert int(metrics["Simulations Monte-Carlo"]) == 5000
assert int(metrics["Candidats testés"]) == 75
assert int(metrics["Sites robustes > 80 %"]) == 6

network = pd.read_csv(RES / "resume_reseau_multimodal_phase5.csv")
network_metrics = dict(zip(network.indicateur, network.valeur))
assert int(network_metrics["Voies d'eau principales (segments)"]) == 5277
assert int(network_metrics["Lignes ferroviaires (segments)"]) == 198
assert int(network_metrics["Gares OSM"]) == 30
assert int(network_metrics["Aérodromes OSM"]) == 142
print("Vérification réussie: les résultats clés correspondent à l'article.")

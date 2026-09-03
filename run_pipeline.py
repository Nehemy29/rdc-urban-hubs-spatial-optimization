"""Exécute le pipeline reproductible des phases 1 à 10."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

REQUIRED_INPUTS = [
    ROOT / "data/01_brutes/localites/extracted/CD.txt",
    ROOT / "restored/zone_etude.gpkg",
    ROOT / "restored/cod_pop_2025_CN_100m_R2025A_v1.tif",
    ROOT / "restored/reseau_routier_zone.gpkg",
    ROOT / "data/01_brutes/osm_multimodal/waterways/waterways.gpkg",
    ROOT / "data/01_brutes/osm_multimodal/railways/railways.gpkg",
    ROOT / "data/01_brutes/osm_multimodal/airports/airports.gpkg",
]

LOCAL_PHASES = [
    "process_phase3_nodes.py",
    "process_phase4_accessibilite.py",
    "process_phase5_multimodal.py",
    "process_phase6_graphe.py",
    "process_phase7_pmedian.py",
    "process_phase8_sites_nouveaux.py",
]

FINAL_PHASES = [
    "process_phase9_environment.py",
    "process_phase10_robustesse.py",
]


def run(script: str) -> None:
    print(f"\n=== {script} ===", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh-environment",
        action="store_true",
        help="Retélécharge WorldCover et interroge OpenTopoData avant les phases 9-10.",
    )
    parser.add_argument(
        "--from-scratch", action="store_true",
        help="Télécharge les sources et reconstruit la zone avant l'analyse.",
    )
    parser.add_argument("--worldpop-url", help="URL officielle du GeoTIFF WorldPop 2025.")
    args = parser.parse_args()

    if args.from_scratch:
        command = [sys.executable, str(ROOT / "scripts/phase1_download_data.py")]
        if args.worldpop_url:
            command.extend(["--worldpop-url", args.worldpop_url])
        subprocess.run(command, check=True)
        run("phase2_build_study_area.py")

    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_INPUTS if not path.exists()]
    if missing:
        raise SystemExit("Entrées manquantes:\n- " + "\n- ".join(missing))

    for script in LOCAL_PHASES:
        run(script)

    environment_cache = ROOT / "data/02_traitees/echantillons_environnement_phase9.csv"
    if args.refresh_environment:
        run("fetch_phase9_environment.py")
    elif not environment_cache.exists():
        raise SystemExit(
            "Le cache environnemental manque. Relancez avec --refresh-environment."
        )

    for script in FINAL_PHASES:
        run(script)
    run("verify_results.py")


if __name__ == "__main__":
    main()

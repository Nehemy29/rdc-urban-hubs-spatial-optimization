"""Construit la zone des dix provinces et extrait son réseau routier."""

from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
PCODES = {
    "CD10": "Kinshasa", "CD20": "Kongo Central",
    "CD31": "Grand Bandundu", "CD32": "Grand Bandundu", "CD33": "Grand Bandundu",
    "CD41": "Grand Équateur", "CD42": "Grand Équateur", "CD43": "Grand Équateur",
    "CD44": "Grand Équateur", "CD45": "Grand Équateur",
}


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return "".join(ch for ch in value.casefold() if ch.isalnum())


def find_vector(directory: Path, token: str) -> Path:
    options = [p for p in directory.rglob("*") if p.suffix.casefold() in {".gpkg", ".shp"}]
    preferred = [p for p in options if token in normalized(p.name)]
    if not preferred:
        raise FileNotFoundError(f"Aucun fichier vectoriel '{token}' sous {directory}")
    return sorted(preferred, key=lambda p: p.stat().st_size, reverse=True)[0]


def identify_column(frame: gpd.GeoDataFrame, options: tuple[str, ...]) -> str:
    columns = {normalized(col): col for col in frame.columns}
    for option in options:
        if normalized(option) in columns:
            return columns[normalized(option)]
    raise KeyError(f"Colonne introuvable parmi {options}; colonnes={list(frame.columns)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundaries", type=Path)
    parser.add_argument("--roads", type=Path)
    args = parser.parse_args()
    boundaries_path = args.boundaries or find_vector(ROOT / "data/01_brutes/boundaries", "adm1")
    roads_path = args.roads or find_vector(ROOT / "data/01_brutes/osm_multimodal/roads", "road")
    boundaries = gpd.read_file(boundaries_path)
    pcode_col = identify_column(boundaries, ("adm1_pcode", "ADM1_PCODE", "pcode"))
    name_col = identify_column(boundaries, ("adm1_name", "ADM1_FR", "ADM1_EN", "shapeName"))
    zone = boundaries[boundaries[pcode_col].astype(str).isin(PCODES)].copy()
    zone = zone.rename(columns={pcode_col: "adm1_pcode", name_col: "adm1_name"})
    zone["macro_espace"] = zone["adm1_pcode"].map(PCODES)
    if set(zone["adm1_pcode"]) != set(PCODES):
        raise ValueError(f"Provinces absentes: {sorted(set(PCODES) - set(zone['adm1_pcode']))}")
    output_zone = ROOT / "restored/zone_etude.gpkg"
    output_zone.parent.mkdir(parents=True, exist_ok=True)
    zone.to_file(output_zone, layer="provinces", driver="GPKG")

    roads = gpd.read_file(roads_path)
    try:
        road_pcode = identify_column(roads, ("adm1_pcode", "ADM1_PCODE"))
        selected = roads[roads[road_pcode].astype(str).isin(PCODES)].copy()
        selected["adm1_pcode"] = selected[road_pcode].astype(str)
    except KeyError:
        selected = gpd.sjoin(roads, zone[["adm1_pcode", "geometry"]], predicate="intersects", how="inner")
        selected = selected.drop(columns=[c for c in ("index_right",) if c in selected])
    selected = selected[selected.geometry.geom_type.isin(["LineString", "MultiLineString"])].copy()
    labels = zone[["adm1_pcode", "adm1_name", "macro_espace"]].drop_duplicates("adm1_pcode")
    selected = selected.drop(columns=[c for c in ("adm1_name", "macro_espace") if c in selected])
    selected = selected.merge(labels, on="adm1_pcode", how="left")
    selected["longueur_km"] = selected.to_crs(6933).length / 1000
    selected.to_file(ROOT / "restored/reseau_routier_zone.gpkg", layer="routes", driver="GPKG")
    print(f"Provinces={len(zone)}; routes={len(selected)}; longueur_km={selected.longueur_km.sum():.1f}")


if __name__ == "__main__":
    main()

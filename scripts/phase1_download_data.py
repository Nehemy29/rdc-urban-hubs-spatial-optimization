"""Télécharge les données brutes et produit un manifeste de provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "01_brutes"
RESTORED = ROOT / "restored"
HDX_API = "https://data.humdata.org/api/3/action/package_search"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, target: Path, force: bool = False) -> dict:
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        status = "existing"
    else:
        temporary = target.with_suffix(target.suffix + ".part")
        request = urllib.request.Request(url, headers={"User-Agent": "rdc-urban-hubs-replication/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as out:
            shutil.copyfileobj(response, out, length=8 * 1024 * 1024)
        temporary.replace(target)
        status = "downloaded"
    return {
        "file": str(target.relative_to(ROOT)), "url": url, "status": status,
        "bytes": target.stat().st_size, "sha256": sha256(target),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def safe_extract(archive: Path, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        base = directory.resolve()
        for member in zf.infolist():
            destination = (directory / member.filename).resolve()
            if base not in destination.parents and destination != base:
                raise ValueError(f"Chemin ZIP non sûr: {member.filename}")
        zf.extractall(directory)


def validate_geopackages(directory: Path) -> None:
    """Refuse une extraction dont un GeoPackage échoue au contrôle SQLite."""
    for path in directory.rglob("*.gpkg"):
        with sqlite3.connect(path) as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"GeoPackage corrompu ({result}): {path}")


def hdx_resources(query: str) -> list[dict]:
    url = HDX_API + "?" + urllib.parse.urlencode({"q": f"COD {query}", "rows": 50})
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = json.load(response)
    if not payload.get("success"):
        raise RuntimeError(f"Recherche HDX infructueuse: {query}")
    resources = []
    for dataset in payload["result"]["results"]:
        for resource in dataset.get("resources", []):
            resources.append({**resource, "dataset": dataset.get("name", "")})
    return resources


def select_hdx_resource(query: str, keyword: str, preferred_format: str = "gpkg") -> dict:
    candidates = [
        r for r in hdx_resources(query)
        if keyword.casefold() in (r.get("name") or "").casefold()
        and any(ext in (r.get("url") or "").casefold() for ext in (".zip", ".gpkg"))
    ]
    if not candidates:
        raise RuntimeError(f"Aucune ressource HDX trouvée pour {query}/{keyword}")
    candidates.sort(key=lambda r: (
        preferred_format.casefold() not in ((r.get("format") or "") + (r.get("name") or "")).casefold(),
        -int(r.get("size") or 0),
    ))
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-hdx", action="store_true", help="Conserve les archives HDX locales.")
    parser.add_argument("--worldpop-url", help="URL officielle du GeoTIFF WorldPop 2025.")
    args = parser.parse_args()
    manifest = []

    geonames = RAW / "localites" / "CD.zip"
    manifest.append(download("https://download.geonames.org/export/dump/CD.zip", geonames, args.force))
    safe_extract(geonames, RAW / "localites" / "extracted")

    if not args.skip_hdx:
        for category in ("roads", "waterways", "railways", "airports"):
            # Le GeoPackage HOT des voies d'eau du snapshot 2026-09-01 est
            # corrompu malgré un ZIP valide; GeoJSON contient les mêmes entités.
            preferred = "geojson" if category == "waterways" else "gpkg"
            resource = select_hdx_resource(category, category, preferred)
            archive = RAW / f"{category}.zip"
            manifest.append(download(resource["url"], archive, args.force))
            if zipfile.is_zipfile(archive):
                safe_extract(archive, RAW / "osm_multimodal" / category)
                validate_geopackages(RAW / "osm_multimodal" / category)
        boundary = select_hdx_resource("administrative boundaries", "admin")
        archive = RAW / "cod_admin_boundaries.zip"
        manifest.append(download(boundary["url"], archive, args.force))
        if zipfile.is_zipfile(archive):
            safe_extract(archive, RAW / "boundaries")
            validate_geopackages(RAW / "boundaries")

    if args.worldpop_url:
        target = RESTORED / "cod_pop_2025_CN_100m_R2025A_v1.tif"
        manifest.append(download(args.worldpop_url, target, args.force))

    provenance = ROOT / "data" / "provenance_manifest.json"
    provenance.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifeste écrit: {provenance}")


if __name__ == "__main__":
    main()

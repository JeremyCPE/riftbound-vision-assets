#!/usr/bin/env python
"""Package Riftbound Vision card assets for GitHub Releases.

The generated ZIP keeps the runtime layout expected by the desktop app:

    cards/index.json
    cards/images/<card-id>.png

The manifest contains size and SHA256 so the app can reject incomplete or
corrupted downloads before extraction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import zipfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_tree(zip_handle: zipfile.ZipFile, source: Path, archive_root: str) -> int:
    file_count = 0
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        arcname = f"{archive_root}/{path.relative_to(source).as_posix()}"
        zip_handle.write(path, arcname)
        file_count += 1
    return file_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Package card image assets")
    parser.add_argument("--source", required=True, help="Path to database/cards")
    parser.add_argument("--version", required=True, help="Asset pack version, e.g. 2026.05.08")
    parser.add_argument("--owner", default="JeremyCPE", help="GitHub owner")
    parser.add_argument("--repo", default="riftbound-vision-assets", help="GitHub repository")
    parser.add_argument("--output-dir", default="dist", help="Output directory")
    parser.add_argument("--pack-id", default="cards-overlay", help="Pack id")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    index_path = source / "index.json"
    images_path = source / "images"
    if not index_path.is_file():
        raise SystemExit(f"Missing card index: {index_path}")
    if not images_path.is_dir():
        raise SystemExit(f"Missing card images directory: {images_path}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pack_name = f"{args.pack_id}-{args.version}.zip"
    pack_path = output_dir / pack_name
    release_tag = f"cards-{args.version}"
    release_base_url = (
        f"https://github.com/{args.owner}/{args.repo}/releases/download/{release_tag}"
    )

    start = time.time()
    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(index_path, "cards/index.json")
        file_count = 1 + add_tree(zf, images_path, "cards/images")

    size = pack_path.stat().st_size
    checksum = sha256_file(pack_path)
    with index_path.open(encoding="utf-8") as handle:
        card_index = json.load(handle)

    manifest = {
        "schema": 1,
        "version": args.version,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "packs": [
            {
                "id": args.pack_id,
                "kind": "overlay",
                "version": args.version,
                "url": f"{release_base_url}/{pack_name}",
                "sha256": checksum,
                "size": size,
                "required": True,
                "layout": "cards/index.json + cards/images/*",
                "total_cards": card_index.get("total_cards"),
                "file_count": file_count,
            }
        ],
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    elapsed = time.time() - start
    print(f"Pack: {pack_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Files: {file_count}")
    print(f"Size: {size / 1024 / 1024:.1f} MB")
    print(f"SHA256: {checksum}")
    print(f"Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


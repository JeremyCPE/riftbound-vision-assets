"""Verify local packs or actual public downloads before activating a manifest."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile

from PIL import Image


def verify(manifest: dict, read_pack, previous_index: dict | None = None) -> dict:
    files = {}
    for pack in manifest["packs"]:
        data = read_pack(pack)
        if len(data) != pack["size"] or hashlib.sha256(data).hexdigest() != pack["sha256"].lower():
            raise ValueError(f"Size or SHA256 mismatch: {pack['id']}")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC mismatch")
            for info in archive.infolist():
                name = info.filename
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                    raise ValueError(f"Unsafe archive path: {name}")
                if info.is_dir():
                    continue
                if name in files:
                    raise ValueError(f"Duplicate archive member: {name}")
                files[name] = archive.read(info)
    index = json.loads(files["cards/index.json"])
    cards = index["cards"]
    ids = {card["id"] for card in cards}
    if len(ids) != len(cards) or len(cards) != manifest["total_cards"]:
        raise ValueError("Catalog count or unique IDs mismatch")
    if previous_index is not None:
        missing = {card["id"] for card in previous_index["cards"]} - ids
        if missing:
            raise ValueError(f"Previous cards removed: {sorted(missing)}")
    for card in cards:
        name = "cards/" + card["image_path"]
        if name not in files:
            raise ValueError(f"Missing image: {name}")
        with Image.open(io.BytesIO(files[name])) as image:
            image.load()
    return {
        "version": manifest["version"],
        "cards": len(cards),
        "sets": dict(sorted(Counter(card["set_code"] for card in cards).items())),
        "previous_cards_preserved": previous_index is not None,
        "packs": len(manifest["packs"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("dist/manifest.json"))
    parser.add_argument("--public", action="store_true", help="Download every actual HTTPS URL; never use local ZIPs")
    parser.add_argument("--previous-index", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    previous = json.loads(args.previous_index.read_text(encoding="utf-8")) if args.previous_index else None

    def read_pack(pack):
        if args.public:
            if urlparse(pack["url"]).scheme != "https":
                raise ValueError("Public verification requires HTTPS URLs")
            with urlopen(pack["url"], timeout=120) as response:
                return response.read()
        return (args.manifest.parent / Path(urlparse(pack["url"]).path).name).read_bytes()

    result = verify(manifest, read_pack, previous)
    result["mode"] = "public_downloads" if args.public else "local_files"
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

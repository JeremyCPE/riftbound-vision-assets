#!/usr/bin/env python
"""Package Riftbound Vision card assets.

The generated ZIP keeps the runtime layout expected by the desktop app:

    cards/index.json
    cards/images/<card-id>.<ext>

The manifest contains size and SHA256 so the app can reject incomplete or
corrupted downloads before extraction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image


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


def write_pack_zip(
    pack_path: Path,
    cards_root: Path,
    image_paths: list[Path],
    *,
    include_index: bool,
) -> int:
    """Write a runtime cards ZIP and return the file count."""
    file_count = 0
    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_STORED) as zf:
        if include_index:
            zf.write(cards_root / "index.json", "cards/index.json")
            file_count += 1
        for image_path in image_paths:
            arcname = f"cards/images/{image_path.relative_to(cards_root / 'images').as_posix()}"
            zf.write(image_path, arcname)
            file_count += 1
    return file_count


def split_images_by_size(image_paths: list[Path], max_bytes: int) -> list[list[Path]]:
    """Split images into parts below max_bytes where practical."""
    if max_bytes <= 0:
        return [image_paths]
    parts: list[list[Path]] = []
    current: list[Path] = []
    current_size = 0
    for image_path in image_paths:
        image_size = image_path.stat().st_size
        if current and current_size + image_size > max_bytes:
            parts.append(current)
            current = []
            current_size = 0
        current.append(image_path)
        current_size += image_size
    if current:
        parts.append(current)
    return parts


def _resize_if_needed(image: Image.Image, max_width: int) -> Image.Image:
    if max_width <= 0 or image.width <= max_width:
        return image
    new_height = round(image.height * max_width / image.width)
    return image.resize((max_width, new_height), Image.Resampling.LANCZOS)


def _build_source_tree(
    source: Path,
    output_root: Path,
    *,
    image_format: str,
    quality: int,
    max_width: int,
) -> Path:
    """Create a runtime cards tree, optionally converting images."""
    index_path = source / "index.json"
    images_path = source / "images"
    output_cards = output_root / "cards"
    output_images = output_cards / "images"
    output_images.mkdir(parents=True, exist_ok=True)

    with index_path.open(encoding="utf-8") as handle:
        card_index: dict[str, Any] = json.load(handle)

    if image_format == "source":
        shutil.copy2(index_path, output_cards / "index.json")
        shutil.copytree(images_path, output_images, dirs_exist_ok=True)
        return output_cards

    output_ext = f".{image_format}"
    for card in card_index.get("cards", []):
        image_path = str(card.get("image_path", ""))
        if not image_path:
            continue
        source_image = source / image_path
        output_name = f"{source_image.stem}{output_ext}"
        output_image = output_images / output_name
        with Image.open(source_image) as image:
            converted = _resize_if_needed(image.convert("RGB"), max_width)
            if image_format == "webp":
                converted.save(output_image, "WEBP", quality=quality, method=6)
            elif image_format in {"jpg", "jpeg"}:
                converted.save(output_image, "JPEG", quality=quality, optimize=True)
            else:
                raise ValueError(f"Unsupported image format: {image_format}")
        card["image_path"] = f"images/{output_name}"

    (output_cards / "index.json").write_text(
        json.dumps(card_index, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return output_cards


def main() -> int:
    parser = argparse.ArgumentParser(description="Package card image assets")
    parser.add_argument("--source", required=True, help="Path to database/cards")
    parser.add_argument("--version", required=True, help="Asset pack version, e.g. 2026.05.08")
    parser.add_argument("--owner", default="JeremyCPE", help="GitHub owner")
    parser.add_argument("--repo", default="riftbound-vision-assets", help="GitHub repository")
    parser.add_argument("--output-dir", default="dist", help="Output directory")
    parser.add_argument("--pack-id", default="cards-overlay", help="Pack id")
    parser.add_argument(
        "--format",
        choices=["source", "webp", "jpg", "jpeg"],
        default="webp",
        help="Image format stored in the runtime pack",
    )
    parser.add_argument("--quality", type=int, default=82, help="WebP/JPEG quality")
    parser.add_argument(
        "--max-width",
        type=int,
        default=0,
        help="Resize images wider than this value. 0 keeps source dimensions.",
    )
    parser.add_argument(
        "--url-base",
        default="",
        help="Base URL used in manifest. Defaults to the GitHub Release URL.",
    )
    parser.add_argument(
        "--split-size-mb",
        type=int,
        default=45,
        help="Split image packs into ZIP files below this size. 0 disables splitting.",
    )
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

    format_suffix = args.format if args.format != "source" else "png"
    release_tag = f"cards-{args.version}"
    release_base_url = (
        f"https://github.com/{args.owner}/{args.repo}/releases/download/{release_tag}"
    )
    url_base = args.url_base.rstrip("/") or release_base_url

    start = time.time()
    generated_packs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        package_cards = _build_source_tree(
            source,
            Path(tmp_dir),
            image_format=args.format,
            quality=args.quality,
            max_width=args.max_width,
        )
        image_paths = sorted((package_cards / "images").rglob("*"))
        image_paths = [path for path in image_paths if path.is_file()]
        split_size_bytes = args.split_size_mb * 1024 * 1024
        image_parts = split_images_by_size(image_paths, split_size_bytes)

        for index, image_part in enumerate(image_parts, start=1):
            suffix = (
                f"{format_suffix}.zip"
                if len(image_parts) == 1
                else f"{format_suffix}-part{index:02d}.zip"
            )
            pack_name = f"{args.pack_id}-{args.version}-{suffix}"
            pack_path = output_dir / pack_name
            file_count = write_pack_zip(
                pack_path,
                package_cards,
                image_part,
                include_index=index == 1,
            )
            generated_packs.append(
                {
                    "path": pack_path,
                    "name": pack_name,
                    "file_count": file_count,
                    "part": index,
                    "part_count": len(image_parts),
                    "sha256": sha256_file(pack_path),
                    "size": pack_path.stat().st_size,
                }
            )

    with index_path.open(encoding="utf-8") as handle:
        card_index = json.load(handle)

    manifest = {
        "schema": 1,
        "version": args.version,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_cards": card_index.get("total_cards"),
        "packs": [
            {
                "id": (
                    args.pack_id
                    if pack["part_count"] == 1
                    else f"{args.pack_id}-part-{pack['part']}"
                ),
                "kind": "overlay",
                "version": args.version,
                "url": f"{url_base}/{pack['name']}",
                "sha256": pack["sha256"],
                "size": pack["size"],
                "required": True,
                "layout": "cards/index.json + cards/images/*",
                "image_format": args.format,
                "quality": args.quality if args.format != "source" else None,
                "max_width": args.max_width,
                "part": pack["part"],
                "part_count": pack["part_count"],
                "total_cards": card_index.get("total_cards"),
                "file_count": pack["file_count"],
            }
            for pack in generated_packs
        ],
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    elapsed = time.time() - start
    for pack in generated_packs:
        print(f"Pack: {pack['path']} ({pack['size'] / 1024 / 1024:.1f} MB)")
    print(f"Manifest: {manifest_path}")
    print(f"Parts: {len(generated_packs)}")
    print(f"Size: {sum(pack['size'] for pack in generated_packs) / 1024 / 1024:.1f} MB")
    print(f"Elapsed: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

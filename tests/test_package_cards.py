"""Tests for strict card asset ZIP splitting."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package_cards import split_images_by_size, write_pack_zip, zip_member_size


class SplitImagesBySizeTests(unittest.TestCase):
    def test_first_part_reserves_index_and_zip_overhead(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cards_root = Path(temp_dir) / "cards"
            images_root = cards_root / "images"
            images_root.mkdir(parents=True)
            index_path = cards_root / "index.json"
            index_path.write_bytes(b"i" * 120)
            image_paths = []
            for index in range(3):
                path = images_root / f"card-{index}.webp"
                path.write_bytes(b"x" * 100)
                image_paths.append(path)

            limit = (
                22
                + zip_member_size(index_path, "cards/index.json")
                + zip_member_size(image_paths[0], "cards/images/card-0.webp")
            )
            parts = split_images_by_size(
                image_paths,
                limit,
                cards_root=cards_root,
                first_part_reserved_bytes=zip_member_size(
                    index_path,
                    "cards/index.json",
                ),
            )

            self.assertEqual([1, 2], [len(part) for part in parts])
            for part_index, part in enumerate(parts):
                zip_path = Path(temp_dir) / f"part-{part_index}.zip"
                write_pack_zip(
                    zip_path,
                    cards_root,
                    part,
                    include_index=part_index == 0,
                )
                self.assertLessEqual(zip_path.stat().st_size, limit)

    def test_rejects_an_image_larger_than_a_part(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "oversized.webp"
            image_path.write_bytes(b"x" * 200)

            with self.assertRaisesRegex(ValueError, "cannot fit"):
                split_images_by_size([image_path], 100)


if __name__ == "__main__":
    unittest.main()

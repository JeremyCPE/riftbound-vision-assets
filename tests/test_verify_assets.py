import hashlib
import io
import json
import unittest
import zipfile

from PIL import Image

from scripts.verify_assets import verify


class VerifyAssetsTests(unittest.TestCase):
    def fixture(self, include_image=True):
        card = {"id": "rad-001", "set_code": "RAD", "image_path": "images/rad-001.webp"}
        image = io.BytesIO()
        Image.new("RGB", (4, 4)).save(image, format="WEBP")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("cards/index.json", json.dumps({"cards": [card]}))
            if include_image:
                archive.writestr("cards/images/rad-001.webp", image.getvalue())
        data = output.getvalue()
        manifest = {"version": "test", "total_cards": 1, "packs": [{
            "id": "part1", "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        }]}
        return manifest, data, {"cards": [card]}

    def test_checks_images_and_preserves_existing_cards(self):
        manifest, data, previous = self.fixture()
        result = verify(manifest, lambda _: data, previous)
        self.assertEqual(result["sets"], {"RAD": 1})
        self.assertTrue(result["previous_cards_preserved"])

    def test_rejects_corrupt_download(self):
        manifest, data, _ = self.fixture()
        with self.assertRaisesRegex(ValueError, "SHA256"):
            verify(manifest, lambda _: data + b"corrupt")

    def test_rejects_removed_previous_card(self):
        manifest, data, _ = self.fixture()
        with self.assertRaisesRegex(ValueError, "Previous cards removed"):
            verify(manifest, lambda _: data, {"cards": [{"id": "ogn-old"}]})

    def test_rejects_missing_image(self):
        manifest, data, _ = self.fixture(include_image=False)
        with self.assertRaisesRegex(ValueError, "Missing image"):
            verify(manifest, lambda _: data)

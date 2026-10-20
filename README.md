# Riftbound Vision Assets

Versioned card image packs for Riftbound Vision.

This repository stores only generated runtime packs, not the source card image
tree. The desktop app consumes `dist/manifest.json`, downloads the ZIP once,
verifies `sha256`, extracts it locally, then serves images from disk to React
and OBS.

## Pack Layout

The default overlay pack ZIP contains optimized WebP images:

```text
cards/
  index.json
  images/
    <card-id>.webp
```

## Build A Pack

From this repository:

```powershell
python scripts/package_cards.py `
  --source G:\sources\riftbound-vision\database\cards `
  --version 2026.07.25 `
  --owner JeremyCPE `
  --repo riftbound-vision-assets `
  --format webp `
  --quality 82 `
  --split-size-mb 45
```

Outputs are written to `dist/`:

- `cards-overlay-<version>-webp-part01.zip`
- `cards-overlay-<version>-webp-part02.zip`
- `cards-overlay-<version>-webp-part03.zip`
- `manifest.json`

## Publish Flow

**Publish and verify the ZIPs before merging the manifest.** The application
reads the manifest from `main`, so merging it activates the download URLs.
Publishing the application alone does not publish its card images.

For the Radiance application 0.1.23 candidate, the complete pack is
`2026.10.20`: 1,408 cards, including 219 RAD and all 1,180 cards from the
previous public pack. The ZIPs remain local until publication is authorized.

Before publication, validate the local release files:

```powershell
python scripts/verify_assets.py --manifest dist/manifest.json
```

After explicit publication approval:

1. Create GitHub release `cards-2026.10.20` and upload all three
   `dist/cards-overlay-2026.10.20-webp-part*.zip` files.
2. Verify the **actual public downloads**, with no local fallback:

   ```powershell
   python scripts/verify_assets.py --manifest dist/manifest.json --public
   ```

   Stop on any error. The verifier checks sizes, SHA256, ZIP contents, catalog
   count and every decoded image. Add `--previous-index <old-index.json>` to
   check that every previous card ID is retained.
3. Merge the assets manifest PR only after step 2 succeeds.
4. Test first installation and upgrade through the now-public manifest.
5. Publish the matching application installer, then its application update
   manifest. Retain the previous asset release for rollback.

See [Radiance readiness](docs/radiance-readiness.md) for local verification and
the publication gate.

ZIP packs are published as GitHub Release assets. Git only stores the small
`dist/manifest.json` file that points to the release files:

```powershell
git add dist/manifest.json
git commit -m "assets: publish cards <version>"
git push
```

For version `2026.07.25`, upload these files to the `cards-2026.07.25` release:

- `dist/cards-overlay-2026.07.25-webp-part01.zip`
- `dist/cards-overlay-2026.07.25-webp-part02.zip`
- `dist/cards-overlay-2026.07.25-webp-part03.zip`

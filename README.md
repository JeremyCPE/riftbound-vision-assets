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
  --version 2026.05.08 `
  --owner JeremyCPE `
  --repo riftbound-vision-assets `
  --format webp `
  --quality 82 `
  --url-base https://raw.githubusercontent.com/JeremyCPE/riftbound-vision-assets/main/dist
```

Outputs are written to `dist/`:

- `cards-overlay-<version>-webp.zip`
- `manifest.json`

## Publish Flow

For the beta, the optimized pack is small enough to publish directly in this
public assets repository:

```powershell
git add dist/manifest.json dist/cards-overlay-<version>-webp.zip
git commit -m "assets: publish cards <version>"
git push
```

For larger future packs, publish the ZIP as a GitHub Release asset and generate
the manifest with the default release URL instead of `--url-base`.

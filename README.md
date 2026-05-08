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
  --split-size-mb 45
```

Outputs are written to `dist/`:

- `cards-overlay-<version>-webp-part01.zip`
- `cards-overlay-<version>-webp-part02.zip`
- `manifest.json`

## Publish Flow

ZIP packs are published as GitHub Release assets. Git only stores the small
`dist/manifest.json` file that points to the release files:

```powershell
git add dist/manifest.json
git commit -m "assets: publish cards <version>"
git push
```

For version `2026.05.08`, upload these files to the `cards-2026.05.08` release:

- `dist/cards-overlay-2026.05.08-webp-part01.zip`
- `dist/cards-overlay-2026.05.08-webp-part02.zip`

# Riftbound Vision Assets

Versioned card image packs for Riftbound Vision.

This repository intentionally does not store card images in Git. Card packs are
published as GitHub Release assets and consumed by the desktop app through a
versioned manifest.

## Pack Layout

The default overlay pack ZIP contains:

```text
cards/
  index.json
  images/
    <card-id>.png
```

## Build A Pack

From this repository:

```powershell
python scripts/package_cards.py `
  --source G:\sources\riftbound-vision\database\cards `
  --version 2026.05.08 `
  --owner JeremyCPE `
  --repo riftbound-vision-assets
```

Outputs are written to `dist/`:

- `cards-overlay-<version>.zip`
- `manifest.json`

## Publish Flow

1. Create a GitHub release named `cards-<version>`.
2. Upload `dist/cards-overlay-<version>.zip`.
3. Upload `dist/manifest.json`.
4. Point the desktop app asset downloader at the release `manifest.json`.

The desktop app should download the ZIP once, verify `sha256`, extract it to a
local assets directory, then serve images locally to React and OBS.


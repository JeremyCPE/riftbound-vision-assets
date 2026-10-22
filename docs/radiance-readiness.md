# Radiance asset pack readiness

Validated on 2026-10-20. Branch based on `origin/main` at `9c619c1`.
Related application PR: https://github.com/JeremyCPE/riftbound-vision/pull/27.

## Verified locally

- Manifest version: `2026.10.20`.
- Catalog: 1,408 unique cards, including 219 Radiance cards.
- All 1,408 WebP images decode successfully.
- Packed catalog matches the final application catalog after converting image
  extensions to WebP.
- All three ZIP archives pass CRC checks; no duplicate or unsafe member paths.
- Every catalog image has exactly one archive entry.
- Archive sizes and SHA256 hashes match `dist/manifest.json`.
- Each archive is below 45 MiB.
- All six packaging and delivery verification tests pass.
- Local installation through the application's `ensure_card_assets` was
  previously verified in the application worktree; the installed pack was also
  used for the native OBS display test documented in application PR #27.

The ZIPs are available locally in `G:\sources\riftbound-vision-assets\dist`
and remain ignored by Git. The three ZIPs are now also uploaded to the GitHub
release draft linked below. This PR contains the manifest, verifier and report;
the classifier model belongs to the application installer.

## Publication gate

**Do not merge this PR or publish a release without the user's approval.**
The application reads the manifest directly from `main`; merging changes the
public download configuration.

Release `cards-2026.10.20` is staged as a **draft**, with all three ZIPs uploaded.
The manifest URLs are not yet publicly downloadable.
The current public pack remains `2026.07.25`, with 1,180 cards.

After approval and application release validation:

1. Publish the reviewed draft `cards-2026.10.20`, which already contains all three ZIPs.
2. Verify public downloads and their hashes.
3. Merge the manifest change only after all URLs work.
4. Verify first installation and upgrade from the previous pack through the
   public manifest.
5. Coordinate with the application release containing the matching classifier.
   Asset publication alone does not update the recognition model.

No release was published and the public manifest was not changed.

Draft (visible to authorized repository users):
https://github.com/JeremyCPE/riftbound-vision-assets/releases/tag/untagged-bde77f0a77b8601e3256

GitHub reports all three assets as uploaded, with sizes and SHA256 digests
matching the manifest. See `radiance-staging-verification.json`.
The delivery verifier decoded all 1,408 images and confirmed that all 1,180
previous card IDs remain present. Run the verifier with `--public` after
approval and publication, before merging the manifest or deploying the app.

## Application upgrade verification (0.1.23 candidate)

The actual application asset installer was exercised locally with both manifests
and their real ZIP files: 2026.07.25 installed 1,180 cards, then 2026.10.20 replaced
it with 1,408 cards, including 219 RAD entries. Every referenced image exists.
Local manifest copies used filesystem URLs; public URLs remain unpublished.
The application PR also tests bounded retries for Windows file locks and restores
the previous pack if activation fails. This check does not replace verification
of public downloads after an explicitly authorized release.

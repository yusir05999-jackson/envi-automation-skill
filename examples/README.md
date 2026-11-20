# Worked example: impervious-surface extraction

This is the validated case from SKILL.md §9, turned into a runnable
walkthrough. It extracts impervious surfaces from high-resolution
imagery with ENVI 6.2 / IDL 9.2.

## What you need

- Windows 10/11, ENVI 5.6 / 6.x with a valid licence
- Python 3.8+, `pip install pillow numpy scipy`
- Your own input raster, in pure-ASCII paths, for example
  `E:\work\data\sub_quac.hdr` (the sample paths below are placeholders
  for your data — no imagery is bundled in this package)

## Steps

1. Run the pre-flight check (no ENVI needed):
   ```bash
   python examples/check_environment.py
   ```
   It checks the ENVI install, `IDL_LICENSE_PATH`, ASCII paths,
   and that `.pro` files use CRLF line endings.

2. Run the segmentation example in `segmentation-example.pro`
   through the stdin-pipe method in SKILL.md §2 — do not use
   `idl.exe -e`. It runs `FXSegmentation` (Edge, scale 50,
   Full Lambda Schedule merge 60, NIR band 6) and writes
   `E:\work\seg.dat`.

3. Run the full pipeline in `scripts/example_pipeline.pro`:
   FXSegmentation, then NDVI < 0.28 and NDSI < 0.13 thresholds,
   then rule-based combination, then `ClassificationToShapefile`.
   Expected outputs: `fx_seg.dat`, `ndvi_lt.dat`, `ndsi_lt.dat`,
   `impervious_cls.dat`, `impervious.shp`.

## Expected results (from the validated case in SKILL.md §9)

| Step | Method | Result |
|---|---|---|
| Segmentation | FXSegmentation Edge/50/FullLambda/60 | 182,127 objects |
| Pixel rules | NDVI < 0.28 and NDSI < 0.13 | 2.699 km² |
| Object filtering | Purity > 50% and >= 800 pixels (200 m²) | 1,318 objects, 0.965 km² |
| Accuracy | 14 manually interpreted ROIs, confusion matrix | OA = 0.7857, Kappa = 0.3226 |

If your numbers differ, that is expected — they depend on your
imagery, bands, and thresholds. Use them as a sanity check, not
as a target to force.

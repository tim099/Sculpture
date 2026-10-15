# Rerun

Requirements: Python 3 with NumPy and Shapely. Tested versions: NumPy 2.2.6, Shapely 2.1.2.

Run from any directory:

```
python /absolute/path/to/yard_verifier/verify.py
```

The script reads only its sibling `input/` directory and writes `progress.json`, `report.json`, `geometry_hashes.json` in its own folder. It does not modify the work, game, frozen inputs or any other verifier output. Runtime observed 8-16 seconds. No author's validation implementation is imported. The negative control exists only in memory.

To verify package integrity, read `MANIFEST.json`, then compare each listed file's byte count and SHA-256. `MANIFEST.json` intentionally does not hash itself. Regenerating a report changes its elapsed runtime field, so regenerate the manifest after a deliberate rerun before distributing a new package.

For a rope-only work change, compare the three entries in `geometry_hashes.json` against an export of the new snapshot using the same serialization. The complete VXK SHA-256 will change when ropes change; that is expected. Only identical body cells, model placements/meshes, and yard source cubes/pivots/placements permit carrying this geometry evidence forward. This does not carry rope or cloth evidence forward.

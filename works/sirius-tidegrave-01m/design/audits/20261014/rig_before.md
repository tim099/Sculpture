# Independent rig / ornament audit

Snapshot: `sirius-tidegrave-01m-assembly/exports/tidegrave_preview.vxk`, SHA256 `90ef3a5b8fbb1810cdfc05b48a0ddb9e8d903be1ce94229ffcced4ff03a6b75f`, 1,037,251 voxels, independently recomputed checksum `8c58dca9`. This snapshot includes relocated wheel (parent confirmation). All reported geometry derives from decoded snapshot, not author's pass/fail output.

Sources: shared VoxelKit `voxel_export.unpack/checksum` decoder only. Own scripts perform segment/unit-box slab intersection and triangle/unit-box separating-axis tests. `capsule.py` adds exact segment-to-box minimum distance (piecewise quadratic) against rope radius. No author's verifier imported. Output only in this folder; no work modified.

## Actionable failures in initial snapshot

- `jib.sheet-S` crosses main hull plus forecastle and ornament; `mizzen-lateen.sheet-P` crosses hull plus poop deck. These are actual interior rope segments, separated from the first/last 3 voxel-length attachment zone.
- `fore-course.sheet-S`, `main-course.sheet-S`, `main-topgallant.brace-S` cross ornament.
- Wheel/lead ropes cross quarter/weather/upper decks and ladders. `capsule_and_reroutes.json` contains every radius-inclusive collision cell, owner source work, along-curve coordinate, and explicit endpoint/interior classification. Tiller ropes have zero capsule collisions.
- `ensign` has 11 occupied cells intersecting triangles whose vertices are all strictly inside the topological mesh boundary; these are flag interior collisions, not pinned-edge attachment. Coordinates in `audit.json`.

Five proposed elevated supported attachment points and one-cell post boxes are in `capsule_and_reroutes.json`. Each existing base is owned by main hull work. Proposed straight `slack=1` rope interior has zero radius-inclusive collisions; all proposed posts have zero triangle intersections with the ten current sail meshes. These are proposed static remedies, requiring re-export and independent post-mutation check. Human routes and animated sail/yard sweep remain unverified.

## Pass / limited checks

- All nine yards carrying sail metadata reference existing sail names. Mizzen crossjack carries no sail reference and must be classified as intentionally bare, not a missing named sail.
- Assembly ropes metadata: 16 sheet ropes have `kind=sheet`; 283 remaining ropes have no metadata. All ten sails have metadata (ensign uses `kind=flag`). This proves sheet metadata coverage, not all-rope coverage.
- Ten complete sail triangle meshes have zero intersections with main hull voxels. Square sails touch their own mast voxels. Jib touches 665 bowsprit and 7 fore mast cells, all on triangles containing topological boundary vertices; strict interior triangle collision is zero. Actual attachment versus near-edge overlap remains unverified.
- Ornament independent event replay: initial 31,405 plus 340 root repairs = 31,745 cells. Every replayed cell/color occurs in export (0 missing/color differences). 219 separate ornament-only face components all attach by a face to non-ornament assembled voxels; none floats. Ornament-only closed air = 0. Mirror y coordinate maps `y -> 240-y`, continuous symmetry plane y=120.5; 0 missing or color differences.
- Ornament motif source statements are in `design/ornament_plan.json` and `design/references/README.md`: D23 model bow/stern observations; broken astrolabe is Sirius design. This verifier has not independently re-read external images/pages; historical fidelity unverified.

Full assembly connectivity/air cavities belongs to the separate structure verifier; ornament-only cavity result must not be reported as whole-ship cavity clearance. `audit.json` preserves counts, event filenames/source hashes, collision coordinate lists, and metadata.

## Additional remedies requested by parent

`wheel_flag_candidates.json`: wheel-P route with single corner `(225.5,106.5,151.5)` avoids ladders and masts. Twelve capsule hits remain on quarter deck, listed per cell for guarded precision holes. Its guide post starts on existing quarter-deck cell `(225,106,138)` and extends to z151. Additional route supports / foot clearance still require game-level validation.

Translate all ensign corners upward 26 voxels (top z231.5, bottom z215.5): existing translated mesh has zero occupied voxel intersections. Extend pole at x105/y120 from occupied ornament cell z208 through z231. Parent must update CLI sail corner definition and re-simulate; translated-mesh candidate is not verification of the later simulation. Pole occupies pinned flag edge as intentional attachment.

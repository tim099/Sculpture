# Tidegrave independent continuous yard verifier

Scope: the frozen `final_heads.vxk` geometry, ten articulated yards against body voxels, all 106 other model meshes, and all 45 yard pairs. Rope and cloth physics are outside this verifier. No author verifier is imported. Source yard cubes/pivots are consumed as frozen raw data from `frozen_yards.json`; original game files are frozen beside the snapshot. The script writes only this directory.

Result: **PASS for this model/body geometric scope**, with explicitly measured central mast attachment intersections. This does not certify rope/cloth, pendulum motion of independently hanging models, runtime integration, or actual gameplay observation.

- 1,060 yard/fixed-model combinations are proved separated by invariant Z bounds. Their meshes therefore cannot contain any tested yard prism; the general surface-only fallback in the script is not needed for this snapshot.
- Every body voxel whose Z slab overlaps a moving source cuboid participates in the XY solid union, including mast, collars, top platforms, railings and all noncentral details.
- The ten complete independent angle ranges are square yards [-0.70, +0.70] rad and gaff/boom [-1.40, +1.40] rad. These are absolute angles, with `rot = absolute - r0`, as derived directly from the frozen `braceYards` implementation. The boom sign-change transition includes angles below BOOM_MIN.
- Body tests: 2,736 adaptive intervals, 1,606 disjoint proof leaves, **0 unresolved** intervals, **0 noncentral intersections**.
- All 45 yard pairs: 42 pairs are separated by invariant Z bounds. The other 3 use independent 2-angle interval envelopes over the entire Cartesian product, rather than synchronous sampling: mizzen topsail/fore topsail, mizzen gaff/main course, mizzen gaff/fore course. No collision or unresolved interval.
- Body/mast attachment contact is quantified in 113 source cuboids across ten yards. Each cuboid consists solely of source cubes all of whose XY corners lie within radius 8 voxels of its pivot. Every individual contact has a source box, angle, positive intersection area and position in `report.json`. The largest witness distance from its pivot is 4.525600 voxels. Only these central cuboids against body are classified as attachment contacts. No model contact or noncentral source box is excluded.

## Continuous proof

Source unit cubes are merged only across contiguous Y coordinates at the same source X/Z and the same explicit central/noncentral classification. Hence the union of the resulting cuboids exactly equals the input solid. Rotation about Z preserves each cuboid's Z slab. Body voxels meeting that slab are exactly projected as unit squares and unioned.

For a cuboid and angular interval [a,b], its swept XY rectangle lies in the convex hull of the endpoint/midpoint rectangles expanded outward by `r*(b-a)^2/8`, where r is the furthest cuboid corner radius. This follows the linear interpolation error bound for an arc whose second derivative norm is at most r. The Shapely polygonal buffer is inflated by `sec(pi/32)` so its segment chords circumscribe the requested distance. Floating-point allowance is 1e-9 voxels. A disjoint envelope proves the whole continuous interval safe; an overlap is subdivided. An exact positive-area midpoint intersection is a collision witness. Pair analysis constructs both envelopes independently and subdivides the larger angular displacement, covering asynchronous angles. The report records zero intervals reaching the unresolved depth limit.

## Real negative control

The negative control restores only the in-memory crossjack `at.z` from 224.5 to the old 255.5. It intersects the unchanged gaff. A robust exact solid witness occurs at absolute angles **crossjack +0.5 rad, gaff -1.2 rad**:

- XY overlap area: **1.0084052488902602 voxel²**.
- Shared solid Z interval: **[255,256]**, giving a positive volume intersection.
- Interior XY witness: **[199.67149989233317,133.25482752601732]**.
- Crossjack source cuboid: `[5,128,4]` to `[6,176,5]`; gaff source cuboid: `[106,119,205]` to `[107,122,206]`.

The actual crossjack remains at **224.5**. Its full Z slab is [223,226], whereas gaff begins at 229: they are separated by 3 voxels for every independent pair of angles. No work file was modified by this verifier.

## Reproduce

Run `python verify.py` from any working directory. Python 3, NumPy and Shapely are required (verified with NumPy 2.2.6 and Shapely 2.1.2). All geometric and game inputs are included in `input/`; original external paths in frozen-yard provenance are informational. `report.json` is the complete machine-readable result. `MANIFEST.json` records SHA-256 and byte length of the portable package files.

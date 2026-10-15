# Forward feet, lowest ratline ratio .065: clear except measured endpoint attachments

Proposed feet (all six are existing original body solid cells):

| Side | 0 | 1 | 2 |
|---|---|---|---|
| P | [290.5,70.5,128.5] | [310.5,70.5,128.5] | [330.5,69.5,128.5] |
| S | [290.5,170.5,128.5] | [310.5,170.5,128.5] | [330.5,171.5,128.5] |

Hounds remain [205.5,116.5,260.5] and [205.5,124.5,260.5]. Six shrouds have radius .4. Forty-two ratlines have radius .125 and interpolate between outer shrouds at ratio `max(j/25,.065)`, j=1..21. Only the two lowest lines differ from the original ratios.

Results:

- All 48 lines clear all ten source-solid yards for the entire continuous absolute rotation ranges: square [-.70,+.70], gaff/boom [-1.40,+1.40]. 4,304 adaptive intervals, 3,380 disjoint proof leaves, 0 unresolved; no angle-grid-only claim.
- All 42 ratline capsules clear the entire original body solid. Safe tested lowest ratio is .065, not a claim that .065 is the mathematical minimum. Original ratio .04 provides the real negative control: P/S lowest each intersect seven rail cells in sibling candidate_forward/report.json.
- Six shrouds have 38 body-contact voxels total, confined to the actual attachment endpoints. Foot-side witness arclength is <=.809365 voxels from the foot. Hounds witnesses reach 1.596245 voxels from the endpoint. These are retained individually in report.json; no interior or noncentral contact is broadly exempted.
- Specifically the P/S0 hounds capsules graze body cells [205,116,258] / [205,124,258] at distance .3917197452 (<radius .4), witness [206.3293439896142,116.05117854679703,259.2120775690697] / its mirror, 1.5962444481 voxels from the endpoint. The script marks only <=1.0-voxel witnesses as `attachment_candidate`; this pair remains explicitly outside that marker for reviewer decision. Other hounds contacts and all feet contacts are within 1.0 voxel. No shroud body contact occurs in its free span outside this measured endpoint extent.

The solid check uses original VXK body unit cubes and frozen source unit cubes for all ten yards. Exact segment/AABB distance is minimized through plane-crossing breakpoints and each interval's stationary point. A rope is the requested-radius capsule. A rotating cuboid is evaluated by inverse-rotating the segment; an interval is proved clear only when midpoint distance exceeds radius plus the maximum cuboid-corner displacement `r*half_angle_width`. Overlapping bounds subdivide until proved clear or an exact positive collision witness exists. Source cube merging is exact contiguous same-X/Z Y runs. The report records no unresolved intervals.

Closest-point witnesses above describe the distance minimizer for each contact voxel. `contact_extent.py` additionally bisects the exact capsule/cube contact entry and exit parameters, retaining `contact_t_interval` for all 38 contacts. The maximum actual contact extent, rather than just the nearest witness, is **1.732236589 voxels** from the hounds endpoint. No contact parameter extends farther into the free span.

Run `python check.py` and then `python contact_extent.py` from any working directory with NumPy installed. Shared frozen inputs live in ../input. These scripts write only this candidate folder and never change the actual work or game. SHA-256 of exact shared inputs is listed in MANIFEST.json. This candidate validation excludes the 106 other external model meshes, cloth physics and rope/rope interaction, per assigned candidate scope.

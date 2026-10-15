# TASK-0603 independent attachment audit

Input `input.vxk` is frozen byte-for-byte from `design/dynamic_20261015/final_dynamic.vxk`, SHA256 `f2561bfc294f91b849f59412d80294e9755e90a2ae1af8d81dea3ea7c2b06c9c`.

This is an independent read-only geometric audit plus an original repair design, not a claim that the live ship has already been changed. No author collision checker is imported. `audit.py` implements segment/triangle intersections and non-axis ray parity directly. `clearance.py` uses the independent rope verifier's prior piecewise-quadratic segment/AABB and closest triangle method, explicitly reproduced rather than importing the author. `support_check.py` independently implements triangle/box SAT. All work is confined to this directory.

## Defects verified in the frozen ship

All 96 breeching ropes leave their cascabel attachment and subsequently cross gun barrel/carriage solids. `intervals.json` retains every interior interval, rather than exempting a generic distance from endpoints. Straightening slack alone still leaves 4.45–7.25 ship-grid units of interior rope. Moving to existing carriage eye anchors also fails.

`steer-wheel-S` crosses its wheel frame at arc 13.0842176284–13.2851834941, midpoint (190.183955224, 140.385009292, 143.156225681). This is remote from the intended drum attachment. `steer-wheel-P` has no centerline interior crossing. Both tiller ropes contact only the named tiller-end: their last 1.9076243373 units enter the local tip of the tiller at x=155.5, z≈74.5–75.7; this cannot reach the rudder blade, whose top is below z=59.

## Repair design

For every gun, C=cascabel, sg=sign(muzzle.y−breech.y), dx=sign(original hull ring.x−C.x). Use three straight rope segments of radius .25:

`C → C+(2dx,−3.5sg,0) → C+(9dx,−3.5sg,0) → original hull ring`.

The exact 96 paths are in `route_clearance.json`. Across full body and all 116 models they have no unrelated model contact and no re-entry into their own gun after the initial attachment. Each path touches exactly its original terminal hull-ring voxel. The initial gun contact belongs to the actual cascabel knob: centerline inside is only approximately .576 units, with radius contact bounded by the local geometry (dense bound .86367 on the representative gun), rather than an arbitrary 5-unit exception.

`gun_fairlead.vox.txt` is an original, reusable 738-voxel source at .05m. It has four hollow fairlead rings, four deck-supported posts, and a common sole plate; the entire source is one 6-connected component. Build source size at least 48×24×32, pivot (24,12,23), model scale .5 at each gun's actual cascabel. Use rotation 0 for S and rotation 180 for P. P swaps aft/fwd source anchors. `gun_prototype.json` contains exact desired source point coordinates; **CLI named anchor records must subtract .5 from each coordinate** because anchor resolution adds .5. Source pivot is already a geometric point and must not be adjusted.

The ring inner radius is 1.5 ship-grid units, outer radius 2.5, discretized into actual half-grid cubes. All 48 placements (35,424 cubes) have zero positive-volume overlap with preexisting body or any of 116 models, zero contact with remaining original rope capsules, and every sole plate is supported by actual deck voxels. No source asset belonging to another author is edited. `support_check.json` records the results.

The new wheel route is:

`(201.2,144.8,148.9) → (199.5,155.5,154.5) → (225.5,155.5,154.5) → (225.5,134.5,151.5) → (175.5,134.5,135.5)`.

All segments are straight. It has no model interior crossing; only the first .62504 units touch the intended drum surface through the rope radius. The only body contact is at the existing wooden pillar voxel (225,134,151). The two new guide rings are actual connected, supported half-grid solids in `wheel_fairlead_1.vox.txt` (90 cells) and `wheel_fairlead_2.vox.txt` (185 cells). `wheel_prototypes.json` gives exact source size, pivot, CLI anchor record, scale and model placement. Both are individually one component and clear all preexisting models/body/remaining original ropes (`wheel_support_check.json`).

Every proposed rope against **all** proposed support cubes has minimum surface distance .7071067812 ship-grid units, exceeding .25 rope radius. The rings have real holes; no guide is an unsupported coordinate. These checks include both mirror orientations and neighboring gun hardware.

New paths versus every remaining old rope and each other also pass the capsule test: 48 contact pairs are the two halves of each gun's same named cascabel knot; one is exactly the shared named lead-S endpoint between wheel-S and lead-S. Every other pair clears. `route_pairs.json` records the actual closest point witnesses, without a generic endpoint-distance exclusion.

## Controls and rerun

Python 3 with numpy/scipy is required. Run scripts here in this order:

1. `python audit.py`
2. `python clearance.py`
3. `python prototype.py`
4. `python wheel_prototypes.py`
5. `python support_check.py`
6. PowerShell: `$env:CHECK_WHEEL='1'; python support_check.py; Remove-Item Env:CHECK_WHEEL`
7. `python controls.py`
8. `python rope_pairs.py`

`controls.json` proves all discarded 96 gun paths fail interior tests and the discarded S wheel path fails remotely from its attachment. Filling a real proposed fairlead hole with a solid cube triggers the same capsule check. No thresholds or report labels are changed for these controls.

The candidate must still be exported and audited after CLI construction. Proposed paths and voxel solids passing here do not substitute for checking actual game-exported bytes, names, model points, rotations, scale, mesh geometry, rope metadata, and bindings.

# 潮墓號裝備配置：獨立幾何複驗

- Reviewer: independent fittings_geometry_review; 2026-10-18.
- Plan SHA256: `364cfd988c58dc365984ea07b10bc9362285f83c2757808b88e535a2097d06b1`.
- Baseline NPZ file SHA256: `4b8c40649bdda99e0b283e210c98458312ac734247cfa25a05ce1494f56b9a18`.
- Baseline parts JSON SHA256: `c1da272e1b377bc9b3315dab9f2aa7e31313f7302c5296e6cf0bba4aa1811f94`.
- Seven source text export byte hashes independently checked against plan; all matched.

## Method

Read placement parameters and source exports directly. Did not import or read author draft_fittings.py. Reimplemented documented model transform from Sculpture.md 9.4.8: at + R*(scale*(p-pivot)). All present rotations are 0 or z=90 degrees, so transformed source cubes stay axis-aligned and positive-volume collision against occupied body cells is exact. Separately sampled each transformed cube centre and eight inset corners. Tested every occupied source cube against 169 pre-existing model conservative boxes, declared reserve boxes, and each other new model. Tested lowest horizontal faces for direct coplanar deck contact by intersection area.

## Result

PASS for supplied static plan: all 22 recomputed boxes match declared boxes; no source cube overlaps body, old model boxes, reserves or another new model with positive volume. Centre/corner body samples also all clear. All 22 have 100% of their lowest horizontal-face area directly touching occupied deck top faces. The body baseline contains 1,033,347 cells.

Bitts: source pivot [0,41,0] and z=90 rotation are consistent with the documented formula; port box [556,102,139,576.5,109.5,151], starboard [556,131,139,576.5,138.5,151]. Their total bottom areas are 40.5 square ship voxels each; fully supported.

MINOR: workboat rests on its keel, without a separately modelled cradle or lashing in this 22-piece plan. Its 495 lowest source cells contact 123.75 square ship voxels, x367.5..450, y150.5..152 (8.25 m by 0.15 m); geometric centre projection [408.75,151.25] lies inside that footprint. This passes static contact and vertical support but is not evidence of resistance to rolling/heeling. A cradle/lashing can remain an explicit visual follow-up rather than claiming this is sea-secured.

UNVERIFIED: rig/sail motion, heeling, model animation envelopes and full vessel physical load/collision. Old models were deliberately conservative boxes; source components were supplied voxel exports, not a new import of all attached ropes/meshes. Do not call this a dynamic sail clearance certificate.

## True negative control

Moved only spare barrel P1 down from z116 to z115 in checker memory. Detector caught 168 source cubes penetrating the occupied deck. Did not mutate plan or sculpture.

A transient EOF occurred while another process rewrote the NPZ, after the successful review. Once stable, both baseline byte hashes and placement SHA matched the reviewed bytes exactly. No work was modified by this reviewer.

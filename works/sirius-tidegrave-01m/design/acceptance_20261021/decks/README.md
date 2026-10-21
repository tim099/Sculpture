# TASK-0545 independent verification — 2026-10-21

Verdict: the remaining TASK-0545 criterion “甲板與梯子結果帳、結構與反向對照、独立複驗保存” can be signed for its stated static asset scope. This folder supplies a new independent reconstruction, current asset check, and genuine negative controls. It does not certify whole-ship safe regeneration, cloth dynamics, navigation or actor collision.

All scripts are new verifier code. No author checker or project Python module is imported; only Python standard libraries, NumPy, SciPy and Pillow are used. Work files, existing code, tasks and tavern were not changed. `patch_ledger.json` confirms the hashed original inputs did not change during this audit.

## Result ledger and drawings

`verify.py` / `report.json`: directly replay original event files, rather than using sculpt_cache. Independently interpret the hull width equation and deck/mast/hatch parameters in plan.json, subtract the pre-deck event state, and reconstruct all six original decks. Historical initial counts are lower 85212, upper 81346, weather 68684, quarter 14932, poop 5228, forecastle 3164. Missing/extra/color differences are 0 for all six. Independently reconstruct the revised seven ladders from step/bridge/foot geometry; expected and event-replayed current result are both 16023, with missing/extra/color 0.

The original deck ledger must not be mistaken for the current asset. Later changes are upper -6, weather -6, quarter -48+26-14, poop -14. `patch_ledger.py` / `patch_ledger.json` compare each of these six later events to its preserved source list: every source SHA matches its recorded event SHA; count, coordinates and available colors match exactly. The 26 added quarter cells are the steering fairlead posts. These later events explain the cache discrepancies reported by another verifier; no cache repair was attempted.

The current six drawing PNGs already depict the later changes. Consequently comparing these PNGs to the INITIAL stage produces upper/weather 2 projected cells each, quarter 17, and poop 7. They are not unexplained defects: `current.py` / `current.json` starts from every non-background PNG pixel and compares to CURRENT event-replayed top projections. All six current PNGs have 0 missing / 0 extra. Original drawing data are top projections, so this pixel test does not separately prove vertical thickness; the independent 3-D reconstruction does.

## Current assembly and structure

Read-only shared snapshot: `../shared/current.vxk`, SHA256 `ec4b54974425029f6b9bd78ef0fea55f80f5b5207b59c1c17e1353a9f751e2a3`; parts SHA `df61f69b49e636a4b866835b9194392567e2879e95051cb39d284ba11e929a93`. This is the 2026-10-21 snapshot, not the 2026-10-14 snapshot. Independently decode VXK deflate/header/chunks in `current.py`; no import of voxel_export or an author verifier.

Current assembly: 1033347 voxels; header checksum `55c4e759`; 6-neighbor components 1; enclosed empty voxels 0. Current source counts: lower 85212, upper 81340, weather 68678, quarter 14896, poop 5214, forecastle 3164, ladders 16023. Every retained event-replayed voxel of all seven children is present in the assembly and matches color (missing 0, color differences 0 for every child). Links report turn0 and common zero-based bounds.

Historical initial hull+six decks+revised ladders: 942597 voxels, 1 component, 0 cavities. Current hull+same seven source children subset: 921149 voxels, 1 component, 0 cavities. These subset counts are explicitly separate from the whole current assembly count.

## Routes and real negative controls

`current.py` independently solves the time interval during which a segment intersects each voxel X slab, then intersects the affine Z range over that interval with a height18 strip. For the fixed Y120.5 path its width7 strip spans Y117..123. Four points use foot → lo+3 → hi+3 → head. All 7 ladders × 3 continuous segments produce 0 obstacles; all 14 landing floor cells exist, with 0 obstacles through the next 14 cells above each landing.

This is the agreed static voxel path envelope, not an avatar/capsule or a demand to forbid walking through masts/hatches. It excludes imported models, ropes, sails, navSnap and animation poses.

Three controls are executed in memory only:

- Result ledger: remove `(304,111,67)` and recolor `(304,111,68)` in the full replayed ladder model. The same comparison reports missing1, color1.
- From the poop PNG pixels select the edge probe `(104,108)` (RGB145,72,0). Its distance to the actual events projection is 0; translate the entire projected asset X+3 and the same probe reads exactly 3.
- Restore the currently absent historical cut voxel `(176,117,157)` in the quarter-poop middle segment. The same continuous route ruler reports 1 obstacle immediately.

Historical independent evidence is retained under `design/audits/20261014/ladder_clearance/final_actual/`; its reported SHA a5994eee… and 1034267 voxels belong to that historical asset only. This audit does not reuse those old numbers as current readings.

## Reproduction

Run `python -I -X utf8` with `verify.py`, `current.py`, and `patch_ledger.py`, all in this folder. Each writes only its own JSON report here. Historical input hashes and event provenance are in report.json; shared snapshot hashes and current readings are in current.json; precise later source guards are in patch_ledger.json.

The final acceptance decision remains with the parent agent. Nothing here closes TASK-0540 or claims all ship stages can be blindly regenerated by the existing construction entrypoint.

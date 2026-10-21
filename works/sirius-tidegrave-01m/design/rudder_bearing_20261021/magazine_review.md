# TASK-0549 first criterion — narrow independent supplement

2026-10-21. Read-only review. `magazine_verify.py` imports only standard libraries and NumPy; no author checker or project module. All outputs are under this verifier's directory. Source events, plan, parts and snapshot hashes are recorded in `magazine_report.json`.

This supplies the missing room-inside-hull, door clearance/frame and barrel containment checks. It complements the hardware verifier's independently established structural attachment faces; it does not attempt a new whole-hull water or game navigation test.

Both magazines are independently reconstructed as45×41×24 rooms with two-cell side/floor walls, top at localz23, and final opening localx43..44, y17..23, z2..22. Each has12129 occupied voxels; original events have missing0, extra0, color0 against this independently constructed final room. Every room voxel/color is retained in the shared current assembly VXK.

Room outside bounds are aft `[240,100,30]..[285,141,54]` and fore `[440,100,30]..[485,141,54]`, with upper bounds exclusive. For every voxel of each whole rectangular room volume (44280 tests each, including empty room air), read actual shell events at that X/Z and require its Y to lie strictly inside the port/starboard shell bounds and not intersect shell wood. Violations0 for each room; minimum lateral distance to the outer shell boundary is32 cells aft and26 cells fore. This is a geometric containment check of rooms below the deck, not certification of a sealed compartment.

Each magazine contains24 barrel models with `kind=powder`,100lb each, stateok; summed inventory2400lb equals the magazine link `kind=magazine`, posaft/fore and2400lb. All24 exported transformed model AABBs per room fit fully inside its actual inner room volume `[x0+2,102,32]..[x0+43,139,53]`. Bounding-box containment is conservative and proves their full exported geometry lies inside that room, and thus within the checked hull interior.

Blast points are aft `(262.5,120.5,40.5)` and fore `(462.5,120.5,40.5)`; door points are aft `(284.5,120.5,32.5)` and fore `(484.5,120.5,32.5)`. They match each source anchor transformed by its link origin plus cell-center0.5, and lie in the chamber/door opening respectively.

The physical door opening is7 cells wide ×21 cells high ×2 cells through the wall. In world coordinates: Y117..123 and Z32..52 inclusive, X283..284 aft /483..484 fore. All294 cells of each opening are empty both in source events and in the current assembly voxel layer. All112 tested frame/floor/lintel cells remain present. Flooding only the local room's empty space from the door reaches the central blast-air cell `(22,20,10)` and32151 empty cells. The room is intentionally open through its door; preserved surrounding frame is not a closed-cavity failure.

True negative control: insert one voxel at local `(44,20,22)` in memory. The identical full-opening test changes from0 to1 blocker in each room. No voxel was written to either asset.

Verdict: the missing geometric portions of TASK-0549's first criterion pass. Together with the hardware verifier's documented36 structural attachment faces per magazine, the first criterion can be signed in its original scope. This does not claim the other three equipment criteria or entire ship are complete.

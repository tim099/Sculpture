# Independent narrow visual review of supplementary general arrangement Rev10

Reviewer: independent deck verifier, 2026-10-21. Read-only review; no original or supplementary design files changed.

Inspected `../general/general_arrangement.png` visually at its displayed 2300×2480 source resolution (tool display resized to 1513×1632), and read `plan_rev10.json`, `report.json`, and original plan.json provenance. PNG SHA256 is `f130a9aa6770bf7ca385bd251995d9a26406297d40b5d88b66c91cba8ea36e69` and matches the two deterministic generation hashes in the supplied report. I did not rerun the author's drawing generator or use its verify JSON as independent proof.

The new general drawing is readable for its intended stage-zero scope:

- Title identifies Rev10 and 0.1m/voxel. The side elevation, top/deck arrangement and body plan occupy distinct regions. Five body sections are visibly present and individually labeled S0.1, S0.25, S0.5, S0.75 and S0.9. None is cropped or covered by other panels.
- Principal dimension line reads hull52.0m, nominal beam13.4m, main mast51.0m and hull-through-bowsprit64.8m. Waterline is separately labeled5.2m. Mast height labels main51.0, fore46.5, mizzen40.5 agree with the parameter values. Hull span(620−100)×0.1=52.0 and main top510×0.1=51.0 can be checked directly from parameters. The 13.4m statement is explicitly nominal, so it does not falsely claim the visible upper-deck beam is13.4m.
- Side elevation shows twelve ports in each of two rows on the displayed side; notes explicitly state48 broadside plus6 fixed chase guns, matching the title54. The top arrangement's six forward dots are visible. The side/top view overlay nature is labeled; it is not presented as a full gun construction section.
- The parts note explicitly separates hull, decks, mast/yard parts, cannon, rudder, helm/wheel, barrels/models, and rope/sail as separate instances. It directs the reader to separate deck and48-port stage construction drawings, and explicitly declines dynamic collision acceptance. This makes the split comprehensible without making the general sheet carry every construction detail.
- Footer datum states +X BOW, +Y STARBOARD, Z0 KEEL and DRAFT GENERAL — NOT CONSTRUCTION ACCEPTANCE. The two new lines identify the supplementary date/revision and both anchors X563.5, preventing silent replacement of the historical Rev9 sheet.

Source provenance is appropriately separated: hull shape/dimensions, deck spacing, mast heights, stations and gun arrangement are design decisions; D23, Vasa and Batavia references supply visual/type context. The drawing says all line coordinates are original design. I have not independently reopened those external source pages and therefore do not certify the author's claim of personally inspecting the D23 miniature or historical fidelity. The material shown here does not require treating a museum reference as a measured construction blueprint.

Attempt to overturn: the top arrangement does not carry explicit numerical deck boundaries or gun dimensions, and each small body section has no separate axis/scale labels. This limits it to a general arrangement, exactly as its footer and detailed-drawing handoff state. It is acceptable for stage-zero legibility; it must not replace six detailed deck sheets or the port aperture checks. This is a scope limitation rather than a failed dimension test.

Minor textual inconsistency: supplementary anchor coordinates are563.5, whereas the inherited `equipment.anchors.note` still says “Moved aft20 cells” from the older560.5 placement. The numerical coordinates and Rev10 sheet are clear; the inherited prose should be marked historical or updated to avoid a reader reconstructing the wrong final anchor position from that sentence. This review does not independently remeasure anchor mesh attachment; the numerical anchor correction is supplied by the parent agent.

The parent report's main-mast event17430, quantized PNG probe355.5/120.5/510.5, whole-asset Z−3 distance0→3, and continuous beam maximization are reported as parent measurements, not new measurements by this reviewer. The separate deck verification in this folder provides its own actual PNG-derived whole-projection X+3 negative control. The supplied report distinguishes quantization and reproducibility checks from original drawing construction, which is sound.

Conclusion: visual/readability and provenance separation pass for the supplementary stage-zero general sheet, with the inherited anchor-note minor recorded above. This does not sign the entire ship or its dynamic behavior.

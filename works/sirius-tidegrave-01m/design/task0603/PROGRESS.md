# TASK-0603 — ongoing repair, not accepted

The user requests completion through dynamic acceptance. Do not mark 0603/0546
complete from preliminary body/model zero counts.

## Applied attachment repair

`../repair_task0603_attachments.py` performs all writes through Senate CLI.
48 shared four-ring gun guides and two wheel guides are real supported meshes.
96 breech ropes become three segments; wheel S becomes four segments.
497 ropes / 166 models / 50 new supported guides, original body and sails intact.

`attachments_candidate.vxk` SHA256:
`80319d1015b026e94d46f91fdd38b30fca598e57df183b0baeaa7da9ee042847`.

Independent actual-byte PASS lives at
`D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/attachment_audit/actual_final/REPORT.md`.
Keep the whole parent audit folder (its scripts depend on the original input).

## Engine under development

Our Blockside files are `src/js/30_rig_physics.js` and `src/tests/cloth_contacts.cjs`. Other dirty
files belong to concurrent work; never stage them with our fix.

The original solver omitted attached cloth collision. The current prototype checks
actual fine triangles through the High-only queue with the normal 1.5 ms budget. Fine
nodes retain the original surface (coarse interpolation changed initial geometry).
Mesh signed volume is negative for all 19 original meshes: outward normals need
orientation correction. Rope collisions must use actual radius, not line crossing.

Important rejected experiment: moving fixed pins to any nearby free solid surface
produced body/model zero but detached clamps by up to tens of cells. **Not a PASS.**
That code was removed; fixed pins now remain at authored/yardPins positions.
Rejected source is preserved only in scratch `rejected_pin_drift_v16.js`.
Flattening the startup pose and zero-wind export also failed and are not adopted.
`rest_candidate.vxk` is an unsuccessful experiment, not a delivery candidate.

Strong independent checker and local rope attachment proofs:
`D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/dynamic_qa`.
It clips complete fine triangles against solid cubes and opaque UV pixels, uses
true mesh intersection/containment, and exact capsule distance. Raw contacts stay
visible; only complete-contact local support certificates can classify attachment.

## Manual acceptance candidate, 2026-10-15

Tim explicitly chose manual acceptance. TASK-0603 and TASK-0546 remain open.
No full automated dynamic PASS is claimed. Full 20-scenario acceptance was not
rerun; previous budgeted runtime checks still contained unresolved free contacts.

Frozen `manual_candidate.vxk` SHA256:
`9081f22cb8b25c33d65b25420e670e2c6af30571bfadbaaf8805228956f93d80`.
500 ropes / 166 models. All writes used Senate sculpture CLI.

Applied route scripts are `../repair_task0603_routes.py`,
`../repair_task0603_mizzen_braces.py`, and `../repair_task0603_standing.py`.
Fore topsail braces and mizzen stay lead to the main truck. Mizzen topsail braces
use two real outboard timber eyes and two-stage cap leads, separated from lifts.
Main stay connects trucks. Fore backstays use new real wood feet at cells
450,73,128 and 450,167,128; original shared shroud anchors were not moved.
Fore stay follows the original jib head ring to the original bowsprit tip;
a separate 4 cm diameter halyard joins fore truck to that same original ring.
The jib sheet uses real forecastle timber cell595,140,158. Its changed lead
recomputes the free clew export equilibrium; sail records and fixed sail points
are preserved. Do not claim the exported jib free surface is byte-identical to
the earlier attachments-only snapshot.

Local contact proofs now require complete intersection sets, actual owner,
material-space and current-space finite boundary strips. Body seam additionally
requires the actual pivot-connected timber component. Coplanar incomplete sets
fail closed. No fixed node may be displaced by collision response. Furl rendering
keeps a full first material row around its unchanged gathered fastening edge,
and leaves all body/rope/yard fastening points untouched in rendered output.
The initial makeShip hidden state no longer triggers an unintended unfurl collapse.

Unit checks passed: immutable pins, bounded per-call corrections, wrong-owner /
remote-material / incomplete-contact rejection, finite timber joint, and furl row.
Final runtime smoke has started in `dynamic_qa/manual_final_smoke` against the
exact final VXK and source hash 6b7df51f (prefix). At t=0, all 186 active physics
pins have zero error; the rendered fastening assertion also passed and initial
furl states are all null. Seven-frame raw contact checking is separate and must
not be represented as a full acceptance PASS or classified with stale seam data.
Isolated two-ship preview roundtrip passed exact body/header/mesh comparisons.
Actual headless game shipcheck passed with 0 errors and 9 broader ship setup
warnings (geometry fallback, anchor/hawse and crew roles); this is a rig candidate,
not a complete TASK-0540 ship delivery.

Final independent readback: all 10 sail meshes and all 166 model records/meshes
are identical to the two-stage candidate. Exactly four existing standing ropes
changed and one halyard was added. Standing routes passed 104 continuous intervals
against all ten yards. All 54 raw jib/fore-stay capsule contacts lie in the actual
declared fixed luff strip, width .5540974 cells; the rejected old lead still fails
the same local test. Full 500-rope combinations of independently rotating yards
have not been certified globally, despite no nonlocal counterexample in the latest
57-angle single-yard discovery sweep. These are not full dynamic acceptance.

Preview: http://127.0.0.1:8763/index.html?ship=tidegrave,constitution&prefs=0&phx=full&p_sailhit=1
Build script: `../build_task0603_preview.py`. Frozen runtime source hashes and exact
VXK/HTML hashes live in scratch `manual-preview/MANIFEST.json`.
Normal game collision defaults and normal fleet configuration are untouched by
the preview builder. Collision remains default off and requires rig High.

Next: Tim inspects wind changes, turns/roll, furl/unfurl and reset. Keep raw
automated contact counts visible and repair concrete failures he reports;
only mark accepted after his result. No `Fixes TASK-0603` before acceptance.

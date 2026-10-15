# Manual candidate: production smoke

Final acceptance is Tim's manual inspection. This is a seven-frame automated smoke, not a whole-matrix or zero-penetration PASS.

Input SHA256: `9081f22cb8b25c33d65b25420e670e2c6af30571bfadbaaf8805228956f93d80`. Actual production `30_rig_physics.js` SHA256: `6b7df51fa1b28ad113ee201eb0992289a19a3f0189313adf992a7760d7790208`.

The fixture uses actual physStep, actual clothContactsRun after ship stepping, actual clothFine/furlDraw, actual empty Q defaults, real performance.now, rig3 and sailhit1. Collision budget1.5 ms and node step1 were not overridden. Seven states cover t=0 through .1 s at 1/60 s. Initial seen handling is fixed and all sails start with furlF=null; later gathering animation is supported by the adapter but is not exercised by this short wind case.

Physical fixed pins: 1,302 checks, maximum error0. Rendered fixed pins: 1,302 checks, maximum error0. All template positions remained authored; no original fixed pin was released. All rendered values were finite.

Raw contacts over seven states: body2824, model1568, rope centerline15, rope capsule415. Exact triangle-local rope-pin/shared-yard endpoint certificates classify274 capsule contacts as local attachment;141 remain unresolved. New body/model certificate DATA was not available when this run executed, so all body/model contacts are retained conservatively as unresolved until a separate matching-input classification is provided. Raw contacts are not erased by attachment certificates.

Known strict unpinned crossings at t=0: fore-topgallant triangles275 and402 against the new jib-halyard. At t=.1, mizzen-lateen triangle255 crosses mizzen-lateen.sheet-P; it has two hk4 vertices and requires local attachment analysis. All witnesses retain actual triangle vertices, source indices, barycentrics and source hashes. Body/model contacts retain complete intersection polygons/components for independent classification.

`input.vxk` and `frozen_source` are frozen inputs. `verifier` contains the exact independent checker implementation used. `qa_results.json` contains all readings and `render_state0.json` retains rendered/physical positions, exact pins and rope bindings. `pins.json` records input SHA256 and template metadata. Because the queue uses a real wall-clock budget, exact solver work and contact counts can vary with host speed/load; this does not affect the stated scope and does not certify full-browser frame time.

Re-run in PowerShell, replacing $D with this result folder's absolute path:

```powershell
$env:CLOTH_SOURCE="$D/frozen_source"
$env:CLOTH_OUT="$D/rerun"
$env:QA_DURATION='0.1'
$env:QA_LV='3'
$env:QA_CAPSULE='1'
$env:QA_WITNESS='1'
Remove-Item Env:QA_SEAM_CERT -ErrorAction SilentlyContinue
node "$D/verifier/check.cjs" "$D/input.vxk"
```

import pathlib,json,hashlib
p=pathlib.Path(r'D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/attachment_audit');q=p/'route_explore';r=json.loads((q/'manual_rope_pairs.json').read_text());new=[x for x in r['contacts']if x['new_route_pair']];print('all static contact witnesses',len(r['contacts']),'new route',len(new),'nonzero',[x for x in new if x['distance']>1e-6])
report='''# TASK-0603 independent route readback and geometry evidence

Final reviewed manual candidate: `manual_candidate.vxk`, SHA256 `9081f22cb8b25c33d65b25420e670e2c6af30571bfadbaaf8805228956f93d80`, 402612 bytes, 500 ropes, 166 models, 10 sails. This package is read-only independent evidence; no sculpture work was mutated by this auditor.

## Exact preservation

`manual_readback.json` verifies body payload bytes, all 166 model/mesh records and all 10 sail exports unchanged versus `two_stage_candidate.vxk`. Exactly main-stay, fore-stay and fore-backstay P/S changed; 495 other existing ropes are identical, and jib-halyard is the sole additional rope. The original author assembly `sails.json` is byte exact against `frozen_sails_design_record.json`; no author fixed pin or yard pin was moved.

Across the earlier 80319 attachment version to the first routes version, the jib free equilibrium export changed (231/240 vertices, max coordinate delta 9.92) after its sheet fairlead moved. This is disclosed in `actual_readback.json`; all other nine sail exports remained exact. Subsequent two-stage and manual candidates preserve all ten sail exports.

## Supported final routes

Fore topsail braces P/S terminate at main/truck (355.5,120.5,510.5). Mizzen stay runs mizzen/truck (205.5,120.5,405.5) to main/truck. Jib sheet S uses true body cell (595,140,158). Final mizzen braces use new outboard source eyes in the original unchanged yard wood, then own side cap (205.5,119.5/121.5,405.5), then main side cap (355.5,119.5/121.5,510.5). `two_stage_actual.json` certifies actual points, old source geometry, transforms and preservation. The full-angle analytic clearance from the adjacent own lift is at least 0.6101765 grid including export rounding, versus summed radii 0.4.

`standing_cases.json` records exact refs and coordinates. Main stay is main/truck to fore/truck. Fore backstays retain the original head and use separate true timber foot cells (450,73,128) / (450,167,128), without moving the original shared shroud feet. Fore stay is fixed jib head ring to the original fixed bowsprit tip/tack. New radius-0.2 jib halyard runs fore/truck to that same unchanged head ring. Both head and tack stay fixed.

## Proof scopes

`two_stage_outboard_continuous.json` and `two_stage_outboard_body_continuous.json` use recursive Lipschitz interval bounds for the full independent yard angle domain and exact body voxels outside enumerated actual cap contacts. They are continuous certificates, not angle samples. `standing_continuous.json` has 104 interval evaluations, zero failure/unresolved cases for all five standing routes against all ten yards. Local own-yard and mast-cap contacts are described by actual solid cells/coordinate extents, never a generic endpoint distance waiver.

`luff_certificate.json` certifies the declared fixed jib luff edge: its actual p0 vertices differ from the original head-to-tack line by at most 0.05409742 grid. Capsule intersections are bounded to a 0.55409742 band around that exact fixed edge. This is a p0 fixed-edge certificate and does not claim all wind deformation states.

`manual_rope_pairs.json` retains all 500-rope static author-pose closest capsule contact witnesses, including existing joints. Newly affected route witnesses are at exact shared terminals. Closest witnesses alone do not certify absence of long overlap. The mizzen own-lift case has the separate analytic bound above. The moving-rope discovery files are samples, explicitly not full independent-angle all-pair proofs. `runtime_bindings.json` records game binding provenance and 41 moving ropes. No full 500-rope arbitrary-angle pair proof or all-cloth/all-wind automatic acceptance is claimed. The candidate is prepared for Tim's manual acceptance.

## Retained negative controls

Direct mizzen brace to main truck has an asynchronous intersection with the main topsail brace (P distance 0.381428, S 0.397214, summed radii 0.4), retained in `rope_sweep_discovery.json`. The first two-stage route from the original earing overlaps its own lift and is rejected despite a misleading shared-endpoint closest witness. The outboard replacement removes that overlap. Old fore stay to the interior bowsprit point pierced five jib triangles, four 5.88–7.34 grid away from the actual fixed luff, and remains rejected. A radius-0.25 halyard scraped fore-topgallant; the final running line is radius 0.2.

## Reproduction

Python requires numpy and scipy. Run `manual_readback.py`, `two_stage_actual.py`, `luff_certificate.py`, and `manual_rope_pairs.py` from this directory. For continuous final two-stage checks set TWO_STAGE=1 and STAGE_FILE=two_stage_outboard.json, then run `continuous.py` and `body_continuous.py`. For standing yard checks also set STANDING=1 and run `continuous.py`. Optional `node runtime_bindings.cjs` reproduces the frozen-source runtime binding snapshot. Older `render_state0.json`/live_short1 witnesses are historical discovery inputs, not final fixed-pin runtime certification. Verifiers are this auditor's independent geometry implementations; no author QA checker was imported.
'''
(q/'REPORT.md').write_text(report,encoding='utf8')

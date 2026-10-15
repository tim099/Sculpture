# Actual attachment export: PASS

Frozen actual bytes: `input.vxk`, SHA256 `80319d1015b026e94d46f91fdd38b30fca598e57df183b0baeaa7da9ee042847`, 402,112 bytes. Source was the author's CLI export `design/task0603/attachments_candidate.vxk`; the audit never modifies it.

`check.py` reads the actual VXK header and independently reconstructs all four guide mesh types from their triangle surfaces using axis-ray parity on every half-grid cell. It does not trust the author's source voxel list or placement metadata. Reconstructed meshes contain 738 / 738 / 90 / 185 solid cubes. All 50 actual placements, 35,699 cubes total, exactly match the independently tested supported geometry in the parent audit folder.

The actual export has 497 ropes, 166 models, 10 sails, 50 guide models. Every repaired segment is an exact match for the independently cleared route, including all 96 three-segment gun ropes and the four-segment wheel-S rope. Color, radius, frame, metadata and original terminal named references are preserved. Numeric intermediate endpoints are carried by real hollow guides; no floating guide coordinate is accepted.

The entire original voxel chunk byte sequence is unchanged. All 116 original model meshes, points, bounds and metadata are unchanged. All ten sails and the other 205 original ropes are unchanged. Consequently the independently measured body/model/support-foot clearances in `../support_check.json` and `../wheel_support_check.json` apply exactly to these bytes, rather than to a guessed or historical placement. The actual 497 rope capsules are additionally retested directly against all actual reconstructed guide solids: zero contact.

All 1,225 pairs of guide model AABBs are disjoint. Every one of 500 guide/yard pairs is separated in Z by at least 47 grid units, invariant under the game's rotation about Z; asynchronous yard angles therefore cannot introduce guide/yard contact.

Existing intentional attachment contacts remain explicitly geometric: the named cascabel knob at the start, the named original hull-ring voxel at the end, wheel drum surface contact only near the named drum point, and the two tiller-end contacts at the local tip of the tiller. The prior negative controls still detect all 96 old gun routes, the old remote wheel-frame penetration, and a filled fairlead hole. No generic endpoint-distance exemption was introduced.

Rerun with `python actual_final/check.py` from the parent folder. It depends only on the frozen files and independent Python scripts in this audit package (numpy/scipy). `report.json` is machine-readable. This signs the attachment repair only; cloth physics acceptance belongs to the separate dynamic verifier.

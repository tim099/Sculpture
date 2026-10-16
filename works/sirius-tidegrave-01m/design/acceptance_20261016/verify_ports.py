"""Compare the declared port design with the historical event, without carving."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parents[1]
P = json.loads((D / "plan.json").read_text(encoding="utf-8"))
H = P["hull"]


def width(x, z):
    # Explicit design law from plan.json, not an imported author checker.
    rake = max(0, 1-z/H["rake_height"])
    lo = H["stern_x"] + H["stern_rake"]*rake
    hi = H["bow_x"] - H["bow_rake"]*rake
    t = (x-lo)/(hi-lo)
    if not 0 <= t <= 1:
        return 0
    beam = np.interp(t, [s[0] for s in H["stations"]], [s[1] for s in H["stations"]])
    floor = H["floor_base"] + H["floor_end_rise"]*abs(2*t-1)**3
    if z <= floor:
        return 0
    norm = math.sqrt(1-math.exp(-(H["tumblehome_start"]-H["floor_base"])/H["bilge_height"]))
    return beam*math.sqrt(1-math.exp(-(z-floor)/H["bilge_height"]))*max(.48, 1-H["tumblehome_per_z"]*max(0,z-H["tumblehome_start"]))/norm


state = {}
for path in sorted((D.parent / "events" / "2026-10-13").glob("*.json")):
    event = json.loads(path.read_text(encoding="utf-8"))
    before = state.copy() if path.name.startswith("231407") else None
    for x,y,z,c in event.get("placed_colored", []):
        assert (x,y,z) not in state
        state[x,y,z] = c
    for x,y,z in event.get("placed_voxels", []):
        assert (x,y,z) not in state
        state[x,y,z] = event["color"]
    for q in event.get("carved_voxels", []):
        del state[tuple(q)]
    if before is not None:
        break
assert before is not None and len(before) == 668008
expected = {}
cross_sections = []
for deck in P["guns"]["decks"]:
    for center in P["guns"]["x"]:
        for x in range(center-8, center+9):
            for z in range(deck+5, deck+20):
                w = width(x,z)
                for y in range(241):
                    if abs(y-P["center_y"]) > w-7:
                        q = (x,y,z)
                        if q in before:
                            expected[q] = before[q]
        for side in (-1,1):
            blocked = sum((x,y,z) in state
                          for x in range(center-8,center+9)
                          for z in range(deck+5,deck+20)
                          for y in range(241)
                          if (y-P["center_y"])*side > width(x,z)-7)
            cross_sections.append({"center_x":center,"deck":deck,"side":side,"blocked_cells":blocked})
actual_removed = before.keys()-state.keys()
assert actual_removed == expected.keys()
assert all(state[q] == c for q,c in before.items() if q not in expected)
assert len(expected) == 6480
assert len(cross_sections) == 48 and all(v["blocked_cells"] == 0 for v in cross_sections)
negative_extra_cut = dict(state)
retained = next(iter(state))
del negative_extra_cut[retained]
assert before.keys()-negative_extra_cut.keys() != expected.keys()
negative_missing_cut = dict(state)
removed = next(iter(expected))
negative_missing_cut[removed] = expected[removed]
assert before.keys()-negative_missing_cut.keys() != expected.keys()
report = {
    "scope":"Frozen port construction, before later decks/equipment/service corridors",
    "plan_sha256":hashlib.sha256((D/"plan.json").read_bytes()).hexdigest(),
    "port_event":path.name,"port_event_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    "declared_design":"12 positions x 2 decks x 2 sides; x center-8..center+8, z deck+5..deck+19, outer seven-cell band from the original hull width law",
    "expected_removed":len(expected),"removed_set_differences":0,"retained_color_or_position_changes":0,
    "open_port_cross_sections":cross_sections,
    "extra_retained_cell_cut_rejected":True,"omitted_declared_cut_rejected":True,
    "all_assertions_passed":True,
}
(Path(__file__).parent/"ports_readback.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"passed":True,"ports":len(cross_sections),"declared_removed":len(expected),"other_changes":0,"negative_controls":2}))

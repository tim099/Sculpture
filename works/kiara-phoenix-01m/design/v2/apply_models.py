# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟五：照 plan_models.py 的結果落刀、搬模型（全部經 CLI）。

1. 開砲門／挖缺口：plan 算出被砲管穿過的船殼格（露天甲板的卡隆砲、追擊砲）與露天甲板格（走道橫樑頂到長砲）—— carvevox 帶色守門。
2. 架艇樑：露天甲板加兩根橫過腰部的樑（stampvox）。
3. 模型：work sub=model 改 at／pivot／rotate／scale／mirror（同名同來源不用 overwrite）；絞盤從露天甲板搬到主砲甲板（先 unmodel 再加）。
用法：python -I -X utf8 apply_models.py | apply | models（只重設模型）
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HULL, TMP, WORKS, load, write_vox, senate

DECK_UP = "kiara-phoenix-01m-deck-upper"
DECK_GUN = "kiara-phoenix-01m-deck-gun"
META = {"capstan": {"kind": "capstan"}}


def fmt(v):
    return ",".join(f"{a:g}" for a in v)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    apply = mode in ("apply", "models")       # models ＝ 只重設模型（砲門、架艇樑已經落過刀時重跑用）
    plan = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan_models.json"), encoding="utf-8"))  # 落點的正式紀錄（入版控）
    lists = {HULL: os.path.join(TMP, "hull_now.txt"), DECK_UP: os.path.join(TMP, "upper_now.txt")}
    carves, beams = {}, []
    if mode != "models":                      # 砲門與架艇樑的清單在 _tmp（plan_models.py 產的）；只重設模型時不讀
        for wk, src in lists.items():
            color = {(x, y, z): c for x, y, z, c in load(src)}
            cells = [tuple(map(int, l.split(","))) for l in open(os.path.join(TMP, f"upper_ports_{wk}.txt"), encoding="utf-8") if l.strip()]
            missing = [c for c in cells if c not in color]
            assert not missing, f"{wk}：{len(missing)} 格不在作品裡（{missing[:3]}）"
            carves[wk] = [(x, y, z, color[(x, y, z)]) for x, y, z in cells]
            print(f"{wk}：開 {len(cells)} 格")
        beams = load(os.path.join(TMP, "boat_beams.txt"))
        upset = {(x, y, z) for x, y, z, c in load(lists[DECK_UP])}
        clash = [b for b in beams if b[:3] in upset]
        assert not clash, f"架艇樑撞到露天甲板 {len(clash)} 格"
    print(f"架艇樑 {len(beams)} 格；模型 {len(plan)} 個")
    if not apply:
        return
    for wk, cells in (carves.items() if mode == "apply" else ()):
        p = write_vox(os.path.join(TMP, f"ports_carve_{wk}.txt"), cells)
        senate("op=carvevox", f"work={wk}", "persona=kiara", f"voxels={p}", "at=0,0,0", f"expect_pixels={len(cells)}", "share=0")
    p = write_vox(os.path.join(TMP, "boat_beams_stamp.txt"), beams)
    if mode == "apply":
        senate("op=stampvox", f"work={DECK_UP}", "persona=kiara", f"voxels={p}", "at=0,0,0", f"expect_pixels={len(beams)}", "share=0")
    have = {}
    for wk in (DECK_UP, DECK_GUN):
        d = json.load(open(f"{WORKS}/{wk}/models.json", encoding="utf-8"))
        have[wk] = {m["name"] for m in d["models"]}
    for m in plan:
        wk, nm = m["container"], m["name"]
        args = ["op=work", "sub=model", f"work={wk}", "persona=kiara", f"name={nm}", f"at={fmt(m['at'])}",
                f"pivot={fmt(m['pivot'])}", f"rotate={fmt(m['rotate'])}", f"scale={fmt(m['scale'])}",
                f"mirror={m['mirror'] or 'none'}"]
        if nm not in have[wk]:
            other = DECK_UP if wk == DECK_GUN else DECK_GUN
            if nm in have[other]:
                senate("op=work", "sub=unmodel", f"work={other}", "persona=kiara", f"name={nm}")
            args += [f"source_work={m['work']}", "meta=" + json.dumps(META[nm], ensure_ascii=False),
                     "note=TASK-0587 v2（design/v2/plan_models.py）"]
        senate(*args)
    print("done")


if __name__ == "__main__":
    main()

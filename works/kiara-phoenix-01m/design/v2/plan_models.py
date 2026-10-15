# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟二：外部模型落點（只算，不寫作品）。

規則（造船規格 §4.2、§10）：
- 每個模型「掉到」它底下的實心上（模型每格的底面 ＝ 最高那一格實心的頂面），⛔ 不寫死 z。
- 零碰撞：模型每格的格心＋八個角都不在組裝件的實心格裡。
- 砲：砲口在船殼外；P 舷 ＝ S 舷對 y 90.5 鏡（mirror=y、at.y ＝ 181 − S；有轉角的取反號）。
- 露天甲板的砲：滑台／砲架往舷外推到貼著舷牆，砲管穿過的舷牆格開砲門（只拿船殼與露天甲板的格）。
輸出 _tmp/plan_models.json（落點）、_tmp/upper_ports_<work>.txt（要開的砲門格）。
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASM, HULL, TMP, WORKS, export_list, load, write_vox, xf

DECK_GUN = "kiara-phoenix-01m-deck-gun"
DECK_UP = "kiara-phoenix-01m-deck-upper"
LONG18 = "basecamp-frigate-constitution-01m-gun-long18"
CARR = "basecamp-frigate-constitution-01m-gun-carronade32"
CORNERS = [(0.5, 0.5, 0.5)] + [(a, b, c) for a in (0.02, 0.98) for b in (0.02, 0.98) for c in (0.02, 0.98)]

src_cache = {}


def src(work):
    if work not in src_cache:
        p = os.path.join(TMP, f"src_{work}.txt")
        src_cache[work] = export_list(work, p) if not os.path.exists(p) else load(p)
    return src_cache[work]


class World:
    def __init__(self, extra=()):
        comp = export_list(ASM, os.path.join(TMP, "composite.txt"))
        self.solid = {(x, y, z) for x, y, z, c in comp}
        self.solid |= set(extra)
        self.cols = {}
        for x, y, z in self.solid:
            self.cols.setdefault((x, y), []).append(z)
        for k in self.cols:
            self.cols[k].sort()

    def top_below(self, x, y, z):
        best = None
        for zz in self.cols.get((x, y), ()):
            if zz < z:
                best = zz
            else:
                break
        return best


def pts(m, corners=CORNERS, pred=None):
    for x, y, z, c in src(m["work"]):
        if pred and not pred(x, y, z):
            continue
        for dx, dy, dz in corners:
            yield (x, y, z), xf(m, (x + dx, y + dy, z + dz))


def drop(m, w, z_start):
    """把模型放在 z_start，往下掉到碰到實心為止；回傳新的 at.z。"""
    m = dict(m); m["at"] = [m["at"][0], m["at"][1], z_start]
    s = m["scale"][2]
    gap = 1e9
    for x, y, z, c in src(m["work"]):
        p = xf(m, (x + 0.5, y + 0.5, z + 0.5))
        bottom = p[2] - 0.5 * s
        t = w.top_below(math.floor(p[0]), math.floor(p[1]), math.floor(bottom + 1e-6) + 1)
        if t is None:
            continue
        gap = min(gap, bottom - (t + 1))
    return round(z_start - gap, 4)


def hits(m, w, pred=None):
    out = set()
    for (sx, sy, sz), p in pts(m, pred=pred):
        k = (math.floor(p[0]), math.floor(p[1]), math.floor(p[2]))
        if k in w.solid:
            out.add(k)
    return out


def mirror_of(m):
    p = dict(m)
    p["at"] = [m["at"][0], 181 - m["at"][1], m["at"][2]]
    p["mirror"] = "y"
    p["rotate"] = [0, 0, -m["rotate"][2]]
    p["name"] = m["name"].replace("-S", "-P")
    return p


def model(container, name, work, at, pivot=(0, 0, 0), rotate=(0, 0, 0), scale=1.0, mirror=""):
    return {"container": container, "name": name, "work": work, "at": list(at), "pivot": list(pivot),
            "rotate": list(rotate), "scale": [scale] * 3, "mirror": mirror}


def main():
    hull = {(x, y, z) for x, y, z, c in export_list(HULL, os.path.join(TMP, "hull_now.txt"))}
    upper = {(x, y, z) for x, y, z, c in export_list(DECK_UP, os.path.join(TMP, "upper_now.txt"))}
    w = World()
    plan, report, ports = [], [], {HULL: set(), DECK_UP: set()}

    def place(m, z_start, need_zero=True, barrel_pred=None):
        m["at"][2] = drop(m, w, z_start)
        h = hits(m, w)
        report.append((m["name"], m["at"], len(h)))
        plan.append(m)
        return h

    # 1. 主砲甲板 24 門長砲（S 舷 y 照舊、z 掉到甲板上）
    long_y = [97.5, 102.5, 106.5, 109.5, 110.5, 111.5, 111.5, 111.5, 109.5, 106.5, 102.5, 95.5]
    for k, yS in enumerate(long_y):
        # z 固定 51（甲板面 50 的上一格）；碰到的露天甲板格（走道橫樑）挖缺口，碰到船殼就是砲門沒對上 ⇒ 印出來
        s = model(DECK_GUN, f"砲-S{k + 1:02d}", LONG18, (128.25 + 25 * k, yS, 51), scale=0.5)
        h = hits(s, w)
        for c in h:
            (ports[DECK_UP] if c in upper else ports.setdefault("hull_hit_long", set())).add(c)
        report.append((s["name"], s["at"], len(h))); plan.append(s)
        p = mirror_of(s); report.append((p["name"], p["at"], -1)); plan.append(p)

    # 2. 露天甲板的砲：往舷外推到砲架碰牆（砲管那段 src y > 40 不算），砲管穿過的格開砲門
    def push_out(m, z_start, carriage_max_y):
        best = None
        y0 = m["at"][1]
        z0 = drop(m, w, z_start)          # 在舷內先掉到甲板上，之後只往舷外平推（⛔ 每步重掉會掉到舷牆頂上）
        for step in range(0, 80):
            t = dict(m); t["at"] = [m["at"][0], y0 + step * 0.5, z0]
            h = hits(t, w, pred=lambda x, y, z: y <= carriage_max_y)
            if h:
                break
            best = t
        return best

    def upper_gun(m, z_start, carriage_max_y):
        t = push_out(m, z_start, carriage_max_y)
        barrel = hits(t, w)
        for k in barrel:
            if k in hull:
                ports[HULL].add(k)
            elif k in upper:
                ports[DECK_UP].add(k)
        report.append((t["name"], t["at"], len(barrel)))
        plan.append(t)
        return t

    # 後甲板舷牆內側每 6 格一根 3×3 支柱（x 131+6k）⇒ 砲管對準兩根支柱中間的空檔，砲架推到碰支柱為止
    for i, cx in enumerate((159.5, 183.5, 207.5)):
        s = model(DECK_UP, f"carronade-S{i + 1:02d}", CARR, (cx - 3.75, 95.0, 0), scale=0.5)
        t = upper_gun(s, 95, 40)
        p = mirror_of(t)
        report.append((p["name"], p["at"], -1)); plan.append(p)
    s = model(DECK_UP, "chase18-S", LONG18, (420, 92, 0), pivot=(13.5, 38.5, 0), rotate=(0, 0, -20), scale=0.5)
    t = upper_gun(s, 95, 40)
    p = mirror_of(t); report.append((p["name"], p["at"], -1)); plan.append(p)
    # P 舷的砲門 ＝ S 舷的鏡像
    for wk in list(ports):
        ports[wk] |= {(x, 180 - y, z) for x, y, z in ports[wk]}
    assert not ports.get("hull_hit_long"), f"長砲撞船殼：{sorted(ports['hull_hit_long'])[:10]}"

    # 3. 甲板上的設備：舵輪在後桅後面、羅經櫃在兩者之間；絞盤在主砲甲板；小艇在腰部的兩根架艇樑上
    place(model(DECK_UP, "wheel", "basecamp-frigate-constitution-01m-wheel", (134, 90.5, 0), pivot=(50, 52, 0), scale=0.2), 100)
    place(model(DECK_UP, "binnacle", "summit-night-falcon-01m-binnacle", (148.5, 90.5, 0), pivot=(9, 13, 0), scale=0.2), 100)
    place(model(DECK_GUN, "capstan", "basecamp-ember-01m-capstan", (235, 90.5, 0), pivot=(40, 40, 0), scale=0.163), 62)

    # 4. 小艇：腰部中間沒有甲板 ⇒ 兩條舷側走道之間架兩根架艇樑（露天甲板的格，色 136 同橫樑），小艇掉在樑上
    beams = []
    for bx, ztop in ((300, 64), (350, 65)):
        for x in (bx, bx + 1):
            for y in range(61, 120):
                for z in (ztop - 1, ztop):
                    beams.append((x, y, z, 136))
    w2 = World(extra=[(x, y, z) for x, y, z, c in beams])
    boat = model(DECK_UP, "boat-cutter", "basecamp-frigate-constitution-01m-whaleboat", (325, 90.5, 0), pivot=(85.5, 18.5, 0), scale=0.5)
    boat["at"][2] = drop(boat, w2, 80)
    hb = hits(boat, w2)
    report.append((boat["name"], boat["at"], len(hb))); plan.append(boat)
    write_vox(os.path.join(TMP, "boat_beams.txt"), beams)

    # ⚠ 寫到 _tmp；確認過再手動複製成 design/v2/plan_models.json（apply_models.py 讀那份）——砲門開過之後重算，卡隆砲會推得更外面
    with open(os.path.join(TMP, "plan_models.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    for wk, cells in ports.items():
        with open(os.path.join(TMP, f"upper_ports_{wk}.txt"), "w", encoding="utf-8") as f:
            for c in sorted(cells):
                f.write(",".join(map(str, c)) + "\n")
        print(f"砲門格 {wk}: {len(cells)}")
    for n, at, h in report:
        print(f" {n}: at {[round(a, 3) for a in at]} hits {h}")


if __name__ == "__main__":
    main()

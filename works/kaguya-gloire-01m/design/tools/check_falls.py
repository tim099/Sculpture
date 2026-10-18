# 光榮號 機艙：從砲甲板的每個開口（艙口、煙囪旁）直直掉下去，落在哪一格、走不走得回甲板 —— 自己寫的（draft_engine_access 的 reach 不算摔）。
#   開口 ＝ 砲甲板（stand z 90）那一層 z 89 沒有格、而且四周有甲板的 (x, y)（ROOM 裡）；落點 ＝ 往下第一格實心的上一格。
#   用法：python -I -X utf8 tools/check_falls.py <design>
import os, sys, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_engine_access as A

G = A.export_grid(None)
S = G > 0
pts = json.load(open(os.path.join(D, 'engine_access_points.json'), encoding='utf-8'))
x0, x1, zt = A.ROOM
st = A.stand_map(S, x0, x1, zt)
lp = [v['points'] for v in pts.values()]
heads = [v['points']['head'] for v in pts.values()]
back = A.reach(st, x0, heads, lp, back=True)
land = {}
for x in range(x0, x1):
    for y in range(120, 281):
        if S[x, y, 89] or not S[x, y, 70:89].sum() == 0:
            continue
        if not (S[x - 3:x + 4, y, 89].any() or S[x, y - 3:y + 4, 89].any()):
            continue                                                     # 不在甲板邊上（船外）
        zs = np.nonzero(S[x, y, :89])[0]
        if not len(zs):
            continue
        z = int(zs[-1]) + 1
        land[(x, y, z)] = (x, y, z) in back
bad = sorted(k for k, v in land.items() if not v)
# 加上「跳下去」（81_fps.js fpTry：半空時往下 FP_FALL 160 格內找地板）：旁邊那一柱在窗裡站不住 ⇒ 落到它往下第一個站得住的高度；再從這些落點量走不走得回去
cols = {}
xs, ys, zs = np.nonzero(st)
for x, y, z in zip((xs + x0).tolist(), ys.tolist(), zs.tolist()):
    cols.setdefault((x, y), []).append(z)


def jump_land(x, y, z):
    out = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c = cols.get((x + dx, y + dy), ())
        if any(-A.FP_DOWN <= z2 - z <= A.FP_UP for z2 in c):
            continue
        below = [z2 for z2 in c if z2 < z - A.FP_DOWN and z - z2 <= 160]
        if below:
            out.append((x + dx, y + dy, max(below)))
    return out


def escapes(p, depth=4):
    """從 p 開始：走（同 reach）或跳下去，depth 次跳之內能不能到 back 集合。"""
    seen, frontier = set(), [p]
    for _ in range(depth):
        nxt = []
        for q in frontier:
            for r in A.reach(st, x0, [list(q)], lp):                   # q 走得到的每一格
                if r in back:
                    return True
                if r in seen:
                    continue
                seen.add(r)
                nxt.extend(jump_land(*r))
        frontier = list(set(nxt))
        if not frontier:
            break
    return False
groups, still = {}, []
for b in bad:
    g = (b[0] // 10, b[2])
    if g not in groups:
        groups[g] = escapes(b)
    if not groups[g]:
        still.append(b)
print(json.dumps({'openings_cells': len(land), 'land_back_ok': sum(land.values()), 'land_trapped_walk_only': len(bad),
                  'land_trapped_even_jumping': len(still), 'still_box': [list(np.array(still).min(0).tolist()), list(np.array(still).max(0).tolist())] if still else None,
                  'trapped_box': [list(np.array(bad).min(0).tolist()), list(np.array(bad).max(0).tolist())] if bad else None,
                  'trapped_by_z': {str(z): sum(1 for b in bad if b[2] == z) for z in sorted({b[2] for b in bad})}}, ensure_ascii=False))

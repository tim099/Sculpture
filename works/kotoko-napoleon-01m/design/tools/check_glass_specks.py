# 拿破崙號船尾窗：玻璃表面上的雜點（Tim 2026-10-25 第一人稱：「有兩個窗戶上面還有一些雜點，應該是船殼溢出的部分」）
# 每扇窗（玻璃 26 連通）當一塊：朝外 n ＝ 玻璃水平四鄰裡不在組裝件那幾側的平均；窗寬 t ⊥ n。
# 把玻璃投影到 (u, z)，一欄 (u, z) 的玻璃深度 d（沿 n，越大越外）。
# 雜點 ＝ 不是玻璃的實心格，(u, z) 落在玻璃投影裡（四周都有玻璃，不算窗框那一圈），
#   而且深度在那一欄玻璃的外側 0..OUT 格（貼在玻璃外面 / 跟玻璃同一層）—— 從艙裡看出去會畫在玻璃上。
# 用法：python -I specks.py hull.txt glass.txt asm.txt
import math, sys, json
from collections import deque, defaultdict

OUT = 3
IN = 2
IX, IY = 260.0, 200.0


def cells(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        x, y, z, c = (int(t) for t in ln.split(','))
        out[(x, y, z)] = c
    return out


hull, glass_d, asm = cells(sys.argv[1]), cells(sys.argv[2]), cells(sys.argv[3])
glass = set(glass_d)
print('glass', len(glass), 'in asm', sum(1 for g in glass if g in asm), 'asm color 155', sum(1 for g in glass if asm.get(g) == 155))
N26 = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
left, windows = set(glass), []
while left:
    s = left.pop(); w = {s}; q = deque([s])
    while q:
        p = q.popleft()
        for a, b, c in N26:
            n = (p[0] + a, p[1] + b, p[2] + c)
            if n in left:
                left.discard(n); w.add(n); q.append(n)
    windows.append(w)
windows.sort(key=lambda w: min(w))
report = []
for wi, w in enumerate(windows):
    cx = sum(g[0] for g in w) / len(w); cy = sum(g[1] for g in w) / len(w)
    sx, sy = cx - IX, cy - IY                      # 朝外 ＝ 從船裡一點指向窗中心（玻璃後面已刻穿，兩側都是空氣，看不出內外）
    nn = math.hypot(sx, sy) or 1
    nx, ny = sx / nn, sy / nn
    tx, ty = -ny, nx
    uz = defaultdict(list)
    for g in w:
        u = round((g[0] - cx) * tx + (g[1] - cy) * ty)
        d = (g[0] - cx) * nx + (g[1] - cy) * ny
        uz[(u, g[2])].append(d)
    us = [k[0] for k in uz]; zs = [k[1] for k in uz]
    umin, umax, zmin, zmax = min(us), max(us), min(zs), max(zs)
    # 候選：窗的外接框附近、朝外 OUT 格以內的實心非玻璃格
    hits = []
    R = int(max(umax - umin, zmax - zmin)) + 6
    for x in range(int(cx) - R, int(cx) + R + 1):
        for y in range(int(cy) - R, int(cy) + R + 1):
            for z in range(zmin, zmax + 1):
                p = (x, y, z)
                if p in glass or p not in asm:
                    continue
                u = round((x - cx) * tx + (y - cy) * ty)
                key = (u, z)
                if key not in uz:
                    continue
                # 不算窗框：那一欄上下左右都還有玻璃欄才算「在玻璃面裡」
                if not all((u + du, z + dz) in uz for du, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                d = (x - cx) * nx + (y - cy) * ny
                dg = max(uz[key]); dlo = min(uz[key])
                if dlo - IN <= d <= dg + OUT:
                    hits.append({'p': p, 'color': asm[p], 'in_hull': p in hull, 'side': 'out' if d > dg + 0.5 else ('in' if d < dlo - 0.5 else 'plane'), 'd_minus_glass': round(d - dg, 2)})
    report.append({'window': wi, 'glass': len(w), 'center': [round(cx, 1), round(cy, 1)], 'z': [zmin, zmax],
                   'n': [round(nx, 2), round(ny, 2)], 'specks': hits})
tot = sum(len(r['specks']) for r in report)
print('windows', len(windows), 'specks total', tot)
for r in report:
    if r['specks']:
        print(f"window {r['window']} glass={r['glass']} center={r['center']} z={r['z']} n={r['n']} specks={len(r['specks'])}")
        for h in r['specks'][:40]:
            print('   ', h)
json.dump(report, open(sys.argv[4] if len(sys.argv) > 4 else 'specks.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

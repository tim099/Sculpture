# -*- coding: utf-8 -*-
"""炎羽號 v2（TASK-0587）步驟八：把浮著的部件接回船上（§10「組裝件 1 元件」）。

10-14 的組裝件就有 39 塊（6 連通）：兩個彈藥庫懸在船艙裡、四個桅頂平台跟桅隔一圈空格、
後甲板與艏樓幾段靠那片寬頂蓋才連到船殼（頂蓋收窄後就斷了）。遊戲照連通判斷，浮著的會掉下去。
處置（只補格、不搬東西）：
- 桅頂平台、甲板：先補「一邊是浮塊、一邊是主體」的那一圈空格（間隙 1 格）；間隙更大的，在同一層找最短的橋（≤ 8 格），
  兩舷各補一條（y ↔ 180−y），格子記在浮塊那件作品；色照它相鄰的浮塊格。
- 彈藥庫：底下四根支柱落到船底（記在船殼；y 74／106 兩舷對稱）。
用法：python -I -X utf8 fix_connect.py | apply
"""
import sys, os, json
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASM, HULL, TMP, WORKS, export_list, write_vox, senate
from fix_overlap import ORDER, link_offsets

N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
POST_C = 136


def components(solid):
    seen, out = set(), []
    for s in solid:
        if s in seen:
            continue
        q = deque([s]); seen.add(s); c = [s]
        while q:
            x, y, z = q.popleft()
            for d in N6:
                n = (x + d[0], y + d[1], z + d[2])
                if n in solid and n not in seen:
                    seen.add(n); q.append(n); c.append(n)
        out.append(c)
    return sorted(out, key=len, reverse=True)


def bridge(frag, main, solid, zr, maxd=8):
    """同一層（z 不變）從浮塊往外 BFS，碰到主體就回傳路徑（不含兩端）。"""
    prev = {}
    q = deque()
    for c in frag:
        for d in N6[:4]:
            n = (c[0] + d[0], c[1] + d[1], c[2])
            if n not in solid and n not in prev:
                prev[n] = c; q.append((n, 1))
    while q:
        cur, dist = q.popleft()
        for d in N6[:4]:
            n = (cur[0] + d[0], cur[1] + d[1], cur[2])
            if n in main:
                path = [cur]
                while prev[path[-1]] not in frag:
                    path.append(prev[path[-1]])
                return path
            if dist < maxd and n not in solid and n not in prev:
                prev[n] = cur; q.append((n, dist + 1))
    return None


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    off = link_offsets()
    owner, color = {}, {}
    for name, work in ORDER:
        ox, oy, oz = off[name]
        for x, y, z, c in export_list(work, os.path.join(TMP, f"cn_{work}.txt")):
            k = (x + ox, y + oy, z + oz)
            if k not in owner:
                owner[k] = work; color[k] = c
    solid = set(owner)
    comps = components(solid)
    main = set(comps[0])
    print(f"元件 {len(comps)}：{[len(c) for c in comps]}")
    add = {}

    def put(work, k, c):
        ox, oy, oz = off[[n for n, w in ORDER if w == work][0]]
        add.setdefault(work, {})[(k[0] - ox, k[1] - oy, k[2] - oz)] = c

    for comp in comps[1:]:
        fs = set(comp)
        work = owner[comp[0]]
        if "magazine" in work:
            xs = [k[0] for k in comp]; zs = [k[2] for k in comp]
            x0, x1, z0 = min(xs), max(xs), min(zs)
            n = 0
            for x in (x0 + 3, x1 - 3):
                for y in (74, 106):
                    z = z0 - 1
                    col = []
                    while z >= 0 and (x, y, z) not in main:
                        col.append((x, y, z)); z -= 1
                    for k in col:
                        put(HULL, k, POST_C)
                    n += len(col)
            print(f"  彈藥庫 {work}：四根支柱共 {n} 格（z {z0 - 1} 往下到船底）")
            continue
        gap = set()
        for c in comp:
            for d in N6:
                e = (c[0] + d[0], c[1] + d[1], c[2] + d[2])
                if e in solid or e in gap:
                    continue
                if any((e[0] + d2[0], e[1] + d2[1], e[2] + d2[2]) in main for d2 in N6):
                    gap.add(e)
        how = f"補間隙 {len(gap)} 格"
        if not gap:
            p = bridge(fs, main, solid, None)
            if p is None:
                print(f"  ⚠ {work} @{min(comp)}（{len(comp)} 格）：8 格內接不到主體"); continue
            gap = set(p)
            how = f"橋 {len(p)} 格"
        for e in list(gap):
            m = (e[0], 180 - e[1], e[2])
            if m not in solid:
                gap.add(m)
        for e in gap:
            nb = [color[(e[0] + d[0], e[1] + d[1], e[2] + d[2])] for d in N6 if (e[0] + d[0], e[1] + d[1], e[2] + d[2]) in fs]
            c = nb[0] if nb else color[comp[0]]
            put(work, e, c)
        print(f"  {work} @{min(comp)}（{len(comp)} 格）：{how}（含鏡像共 {len(gap)}）")
    for work, cells in add.items():
        print(f"{work}：補 {len(cells)} 格")
    if not apply:
        return
    for work, cells in add.items():
        lst = [(x, y, z, c) for (x, y, z), c in sorted(cells.items())]
        p = write_vox(os.path.join(TMP, f"connect_{work}.txt"), lst)
        senate("op=stampvox", f"work={work}", "persona=kiara", f"voxels={p}", "at=0,0,0", f"expect_pixels={len(lst)}", "share=0")
    print("done")


if __name__ == "__main__":
    main()

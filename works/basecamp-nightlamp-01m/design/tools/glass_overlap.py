# 夜燈號 船尾兩舷窗（TASK-1042）第二刀：把一格厚的玻璃當成每一柱 (x, z) 一段 y 的面 ⇒ 6 連通擋得住水 ⟺ 相鄰兩柱（x 或 z 差 1）的 y 段互相有疊到。
#   沒疊到 ⇒ 外側那一柱往艙裡那一側（左舷 y 變大、右舷 y 變小）補玻璃，補到碰到鄰柱的段為止。鄰柱是窗框、窗台、楣（不是玻璃的實心）⇒ 照那一柱在這附近的實心段算。
#   第一刀（glass_bridge.py：只在邊相碰的兩格補一格）擋不住 y 一次跳兩格的地方（x 85–86：z 117 在 y 105、z 118 在 y 107）。
#   用法：glass_bridge.py 補完、重新匯出組裝件（asm2.txt）與玻璃子作品（glass2.txt，links=none）放同一個資料夾，
#     python -I -X utf8 glass_overlap.py ⇒ overlap.vox.txt（stampvox 到 basecamp-nightlamp-01m-stern-glass、at=0,0,0）。2026-10-27 補了 8 格；再跑一次 ⇒ 補 0 格。
import sys, numpy as np, collections
sys.stdout.reconfigure(encoding='utf-8')
L = lambda f: np.loadtxt(f, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
A = L('asm2.txt'); G = L('glass2.txt')
col = collections.Counter(G[:, 3].tolist()).most_common(1)[0][0]
S = set(map(tuple, A[:, :3]))
add = []
for sgn, sel in ((+1, G[:, 1] < 130), (-1, G[:, 1] > 190)):          # 左舷 y 小、往裡 ＝ y 變大；右舷鏡過來
    Gs = G[sel][:, :3]
    iv = {}
    for x, y, z in Gs:
        u = sgn * y
        a = iv.get((x, z)); iv[(x, z)] = (min(a[0], u), max(a[1], u)) if a else (u, u)
    glass_cols = set(iv)
    def frame_iv(x, z, near):                                       # 不是玻璃的鄰柱：那一柱在 near 附近 ±4 格的實心段
        us = [sgn * y for y in range(min(sgn * near[0], sgn * near[1]) - 4, max(sgn * near[0], sgn * near[1]) + 5) if (x, y, z) in S]
        return (min(us), max(us)) if us else None
    changed = True; rounds = 0
    while changed:
        changed = False; rounds += 1
        for (x, z) in sorted(glass_cols):
            a = iv[(x, z)]
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, z + dz)
                b = iv.get(n) if n in glass_cols else frame_iv(n[0], n[1], a)
                if b is None: continue
                if a[1] < b[0]:                                     # 這一柱在外側 ⇒ 往裡補到 b[0]
                    for u in range(a[1] + 1, b[0] + 1):
                        p = (x, sgn * u, z)
                        if p not in S: S.add(p); add.append(p)
                    a = (a[0], b[0]); iv[(x, z)] = a; changed = True
                elif b[1] < a[0] and n in glass_cols:              # 鄰柱在外側 ⇒ 那一柱往裡補（輪到它時也會補；這裡直接補）
                    for u in range(b[1] + 1, a[0] + 1):
                        p = (n[0], sgn * u, n[1])
                        if p not in S: S.add(p); add.append(p)
                    iv[n] = (b[0], a[0]); changed = True
    print('%s：%d 柱、補到第 %d 輪' % ('左舷' if sgn > 0 else '右舷', len(glass_cols), rounds))
print('補 %d 格（顏色 %d）' % (len(add), col))
if add:
    xs = np.array(add); print('範圍 x %d–%d y %d–%d z %d–%d；左舷 %d、右舷 %d' % (xs[:, 0].min(), xs[:, 0].max(), xs[:, 1].min(), xs[:, 1].max(), xs[:, 2].min(), xs[:, 2].max(), (xs[:, 1] < 160).sum(), (xs[:, 1] > 160).sum()))
    with open('overlap.vox.txt', 'w', encoding='utf-8', newline='\n') as f:
        f.write('# TASK-1042 夜燈號 船尾兩舷窗：相鄰兩柱的玻璃段疊起來（at=0,0,0）\n')
        for q in sorted(add): f.write('%d,%d,%d,%d\n' % (q[0], q[1], q[2], col))

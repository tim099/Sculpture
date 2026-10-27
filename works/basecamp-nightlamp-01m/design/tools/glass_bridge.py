# 夜燈號 船尾兩舷窗（TASK-1042）：一格厚的玻璃斜著走、相鄰兩格只在邊或角相碰 ⇒ 6 連通的水鑽得過去。
#   凡是兩格玻璃只在邊（兩軸各差 1）或角（三軸各差 1）相碰、中間沒有實心可以 6 連通接上的，補一格玻璃：
#   挑離中線（y＝160）近的那一格 ⇒ 補在窗的內側、外面看起來不變。重複到沒有要補的為止。只動兩舷的窗（y < 130 或 y > 190，船尾面那一排不動）。
#   用法：在一個資料夾裡放 senate cmd sculpture op=export format=list 匯出的組裝件（basecamp-nightlamp-01m-assembly.txt）與玻璃子作品（basecamp-nightlamp-01m-stern-glass.txt，links=none），
#     python -I -X utf8 glass_bridge.py ⇒ bridge.vox.txt（stampvox 到 basecamp-nightlamp-01m-stern-glass、at=0,0,0）。2026-10-27 補了 370 格；之後再跑 glass_overlap.py。
import sys, numpy as np, itertools, collections
sys.stdout.reconfigure(encoding='utf-8')
A = np.loadtxt('basecamp-nightlamp-01m-assembly.txt', delimiter=',', comments='#', dtype=np.int64, ndmin=2)
G = np.loadtxt('basecamp-nightlamp-01m-stern-glass.txt', delimiter=',', comments='#', dtype=np.int64, ndmin=2)
YC = 160
col = collections.Counter(G[:, 3].tolist()).most_common(1)[0][0]
S = set(map(tuple, A[:, :3]))
side = lambda p: p[1] < 130 or p[1] > 190
GS = set(p for p in map(tuple, G[:, :3]) if side(p))
add = []
def solid(p): return p in S
def inner(c): return min(c, key=lambda q: (abs(q[1] - YC), q[2], q[0]))
changed = True; rounds = 0
while changed:
    changed = False; rounds += 1
    for g in sorted(GS):
        for a, b in ((0, 1), (0, 2), (1, 2)):
            for sa, sb in itertools.product((1, -1), repeat=2):
                h = list(g); h[a] += sa; h[b] += sb; h = tuple(h)
                if h not in GS: continue
                e1 = list(g); e1[a] += sa; e1 = tuple(e1); e2 = list(g); e2[b] += sb; e2 = tuple(e2)
                if solid(e1) or solid(e2): continue
                c = inner([e1, e2]); S.add(c); GS.add(c); add.append(c); changed = True
        for s in itertools.product((1, -1), repeat=3):          # 角：三軸各差 1，中間 6 條路（照順序走三步）都要有一條全是實心
            h = (g[0] + s[0], g[1] + s[1], g[2] + s[2])
            if h not in GS: continue
            ok = False
            for order in itertools.permutations(range(3)):
                p = list(g); path = []
                for ax in order[:2]: p[ax] += s[ax]; path.append(tuple(p))
                if all(solid(q) for q in path): ok = True; break
            if ok: continue
            # 補：照離中線近的那一條路，把缺的格補上
            best = None
            for order in itertools.permutations(range(3)):
                p = list(g); path = []
                for ax in order[:2]: p[ax] += s[ax]; path.append(tuple(p))
                miss = [q for q in path if not solid(q)]
                k = (len(miss), sum(abs(q[1] - YC) for q in miss))
                if best is None or k < best[0]: best = (k, miss)
            for q in best[1]: S.add(q); GS.add(q); add.append(q)
            changed = True
print('補 %d 格（%d 輪），顏色 %d' % (len(add), rounds, col))
if not add: sys.exit(0)
xs = np.array(add)
print('範圍 x %d–%d y %d–%d z %d–%d' % (xs[:, 0].min(), xs[:, 0].max(), xs[:, 1].min(), xs[:, 1].max(), xs[:, 2].min(), xs[:, 2].max()))
print('左舷 %d、右舷 %d' % ((xs[:, 1] < 160).sum(), (xs[:, 1] > 160).sum()))
with open('bridge.vox.txt', 'w', encoding='utf-8', newline='\n') as f:
    f.write('# TASK-1042 夜燈號 船尾兩舷窗的玻璃補縫（at=0,0,0）\n')
    for q in sorted(add): f.write('%d,%d,%d,%d\n' % (q[0], q[1], q[2], col))

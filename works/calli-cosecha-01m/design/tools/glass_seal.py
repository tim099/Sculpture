# 出處：apex-two-galeon-01m/design/tools/glass_seal.py（康塞普西翁號，照抄 —— 收穫號 TASK-1027；作品 id 換成收穫號）
# 步驟 19：窗玻璃封不封得住（Tim 2026-10-27「玻璃好像有縫」「可以用程式檢查船尾玻璃處密封性嗎」）
#   每一片玻璃（玻璃清單 26 連通的一塊）各自量：窗的框外擴一圈、穿過牆那個方向外擴 8 格的盒子裡，從船外那一面的空格灌（6 連通，玻璃與所有格都算實心），
#   灌得到艙裡那一面（被船圍住的空格）⇒ 漏；印出那條縫上的格（船外灌得到、艙裡也灌得到的空格）。
#   ⚠ 整艘船不能一次灌：甲板上的艙口、門本來就通到艙裡 ⇒ 只看窗自己那一圈。
#   用法：python -I -X utf8 tools/glass_seal.py <design> [--drop=N]（反向對照：拿掉第 N 片玻璃正中間那一格 ⇒ 那一片要報漏）
#   · 盒子框到隔壁那一片的洞也會報漏（反向對照 --drop=5 ⇒ 第 4、5 片都報）⇒ 看漏的格落在哪一片的框裡
import sys, os, json
from collections import deque
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
drop = int(next((a.split('=')[1] for a in sys.argv[2:] if a.startswith('--drop=')), -1))
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list

A = export_list('calli-cosecha-01m-assembly', None, links=None)[:, :3]
H = export_list('calli-cosecha-01m', None)[:, :3]          # 船殼本身（認艙裡：船殼圍住的空格；拿整個組裝件認 ⇒ 陽台欄杆把船尾轉角外面也圍成「艙裡」）
G = np.loadtxt(os.path.join(design, 'masks', 'glass', 'stern_glass.vox.txt'), delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3]
YC = 160
lo = np.array([0, 0, max(0, int(G[:, 2].min()) - 24)])
hi = np.array([int(A[:, 0].max()) + 1, int(A[:, 1].max()) + 1, int(G[:, 2].max()) + 25])     # x、y 整艘船（艙裡照船殼兩頭兩舷圍住來認）
occ = np.zeros(tuple(hi - lo), bool)
m = np.all((A >= lo) & (A < hi), axis=1)
occ[tuple((A[m] - lo).T)] = True
gl = np.zeros(occ.shape, bool)
gl[tuple((G - lo).T)] = True
lab, n = ndimage.label(gl, structure=np.ones((3, 3, 3)))
if drop >= 1:                                               # 反向對照：那一片正中間那一格拿掉
    c = np.argwhere(lab == drop)
    k = c[np.argmin(((c - c.mean(axis=0)) ** 2).sum(axis=1))]
    occ[tuple(k)] = False
    print('反向對照：第 %d 片拿掉 %s' % (drop, tuple(int(v) for v in k + lo)))
# 被船圍住：±x、±y 四個方向都碰得到實心（只拿來認「艙裡那一面」）
def enclosed(o):
    f = lambda a, ax: np.maximum.accumulate(a, axis=ax)
    b = lambda a, ax: np.flip(f(np.flip(a, ax), ax), ax)
    return f(o, 0) & b(o, 0) & f(o, 1) & b(o, 1)
hull = np.zeros(occ.shape, bool)
mh = np.all((H >= lo) & (H < hi), axis=1)
hull[tuple((H[mh] - lo).T)] = True
inside = enclosed(hull) & ~occ

def flood(air, seeds):
    seen = np.zeros(air.shape, bool)
    q = deque()
    for s in seeds:
        if air[s] and not seen[s]:
            seen[s] = True
            q.append(s)
    while q:
        x, y, z = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            p = (x + d[0], y + d[1], z + d[2])
            if 0 <= p[0] < air.shape[0] and 0 <= p[1] < air.shape[1] and 0 <= p[2] < air.shape[2] and air[p] and not seen[p]:
                seen[p] = True
                q.append(p)
    return seen

res = []
for i in range(1, n + 1):
    c = np.argwhere(lab == i)
    b0, b1 = c.min(axis=0), c.max(axis=0)
    ext = b1 - b0 + 1
    ax = 0 if ext[0] <= ext[1] else 1                       # 穿過牆的方向：船尾面的窗 x、兩舷的窗 y
    pad = np.array([3, 3, 3]); pad[ax] = 8
    q0, q1 = np.maximum(b0 - pad, 0), np.minimum(b1 + pad + 1, occ.shape)
    sub = (slice(q0[0], q1[0]), slice(q0[1], q1[1]), slice(q0[2], q1[2]))
    air = ~occ[sub]
    ins = inside[sub]
    if ax == 0:
        out_face, in_face = (0, slice(None), slice(None)), (-1, slice(None), slice(None))     # 船尾在 x 小的那邊
    else:
        far = (c[:, 1].mean() + lo[1]) > YC
        out_face = (slice(None), -1 if far else 0, slice(None))
        in_face = (slice(None), 0 if far else -1, slice(None))
    def face_cells(fc, extra=None):
        mk = np.zeros(air.shape, bool); mk[fc] = True
        if extra is not None:
            mk &= extra
        return [tuple(p) for p in np.argwhere(mk & air)]
    so = flood(air, face_cells(out_face, ~ins))
    si = flood(air, face_cells(in_face, ins))
    leak = so & si
    pts = [tuple(int(v) for v in p + q0 + lo) for p in np.argwhere(leak)]
    r = {'pane': i, 'cells': int(len(c)), 'axis': 'xy'[ax], 'bbox': [[int(v) for v in b0 + lo], [int(v) for v in b1 + lo]],
         'inner_seeds': len(face_cells(in_face, ins)), 'leak_cells': len(pts), 'leak': pts[:12]}
    res.append(r)
bad = [r for r in res if r['leak_cells']]
noin = [r for r in res if not r['inner_seeds']]
for r in res:
    print('%s 第 %2d 片 %3d 格（穿牆 %s，框 %s–%s）：%s' % ('✗' if r['leak_cells'] else ('？' if not r['inner_seeds'] else '✓'), r['pane'], r['cells'], r['axis'],
          tuple(r['bbox'][0]), tuple(r['bbox'][1]), ('漏 %d 格 %s' % (r['leak_cells'], r['leak'][:6])) if r['leak_cells'] else ('艙裡那一面判不出（後面沒有被船殼圍住的空格 —— 例：露天甲板舷牆上的窗，後面本來就是外面）' if not r['inner_seeds'] else '封住')))
print('玻璃 %d 片：漏 %d 片、判不出 %d 片' % (n, len(bad), len(noin)))
json.dump(res, open(os.path.join(design, 'verify_glass_seal.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

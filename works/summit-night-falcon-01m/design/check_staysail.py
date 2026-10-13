# 階段十七驗收（main staysail）：只讀引擎匯出（組裝件 obj＝模擬後的布、list）。
# 用法：python -I -X utf8 -B check_staysail.py <組裝件 list> <組裝件 obj> [帆名] [偏移 dx,dy,dz]
#   ① 布（三角形面上取樣，離 luff 那條 stay 1.2 格以內的不算）落在實心格的取樣點數
#   ② 布到其他帆、每條繩（自己的 stay 與帆腳索不算）、每個模型的最近距離（表面取樣、KD-tree）—— 列最近的幾個
#   偏移 ＝ 反向對照：把這面帆的取樣點整批平移
import sys, re
import numpy as np
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding='utf-8')
NAME = sys.argv[3] if len(sys.argv) > 3 else 'main-staysail'
off = np.array([float(v) for v in sys.argv[4].split(',')]) if len(sys.argv) > 4 else np.zeros(3)
a = np.loadtxt(sys.argv[1], delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((384, 161, 320), bool); occ[a[:, 0], a[:, 1], a[:, 2]] = True

vs = []; cur = None; faces = {}
for line in open(sys.argv[2], encoding='utf-8'):
    if line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]])
    elif line.startswith('o '):
        m = re.match(r'o (\w+?)_\d+ # (.*)', line.strip())
        cur = (m.group(1), m.group(2)) if m else None
    elif line.startswith('f ') and cur:
        faces.setdefault(cur, []).append([int(t.split('/')[0]) - 1 for t in line.split()[1:4]])
vs = np.array(vs)[:, [0, 2, 1]]                                   # obj 是 y 朝上（階段十三）


def samples(key, n=6):
    A = vs[np.array(faces[key])]
    g = [(i / n, j / n) for i in range(n + 1) for j in range(n + 1 - i)]
    return np.concatenate([A[:, 0] + (A[:, 1] - A[:, 0]) * u + (A[:, 2] - A[:, 0]) * v for u, v in g])


me = samples(('sail', NAME)) + off
# 自己的 luff：stay 那條繩
own = {('rope', 'main-stay'), ('rope', NAME + '-sheet-S'), ('rope', NAME + '-sheet-P')}
stay = samples(('rope', 'main-stay'), 3)
d_stay = cKDTree(stay).query(me)[0]
free = me[d_stay > 1.2]
i = np.floor(free).astype(int)
ok = (i >= 0).all(1) & (i[:, 0] < 384) & (i[:, 1] < 161) & (i[:, 2] < 320)
print('① %s 布取樣 %d（離 luff >1.2 的 %d）落在實心格：%d' % (NAME, len(me), len(free), int(occ[i[ok, 0], i[ok, 1], i[ok, 2]].sum())))
near = []
for key in faces:
    if key == ('sail', NAME) or key in own:
        continue
    q = cKDTree(samples(key, 3 if key[0] == 'rope' else 4)).query(free)[0].min()
    near.append((round(float(q), 2), key[0], key[1]))
near.sort()
print('② 最近的東西：', near[:8])
print('   其他帆：', [x for x in near if x[1] == 'sail'][:5])

# 階段十八讀數：只讀引擎匯出 —— 子作品 -organ vs 清單；obj 裡 甲板-後/管風琴 的頂點（往內縮 0.02）落在實心幾個、底面頂點正下方是實心幾個；外框裡的繩頂點
# 用法：python -I -X utf8 -B check_organ.py <design> <stage18 匯出資料夾（assembly.list.txt、assembly.obj、organ.list.txt）> [偏移 dx,dy,dz]   偏移 ＝ 反向對照（obj 頂點整批平移）
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D, E = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
off = np.array([float(v) for v in sys.argv[3].split(',')]) if len(sys.argv) > 3 else np.zeros(3)
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
V = json.load(open(os.path.join(D, 'verify_organ.json'), encoding='utf-8'))


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


m, e = rd(os.path.join(D, V['file'])), rd(os.path.join(E, 'organ.list.txt'))
print('① -organ：清單 %d vs 引擎 %d｜缺 %d、多 %d、色差 %d' % (len(m), len(e), len(set(m) - set(e)), len(set(e) - set(m)), sum(1 for k in m if k in e and m[k] != e[k])))
a = np.loadtxt(os.path.join(E, 'assembly.list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((NX, NY, NZ), bool); occ[a[:, 0], a[:, 1], a[:, 2]] = True
name = V['host_link'] + '/' + V['model']
vs, own, cur = [], [], ''
for line in open(os.path.join(E, 'assembly.obj'), encoding='utf-8'):
    if line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if '#' in line else line[2:].strip()
        if line[2:].startswith('rope_'):
            cur = '~rope'
    elif line.startswith('v '):
        t = line.split(); vs.append((float(t[1]), float(t[3]), float(t[2]))); own.append(cur)
vs = np.array(vs); own = np.array(own)
P = vs[own == name] + off
c = P.mean(0); Q = P + np.sign(c - P) * 0.02
i = np.floor(Q).astype(int)
zmin = P[:, 2].min(); bot = P[np.abs(P[:, 2] - zmin) < 1e-6]
j = np.floor(bot + [0, 0, -0.5]).astype(int)
R = vs[own == '~rope']
print('② obj %s：頂點 %d、落在實心 %d｜底面 z %.3f、底面頂點 %d、正下方實心 %d｜外框內繩頂點 %d' % (
    name, len(P), int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()), zmin, len(bot), int(occ[j[:, 0], j[:, 1], j[:, 2]].sum()),
    int(((R >= P.min(0) - 0.3) & (R <= P.max(0) + 0.3)).all(1).sum())))

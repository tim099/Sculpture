# 階段十五讀數（落格之後）：只讀引擎的匯出，跟設計那一側（verify_helm.json、masks/helm）比。
# 用法：python -I -X utf8 -B check_helm.py <design> <stage15 匯出資料夾> [偏移 dx,dy,dz]
#   匯出資料夾裡：assembly.list.txt、assembly.obj、parts.json、wheel.list.txt、helm-stand.list.txt
#   偏移 ＝ 反向對照：obj 裡三個模型的頂點、與我這邊預期的外框整批平移，該報的要報出來。
# 量的東西：
#   ① 子作品：引擎匯出的格 vs mask（缺／多／色差）
#   ② parts.json：三個模型在不在、meta 對不對、外框（引擎）vs 我算的；舵輪的固定點（引擎換算過的世界座標）vs 我算的
#   ③ obj：三個模型的三角形頂點（往內縮 0.02，避開剛好貼著格面的頂點）落在實心格的個數；底面那一層頂點正下方是實心的比例（著地）
#   ④ obj：三個模型外框（外擴 0.3）裡，繩的管子頂點有幾個
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); E = os.path.abspath(sys.argv[2])
off = np.array([float(v) for v in sys.argv[3].split(',')]) if len(sys.argv) > 3 else np.zeros(3)
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
V = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


for key, f in (('wheel', 'wheel.list.txt'), ('stand', 'helm-stand.list.txt')):
    a, b = rd(os.path.join(D, V[key]['file'])), rd(os.path.join(E, f))
    print('① %s：mask %d vs 引擎 %d｜缺 %d、多 %d、色差 %d' % (V[key]['work'], len(a), len(b), len(set(a) - set(b)), len(set(b) - set(a)), sum(1 for k in a if k in b and a[k] != b[k])))

PJ = json.load(open(os.path.join(E, 'parts.json'), encoding='utf-8'))
em = {m['path']: m for m in PJ['models']}
for m in V['models']:
    p = V['host_link'] + '/' + m['name']
    e = em.get(p)
    if e is None:
        print('② %s：引擎沒有' % p); continue
    mine = np.array(m['box'][0] + m['box'][1]) + np.array([0.3] * 3 + [-0.3] * 3)     # draft 的 box 外擴了 rope_clear 0.6 ⇒ 這裡只比到 ±0.3 內
    eb = np.array(e['box'], float)
    print('② %s：state %s、meta %s｜引擎外框 %s' % (p, e.get('state'), e.get('meta'), eb.round(2).tolist()))
    if m['name'] == '舵輪':
        S = m['scale']; piv = np.array(m['pivot']); at = np.array(m['at'])
        worst = 0.0
        for k, v in V['wheel']['anchors'].items():
            exp = (np.array(v, float) + 0.5 - piv) * S + at + off
            got = np.array((e.get('points') or {}).get(k, [np.nan] * 3), float)
            worst = max(worst, float(np.abs(got - exp).max()))
        print('   舵輪固定點 %d 個：引擎 vs 我算的 最大差 %.4f' % (len(V['wheel']['anchors']), worst))

a = np.loadtxt(os.path.join(E, 'assembly.list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((NX, NY, NZ), bool); occ[a[:, 0], a[:, 1], a[:, 2]] = True
names = {V['host_link'] + '/' + m['name'] for m in V['models']}
vs, owner, cur, kind = [], [], None, 'other'
for line in open(os.path.join(E, 'assembly.obj'), encoding='utf-8'):
    if line.startswith('o '):
        cur = line.split('#', 1)[1].strip() if '#' in line else line[2:].strip()
        kind = 'rope' if line[2:].startswith('rope_') else 'other'
    elif line.startswith('v '):
        vs.append([float(t) for t in line.split()[1:4]]); owner.append(cur if cur in names else ('~rope' if kind == 'rope' else ''))
vs = np.array(vs)[:, [0, 2, 1]]; owner = np.array(owner)
for nm in sorted(names):
    P = vs[owner == nm] + off
    c = P.mean(0)
    Q = P + np.sign(c - P) * 0.02
    i = np.floor(Q).astype(int)
    inside = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
    zmin = P[:, 2].min(); bot = P[np.abs(P[:, 2] - zmin) < 1e-6]
    j = np.floor(bot + [0, 0, -0.5]).astype(int)
    sup = int(occ[j[:, 0], j[:, 1], j[:, 2]].sum())
    lo, hi = P.min(0) - 0.3, P.max(0) + 0.3
    R = vs[owner == '~rope']
    nr = int(((R >= lo) & (R <= hi)).all(1).sum())
    print('③④ %s：頂點 %d，落在實心 %d｜底面 z %.3f、底面頂點 %d 個、正下方是實心 %d｜外框內繩頂點 %d' % (nm, len(P), inside, zmin, len(bot), sup, nr))

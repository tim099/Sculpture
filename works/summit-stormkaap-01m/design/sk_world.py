# 風暴角號現況的「格 → 哪一件」標籤表（設計那一側；階段八之後的產生程式與讀數共用）。
# 從 draft_rigging.py 抽出來（那一支照舊自己建，⛔ 不改它 —— 改了它的產物就不逐位元組相同了）。
#   · 船（hull、各層甲板、船尾裝飾、側窗廊、船頭）＝ sk_state 重播到 stage6a（z < 200）；
#   · 三根桅、斜桅 ＝ masks/masts/ 的清單；channels ＝ 階段六清單 − 階段八刻 ＋ 階段八貼（右舷）＋ 鏡像（左舷）；
#   · 帆桁（外部模型、預設角）照 verify_yards.json 轉進世界座標（with_yards=True 時）。
#   · 每一件都 assert 不跟已經放進去的重疊。int8 一張表 ＝ 110 MB；一件一個 bool 陣列放不下。
# 用法：from sk_world import World; w = World(d, with_yards=True); w.lab[x, y, z] → 碼；w.names[碼] → 件名
import os, json, math
import numpy as np

from sk_state import state_after

NZ = 576


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def rot(p, c, ry, rz):
    x, y, z = p[0] - c[0], p[1] - c[1], p[2] - c[2]
    b = math.radians(ry); x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    g = math.radians(rz); x, y = x * math.cos(g) - y * math.sin(g), x * math.sin(g) + y * math.cos(g)
    return [c[0] + x, c[1] + y, c[2] + z]


class World:
    def __init__(s, d, with_yards=True, extra=()):
        s.d = d
        s.plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
        F = s.plan['frame']; s.NX, s.NY, s.YC = F['NX'], F['NY'], F['YC']
        s.names = ['']; s.lab = np.zeros((s.NX, s.NY, NZ), np.int8)
        s.color = {}
        W = state_after(d, 'stage6a', nz=200)
        for k, v in W.items():
            if k.endswith('_model') or not (v > 0).any(): continue
            p = np.argwhere(v > 0); s.put(k, p)
            s.color[k] = v
        VM = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8'))
        s.mast = {}
        for k in ('mizzen', 'main', 'fore', 'bowsprit'):
            a = load(os.path.join(d, VM['stamp_order'][k][0]['file'])); s.mast[k] = a
            s.put('mast_' + k if k != 'bowsprit' else 'bowsprit', a[:, :3])
        ch = {tuple(int(c) for c in r[:3]): int(r[3]) for r in load(os.path.join(d, VM['stamp_order']['channels'][0]['file']))}
        VR = json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))
        for o in VR['stamp_order']['channels']:
            for r in load(os.path.join(d, o['file'])):
                k = tuple(int(c) for c in r[:3])
                if o['op'] == 'carvevox': assert ch.pop(k) == r[3]
                else: ch[k] = int(r[3])
        s.channels = ch
        p = np.array(sorted(ch)); s.put('channels_S', p)
        q = p.copy(); q[:, 1] = s.NY - 1 - q[:, 1]; s.put('channels_P', q)
        for name, pts in extra: s.put(name, pts)
        s.occ200 = s.lab[:, :, :200] > 0
        if with_yards:
            yv = json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))
            s.yard_place = {P['member']: P for P in yv['placements']}
            for P in yv['placements']:
                a = load(os.path.join(d, P['file']))
                g = set()
                for c in a[:, :3] + np.asarray(P['origin']):
                    w = rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2])
                    g.add(tuple(int(math.floor(v)) for v in w))
                g = np.array(sorted(g))
                free = s.lab[tuple(g.T)] == 0
                s.names.append('yard:' + P['member']); s.lab[tuple(g[free].T)] = len(s.names) - 1

    def put(s, name, pts):
        pts = np.asarray(pts)
        assert not s.lab[tuple(pts.T)].any(), ('重疊', name, [s.names[c] for c in np.unique(s.lab[tuple(pts.T)]) if c])
        s.names.append(name); s.lab[tuple(pts.T)] = len(s.names) - 1

    def code(s, name):
        return s.names.index(name)

    def at(s, c):
        v = s.lab[c]; return s.names[v] if v else None

    def deck_top(s, x, dy=10, keys=('kamp', 'half', 'bak', 'upper')):
        """那一欄（中線外 dy）最上面那一層甲板的頂面格 z 與甲板名（甲板面 ＝ z＋1）。"""
        best = None
        for k in keys:
            if k not in s.color: continue
            c = np.nonzero(s.color[k][x, s.YC + dy, :])[0]
            if len(c) and (best is None or c.max() > best[0]): best = (int(c.max()), k)
        return best

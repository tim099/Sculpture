# 風暴角號現況重建（設計那一側）：照各階段的 verify_*.json 清單、照落子順序重播成世界座標的色陣列。
# 從夜隼號 nf_state.py（TASK-0529）改：框讀 plan.frame。
# 每一刀都驗：carvevox 那一格現在要是清單上的顏色、stampvox（非 overwrite）那一格原本要是空的 —— 對不上就丟例外（清單跟設計對不上，⛔ 不猜）。
# 用法：from sk_state import state_after; W = state_after(d, 'stage3')   # dict：作品鍵 → (NX, NY, NZ) int16
import os, json
import numpy as np

STAGES = [
    ('stage2', 'verify_hull.json', {None: 'hull'}),
    ('stage3', 'verify_planking.json', {None: 'hull'}),
    ('stage4', 'verify_decks.json', {'hull': 'hull', 'lower': 'lower', 'upper': 'upper', 'half': 'half', 'kamp': 'kamp', 'bak': 'bak'}),
]
KEYS = ('hull', 'lower', 'upper', 'half', 'kamp', 'bak')
WORK_OF = {'hull': '', 'lower': '-deck-lower', 'upper': '-deck-upper', 'half': '-deck-half', 'kamp': '-deck-kampanje', 'bak': '-deck-bak'}


def frame(d):
    f = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))['frame']
    return f['NX'], f['NY'], f['NZ_work'] if 'NZ_work' in f else 576


def read_list(path):
    return np.loadtxt(path, delimiter=',', dtype=int, comments='#', ndmin=2)


def _apply(tgt, o, d, origin=(0, 0, 0), mirror_ny=None):
    a = read_list(os.path.join(d, o['file'])); p = a[:, :3] + np.asarray(origin)
    if mirror_ny is not None: p[:, 1] = mirror_ny - 1 - p[:, 1]
    op = o.get('op', 'stampvox')
    if op == 'carvevox':
        if not (tgt[tuple(p.T)] == a[:, 3]).all(): raise ValueError('carve 守門對不上：' + o['file'])
        tgt[tuple(p.T)] = 0
    else:
        if not o.get('overwrite') and (tgt[tuple(p.T)] != 0).any(): raise ValueError('貼的格原本不是空的：' + o['file'])
        tgt[tuple(p.T)] = a[:, 3]


def state_after(d, upto, nz=None):
    NX, NY, NZ = frame(d)
    if nz is not None: NZ = nz      # 只重建到 nz 層（框全高 576 的陣列太大）；清單有格超出 ⇒ numpy 會丟 IndexError，⛔ 不會默默截掉
    W = {k: np.zeros((NX, NY, NZ), np.int16) for k in KEYS}
    for name, fn, keys in STAGES:
        V = json.load(open(os.path.join(d, fn), encoding='utf-8'))['stamp_order']
        groups = [(None, V)] if isinstance(V, list) else list(V.items())
        for sub, L in groups:
            key = keys[sub]
            for o in L:
                _apply(W[key], o, d, o.get('origin_world', (0, 0, 0)))
        if name == upto: break
    return W


def occupancy(W):
    occ = None
    for k, v in W.items():
        if k.endswith('_model'): continue
        occ = (v > 0) if occ is None else (occ | (v > 0))
    return occ

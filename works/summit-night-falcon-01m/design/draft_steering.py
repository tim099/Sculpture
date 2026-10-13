# 階段十六：舵柄與舵索 —— 舵柄加進舵子作品（跟著舵轉）、艉板開舵柄口（舵柄轉 ±max_deg 掃過的格）、
#   後甲板板下的導索塊與兩舷滑車、舵輪座底板與甲板板上的繩孔、舵索 6 段（每舷 3 段：鼓輪 → 導索塊 → 滑車 → 舵柄頭）
# 設計 plan.json steering（出處 provenance steering.*）；現況 nf_state stage15；舵的轉軸 verify_helm.json。
# 輸出：masks/steering/*.vox.txt、verify_steering.json（stamp_order、anchors、ropes、讀數）
# 用法：python -I -X utf8 -B draft_steering.py <design 資料夾>
import sys, os, json, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__))
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
ST = plan['steering']
VH = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))
W = state_after(D, 'stage15')
occ = np.zeros((NX, NY, NZ), bool)
for k, v in W.items():
    if not k.endswith('_model'):
        occ |= v > 0
R = W['rudder_model']


def rot_axis(P, o, u, deg):
    th = math.radians(deg); u = u / np.linalg.norm(u); v = P - o
    return o + v * math.cos(th) + np.cross(u, v) * math.sin(th) + np.outer(v @ u, u) * (1 - math.cos(th))


def write(name, cells, title):
    path = os.path.join(D, 'masks', 'steering', name + '.vox.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# ' + title + '（draft_steering.py）x,y,z,color —— 子作品座標 ＝ 世界\n')
        for k, c in sorted(cells.items()):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))
    return 'masks/steering/' + name + '.vox.txt'


def main():
    T = ST['tiller']
    x0, x1 = T['x']
    tiller = {}
    for x in range(x0, x1 + 1):
        for z in range(T['z'][0], T['z'][1] + 1):
            k = (x, T['y'], z)
            assert R[k] == 0, ('舵柄撞到舵自己', k)
            tiller[k] = T['end_color'] if x == x1 else T['color']
    # 舵柄要接在舵頭上（6 連通）
    touch = sum(1 for (x, y, z) in tiller if R[x - 1, y, z])
    assert touch > 0, '舵柄沒接到舵頭'
    # ── 舵柄口：舵柄轉 −max..+max（每 1°）掃過、現況的實心格 ──
    o = np.array(VH['rudder']['pivot']); hb = np.array(plan['helm']['rudder']['hinge_top']); u = hb - o
    g5 = (np.arange(5) + 0.5) / 5
    o5 = np.array([[a, b, c] for a in g5 for b in g5 for c in g5])
    ts = (np.array(sorted(tiller), float)[:, None, :] + o5[None]).reshape(-1, 3)
    swept = set()
    for deg in range(-ST['max_deg'], ST['max_deg'] + 1):
        i = np.floor(rot_axis(ts, o, u, deg)).astype(int)
        swept |= set(map(tuple, i))
    port = {k for k in swept if occ[k]}
    # 刻完之後落單的碎塊（≤ orphan_max 格、在舵柄口外框 ±2 內）一起刻（v1 柱子兩側各剩一格斷開）
    from scipy import ndimage
    tmp = occ.copy()
    for k in port:
        tmp[k] = False
    P_ = np.array(sorted(port)); lo, hi = P_.min(0) - 2, P_.max(0) + 3
    sub = tmp[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    lab, n = ndimage.label(tmp, structure=ndimage.generate_binary_structure(3, 1))
    sizes = ndimage.sum(tmp, lab, range(1, n + 1))
    orphans = set()
    for i, sz in enumerate(sizes, 1):
        if sz <= ST['orphan_max']:
            c = np.argwhere(lab == i)
            if (c >= lo).all() and (c < hi).all():
                orphans |= set(map(tuple, c))
    port |= orphans
    owners = {}
    for k in port:
        for name, v in W.items():
            if not name.endswith('_model') and v[k]:
                owners.setdefault(name, {})[k] = int(v[k])
    # ── 後甲板板下：導索塊（鼓輪正下方）、兩舷滑車；板上的繩孔 ──
    Q = W['quarter']
    blocks, holes = {}, {}
    for nm, (x, y) in ST['leads'].items():
        zp = int(np.nonzero(Q[x, y, :])[0].max())                      # 甲板板那一格
        assert not Q[x, y, zp - 1] and not occ[x, y, zp - 1], ('導索塊那格不是空的', nm)
        holes[(x, y, zp)] = int(Q[x, y, zp])
        blocks[(x, y, zp - 1)] = ST['block_color']
    sheaves_v1, sheaves = {}, {}
    for src, dst in ((ST['sheaves_v1'], sheaves_v1), (ST['sheaves'], sheaves)):
        for nm, (x, y) in src.items():
            zp = int(np.nonzero(Q[x, y, :])[0].max())
            for dz in (1, 2):
                k = (x, y, zp - dz)
                assert not occ[k], ('滑車那格不是空的', nm, k)
                dst[k] = ST['block_color']
    blocks.update(sheaves_v1)          # v1 照當時落的那一刀（導索塊＋舊滑車）重產，之後刻掉舊滑車、貼新滑車
    # ── 舵輪座底板的孔（0.02 m 子作品座標）、鼓輪上的繩點 ──
    S = VH['scale']; piv = np.array(VH['pivot']); at = np.array(VH['at'])
    stand = {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(os.path.join(D, VH['stand']['file']), encoding='utf-8') if not l.startswith('#')}
    wheel = {tuple(map(int, l.split(',')[:3])) for l in open(os.path.join(D, VH['wheel']['file']), encoding='utf-8') if not l.startswith('#')}
    base_holes, drum_pts = {}, {}
    for nm, (x, y) in ST['leads'].items():
        sx = int(math.floor((x + 0.5 - at[0]) / S + piv[0])); sy = int(math.floor((y + 0.5 - at[1]) / S + piv[1]))
        r = ST['base_hole_half']
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for z in range(0, 3):
                    k = (sx + dx, sy + dy, z)
                    if k in stand:
                        base_holes[k] = stand[k]
        zb = min(z for (a, b, z) in wheel if a == sx and b == sy)     # 鼓輪最底那一格
        drum_pts[nm] = (sx, sy, zb)
    # ── 固定點與繩 ──
    anchors = {'rudder': [{'name': 'tiller-end', 'at': [x1, T['y'], T['z'][0]]}],
               'quarter': [{'name': 'lead-' + nm, 'at': [x, y, int(np.nonzero(Q[x, y, :])[0].max()) - 1]} for nm, (x, y) in ST['leads'].items()]
                          + [{'name': 'sheave-' + nm, 'at': [x, y, int(np.nonzero(Q[x, y, :])[0].max()) - 1]} for nm, (x, y) in ST['sheaves'].items()],
               'wheel': [{'name': 'tiller-rope-' + nm, 'at': list(p)} for nm, p in drum_pts.items()]}
    RP = ST['rope']
    ropes = []
    for nm, side in ST['pairs'].items():
        ropes.append(dict(name=f'舵索-{nm}1', **{'from': f'model:甲板-後/舵輪/tiller-rope-{nm}', 'to': f'甲板-後/lead-{nm}'}, **RP, group='steering'))
        ropes.append(dict(name=f'舵索-{nm}2', **{'from': f'甲板-後/lead-{nm}', 'to': f'甲板-後/sheave-{side}'}, **RP, group='steering'))
        ropes.append(dict(name=f'舵索-{nm}3', **{'from': f'甲板-後/sheave-{side}', 'to': 'model:舵/tiller-end'}, **RP, group='steering'))
    files = {'tiller': write('tiller', tiller, '舵柄（加進舵子作品）'),
             'blocks': write('quarter_blocks', blocks, '導索塊與滑車（加進後甲板子作品）'),
             'holes': write('quarter_holes', holes, '甲板板上的繩孔（從後甲板子作品刻掉）'),
             'base_holes': write('stand_holes', base_holes, '舵輪座底板的繩孔（0.02 m 子作品座標）'),
             'sheaves_v1': write('quarter_sheaves_v1', sheaves_v1, '舊滑車 v1（y 74／86；刻掉：舵柄頭擺得比它還外面）'),
             'sheaves': write('quarter_sheaves', sheaves, '滑車 v2（y 64／96，舵柄頭擺不到）')}
    stamp = {'rudder': [{'name': 'tiller', 'op': 'stampvox', 'file': files['tiller'], 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(tiller)}],
             'quarter': [{'name': 'rope_holes', 'op': 'carvevox', 'file': files['holes'], 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(holes)},
                         {'name': 'blocks', 'op': 'stampvox', 'file': files['blocks'], 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(blocks)},
                         {'name': 'sheaves_v1_out', 'op': 'carvevox', 'file': files['sheaves_v1'], 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(sheaves_v1)},
                         {'name': 'sheaves', 'op': 'stampvox', 'file': files['sheaves'], 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(sheaves)}]}
    for name, cells in sorted(owners.items()):
        f = write('port_' + name, cells, '舵柄口（從 %s 刻掉：舵柄轉 ±%d° 掃過的格）' % (name, ST['max_deg']))
        stamp.setdefault(name, []).append({'name': 'tiller_port', 'op': 'carvevox', 'file': f, 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(cells)})
    out = {'note': 'draft_steering.py（階段十六）—— 現況 nf_state stage15；舵軸 verify_helm.json',
           'stamp_order': stamp, 'stand_holes': {'file': files['base_holes'], 'voxels': len(base_holes), 'work': VH['stand']['work']},
           'anchors': anchors, 'ropes': ropes,
           'counts': {'orphans': len(orphans), 'tiller': len(tiller), 'tiller_touch_head': touch, 'port': {k: len(v) for k, v in owners.items()}, 'blocks': len(blocks), 'sheaves_v1': len(sheaves_v1), 'sheaves': len(sheaves),
                      'holes': len(holes), 'base_holes': len(base_holes), 'ropes': len(ropes)},
           'drum_points': {k: list(v) for k, v in drum_pts.items()}}
    with open(os.path.join(D, 'verify_steering.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out['counts'], ensure_ascii=False), 'drum', out['drum_points'])


if __name__ == '__main__':
    main()

# 外部模型的擺法（唯一的一份）：武器、舷側舵、三角帆桁、火藥桶 —— 算 at／pivot／rotate／scale／mirror＋meta，
# 再量「退到零碰撞」（造船規格 §4.2：模型每一格的格心＋八個角都不在實心格裡；實心 ＝ 船殼＋甲板＋上層結構＋桅）。
# 變換（跟引擎同一套）：world ＝ at ＋ Rz·Ry·Rx ·（scale ·（鏡像（p − pivot）））；p ＝ 來源作品的格心／格角。
# 用法：python -I -X utf8 -B placements.py ⇒ verify_models.json（含每個模型的碰撞讀數）
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import dro

D = dro.D
YC, YM = dro.YC, dro.YM
VH = json.load(open(os.path.join(D, 'verify_hull.json'), encoding='utf-8')); ZAIR = VH['zair']
VU = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
VR = json.load(open(os.path.join(D, 'verify_rig.json'), encoding='utf-8'))
VW = json.load(open(os.path.join(D, 'verify_weapons.json'), encoding='utf-8'))
VS = json.load(open(os.path.join(D, 'verify_steer.json'), encoding='utf-8'))
geo = VU['_geo']


def rot(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def xform(pts, m):
    s = np.asarray(m['scale'], float) if isinstance(m['scale'], (list, tuple)) else np.full(3, float(m['scale']))
    q = pts - np.asarray(m['pivot'], float)
    if 'y' in m.get('mirror', ''):
        q[:, 1] = -q[:, 1]
    if 'x' in m.get('mirror', ''):
        q[:, 0] = -q[:, 0]
    q = q * s
    return (rot(*m['rotate']) @ q.T).T + np.asarray(m['at'], float)


def load(path):
    a = np.loadtxt(os.path.join(D, path), delimiter=',', comments='#', dtype=int, ndmin=2)
    return a


SOLID = np.zeros((dro.NX, dro.NY, dro.NZ), bool)
for f in ['lists/hull.txt', 'lists/deck_main.txt', 'lists/deck_hold.txt'] + [VU[k]['file'] for k in ('forecastle', 'castles', 'fittings', 'magazine', 'ladders')] + [VR['masts'][k]['file'] for k in VR['masts']]:
    a = load(f); SOLID[a[:, 0], a[:, 1], a[:, 2]] = True

M = []     # 每個：name, host（掛在哪件作品）, source_work, file（來源清單，算碰撞與預覽）, at, pivot, rotate, scale, mirror, meta, check
W = 'erina-dromon-01m-'

# ── 武器 ──（siphon、弩砲、投石機都是 kind=gun；弩砲 2026-10-18 晚改打火箭 ammo=firebolt：Tim「是否可以讓弩炮改發射火箭(有點燃效果)」）
#   弩砲（Tim 2026-10-18 晚：「弩炮目前我想直接做成換皮大炮(只是彈藥不同) 一樣走裝彈 發射流程」「弩炮可以給一定的轉動空間(參考維吉尼亞號的前後炮)」）⇒
#   kind=gun gun=ballista（Blockside 砲種表 ballista、彈種弩箭）＋ mount=pivot ports（停在這幾個角度，量過零碰撞；+ ＝ 往格 +y 轉）。
# （原註：kind=gun＋weapon／ammo：之後遊戲加彈種與武器種類時照這兩個鍵分；現在 gun= 用現有的砲種代碼頂著）
sw = VW['siphon']; piv = [sw['anchors']['pivot'][0] + 0.5, sw['anchors']['pivot'][1] + 0.5, 0]
M.append(dict(name='siphon', host='assembly', source_work=W + 'siphon', file=sw['file'], scale=0.5, rotate=[0, 0, -90], mirror='',
              pivot=piv, at=[332.0, YM, float(max(ZAIR[323:355]))],
              meta={'kind': 'gun', 'gun': 'siphon', 'weapon': 'siphon', 'ammo': 'greekfire', 'safe': 1}))
bw = VW['ballista']; pb = [bw['anchors']['pivot'][0] + 0.5, bw['anchors']['pivot'][1] + 0.5, 0]
BALLISTA_PORTS = {'bow': '0,35,-35', 'castle': '0,45,-45'}
FX0, FX1, FZ = geo['forecastle']
M.append(dict(name='ballista-bow', host='forecastle', source_work=W + 'ballista', file=bw['file'], scale=0.4, rotate=[0, 0, -90], mirror='',
              pivot=pb, at=[333.5, YM, float(FZ + 1)], meta={'kind': 'gun', 'gun': 'ballista', 'weapon': 'toxoballistra', 'ammo': 'firebolt', 'mount': 'pivot', 'ports': BALLISTA_PORTS['bow']}))
KX0, KX1, KO0, KO1, KZ = geo['castles']
for s, rz in (('S', 0), ('P', 180)):
    # 木塔上的小弩砲（0.3 ⇒ 1.4 m）：內端退到離中線 9 格 ⇒ 5–7 格那條給送藥手（遊戲在砲口 x、離中線 ±9 格、半徑 4 找；砲的外框再外 1 格不能站）、外側 19 格那排給砲手
    M.append(dict(name='ballista-castle-' + s, host='castles', source_work=W + 'ballista', file=bw['file'], scale=0.3, rotate=[0, 0, rz], mirror='',
                  pivot=pb, at=[226.5, YM + (13.95 if s == 'S' else -13.95), float(KZ + 1)], meta={'kind': 'gun', 'gun': 'ballista', 'weapon': 'toxoballistra', 'ammo': 'firebolt', 'mount': 'pivot', 'ports': BALLISTA_PORTS['castle']}))
mw = VW['mangonel']; pm = [mw['anchors']['pivot'][0] + 0.5, mw['anchors']['pivot'][1] + 0.5, 0]
# 投石機（Tim 2026-10-18 晚：「接著做投石機吧(同時把一些零件換成繩索)」「投石機是否可以給高拋物線彈道(可以砸到甲板)」）⇒ 換皮大砲：kind=gun gun=mangonel
#   （Blockside 砲種表 mangonel：石彈、曲射 lob、最大仰角 75°）＋整圈轉 mount=turret arc −180,180（持火號多半船頭對敵 ⇒ 只有兩舷 ports 0,180 的時候 120 秒對得到 6.5 秒、一發都沒開；
#   每 30° 量過零碰撞：12 個角度全 0）。投臂另一件 mangonel-arm 放在同一點（同框、同 pivot、同 at ⇒ 對齊），
#   meta spin=gun：照那門投石機的開火進度繞鐵軸（固定點 spin-a → spin-b）轉到 spin_k −135°（長臂甩到正上方）、裝填時轉回來；投石機迴旋時跟著轉（Blockside 26_spin.js）。
MG_AT = [255.5, YM - 1.5, float(max(ZAIR[247:266]))]
M.append(dict(name='mangonel', host='assembly', source_work=W + 'mangonel', file=mw['file'], scale=0.45, rotate=[0, 0, 0], mirror='',
              pivot=pm, at=MG_AT,
              meta={'kind': 'gun', 'gun': 'mangonel', 'weapon': 'manganikon', 'ammo': 'stone', 'mount': 'turret', 'arc': '-180,180', 'rate': 10}))
aw = VW['mangonel-arm']
M.append(dict(name='mangonel-arm', host='assembly', source_work=W + 'mangonel-arm', file=aw['file'], scale=0.45, rotate=[0, 0, 0], mirror='',
              pivot=pm, at=MG_AT, meta={'spin': 'gun', 'spin_gun': 'mangonel', 'spin_k': -135, 'spin_lag': 0}))

# ── 舷側舵（S 原樣、P 鏡像）──
hS, hP = VS['hinge_S'], VS['hinge_P']
for s, h, mir in (('S', hS, ''), ('P', hP, 'y')):
    meta = {'kind': 'rudder', 'hinge_x': h[0], 'hinge_y': h[1], 'hinge_z': h[2], 'axis_x': 0, 'axis_y': 0, 'axis_z': 1, 'max_deg': 35, 'turn_axis': 'hinge',
            'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3, 'rudder': 'quarter'}
    M.append(dict(name='rudder-' + s, host='assembly', source_work=W + 'rudder', file=VS['file'], scale=1, rotate=[0, 0, 0], mirror=mir,
                  pivot=list(hS), at=list(h), meta=meta))

# ── 三角帆桁（掛在各自的桅子作品裡）──
for nm, y in VR['yards'].items():
    mdl = y['model']
    L = dro.PLAN['rig']['yards'][nm]['length']
    meta = {'kind': 'yard', 'mast': y['mast'], 'yard': 'gaff', 'rig': 'lateen', 'sail': nm, 'length_ft': round(L * 0.1 / 0.3048, 1),
            'diameter_in': round(2 * dro.PLAN['rig']['yards'][nm]['r_mid'] * 0.1 / 0.0254, 1), 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': mdl['rotate'][2]}
    M.append(dict(name='yard-' + nm, host='mast-' + y['mast'], source_work=W + 'yard-' + nm, file=y['file'], scale=1, rotate=mdl['rotate'], mirror='',
                  pivot=mdl['pivot'], at=mdl['at'], meta=meta, check=False))

# ── 藥庫的補給（掛在藥庫子作品裡）：希臘火陶罐 ×4、弩箭箱 ×2（draft_stores.py；遊戲當火藥桶 kind=powder，取用點輪流擺這兩種樣子 —— Tim 2026-10-18「彈藥箱可以有不同外觀(但實際上都能補彈)」）──
#   （原本是憲法號的火藥桶 ×6 頂著）
MX0, MX1 = geo['magazine']
hz = dro.PLAN['deck_hold']['z']
VST = json.load(open(os.path.join(D, 'verify_stores.json'), encoding='utf-8'))
k = 0
for bx in (133.5, 138.5, 143.5):                        # 跟著隔艙壁 x 130／147 挪一格
    for by in (YC - 4.5, YC + 5.5):
        k += 1
        st = 'boltbox' if bx > 140 else 'amphora'
        sp = VST[st]; pv = [sp['anchors']['pivot'][0] + 0.5, sp['anchors']['pivot'][1] + 0.5, 0]
        M.append(dict(name='桶-%03d' % k, host='magazine', source_work=W + 'store-' + st, file=sp['file'],
                      scale=0.5, rotate=[0, 0, 0], mirror='', pivot=pv, at=[bx, by, float(hz + 1)], meta={'kind': 'powder', 'powder_lb': 100, 'store': 'bolt' if st == 'boltbox' else 'greekfire'}))

# ── 錨（共用元件 憲法號 bower，縮到 0.3 ⇒ 1.4 × 1.7 m；掛在艏部兩舷的吊錨架下，錨環頂貼著吊錨架底）──
cx_, wc_, zc_ = geo['cathead']
for s, mir in (('S', ''), ('P', 'y')):
    yy = YM + (wc_ + 7) * (1 if s == 'S' else -1)
    M.append(dict(name='anchor-' + s, host='fittings', source_work='basecamp-frigate-constitution-01m-anchor', file='lists/ext_anchor.txt',
                  scale=0.3, rotate=[0, 0, 90], mirror=mir, pivot=[23.5, 16.5, 57.0], at=[cx_ + 1.5, yy, zc_ - 0.3],
                  meta={'kind': 'anchor', 'anchor': 'bower'}))

# ── 量 ──
corners = np.array([[dx, dy, dz] for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)], float)
OUT = []
for m in M:
    a = load(m['file'])
    if m.get('check', True):
        c = a[:, :3].astype(float)
        pts = np.vstack([c + 0.5] + [c + corners[i] * 0.999 + 0.0005 for i in range(8)]) if m['scale'] >= 0.99 else np.vstack([c + 0.5] + [c + corners[i] for i in range(8)])
        w = xform(pts, m)
        ij = np.floor(w).astype(int)
        ok = (ij[:, 0] >= 0) & (ij[:, 0] < dro.NX) & (ij[:, 1] >= 0) & (ij[:, 1] < dro.NY) & (ij[:, 2] >= 0) & (ij[:, 2] < dro.NZ)
        hit = np.zeros(len(ij), bool); hit[ok] = SOLID[ij[ok, 0], ij[ok, 1], ij[ok, 2]]
        n = len(c)
        cell_hit = hit.reshape(9, n).any(0)
        m['collide_cells'] = int(cell_hit.sum())
        bad = np.unique(ij[hit], axis=0)[:6].tolist()
        m['collide_sample'] = bad
    else:
        m['collide_cells'] = None
    if m['meta'].get('mount') == 'pivot':             # 迴旋：每個停靠角度都量（繞 z、+ ＝ 往 +y 轉）
        m['ports_collide'] = {}
        for ang in [float(v) for v in m['meta']['ports'].split(',')]:
            mm = dict(m); mm['rotate'] = [m['rotate'][0], m['rotate'][1], m['rotate'][2] + ang]
            c = a[:, :3].astype(float)
            w = xform(np.vstack([c + 0.5] + [c + corners[i] for i in range(8)]), mm)
            ij = np.floor(w).astype(int)
            ok = (ij[:, 0] >= 0) & (ij[:, 0] < dro.NX) & (ij[:, 1] >= 0) & (ij[:, 1] < dro.NY) & (ij[:, 2] >= 0) & (ij[:, 2] < dro.NZ)
            hit = np.zeros(len(ij), bool); hit[ok] = SOLID[ij[ok, 0], ij[ok, 1], ij[ok, 2]]
            m['ports_collide']['%g' % ang] = int(hit.reshape(9, len(c)).any(0).sum())
    wc = xform(a[:, :3].astype(float) + 0.5, m)
    m['bbox'] = [np.round(wc.min(0), 1).tolist(), np.round(wc.max(0), 1).tolist()]
    OUT.append(m)
json.dump(OUT, open(os.path.join(D, 'verify_models.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
for m in OUT:
    print('%-18s host %-10s collide %-5s bbox %s' % (m['name'], m['host'], m['collide_cells'], m['bbox']), m.get('collide_sample', '')[:3] if m['collide_cells'] else '', m.get('ports_collide', ''))

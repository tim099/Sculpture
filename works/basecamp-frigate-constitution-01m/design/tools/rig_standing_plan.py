# 靜索（standing rigging）試掛（階段十九前，2026-10-11）：從桅杆／bowsprit／船殼／knee 的實際格子量固定點，
# 再列出每一條繩的兩端 ⇒ design/rig_standing.json（給 rig_standing_apply.py 一條一條下 CLI）
# 用法：python -I rig_standing_plan.py <design 資料夾>
import sys, os, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_masts import export_list   # noqa: E402
PRE = 'basecamp-frigate-constitution-01m'
YC = 160

A = {m: export_list(PRE + ('-bowsprit' if m == 'bowsprit' else '-mast-' + m), draft=False, links='none') for m in ('main', 'fore', 'mizzen', 'bowsprit')}
HULL = export_list(PRE, draft=False, links='none')
KNEE = export_list(PRE + '-head-knee', draft=False, links='none')
SOL = {k: {(int(x), int(y), int(z)) for x, y, z, c in v} for k, v in list(A.items()) + [('hull', HULL), ('knee', KNEE)]}

# 量到的高度（桅杆子作品、世界座標；2026-10-11 逐層印剖面讀的：trestletrees 下一格 ＝ hounds、crosstrees 下一格 ＝ topmast head、royal yard 下兩格 ＝ topgallant head）
MAST = {
    'main':   {'link': '主桅', 'xc': 344, 'hounds': 281, 'top': (284, 286), 'tm_head': 462, 'xtree': 464, 'tg_head': 634, 'truck': 646,
               'futtock': 267, 'rim_dx': [-12, -6, 0, 6], 'low_in': 120},
    'fore':   {'link': '前桅', 'xc': 584, 'hounds': 258, 'top': (261, 263), 'tm_head': 423, 'xtree': 425, 'tg_head': 586, 'truck': 598,
               'futtock': 245, 'rim_dx': [-11, -5, 1, 7]},
    'mizzen': {'link': '後桅', 'xc': 196, 'hounds': 236, 'top': (239, 241), 'tm_head': 374, 'xtree': 376, 'tg_head': 498, 'truck': 509,
               'futtock': 226, 'rim_dx': [-9, -3, 3]},
}
ROPE_C = '#2b2620'            # 靜索：上過焦油的深褐黑


def core(m, z, xc, r=12):
    s = [(x, y) for (x, y, zz) in SOL[m] if zz == z and abs(y - YC) <= 8 and abs(x - xc) <= r]
    assert s, (m, z)
    return s


def side_cell(m, z, xc, side):
    s = core(m, z, xc)
    ys = [y for x, y in s]
    y = max(ys) if side == 'S' else min(ys)
    xs = sorted(x for x, yy in s if yy == y)
    return (xs[len(xs) // 2], y, z)


def face_cell(m, z, xc, face):
    s = [(x, y) for x, y in core(m, z, xc) if y == YC]
    xs = [x for x, y in s]
    return ((max(xs) if face == 'fwd' else min(xs)), YC, z)


def rim_cell(m, z, x, side):
    ys = [y for (xx, y, zz) in SOL[m] if zz == z and xx == x]
    assert ys, (m, z, x)
    return (x, max(ys) if side == 'S' else min(ys), z)


anchors = []      # {work, link, name, at(本作品座標), world}
ropes = []


def anchor(work_key, link, name, world, at=None):
    w = tuple(int(v) for v in world)
    if work_key in SOL:
        assert w in SOL[work_key], ('固定點不在實心格上', work_key, name, w)
    anchors.append({'work': work_key, 'link': link, 'name': name, 'world': list(w), 'at': list(at or w)})
    return link + '/' + name


def rope(name, a, b, th, slack, group):
    ropes.append({'name': name, 'from': a, 'to': b, 'thickness': th, 'slack': slack, 'color': ROPE_C, 'group': group})


# ── 桅杆上的固定點 ──
P = {}
for m, M in MAST.items():
    L, xc = M['link'], M['xc']
    p = P[m] = {}
    for sd in ('S', 'P'):
        p['shrouds-' + sd] = anchor(m, L, 'shrouds-' + sd, side_cell(m, M['hounds'], xc, sd))
        p['futtock-' + sd] = anchor(m, L, 'futtock-' + sd, side_cell(m, M['futtock'], xc, sd))
        p['tm-' + sd] = anchor(m, L, 'tm-' + sd, side_cell(m, M['tm_head'], xc, sd))
        for k, dx in enumerate(M['rim_dx']):
            p['rim-%s%d' % (sd, k + 1)] = anchor(m, L, 'rim-%s%d' % (sd, k + 1), rim_cell(m, M['top'][1], xc + dx, sd))
            p['rimlow-%s%d' % (sd, k + 1)] = anchor(m, L, 'rimlow-%s%d' % (sd, k + 1), rim_cell(m, M['top'][0], xc + dx, sd))
        # crosstrees 兩端（前後兩根）
        cs = [(x, y) for (x, y, z) in SOL[m] if z == M['xtree'] and abs(x - xc) <= 12]
        ye = max(y for x, y in cs) if sd == 'S' else min(y for x, y in cs)
        xs = sorted(x for x, y in cs if y == ye)
        p['xtree-%s1' % sd] = anchor(m, L, 'xtree-%s1' % sd, (xs[0], ye, M['xtree']))
        p['xtree-%s2' % sd] = anchor(m, L, 'xtree-%s2' % sd, (xs[-1], ye, M['xtree']))
    p['tg-head'] = anchor(m, L, 'tg-head', face_cell(m, M['tg_head'], xc, 'fwd'))
    p['stay-out'] = anchor(m, L, 'stay-out', face_cell(m, M['hounds'], xc, 'fwd'))
    p['tm-stay-out'] = anchor(m, L, 'tm-stay-out', face_cell(m, M['tm_head'], xc, 'fwd'))
    p['royal-stay-out'] = anchor(m, L, 'royal-stay-out', face_cell(m, M['truck'], xc, 'fwd'))
    if m in ('main', 'fore'):
        p['stay-in-top'] = anchor(m, L, 'stay-in-top', face_cell(m, M['hounds'], xc, 'aft'))
        p['stay-in-tm'] = anchor(m, L, 'stay-in-tm', face_cell(m, M['tm_head'], xc, 'aft'))
        p['stay-in-tg'] = anchor(m, L, 'stay-in-tg', face_cell(m, M['tg_head'], xc, 'aft'))
    if m == 'main':
        p['stay-in-low'] = anchor(m, L, 'stay-in-low', face_cell(m, M['low_in'], xc + 6, 'aft'))

# ── bowsprit、船殼（knightheads）、knee ──
B = {}
B['forestay'] = anchor('bowsprit', '艏斜桅', 'forestay', (700, 160, 147))
B['cap'] = anchor('bowsprit', '艏斜桅', 'cap', (786, 160, 175))
B['jibboom-end'] = anchor('bowsprit', '艏斜桅', 'jibboom-end', (879, 160, 203))
B['flying-end'] = anchor('bowsprit', '艏斜桅', 'flying-end', (957, 160, 224))
for i, x in enumerate((745, 770)):
    zb = min(z for (xx, y, z) in SOL['bowsprit'] if xx == x and y == YC)
    B['bobstay-%d' % (i + 1)] = anchor('bowsprit', '艏斜桅', 'bobstay-%d' % (i + 1), (x, YC, zb))
for i, z in enumerate((96, 104)):
    xk = max(x for (x, y, zz) in SOL['knee'] if zz == z and y == YC)
    B['knee-%d' % (i + 1)] = anchor('knee', '船頭-knee', 'bobstay-%d' % (i + 1), (xk, YC, z))
for sd, y in (('S', 170), ('P', 150)):
    zt = max(z for (x, yy, z) in SOL['hull'] if x == 660 and yy == y)
    B['knighthead-' + sd] = anchor('hull', '船殼', 'mainstay-' + sd, (660, y, zt))

# ── channels 的 deadeye（子作品只有 S 那一舷；P ＝ 鏡像關聯）──
CH_AT = (150, 161, 70)
ch = json.load(open(os.path.join(D, 'rig_points_channels.json'), encoding='utf-8'))['points']
DE = {}
for q in ch:
    if q['side'] != 'S':
        continue
    mast = q['name'].split('-')[0]
    i = int(q['name'].rsplit('S', 1)[1])
    w = q['world']
    nm = '%s.deadeye-%d' % (mast, i)
    anchor('channels', 'channels', nm, w, at=(w[0] - CH_AT[0], w[1] - CH_AT[1], w[2] - CH_AT[2]))
    DE[(mast, i)] = nm

# ── 繩 ──
CH = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['channels']['masts']
TH = {'main': 0.9, 'fore': 0.85, 'mizzen': 0.65}
for M in CH:
    m, ns, nb = M['mast'], M['shrouds'], M['backstays']
    p = P[m]
    for sd, cl in (('S', 'channels'), ('P', 'channels-鏡像')):
        for i in range(1, ns + 1):
            rope('%s-shroud-%s%d' % (m, sd, i), cl + '/' + DE[(m, i)], p['shrouds-' + sd], TH[m], 1.0, 'lower shrouds')
        for j in range(1, nb + 1):
            top = p['tg-head'] if j == nb else p['tm-' + sd]
            rope('%s-backstay-%s%d' % (m, sd, j), cl + '/' + DE[(m, ns + j)], top, TH[m] * 0.9, 1.0, 'backstays')
        k = len(MAST[m]['rim_dx'])
        for i in range(1, k + 1):
            rope('%s-futtock-%s%d' % (m, sd, i), p['rimlow-%s%d' % (sd, i)], p['futtock-' + sd], 0.5, 1.0, 'futtock shrouds')
            rope('%s-tmshroud-%s%d' % (m, sd, i), p['rim-%s%d' % (sd, i)], p['tm-' + sd], 0.55, 1.0, 'topmast shrouds')
        for i in (1, 2):
            rope('%s-tgshroud-%s%d' % (m, sd, i), p['xtree-%s%d' % (sd, i)], p['tg-head'], 0.4, 1.0, 'topgallant shrouds')

S = 'stays'
rope('fore-stay', P['fore']['stay-out'], B['forestay'], 1.4, 1.0008, S)
rope('fore-topmast-stay', P['fore']['tm-stay-out'], B['cap'], 0.8, 1.0006, S)
rope('jib-stay', P['fore']['tg-head'], B['jibboom-end'], 0.55, 1.0006, S)
rope('flying-jib-stay', P['fore']['royal-stay-out'], B['flying-end'], 0.45, 1.0006, S)
rope('main-stay', P['main']['stay-out'], B['knighthead-S'], 1.5, 1.0008, S)
rope('main-preventer-stay', P['main']['stay-out'], B['knighthead-P'], 1.2, 1.0008, S)
rope('main-topmast-stay', P['main']['tm-stay-out'], P['fore']['stay-in-top'], 0.8, 1.0006, S)
rope('main-topgallant-stay', P['main']['tg-head'], P['fore']['stay-in-tm'], 0.55, 1.0006, S)
rope('main-royal-stay', P['main']['royal-stay-out'], P['fore']['stay-in-tg'], 0.45, 1.0006, S)
rope('mizzen-stay', P['mizzen']['stay-out'], P['main']['stay-in-low'], 0.9, 1.0008, S)
rope('mizzen-topmast-stay', P['mizzen']['tm-stay-out'], P['main']['stay-in-top'], 0.6, 1.0006, S)
rope('mizzen-topgallant-stay', P['mizzen']['tg-head'], P['main']['stay-in-tm'], 0.45, 1.0006, S)
rope('mizzen-royal-stay', P['mizzen']['royal-stay-out'], P['main']['stay-in-tg'], 0.4, 1.0006, S)
rope('bobstay-1', B['knee-1'], B['bobstay-1'], 1.0, 1.0, S)
rope('bobstay-2', B['knee-2'], B['bobstay-2'], 1.0, 1.0, S)

json.dump({'anchors': anchors, 'ropes': ropes}, open(os.path.join(D, 'rig_standing.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
import collections
print('anchors', len(anchors), dict(collections.Counter(a['link'] for a in anchors)))
print('ropes', len(ropes), dict(collections.Counter(r['group'] for r in ropes)))
for a in anchors:
    if a['name'] in ('shrouds-S', 'stay-out', 'tg-head', 'stay-in-low', 'mainstay-S', 'bobstay-1', 'xtree-S1', 'xtree-S2', 'rim-S1', 'futtock-S'):
        print(a['link'], a['name'], a['world'])

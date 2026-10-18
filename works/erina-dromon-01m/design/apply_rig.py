# 帆與繩（新圖紙 03 的後半）：兩面三角帆、帆腳索（sheet）、tack 繩、升降索（halyard）、側支索（每根桅每舷 2 條）、艉旗＋旗桿。
#   lateen 沒有前後支索（Pryor p.218；ref §4）⇒ 只拉側支索。帆的 meta sail=gaff（縱帆）、set=1（只有這兩面帆、收帆也要張著；槳還沒做）。
# 用法：python -I -X utf8 -B apply_rig.py [anchors|sails|ropes|meta|all]
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cli, dro

D = dro.D
step = sys.argv[1] if len(sys.argv) > 1 else 'all'
YC = dro.YC
VH = json.load(open(os.path.join(D, 'verify_hull.json'), encoding='utf-8')); ZAIR = VH['zair']
VU = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
VR = json.load(open(os.path.join(D, 'verify_rig.json'), encoding='utf-8'))
VM = {m['name']: m for m in json.load(open(os.path.join(D, 'verify_models.json'), encoding='utf-8'))}
HULL, ASM = 'erina-dromon-01m', 'erina-dromon-01m-assembly'
geo = VU['_geo']


def rot(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def ywp(nm, pt):        # 帆桁固定點的世界座標
    m = VM['yard-' + nm]
    p = np.asarray(VR['yards'][nm]['anchors'][pt], float) + 0.5
    return rot(*m['rotate']) @ (p - np.asarray(m['pivot'])) + np.asarray(m['at'])


T = {n: ywp(n, 'tack') for n in ('fore', 'main')}
PK = {n: ywp(n, 'peak') for n in ('fore', 'main')}
# 帆腳角（clew）：前帆在木塔之前、投石機頂上；中帆在中桅後面、艙口前
CLEW = {'fore': (247.5, dro.YM, 52.5), 'main': (152.5, dro.YM, 34.5)}


def gunwale(x, s):       # 舷牆頂最外那一格（側支索的下端）
    za = ZAIR[x] + dro.PLAN['hull']['bulwark']['h'] - 1
    ys = [y for y in range(dro.NY) if dro.hb(x + 0.5, za + 0.5) >= abs(y + 0.5 - dro.YM)]
    return (x, max(ys) if s > 0 else min(ys), za)


HA = {}   # 船殼上的固定點
for mast, xs in (('fore', (262, 252)), ('main', (184, 174))):
    for s, tag in ((1, 'S'), (-1, 'P')):
        for k, x in enumerate(xs, 1):
            HA['shroud-%s-%s%d' % (mast, tag, k)] = gunwale(x, s)
DA = {'halyard-fore': (264, YC, ZAIR[264] - 1), 'halyard-main': (186, YC, ZAIR[186] - 1), 'tack-main': (240, YC, ZAIR[240] - 1)}
def edge(x, z, s):       # 船殼在 (x, z) 最外那一格
    ys = [y for y in range(dro.NY) if dro.hb(x + 0.5, z + 0.5) >= abs(y + 0.5 - dro.YM)]
    return (x, max(ys) if s > 0 else min(ys), z)
HA['hawse-S'] = edge(336, 27, 1)          # 錨鏈孔（艏部兩舷、吊錨架前面）
HA['hawse-P'] = edge(336, 27, -1)
FA = {'tack-fore': (geo['forecastle'][1], YC, geo['forecastle'][2] + 4)}
FLAG = {'flagstaff-lo': (40, YC, 51), 'flagstaff-hi': (40, YC, 60)}       # 艉柱頭上面的旗桿（下面在 fittings 加一根小桿）

if step in ('anchors', 'all'):
    for k, v in HA.items():
        cli.anchor(HULL, k, v, '側支索下端：舷牆頂最外那一格（apply_rig.py）')
    for k, v in DA.items():
        cli.anchor(HULL + '-deck-main', k, v, '甲板板那一格（apply_rig.py）')
    for k, v in FA.items():
        cli.anchor(HULL + '-forecastle', k, v, '艏樓前胸牆頂（apply_rig.py）')
    print('  anchors', len(HA) + len(DA) + len(FA))

if step in ('sails', 'all'):
    for n in ('fore', 'main'):
        y = 'model:桅-%s/yard-%s' % (n, n)
        corners = '%s/tack|%s/peak|%s' % (y, y, cli.xyz(CLEW[n]))
        cli.run(['op=work', 'sub=sail', 'persona=erina', 'work=' + ASM, 'name=' + n, 'corners=' + corners, 'corner_names=tack|peak|clew',
                 'bind=0', 'free=clew', 'overwrite=1'])
    # 艉旗：深紫底（帝國紫；設計）—— 兩角釘在旗桿上、兩角放開
    cli.run(['op=work', 'sub=sail', 'persona=erina', 'work=' + ASM, 'name=ensign',
             'corners=%s|%s|%s|%s' % (cli.xyz((40.5, dro.YM, 60.5)), cli.xyz((40.5, dro.YM, 54.5)), cli.xyz((30.5, dro.YM, 54.5)), cli.xyz((30.5, dro.YM, 60.5))),
             'corner_names=hoist-hi|hoist-lo|fly-lo|fly-hi', 'bind=0', 'free=fly-lo,fly-hi', 'color=#5a1e6e', 'overwrite=1'])
    cli.run(['op=work', 'sub=wind', 'persona=erina', 'work=' + ASM, 'wind=4.5,-1.5,0', 'sail_seconds=3'])

ROPES = []    # (name, from, to, slack, thick, color, group, meta)
STAND, RUN = '#2b2620', '#a08458'
for n in ('fore', 'main'):
    y = 'model:桅-%s/yard-%s' % (n, n)
    ROPES.append(('%s-sheet' % n, 'sail:%s/clew' % n, '舵橫樑與吊架/bitt-%s-S' % ('240' if n == 'fore' else '150'), 1.0, 0.5, RUN, 'running/' + n, {'kind': 'sheet', 'sail': n}))
    ROPES.append(('%s-tack' % n, '%s/tack' % y, ('艏樓/tack-fore' if n == 'fore' else '甲板-main/tack-main'), 1.0, 0.6, RUN, 'running/' + n, {'kind': 'tack', 'sail': n}))
    ROPES.append(('%s-halyard' % n, '%s/sling' % y, '桅-%s/sheave-aft' % n, 1.0, 0.6, RUN, 'running/' + n, None))          # halyard 不標 kind（遊戲的規格表沒有 halyard；當一般繩）
    ROPES.append(('%s-halyard-fall' % n, '桅-%s/sheave-aft' % n, '甲板-main/halyard-%s' % n, 1.0, 0.6, RUN, 'running/' + n, None))
    for tag in ('S', 'P'):
        for k in (1, 2):
            ROPES.append(('%s-shroud-%s%d' % (n, tag, k), '桅-%s/head' % n, '船殼/shroud-%s-%s%d' % (n, tag, k), 1.0, 0.8, STAND, 'standing/' + n, {'kind': 'shroud'}))

if step in ('ropes', 'all'):
    for name, a, b, sl, th, col, grp, meta in ROPES:
        cli.run(['op=work', 'sub=rope', 'persona=erina', 'work=' + ASM, 'name=' + name, 'from=' + a, 'to=' + b, 'slack=%g' % sl,
                 'thickness=%g' % th, 'color=' + col, 'group=' + grp, 'overwrite=1'], quiet=True)
        print('  rope', name)

if step in ('meta', 'all'):
    lines = []
    # 帆段（Tim 2026-10-18：「目前 滿帆 戰鬥帆 收帆都是兩個帆 只有全收會一次收掉(沒有單帆狀態)」）：中桅（小、15 m 帆桁）set 1 ⇒ 收帆起就張；
    #   前桅（大、20 m 帆桁）set 3 ⇒ 只有滿帆才張 ⇒ 收帆、戰鬥帆 ＝ 只張中桅那一面（槳帆船接戰前收帆、靠槳；兩面帆分不出第四段）。
    for n in ('fore', 'main'):
        lines.append('sail\t%s\t%s' % (n, json.dumps({'kind': 'sail', 'mast': n, 'sail': 'gaff', 'set': 3 if n == 'fore' else 1, 'rig': 'lateen'}, ensure_ascii=False)))
    lines.append('sail\tensign\t%s' % json.dumps({'kind': 'flag', 'flag': 'ensign'}))
    for name, a, b, sl, th, col, grp, meta in ROPES:
        if meta:
            lines.append('rope\t%s\t%s' % (name, json.dumps(meta, ensure_ascii=False)))
        else:                                               # 沒 meta 的繩：清掉（批次檔不收 null ⇒ 一條一條 meta=none）
            cli.run(['op=work', 'sub=meta', 'persona=erina', 'work=' + ASM, 'part=rope', 'name=' + name, 'meta=none'], quiet=True)
    p = os.path.join(D, 'meta_rig.tsv')
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    cli.run(['op=work', 'sub=meta', 'persona=erina', 'work=' + ASM, 'file=' + p.replace('\\', '/')])
print(step, 'done', {n: np.round(T[n], 1).tolist() for n in T}, {n: np.round(PK[n], 1).tolist() for n in PK})

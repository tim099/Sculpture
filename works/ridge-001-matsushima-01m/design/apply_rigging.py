# 松島號的索具（2026-10-24；Tim「這根桿子沒有綁纜繩嗎 以及是否可以參考資料補上其他纜繩(缺乏松島號資料可以參考其他類似船的資料由你設計)」
#   「桅杆入口看起來開在這裡 不過沒有繩梯接到這裡」）—— 固定點、纜繩、繩梯；重跑：固定點先拿掉再登記、繩帶 overwrite、繩梯先拿掉再拉 ⇒ 結果一樣。
# 用法：python -I -X utf8 -B apply_rigging.py <gen_matsushima 輸出> [--dry]（先跑 gen_matsushima.py；apply_links.py 拉的五條靜索照舊在那邊）
# 松島號查不到索具圖 ⇒ 照同時代的鐵甲巡洋艦（軍用桅＋桅樓、桅腳的吊艇桿、單煙囪）慣例設計：
#   側支索收到下桅樓外緣底下（futtock 那樣接到桅樓邊）、繩梯從那裡進桅樓的門；吊艇桿一條起重索（到上桅樓底下）＋兩舷穩索；
#   煙囪每舷三條拉索（前、正橫、後；煙囪帶下面一圈）；頂桿兩舷各兩條側支索到上桅樓的裝甲帶、兩條後支索到船首樓後端；
#   兩根信號桁每端一條吊索（到頂桿）、一條信號旗繩（到船首樓甲板）；斜桁一條頂端吊索（到桅身、下桅樓底下）。
import sys, os, json, math, subprocess, shutil
import numpy as np
out = sys.argv[1]; DRY = '--dry' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['params']
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
S = shutil.which('senate'); W = 'ridge-001-matsushima-01m'; ASM = W + '-assembly'; PER = 'ridge-001'
WORKS = os.path.join(HERE, '..', '..')
YC = (P['frame'][1] - 1) // 2
M = P['mast']; mx = M['x']; t1, t2 = M['top1'], M['top2']
ZF = P['z_fc_deck'] + 1                                                    # 船首樓甲板的走路格（繩落在甲板面上）
TOP_DOOR_DEG = M.get('door_deg', 115)                                      # 下桅樓兩扇門的方位（gen_matsushima.py 同一個數）


def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    if DRY: print('· ' + ' '.join('%s=%s' % kv for kv in a)); return ''
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0:
        print('✗ ' + ' '.join(v for k, v in a if k in ('sub', 'work', 'name')) + '\n' + (p.stdout + p.stderr)[-900:]); sys.exit(1)
    return p.stdout


def listed(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    if not os.path.exists(f): return []
    return [x['name'] for x in json.load(open(f, encoding='utf-8')).get(key, [])]


def anchor(work, nm, at):
    if nm in listed(work, 'anchors.json', 'anchors'):
        run(('op', 'work'), ('sub', 'unanchor'), ('work', work), ('persona', PER), ('name', nm))
    run(('op', 'work'), ('sub', 'anchor'), ('work', work), ('persona', PER), ('name', nm), ('at', '%d,%d,%d' % tuple(int(round(v)) for v in at)))


def cell(part, x, y, z): return own[x, y, z] == names.index(part) + 1


def deck_spot(x, dy):
    """船首樓甲板上落繩的一點：腳下是船首樓甲板的格、上面兩格空（不壓到欄杆、梯子、艙口）；不行 ⇒ 擋下來（別讓繩落在空中）。"""
    for s in (1, -1):
        y = YC + s * dy
        assert cell('deck-fc', x, y, ZF - 1) and own[x, y, ZF] == 0 and own[x, y, ZF + 1] == 0, ('甲板上落不了繩', x, y)
    return [x, YC + dy, ZF], [x, YC - dy, ZF]


def ring(cx, cy, r, deg, z): return [cx + r * math.cos(math.radians(deg)), cy + r * math.sin(math.radians(deg)), z]


# ── 固定點 ──
A = {}                                                                       # 名字 ⇒ 繩端寫法
def add(work, link, nm, at):
    anchor(work, nm, at); A[nm] = (link + '/' if link else '') + nm


# 側支索收到下桅樓外緣底下（門的方位、外緣下面一格）⇒ 繩梯頂端接到門口
for s, sg in (('S', 1), ('P', -1)):
    add(W + '-mast', '桅', 'shroud-' + s, ring(mx, YC, M['r1'] - 0.8, sg * TOP_DOOR_DEG, t1 - 2))
# 吊艇桿：頭（起重索、穩索都綁這裡）、起重索的上端（上桅樓外緣底下、正前方）
(dx0, dz0), (dx1, dz1) = M['derrick']
add(W + '-mast', '桅', 'derrick-head', [dx1, YC, dz1])
add(W + '-mast', '桅', 'derrick-lift', [mx + M['r2'] - 0.5, YC, t2 - 2])
# 頂桿：兩舷側支索的上端（頂桿上、上桅樓之上 9.5 m）、下端（上桅樓裝甲帶頂：正橫與偏後）；斜桁吊索的下端（桅身後面、下桅樓底下）
for s, sg in (('S', 1), ('P', -1)):
    add(W + '-mast', '桅', 'pole-' + s, [mx, YC + sg * 2, t2 + 95])
    add(W + '-mast', '桅', 'band2-' + s, ring(mx, YC, M['r2'] - 0.5, sg * 90, t2 + M['band'][1]))
    add(W + '-mast', '桅', 'band2a-' + s, ring(mx, YC, M['r2'] - 0.5, sg * 135, t2 + M['band'][1]))
add(W + '-mast', '桅', 'gaff-lift', [mx - M['r'], YC, t1 - 6])
# 煙囪：帶下面一圈（每舷前 40°、正橫 90°、後 140°）
F = P['funnel']; fx, fr = F['x'], F['r']; zc = F['top'] - F['band']
for s, sg in (('S', 1), ('P', -1)):
    for k, deg in (('f', 40), ('b', 90), ('a', 140)):
        add(W + '-funnel', '煙囪', 'guy-%s-%s' % (k, s), ring(fx, YC, fr + 0.5, sg * deg, zc))
# 船首樓甲板上的落點
DK = W + '-deck-fc'
for nm, x, dy in (('derrick-guy', 575, 58), ('funnel-f', 655, 58), ('funnel-b', 625, 60), ('funnel-a', 595, 58),
                  ('backstay', 392, 56), ('halyard-up', 452, 50), ('halyard-lo', 447, 45)):
    pS, pP = deck_spot(x, dy)
    add(DK, '甲板-fc', nm + '-S', pS); add(DK, '甲板-fc', nm + '-P', pP)

# ── 纜繩 ──
WIRE, HEMP = '#2b2620', '#8a7a58'                                           # 鋼索（上焦油）、麻繩（動索）
ROPES = [  # 名字, 一端, 另一端, 組, 粗細（格）, 顏色
    ('derrick-lift', A['derrick-head'], A['derrick-lift'], 'running/derrick', 0.6, WIRE),
    ('gaff-peak-lift', '桅/gaff-peak', A['gaff-lift'], 'running/gaff', 0.5, WIRE),
]
for s in ('S', 'P'):
    ROPES += [
        ('derrick-guy-' + s, A['derrick-head'], A['derrick-guy-' + s], 'running/derrick', 0.5, HEMP),
        ('pole-shroud-' + s, A['pole-' + s], A['band2-' + s], 'standing/topmast', 0.6, WIRE),
        ('pole-shroud-a-' + s, A['pole-' + s], A['band2a-' + s], 'standing/topmast', 0.6, WIRE),
        ('backstay-' + s, '桅/pole-head', A['backstay-' + s], 'standing/stays', 0.8, WIRE),
    ]
    for k, dk in (('f', 'funnel-f'), ('b', 'funnel-b'), ('a', 'funnel-a')):
        ROPES.append(('funnel-guy-%s-%s' % (k, s), A['guy-%s-%s' % (k, s)], A['%s-%s' % (dk, s)], 'standing/funnel', 0.6, WIRE))
# 信號桁（帆桁模型、apply_links.py：at mx+5.5、中線、yz+0.5，半長 yh）：每端一條吊索到頂桿、一條旗繩到甲板
for (yz, yh), tag in zip(sorted(M['yards'], reverse=True), ('up', 'lo')):
    for s, sg in (('S', 1), ('P', -1)):
        arm = '%.1f,%.1f,%.1f' % (mx + 5.5, YC + 0.5 + sg * (yh - 1), yz + 0.5)
        ROPES.append(('yard-lift-%s-%s' % (tag, s), '%.1f,%.1f,%.1f' % (mx + 0.5, YC + 0.5 + sg * 1.5, yz + 20.5), arm, 'running/signal', 0.35, WIRE))
        ROPES.append(('halyard-%s-%s' % (tag, s), arm, A['halyard-%s-%s' % (tag, s)], 'running/signal', 0.3, HEMP))

# 繩掃過的格（直線，粗略）：除了兩端 3 格內，碰到實心就報（模型不在 own 裡 ⇒ 小艇、砲另外看預覽）
def pt(v):
    if isinstance(v, str) and '/' not in v: return [float(q) for q in v.split(',')]
    nm = v.split('/')[-1]
    for wid in (W + '-mast', W + '-funnel', DK, W):
        for a in json.load(open(os.path.join(WORKS, wid, 'anchors.json'), encoding='utf-8'))['anchors'] if os.path.exists(os.path.join(WORKS, wid, 'anchors.json')) else []:
            if a['name'] == nm: return [c + 0.5 for c in a['at']]
    raise KeyError(v)


if not DRY:
    bad = 0
    for nm, a_, b_, grp, th, col in ROPES:
        p0, p1 = np.array(pt(a_)), np.array(pt(b_)); L = np.linalg.norm(p1 - p0)
        hit = set()
        for t in np.linspace(0, 1, int(L * 2) + 2):
            q = p0 + (p1 - p0) * t
            if min(np.linalg.norm(q - p0), np.linalg.norm(q - p1)) < 3: continue
            i, j, k = (int(math.floor(c)) for c in q)
            if own[i, j, k]: hit.add(names[own[i, j, k] - 1])
        if hit: bad += 1; print('⚠ 繩 %s 穿過 %s' % (nm, sorted(hit)))
    print('穿格檢查：%d 條、%d 條有碰' % (len(ROPES), bad))

have = listed(ASM, 'ropes.json', 'ropes')
for nm, a_, b_, grp, th, col in ROPES:
    a = [('op', 'work'), ('sub', 'rope'), ('work', ASM), ('persona', PER), ('name', nm), ('from', a_), ('to', b_), ('slack', '1.0'),
         ('thickness', str(th)), ('color', col), ('group', grp)]
    if nm in have: a.append(('overwrite', '1'))
    run(*a)
print('✓ 繩 %d 條' % len(ROPES), flush=True)

# ── 繩梯：側支索的頂端改到桅樓外緣 ⇒ 重拉（head 在門裡面、桅樓地板上）──
have_rl = listed(ASM, 'ropes.json', 'ratlines')
for s, sg in (('S', 1), ('P', -1)):
    nm = 'main-lower-' + s
    if nm in have_rl: run(('op', 'work'), ('sub', 'unratlines'), ('work', ASM), ('persona', PER), ('name', nm))
    hd = ring(mx, YC, M['r1'] - 5, sg * TOP_DOOR_DEG, t1 + 1)
    run(('op', 'work'), ('sub', 'ratlines'), ('work', ASM), ('persona', PER), ('name', nm), ('rope_a', 'shroud-a-' + s), ('rope_b', 'shroud-b-' + s),
        ('step', '4'), ('start', '4'), ('min_span', '5'), ('climb', '1'), ('foot', '%d,%d,%d' % (mx + 1, YC + sg * 62, ZF)),
        ('head', '%d,%d,%d' % (round(hd[0]), round(hd[1]), hd[2])), ('color', '#2b2620'), ('thickness', '0.3'), ('group', 'ratlines/lower'))
    print('✓ 繩梯', nm, flush=True)
# 信號桁兩端寫成座標 ⇒ 繩端綁定檢查改綁成 model:桅/信號桁-…（端點不動；遊戲照它、不猜）
run(('op', 'work'), ('sub', 'ropecheck'), ('work', ASM), ('persona', PER), ('fix', '1'))
print('done')

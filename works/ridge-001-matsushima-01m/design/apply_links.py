# 組裝件的關聯（at 0,0,0）＋ meta；各子作品的固定點；砲塔層（主砲）；外部模型（舵、螺旋槳、砲、小艇、錨、舵輪、羅經櫃、火藥桶）；
#   鋼索、旭日旗、預覽 preset。重跑：已經有的關聯／模型帶 overwrite、固定點先拿掉再登記 ⇒ 結果一樣。
# 用法：python -I -X utf8 -B apply_links.py <gen_matsushima 輸出> <gen_parts 輸出> [--dry]
# 寫法照定遠號的 apply_links.py（trailhead）。
import sys, os, json, math, subprocess, shutil
import numpy as np
out, pout = sys.argv[1], sys.argv[2]; DRY = '--dry' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P, PP = PLAN['params'], PLAN['parts']
M = json.load(open(os.path.join(out, 'matsushima_meta.json'), encoding='utf-8'))
PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))
ARC = json.load(open(os.path.join(out, 'arcs.json'), encoding='utf-8'))['turret-main']
GUNS = json.load(open(os.path.join(out, 'guns.json'), encoding='utf-8'))
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
A = M['anchors']
S = shutil.which('senate'); W = 'ridge-001-matsushima-01m'; ASM = W + '-assembly'; PER = 'ridge-001'
WORKS = os.path.join(HERE, '..', '..')
YC = M['plan']['YC']; WALK = M['plan']['walk']


def run(*a, ok=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    if DRY: print('· ' + ' '.join('%s=%s' % kv for kv in a if kv[0] != 'meta')); return ''
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok:
        print('✗ ' + ' '.join(v for k, v in a if k in ('sub', 'work', 'name')) + '\n' + (p.stdout + p.stderr)[-900:]); sys.exit(1)
    return p.stdout


def listed(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    if not os.path.exists(f): return []
    return [x['name'] for x in json.load(open(f, encoding='utf-8')).get(key, [])]


KEEP = ('id', 'funnel', 'hoist', 'propeller')                             # Blockside `admin.py ids` 發的 id 與換成 id 寫法的指名鍵：重跑照留（meta= 是整份覆寫）；照 trailhead 定遠號的寫法


def kept(work, fn, key, nm, meta):
    f = os.path.join(WORKS, work, fn)
    if not os.path.exists(f): return meta
    old = [x for x in json.load(open(f, encoding='utf-8')).get(key, []) if x['name'] == nm]
    om = (old[0].get('meta') or {}) if old else {}
    keep = {k: om[k] for k in KEEP if k in om and (k == 'id' or '-' in str(om[k]).split('#')[0] and '/' not in str(om[k]))}
    return dict(meta or {}, **keep) if keep else meta


def link(work, nm, src, meta=None, at=(0, 0, 0), mirror='', turn=0):
    meta = kept(work, 'links.json', 'links', nm, meta)
    a = [('op', 'work'), ('sub', 'link'), ('work', work), ('persona', PER), ('name', nm), ('source_work', src), ('at', '%d,%d,%d' % tuple(at))]
    if turn: a.append(('turn', str(turn)))
    if mirror: a.append(('mirror', mirror))
    if meta: a.append(('meta', json.dumps(meta, ensure_ascii=False)))
    if nm in listed(work, 'links.json', 'links'): a.append(('overwrite', '1'))
    run(*a); print('✓ 關聯 %s/%s' % (work, nm), flush=True)


def anchor(work, nm, at):
    if nm in listed(work, 'anchors.json', 'anchors'):
        run(('op', 'work'), ('sub', 'unanchor'), ('work', work), ('persona', PER), ('name', nm))
    run(('op', 'work'), ('sub', 'anchor'), ('work', work), ('persona', PER), ('name', nm), ('at', '%d,%d,%d' % tuple(int(round(v)) for v in at)))


def model(work, nm, src, at, pivot, rot, sc, meta, mirror='', recolor=''):
    meta = kept(work, 'models.json', 'models', nm, meta)
    a = [('op', 'work'), ('sub', 'model'), ('work', work), ('persona', PER), ('name', nm), ('source_work', src),
         ('at', '%.2f,%.2f,%.2f' % tuple(at)), ('pivot', '%.2f,%.2f,%.2f' % tuple(pivot)), ('rotate', '%g,%g,%g' % tuple(rot)),
         ('scale', '%g,%g,%g' % ((sc,) * 3 if np.isscalar(sc) else tuple(sc))), ('meta', json.dumps(meta, ensure_ascii=False))]
    if mirror: a.append(('mirror', mirror))
    if recolor: a.append(('recolor', recolor))
    if nm in listed(work, 'models.json', 'models'): a.append(('overwrite', '1'))
    run(*a); print('✓ 模型 %s/%s' % (work, nm), flush=True)


def cells(part):
    return own == names.index(part) + 1


def deck_floor(parts, ztop):
    m = np.zeros(own.shape[:2], bool)
    for p in parts: m |= cells(p)[:, :, ztop]
    xs = np.nonzero(m.any(1))[0]
    return '%d:%d,%d:%d' % (xs.min(), ztop + 1, xs.max(), ztop + 1)


IRON = {'material': 'iron', 'render': 'smooth'}
zl, zm, zu, zf, zb = P['z_lower_deck'], P['z_middle_deck'], P['z_upper_deck'], P['z_fc_deck'], P['z_bridge']
DECKS = {
    'engine': {'kind': 'deck', 'deck': 'engine', 'level': -1, 'name': '機艙與鍋爐艙', 'floor': '%d:5,%d:5' % (P['engine_room'][0], P['boiler_room'][1]), 'thick': 2},
    'lower': {'kind': 'deck', 'deck': 'lower', 'level': 0, 'name': '防護甲板', 'floor': deck_floor(['deck-lower'], zl), 'thick': 5, 'material': 'iron*0.28', 'render': 'voxel'},   # 混合材質（厚度乘數）：格子厚約實船 4 倍（0.18 m 對 2 in）⇒ 鐵 28%；整片 iron 會重 1,703 t、全船超重 514 t
    'middle': {'kind': 'deck', 'deck': 'middle', 'level': 1, 'name': '中甲板（12 cm 砲列）', 'floor': deck_floor(['deck-middle'], zm), 'thick': 5},
    'upper': {'kind': 'deck', 'deck': 'upper', 'level': 2, 'name': '上甲板（後甲板露天）', 'floor': deck_floor(['deck-upper'], zu), 'thick': 5},
    'fc': {'kind': 'deck', 'deck': 'forecastle', 'level': 3, 'name': '船首樓甲板', 'floor': deck_floor(['deck-fc'], zf), 'thick': 5},
    'bridge': {'kind': 'deck', 'deck': 'bridge', 'level': 4, 'name': '艦橋', 'floor': deck_floor(['bridge'], zb), 'thick': 2},
    # 兩層桅樓（2026-10-24）：各自一層甲板 ⇒ 桅樓的砲自成砲甲板（送藥手照桅樓的高度站）、繩梯與桅後的梯子兩頭都在甲板上（尋路才走）
    'top-lower': {'kind': 'deck', 'deck': 'top-lower', 'level': 5, 'name': '下桅樓', 'floor': deck_floor(['top-lower'], P['mast']['top1']), 'thick': 1, 'material': 'iron*0.1'},
    'top-upper': {'kind': 'deck', 'deck': 'top-upper', 'level': 6, 'name': '上桅樓', 'floor': deck_floor(['top-upper'], P['mast']['top2']), 'thick': 1, 'material': 'iron*0.1'},
}
ENG = {'kind': 'engine', 'engine': 'direct', 'cylinders': 3, 'ihp': 2700, 'kn': 15, 'kn_max': 16.5, 'material': 'iron', 'render': 'smooth'}
BOIL = {'kind': 'boiler', 'boilers': 3, 'funnel': '煙囪', 'material': 'boiler', 'render': 'smooth'}
LINKS = [
    ('船殼', W, {'kind': 'ship', 'waterline_z': M['plan']['z_waterline'], 'material': 'iron*0.15'}, ''),   # 鋼殼：2 格外板＝0.2 m，實船外板＋肋骨約 3 cm 鐵 ⇒ 鐵 15%（外觀照鐵：金屬、平滑）
    ('甲板-engine', W + '-floor', DECKS['engine'], ''),
    ('甲板-lower', W + '-deck-lower', DECKS['lower'], ''),
    ('甲板-middle', W + '-deck-middle', DECKS['middle'], ''),
    ('甲板-upper', W + '-deck-upper', DECKS['upper'], ''),
    ('甲板-fc', W + '-deck-fc', DECKS['fc'], ''),
    ('艦橋', W + '-bridge', DECKS['bridge'], ''),
    ('上層建築', W + '-superstructure', {'material': 'iron*0.1'}, ''),   # 鋼：2 格牆（0.2 m）≈ 外板＋骨架 2 cm
    ('欄杆', W + '-rails', {'material': 'iron*0.05', 'render': 'smooth'}, ''),   # 鋼管欄杆：2 格粗才平滑得起來（方塊面不反光，Tim 2026-10-24 要金屬）；實船 5 cm 管 ⇒ 鐵 5%
    ('司令塔', W + '-conning', IRON, ''),
    ('海圖室', W + '-chart-house', None, ''),
    ('煙囪', W + '-funnel', dict(IRON, kind='funnel'), ''),
    ('鍋爐', W + '-boilers', BOIL, ''),
    ('鍋爐-鏡像', W + '-boilers', BOIL, 'y'),
    ('主機', W + '-engine', dict(ENG, propeller='螺旋槳-S'), ''),
    ('主機-鏡像', W + '-engine', dict(ENG, propeller='螺旋槳-P'), 'y'),
    ('軸', W + '-shaft', dict(IRON, kind='shaft'), ''),
    ('軸-鏡像', W + '-shaft', dict(IRON, kind='shaft'), 'y'),
    ('露砲台', W + '-barbette', IRON, ''),
    ('露砲台撐柱', W + '-barbette-posts', {'material': 'iron*0.2'}, ''),
    ('桅', W + '-mast', {'material': 'iron*0.1'}, ''),   # 軍艦桅（鋼管＋桅樓）：實心 1.2 m 管 ≈ 空心管 ⇒ 鐵 10%
    ('通風筒', W + '-vents', {'material': 'iron*0.05'}, ''),   # 實心管（空心會封成空腔）⇒ 鐵 5%
    ('艇架', W + '-skids', None, ''),
    ('彈藥庫-前', W + '-mag-fore', {'kind': 'magazine', 'pos': 'fore', 'hoist': '梯子/lm-fwd,梯子/mu-fwd,梯子/uf-fwd,梯子/bridge-S,main-lower-S,梯子/mast-top'}, ''),   # main-lower-S ＝ 繩梯（遊戲照 ratlines 組名認）⇒ 下桅樓；mast-top ⇒ 上桅樓
    ('彈藥庫-後', W + '-mag-aft', {'kind': 'magazine', 'pos': 'aft', 'hoist': '梯子/mu-aft'}, ''),   # 主砲改由揚弾筒吊（TASK-0841）⇒ 不再寫 梯子/barbette
    ('揚弾筒', W + '-hoist', dict(IRON, kind='hoist', guns='gun-27'), ''),   # 主砲（主砲塔/砲 的物件 id）；trip／rounds 照遊戲預設
    ('艙壁', W + '-bulkheads', {'material': 'iron*0.1', 'render': 'voxel'}, ''),   # 水密艙壁 1 格 ⇒ 方塊
    ('艦橋撐柱', W + '-bridge-posts', {'material': 'iron*0.1', 'render': 'smooth'}, ''),   # 鋼管撐柱 0.3 m 實心 ≈ 空心管 ⇒ 鐵 10%（2026-10-24 從艦橋拆出來、收進船首樓甲板）
    ('桅樓-下', W + '-top-lower', DECKS['top-lower'], ''),
    ('桅樓-上', W + '-top-upper', DECKS['top-upper'], ''),
    ('梯子', W + '-ladders', {'kind': 'ladders', 'material': 'iron*0.2', 'render': 'voxel'}, ''),
]
for nm, src, meta, mir in LINKS:
    link(ASM, nm, src, meta, mirror=mir)

# ── 固定點 ──
for L in A['ladders']:
    for k in ('foot', 'lo', 'hi', 'head'): anchor(W + '-ladders', L['name'] + '.' + k, L[k])
for k in ('bottom', 'top'): anchor(W + '-hoist', k, A['hoist'][k])   # 艙底接收處／砲尾接收點（轉軸上）
MAGW = {'mag-fore': W + '-mag-fore', 'mag-aft': W + '-mag-aft'}
for nm, mm in A['mags'].items():
    for k in ('blast', 'door'): anchor(MAGW[nm], k, mm[k])
anchor(W + '-funnel', 'smoke', A['funnel']['smoke'])
for k, v in A['boilers'].items(): anchor(W + '-boilers', k, v)
for k, v in A['engine'].items(): anchor(W + '-engine', k, v)
for k, v in A['shaft'].items(): anchor(W + '-shaft', k, v)
for s in ('s', 'p'):
    for k, v in A['screw-' + s].items(): anchor(W + '-screw-' + s, k, v)
anchor(W + '-rudder', 'stock-top', A['rudder']['stock-top'])
hull = cells('hull')


def side_cell(x, z, sgn):
    ys = np.nonzero(hull[x, :, z])[0]
    return [x, int(ys.max() if sgn > 0 else ys.min()), z]


an = P['anchors']
anchor(W, 'hawse-S', side_cell(an['hawse_x'], an['hawse_z'], 1)); anchor(W, 'hawse-P', side_cell(an['hawse_x'], an['hawse_z'], -1))
zs = zf + 1
ROPE_FOOT = {'chain-a-S': side_cell(422, zs, 1), 'chain-a-P': side_cell(422, zs, -1), 'chain-b-S': side_cell(458, zs, 1), 'chain-b-P': side_cell(458, zs, -1)}
xs_ = np.nonzero(hull[:, YC, zs])[0]
ROPE_FOOT['stem-head'] = [int(xs_.max()), YC, zs]
for k, v in ROPE_FOOT.items(): anchor(W, k, v)
MS = M['mast']; mx = MS['x']
anchor(W + '-mast', 'shroud-S', [mx, YC + 6, MS['top1'] - 8]); anchor(W + '-mast', 'shroud-P', [mx, YC - 6, MS['top1'] - 8])
anchor(W + '-mast', 'pole-head', [mx, YC, MS['pole_top'] - 4])
gp = MS['gaff_peak']
anchor(W + '-mast', 'gaff-peak', [int(math.floor(gp[0])) + 1, YC, int(math.floor(gp[2])) - 1])
# 通用部件的固定點
for key, wid in (('gun320', W + '-gun-canet320'), ('gun120', W + '-gun-armstrong120'), ('gun57', W + '-gun-hotchkiss57'), ('gun47', W + '-gun-hotchkiss47')):
    for k, v in PM[key]['anchors'].items(): anchor(wid, k, v)
# ── 砲塔層（主砲）──
TM = P['turret_main']; CX = PM['turret-main-shell']['geom']['CX']
G = PM['gun320']['anchors']; piv = [G['trunnion'][0] + 0.5, G['trunnion'][1] + 0.5, 0]
TW = W + '-turret-main'
link(TW, '殼', W + '-turret-main-shell', IRON, turn=90)                    # 殼的前方 +y ⇒ 轉 90° 朝 −x（船尾）
model(TW, '砲', W + '-gun-canet320', [CX + 0.5 - TM['gun_u'], CX + 0.5, 1], piv, [0, 0, 90], 0.5, {'kind': 'gun', 'gun': '320c', 'safe': 1})
anchor(TW, 'pivot', [CX, CX, 0]); anchor(TW, 'front', [0, CX, 0])
arc = [max(ARC['arc'][0], -140), min(ARC['arc'][1], 140)]                   # 史料：左右各 140°（量出來 ±142）
link(ASM, '主砲塔', TW, {'kind': 'turret', 'arc': '%d,%d' % tuple(arc), 'fire': '%d,%d' % tuple(ARC['fire']), 'rate': 4},
     at=(P['barbette']['x'] - CX, YC - CX, TM['z_table']))
# ── 外部模型 ──
R = P['rudder']; hinge = [R['x'][1] + 0.5, YC + 0.5, R['z'][0]]
model(ASM, '舵', W + '-rudder', hinge, hinge, [0, 0, 0], 1,
      {'kind': 'rudder', 'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2], 'axis_x': 0, 'axis_y': 0, 'axis_z': 1, 'max_deg': 35, 'turn_axis': 'hinge',
       'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3})
SCw = P['screw']
for s, sg in (('S', 1), ('P', -1)):
    hub = [SCw['x'] + 0.5, YC + sg * SCw['dy'] + 0.5, SCw['z'] + 0.5]
    model(ASM, '螺旋槳-' + s, W + '-screw-' + s.lower(), hub, hub, [0, 0, 0], 1,
          {'kind': 'propeller', 'axis_x': -sg, 'axis_y': 0, 'axis_z': 0, 'blades': SCw['blades'], 'diameter_m': 3.2, 'rpm_max': 105})   # 內旋（泉 下 p.48）
SRC = {'gun120': (W + '-gun-armstrong120', 0.5, '120a'), 'gun57': (W + '-gun-hotchkiss57', 0.2, 'h57'), 'gun47': (W + '-gun-hotchkiss47', 0.2, 'h47'),
       'h37': ('trailhead-dingyuan-01m-gun-hotchkiss37', 0.2, 'h37')}
DECKW = {'甲板-middle': W + '-deck-middle', '甲板-upper': W + '-deck-upper', '甲板-fc': W + '-deck-fc', '艦橋': W + '-bridge'}   # 桅樓的砲見下面 dw：以前掛在艦橋底下（桅不是甲板 ⇒ 退到機艙；掛船首樓 ⇒ 整層照桅樓高度找取用點），跟艦橋的 37 mm 共用一個高度帶 ⇒ 送藥手在兩個高度之間直線飛（Tim 2026-10-24「送藥手取彈藥會浮空」）
for lo, nm in ((0, '信號桁-下'), (1, '信號桁-上')):   # 信號桁 ＝ 帆桁模型（引用定遠號的 yard-main，縮放）：遊戲照帆桁 meta mast 找桅（10_ship.js findMasts）
    yz, yh = sorted(P['mast']['yards'])[lo]
    model(W + '-mast', nm, 'trailhead-dingyuan-01m-yard-main', [mx + 5.5, YC + 0.5, yz + 0.5], [1.5, 40.5, 1.5], [0, 0, 0], (0.67, round((2 * yh + 1) / 81, 4), 0.67),
          {'kind': 'yard', 'mast': 'main', 'yard': 'signal', 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0, 'length_ft': round((2 * yh + 1) * 0.328, 1), 'diameter_in': 8}, recolor='213:255')
for nm in [n for n in listed(W + '-mast', 'models.json', 'models') if n.startswith('機關砲-')]:   # 舊版掛在桅上的（重跑時已經沒有）
    run(('op', 'work'), ('sub', 'unmodel'), ('work', W + '-mast'), ('persona', PER), ('name', nm))
for nm, g in GUNS.items():
    if g['src'] not in SRC: continue
    src, sc, code = SRC[g['src']]
    if g['src'] == 'h37': pv = [18.5, 40.5, 0]
    else:
        a = PM[g['src']]['anchors']['pivot']; pv = [a[0] + 0.5, a[1] + 0.5, 0]
    meta = {'kind': 'gun', 'gun': code}
    if g['deck'] in ('甲板-fc', '桅', '艦橋') or nm.startswith('機關砲-艉'):
        meta.update({'mount': 'turret', 'arc': '-110,110' if g['deck'] == '桅' else '-120,120', 'rate': 40, 'safe': 1})
    dw = DECKW[g['deck']] if g['deck'] != '桅' else W + ('-top-lower' if g['at'][2] < P['mast']['top2'] else '-top-upper')   # 2026-10-24 起桅樓的砲掛在自己那層桅樓（甲板）底下；砲座（…座，ame 拆的）不在這支裡，搬家要連座一起
    model(dw, nm, src, g['at'], pv, [0, 0, g['rz']], sc, meta)
BR = M['bridge']
model(W + '-bridge', '舵輪', 'basecamp-frigate-constitution-01m-wheel', [BR['x0'] + 13.5, YC + 0.5, BR['z']], [50, 52, 0], [0, 0, 0], 0.2,
      {'kind': 'wheel', 'spin': 'rudder', 'spin_k': 540, 'spin_lag': 0.6})
model(W + '-bridge', '羅經櫃', 'basecamp-ember-01m-binnacle', [BR['x0'] + 23.5, YC + 0.5, BR['z']], [12, 23, 0], [0, 0, 0], 0.2, {'kind': 'binnacle'})
BOATM = {'basecamp-ember-01m-boat': {'kind': 'boat', 'boat': 'cutter', 'length_m': 9}, 'basecamp-frigate-constitution-01m-whaleboat': {'kind': 'boat', 'boat': 'whaleboat', 'length_m': 8.5}}
for nm, g in GUNS.items():
    if g['src'] in BOATM:
        model(W + '-skids', nm, g['src'], g['at'], g['pivot'], [0, 0, 0], g['scale'], BOATM[g['src']])
    elif g['src'] == 'basecamp-frigate-constitution-01m-anchor':
        model(ASM, nm, g['src'], g['at'], g['pivot'], [0, 0, 0], g['scale'], {'kind': 'anchor', 'anchor': 'bower'})
# 火藥桶（憲法號元件 scale 0.2、pivot 11,11,0）
BARREL = 'basecamp-frigate-constitution-01m-powder-barrel'
tot = {}
for nm, sp in M['spots'].items():
    wid = MAGW[nm]; n = 0
    for (x, y, z) in sp[:16]:
        n += 1
        model(wid, '桶-%02d' % n, BARREL, [x, y, z], [11, 11, 0], [0, 0, 0], 0.2, {'kind': 'powder', 'powder_lb': 100})
    tot[nm] = n
LN = {'mag-fore': '彈藥庫-前', 'mag-aft': '彈藥庫-後'}
for nm, n in tot.items():
    run(('op', 'work'), ('sub', 'meta'), ('work', ASM), ('persona', PER), ('part', 'link'), ('name', LN[nm]), ('meta', json.dumps({'powder_lb': n * 100})))
print('桶', tot)
# ── 鋼索（靜索：上焦油的鋼索色）──
ROPES = [
    ('shroud-a-S', '桅/shroud-S', '船殼/chain-a-S', 'standing/shrouds'), ('shroud-a-P', '桅/shroud-P', '船殼/chain-a-P', 'standing/shrouds'),
    ('shroud-b-S', '桅/shroud-S', '船殼/chain-b-S', 'standing/shrouds'), ('shroud-b-P', '桅/shroud-P', '船殼/chain-b-P', 'standing/shrouds'),
    ('forestay', '桅/pole-head', '船殼/stem-head', 'standing/stays'),
]
have = listed(ASM, 'ropes.json', 'ropes')
for nm, a_, b_, grp in ROPES:
    a = [('op', 'work'), ('sub', 'rope'), ('work', ASM), ('persona', PER), ('name', nm), ('from', a_), ('to', b_), ('slack', '1.0'), ('thickness', '0.9'), ('color', '#2b2620'), ('group', grp)]
    if nm in have: a.append(('overwrite', '1'))
    run(*a); print('✓ 繩', nm, flush=True)
# ── 繩梯（照憲法號 ratlines/lower：兩條側支索之間每 4 格一道、climb ⇒ 遊戲裡爬得上下桅樓；兩條在桅上收成一點 ⇒ 短於 0.5 m 就停）──
for s_, sg in (('S', 1), ('P', -1)):
    run(('op', 'work'), ('sub', 'ratlines'), ('work', ASM), ('persona', PER), ('name', 'main-lower-' + s_), ('rope_a', 'shroud-a-' + s_), ('rope_b', 'shroud-b-' + s_),
        ('step', '4'), ('start', '4'), ('min_span', '5'), ('climb', '1'), ('foot', '%d,%d,%d' % (mx + 1, YC + sg * 62, P['z_fc_deck'] + 1)),
        ('head', '%d,%d,%d' % (mx, YC + sg * 16, MS['top1'] + 1)), ('color', '#2b2620'), ('thickness', '0.3'), ('group', 'ratlines/lower'))
    print('✓ 繩梯 main-lower-' + s_, flush=True)
# ── 旭日旗（後桅斜桁頂；2:3，2.4 × 3.6 m）──
gx, gz = int(math.floor(gp[0])) + 1, int(math.floor(gp[2])) - 1
corners = '桅/gaff-peak|%g,%g,%g|%g,%g,%g|%g,%g,%g' % (gx - 36, YC + 0.5, gz + 0.5, gx - 36, YC + 0.5, gz - 23.5, gx + 0.5, YC + 0.5, gz - 23.5)
a = [('op', 'work'), ('sub', 'sail'), ('work', ASM), ('persona', PER), ('name', 'ensign'), ('corners', corners), ('corner_names', 'head|fly-top|fly-foot|foot'),
     ('bind', '3'), ('free', '1,2'), ('color', '#f8f8f6'), ('texture', os.path.join(pout, 'flag_rising_sun.png').replace(os.sep, '/'))]
if 'ensign' in listed(ASM, 'sails.json', 'sails'): a.append(('overwrite', '1'))
run(*a)
run(('op', 'work'), ('sub', 'meta'), ('work', ASM), ('persona', PER), ('part', 'sail'), ('name', 'ensign'), ('meta', json.dumps({'kind': 'flag', 'flag': 'ensign', 'mast': 'main'})))
run(('op', 'work'), ('sub', 'wind'), ('work', ASM), ('persona', PER), ('wind', '-4,1.5,0'))
print('✓ 旗')


# ── 預覽 preset ──
def preset(nm, note, **kw):
    run(*([('op', 'work'), ('sub', 'preset'), ('work', ASM), ('persona', PER), ('name', nm), ('note', note)] + list(kw.items())))


preset('藏船殼看裡面', '拿掉外板：看甲板、砲列、機艙、鍋爐、彈藥庫、梯子', hide_links='船殼')
preset('只看動力', '鍋爐、煙囪、主機、軸', links='鍋爐,鍋爐-鏡像,煙囪,主機,主機-鏡像,軸,軸-鏡像', hide_links='self')
preset('只看主砲', '露砲台、主砲塔、後甲板', links='露砲台,露砲台撐柱,主砲塔,甲板-upper', hide_links='self')
preset('只看砲列', '中甲板與 12 cm 砲列', links='甲板-middle', hide_links='self')
print('done')

# 組裝件的關聯（at 0,0,0）＋ meta；各子作品的固定點；砲塔層（主砲塔兩座、15 cm 兩座）；外部模型（舵、螺旋槳、砲、小艇、魚雷艇、錨、舵輪、羅經櫃、絞盤、火藥桶）；
#   鋼索、黃龍旗、預覽 preset。重跑：已經有的關聯／模型帶 overwrite、固定點先拿掉再登記 ⇒ 結果一樣。
# 用法：python -I -X utf8 -B apply_links.py <gen_dingyuan 輸出> <gen_parts 輸出> [--dry]
import sys, os, json, math, subprocess, shutil
import numpy as np
out, pout = sys.argv[1], sys.argv[2]; DRY = '--dry' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
P, PP = PLAN['params'], PLAN['parts']
M = json.load(open(os.path.join(out, 'dingyuan_meta.json'), encoding='utf-8'))
PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))
ARC = json.load(open(os.path.join(out, 'arcs.json'), encoding='utf-8'))
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
A = M['anchors']
S = shutil.which('senate'); W = 'trailhead-dingyuan-01m'; ASM = W + '-assembly'; PER = 'trailhead'
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


KEEP = ('id', 'funnel', 'hoist', 'propeller')                             # Blockside `admin.py ids` 發的 id 與換成 id 寫法的指名鍵：重跑照留（meta= 是整份覆寫）


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
    run(*a); print('✓ 關聯 %s/%s' % (work, nm))


def anchor(work, nm, at):
    if nm in listed(work, 'anchors.json', 'anchors'):
        run(('op', 'work'), ('sub', 'unanchor'), ('work', work), ('persona', PER), ('name', nm))
    run(('op', 'work'), ('sub', 'anchor'), ('work', work), ('persona', PER), ('name', nm), ('at', '%d,%d,%d' % tuple(int(round(v)) for v in at)))


def model(work, nm, src, at, pivot, rot, sc, meta, mirror=''):
    meta = kept(work, 'models.json', 'models', nm, meta)
    a = [('op', 'work'), ('sub', 'model'), ('work', work), ('persona', PER), ('name', nm), ('source_work', src),
         ('at', '%.2f,%.2f,%.2f' % tuple(at)), ('pivot', '%.2f,%.2f,%.2f' % tuple(pivot)), ('rotate', '%g,%g,%g' % tuple(rot)),
         ('scale', '%g,%g,%g' % ((sc,) * 3 if np.isscalar(sc) else tuple(sc))), ('meta', json.dumps(meta, ensure_ascii=False))]
    if mirror: a.append(('mirror', mirror))
    if nm in listed(work, 'models.json', 'models'): a.append(('overwrite', '1'))
    run(*a); print('✓ 模型 %s/%s' % (work, nm))


def cells(part):
    return own == names.index(part) + 1


def deck_floor(parts, ztop):
    m = np.zeros(own.shape[:2], bool)
    for p in parts: m |= cells(p)[:, :, ztop]
    xs = np.nonzero(m.any(1))[0]
    return '%d:%d,%d:%d' % (xs.min(), ztop + 1, xs.max(), ztop + 1)


IRON = {'material': 'iron', 'render': 'smooth'}
zl, zm, zu, zh = P['z_lower_deck'], P['z_main_deck'], P['z_upper_deck'], P['z_hurricane']
DECKS = {
    'lower': {'kind': 'deck', 'deck': 'lower', 'level': 0, 'name': '下甲板（城堡上是裝甲甲板）', 'floor': deck_floor(['deck-lower', 'armour-deck'], zl), 'thick': 4},
    'main': {'kind': 'deck', 'deck': 'main', 'level': 1, 'name': '主甲板（舯部露天、兩座露砲台）', 'floor': deck_floor(['deck-main'], zm), 'thick': 5},
    'barbette': {'kind': 'deck', 'deck': 'barbette', 'level': 2, 'name': '露砲台（兩座砲塔的轉盤）',
                 'floor': '%d:%d,%d:%d' % (min(b['x'] for b in P['barbettes']) - P['turret_main']['r_table'], P['turret_main']['z_table'],
                                           max(b['x'] for b in P['barbettes']) + P['turret_main']['r_table'], P['turret_main']['z_table']), 'thick': 1},
    'poop': {'kind': 'deck', 'deck': 'poop', 'level': 3, 'name': '艉樓甲板', 'floor': deck_floor(['deck-poop'], zu), 'thick': 5},
    'fc': {'kind': 'deck', 'deck': 'forecastle', 'level': 4, 'name': '艏樓甲板', 'floor': deck_floor(['deck-fc'], zu), 'thick': 5},
    'hurricane': {'kind': 'deck', 'deck': 'hurricane', 'level': 5, 'name': '飛橋甲板', 'floor': deck_floor(['deck-hurricane'], zh), 'thick': 2},
}
E = P['engine']
ENG = {'kind': 'engine', 'engine': 'direct', 'cylinders': 3, 'ihp': 3000, 'kn': 14.5, 'kn_max': 15.4, 'material': 'iron', 'render': 'smooth'}
LINKS = [
    ('船殼', W, {'kind': 'ship', 'waterline_z': M['plan']['z_waterline'], 'material': 'iron', 'render': 'smooth'}, ''),
    ('裝甲帶', W + '-belt', IRON, ''),
    ('露砲台', W + '-barbettes', IRON, ''),
    ('露砲台平台', W + '-barbette-platforms', dict(DECKS['barbette'], material='iron', render='voxel'), ''),   # 露砲台頂 ＝ 一層甲板：兩座主砲歸這一層（⛔ 歸主甲板 ⇒ 主甲板的站位高度照砲算成 z 97–110，木工台、帆布櫃被擺到露砲台中間的小平台上掉下去）
    ('裝甲甲板', W + '-armour-deck', {'material': 'iron', 'render': 'voxel'}, ''),
    ('甲板-lower', W + '-deck-lower', DECKS['lower'], ''),
    ('甲板-main', W + '-deck-main', DECKS['main'], ''),
    ('甲板-poop', W + '-deck-poop', DECKS['poop'], ''),
    ('甲板-fc', W + '-deck-fc', DECKS['fc'], ''),
    ('甲板-hurricane', W + '-deck-hurricane', DECKS['hurricane'], ''),
    ('機艙地板', W + '-floor', None, ''),
    ('上層建築', W + '-superstructure', None, ''),
    ('欄杆', W + '-rails', None, ''),
    ('司令塔', W + '-conning', IRON, ''),
    ('海圖室', W + '-chart-house', None, ''),
    ('煙囪-後', W + '-funnel-aft', dict(IRON, kind='funnel'), ''),
    ('煙囪-前', W + '-funnel-fwd', dict(IRON, kind='funnel'), ''),
    ('鍋爐-後', W + '-boilers-aft', {'kind': 'boiler', 'boilers': 2, 'funnel': '煙囪-後', 'material': 'boiler', 'render': 'smooth'}, ''),
    ('鍋爐-後-鏡像', W + '-boilers-aft', {'kind': 'boiler', 'boilers': 2, 'funnel': '煙囪-後', 'material': 'boiler', 'render': 'smooth'}, 'y'),
    ('鍋爐-前', W + '-boilers-fwd', {'kind': 'boiler', 'boilers': 2, 'funnel': '煙囪-前', 'material': 'boiler', 'render': 'smooth'}, ''),
    ('鍋爐-前-鏡像', W + '-boilers-fwd', {'kind': 'boiler', 'boilers': 2, 'funnel': '煙囪-前', 'material': 'boiler', 'render': 'smooth'}, 'y'),
    ('主機', W + '-engine', dict(ENG, propeller='螺旋槳-S'), ''),
    ('主機-鏡像', W + '-engine', dict(ENG, propeller='螺旋槳-P'), 'y'),
    ('軸', W + '-shaft', dict(IRON, kind='shaft'), ''),
    ('軸-鏡像', W + '-shaft', dict(IRON, kind='shaft'), 'y'),
    ('主桅', W + '-mast-main', None, ''),
    ('前桅', W + '-mast-fore', None, ''),
    ('通風筒', W + '-vents', None, ''),
    ('艇架', W + '-skids', None, ''),
    ('彈藥庫-前左', W + '-mag-fore-p', {'kind': 'magazine', 'pos': 'fore', 'hoist': '梯子/barbette-P'}, ''),
    ('彈藥庫-前右', W + '-mag-fore-s', {'kind': 'magazine', 'pos': 'fore', 'hoist': '梯子/barbette-S,梯子/turret15-fwd'}, ''),
    ('彈藥庫-後', W + '-mag-aft', {'kind': 'magazine', 'pos': 'aft', 'hoist': '梯子/turret15-aft'}, ''),
    ('艙壁', W + '-bulkheads', None, ''),
    ('梯子', W + '-ladders', {'kind': 'ladders', 'poop-break-P.decks': 'main,poop', 'poop-break-S.decks': 'main,poop', 'fc-break-a.decks': 'main,forecastle', 'fc-break-b.decks': 'main,forecastle'}, ''),
]
for old in ('甲板-engine',):                                               # 改過名、拿掉的關聯（機艙地板 2026-10-21 不當甲板：沒有砲的層也會被要求火藥取用點）
    if old in listed(ASM, 'links.json', 'links'):
        run(('op', 'work'), ('sub', 'unlink'), ('work', ASM), ('persona', PER), ('name', old)); print('✓ 拿掉關聯', old)
for nm, src, meta, mir in LINKS:
    link(ASM, nm, src, meta, mirror=mir)

# ── 固定點 ──
for L in A['ladders']:
    for k in ('foot', 'lo', 'hi', 'head'): anchor(W + '-ladders', L['name'] + '.' + k, L[k])
MAGW = {'mag-fore-P': W + '-mag-fore-p', 'mag-fore-S': W + '-mag-fore-s', 'mag-aft': W + '-mag-aft'}
for nm, mm in A['mags'].items():
    for k in ('blast', 'door'): anchor(MAGW[nm], k, mm[k])
for f in ('aft', 'fwd'):
    anchor(W + '-funnel-' + f, 'smoke', A['funnel-' + f]['smoke'])
    for k, v in A['boilers-' + f].items(): anchor(W + '-boilers-' + f, k, v)
for k, v in A['engine'].items(): anchor(W + '-engine', k, v)
for k, v in A['shaft'].items(): anchor(W + '-shaft', k, v)
for s in ('s', 'p'):
    for k, v in A['screw-' + s].items(): anchor(W + '-screw-' + s, k, v)
anchor(W + '-rudder', 'stock-top', A['rudder']['stock-top'])
# 船殼：錨鏈孔、桅的鋼索腳（舷牆頂最外那一格）、艏柱頭
hull = cells('hull')


def side_cell(x, z, sgn):
    ys = np.nonzero(hull[x, :, z])[0]
    return [x, int(ys.max() if sgn > 0 else ys.min()), z]


ax_ = P['anchors']; hz = P['anchors']['hawse_z']
anchor(W, 'hawse-S', side_cell(ax_['hawse_x'], hz, 1)); anchor(W, 'hawse-P', side_cell(ax_['hawse_x'], hz, -1))
ROPE_FOOT = {'chain-main-S': side_cell(214, zu + 1, 1), 'chain-main-P': side_cell(214, zu + 1, -1),
             'backstay-S': side_cell(150, zu + 1, 1), 'backstay-P': side_cell(150, zu + 1, -1),
             'chain-fore-S': side_cell(712, zu + 1, 1), 'chain-fore-P': side_cell(712, zu + 1, -1)}
zs = zu + 1; xs_ = np.nonzero(hull[:, YC, zs])[0]
ROPE_FOOT['stem-head'] = [int(xs_.max()), YC, zs]
for k, v in ROPE_FOOT.items(): anchor(W, k, v)
MS = M['masts']
for mn, wid in (('main', W + '-mast-main'), ('fore', W + '-mast-fore')):
    mx = MS[mn]['x']; tz = MS[mn]['top']
    anchor(wid, 'shroud-S', [mx, YC + 5, tz - 8]); anchor(wid, 'shroud-P', [mx, YC - 5, tz - 8])
    anchor(wid, 'pole-head', [mx, YC, MS[mn]['pole_top'] - 4])
gp = MS['gaff_peak']
anchor(W + '-mast-main', 'gaff-peak', [int(math.floor(gp[0])) + 1, YC, int(math.floor(gp[2])) - 1])

# 通用部件的固定點（砲：muzzle 內膛那一格、breech、trunnion；37 mm：pivot ＝ 立柱中心）
for key, wid in (('gun305', W + '-gun-krupp305'), ('gun150', W + '-gun-krupp150'), ('gun37', W + '-gun-hotchkiss37')):
    for k, v in PM[key]['anchors'].items(): anchor(wid, k, v)
# ── 砲塔層 ──
TMG = PM['turret-main-shell']['geom']; CXM = TMG['CX']
G305 = PM['gun305']['anchors']; piv305 = [G305['trunnion'][0] + 0.5, G305['trunnion'][1] + 0.5, 0]
TM = P['turret_main']
for b in P['barbettes']:
    side = b['name']; wid = W + '-turret-' + side.lower(); sg = 1 if b['dy'] > 0 else -1
    link(wid, '殼', W + '-turret-main-shell', {'material': 'iron', 'render': 'voxel'}, turn=0 if sg > 0 else 180)
    for gn, lat in (('砲-a', -TM['gun_dx']), ('砲-b', TM['gun_dx'])):
        at = [CXM + 0.5 + sg * lat, CXM + 0.5 + sg * TM['gun_fwd'], 1]
        model(wid, gn, W + '-gun-krupp305', at, piv305, [0, 0, 0 if sg > 0 else 180], 0.5, {'kind': 'gun', 'gun': '305k', 'safe': 1})
    anchor(wid, 'pivot', [CXM, CXM, 0]); anchor(wid, 'front', [CXM, CXM + sg * CXM, 0])
    ar = ARC['turret-' + side]
    link(ASM, '砲塔-' + side, wid, {'kind': 'turret', 'arc': '%d,%d' % tuple(ar['arc']), 'fire': '%d,%d' % tuple(ar['fire']), 'rate': 10},
         at=(b['x'] - CXM, YC + b['dy'] - CXM, TM['z_table']))
T15 = P['turret_15']; T15G = PM['turret15-shell']['geom']; CX15 = T15G['CX']
G150 = PM['gun150']['anchors']; piv150 = [G150['trunnion'][0] + 0.5, G150['trunnion'][1] + 0.5, 0]
for t in P['turrets_15']:
    wid = W + '-turret15-' + t['name']; f = t['front']
    link(wid, '殼', W + '-turret15-shell', {'material': 'iron', 'render': 'voxel'}, turn=270 if f > 0 else 90)
    model(wid, '砲', W + '-gun-krupp150', [CX15 + 0.5 + f * T15['gun_fwd'], CX15 + 0.5, 0], piv150, [0, 0, -90 if f > 0 else 90], 0.5, {'kind': 'gun', 'gun': '150k', 'safe': 1})
    anchor(wid, 'pivot', [CX15, CX15, 0]); anchor(wid, 'front', [CX15 + f * CX15, CX15, 0])
    ar = ARC['turret15-' + t['name']]
    link(ASM, '砲塔-' + ('艉' if f < 0 else '艏'), wid, {'kind': 'turret', 'arc': '%d,%d' % tuple(ar['arc']), 'fire': '%d,%d' % tuple(ar['fire']), 'rate': 15},
         at=(t['x'] - CX15, YC - CX15, T15['z0']))

# ── 外部模型 ──
R = P['rudder']; hinge = [R['x'][1], YC + 0.5, R['z'][0]]
model(ASM, '舵', W + '-rudder', hinge, hinge, [0, 0, 0], 1,
      {'kind': 'rudder', 'hinge_x': hinge[0], 'hinge_y': hinge[1], 'hinge_z': hinge[2], 'axis_x': 0, 'axis_y': 0, 'axis_z': 1, 'max_deg': 35, 'turn_axis': 'hinge',
       'spin': 'rudder', 'spin_k': 35, 'spin_min': -35, 'spin_max': 35, 'spin_lag': 0.3})
SC = P['screw']
for s, sg in (('S', 1), ('P', -1)):
    hub = [SC['x'] + 0.5, YC + sg * SC['dy'] + 0.5, SC['z'] + 0.5]
    model(ASM, '螺旋槳-' + s, W + '-screw-' + s.lower(), hub, hub, [0, 0, 0], 1, {'kind': 'propeller', 'axis_x': sg, 'axis_y': 0, 'axis_z': 0, 'blades': SC['blades'], 'diameter_m': 3.0})
ch = M['chart']
model(W + '-chart-house', '舵輪', 'basecamp-frigate-constitution-01m-wheel', [ch['x0'] + 10.5, YC + 0.5, ch['z']], [50, 52, 0], [0, 0, 0], 0.2,
      {'kind': 'wheel', 'spin': 'rudder', 'spin_k': 540, 'spin_lag': 0.6})
model(W + '-chart-house', '羅經櫃', 'basecamp-ember-01m-binnacle', [ch['x0'] + 22.5, YC + 0.5, ch['z']], [12, 23, 0], [0, 0, 0], 0.2, {'kind': 'binnacle'})
# 錨：吊在船頭兩舷錨鏈孔下（錨幹直、橫桿沿船長、靠船殼那一隻爪貼著外板）
for s, sg in (('S', 1), ('P', -1)):
    hc = side_cell(ax_['hawse_x'] - 12, 92, sg)
    sc_ = 0.6
    at = [hc[0] + 0.5, hc[1] + 0.5 + sg * (14 * sc_ + 1.5), 108]
    model(ASM, '錨-' + s, 'basecamp-frigate-constitution-01m-anchor', at, [23.5, 16.5, 56.5], [0, 0, 0], sc_, {'kind': 'anchor', 'anchor': 'bower'})
# 魚雷艇（艇架上）、小艇（艉樓艇架上、艏樓甲板上）
tb = P['torpedo_boats']; tbl = PP['torpedo_boat']['len']
for s, sg in (('S', 1), ('P', -1)):
    model(W + '-skids', '魚雷艇-' + s, W + '-boat-torpedo', [tb['x'] + tbl / 2 + 0.5, YC + sg * tb['dy'] + 0.5, tb['z']], [tbl / 2 + 1.0, PP['torpedo_boat']['half'] + 1.5, 0], [0, 0, 0], 1,
          {'kind': 'boat', 'boat': 'torpedo', 'length_m': 18.5})
sb, fb = P['stern_boats'], P['fwd_boats']
BOAT = 'basecamp-ember-01m-boat'
for s, sg in (('S', 1), ('P', -1)):
    model(W + '-skids', '小艇-艉' + s, BOAT, [sb['x'] + 55.5, YC + sg * sb['dy'] + 0.5, sb['z']], [90, 26, 0], [0, 0, 0], 0.5, {'kind': 'boat', 'boat': 'cutter', 'length_m': 9})
    model(W + '-deck-fc', '小艇-艏' + s, BOAT, [fb['x'] + 40.5, YC + sg * fb['dy'] + 0.5, zu + 1], [90, 26, 0], [0, 0, 0], 0.5, {'kind': 'boat', 'boat': 'cutter', 'length_m': 9})
# 37 mm 轉膛砲：飛橋甲板四角四門、艉樓兩舷兩門（往舷外）。⛔ 桅樓不放：桅樓不是甲板 ⇒ 遊戲把那幾門歸到最底下一層、那一層就要火藥取用點（匯入檢查 ✗）
G37 = PM['gun37']['anchors']; piv37 = [G37['pivot'][0] + 0.5, G37['pivot'][1] + 0.5, 0]
A37 = {'kind': 'gun', 'gun': 'h37', 'mount': 'turret', 'arc': '-120,120', 'rate': 40, 'safe': 1}
for mn, wid in (('main', W + '-mast-main'), ('fore', W + '-mast-fore')):
    for s in ('S', 'P'):
        if '機關砲-' + s in listed(wid, 'models.json', 'models'):
            run(('op', 'work'), ('sub', 'unmodel'), ('work', wid), ('persona', PER), ('name', '機關砲-' + s)); print('✓ 拿掉 %s/機關砲-%s' % (wid, s))
hd = P['hurricane']
for s in ('S', 'P'):                                                      # 飛橋甲板後角不放（2026-10-21 試過）：艉樓沒有別的砲 ⇒ 艉 15 cm 砲那一層生不出送藥手（匯入檢查 ✗）；艉樓這兩門的送藥手撐著那一層
    if '機關砲-後' + s in listed(W + '-deck-hurricane', 'models.json', 'models'):
        run(('op', 'work'), ('sub', 'unmodel'), ('work', W + '-deck-hurricane'), ('persona', PER), ('name', '機關砲-後' + s)); print('✓ 拿掉 飛橋/機關砲-後' + s)
CM = P['casemates37']
for s, sg in (('S', 1), ('P', -1)):
    model(W + '-deck-hurricane', '機關砲-' + s, W + '-gun-hotchkiss37', [hd['x'][1] - 14.5, YC + 0.5 + sg * (hd['half'] - 8), zh + 1], piv37, [0, 0, 0 if sg > 0 else 180], 0.2, A37)
    model(W + '-deck-poop', '機關砲-' + s, W + '-gun-hotchkiss37', [196.5, YC + 0.5 + sg * 70, zu + 1], piv37, [0, 0, 0 if sg > 0 else 180], 0.2, A37)
    for k, cxx in enumerate(CM['x']):                                        # 舷牆砲眼（casemate）：只轉得了 ±20°
        model(W + '-deck-main', '機關砲-%s%d' % (s, k + 1), W + '-gun-hotchkiss37', [cxx + 0.5, YC + 0.5 + sg * CM['dy'], zm + 1], piv37, [0, 0, 0 if sg > 0 else 180], 0.2,
              dict(A37, arc='-20,20'))
# 火藥桶（憲法號元件 scale 0.2、pivot 11,11,0）
BARREL = 'basecamp-frigate-constitution-01m-powder-barrel'
tot = {}
for nm, sp in M['spots'].items():
    wid = MAGW[nm]; n = 0
    for (x, y, z) in sp[:16]:
        n += 1
        model(wid, '桶-%02d' % n, BARREL, [x, y, z], [11, 11, 0], [0, 0, 0], 0.2, {'kind': 'powder', 'powder_lb': 100})
    tot[nm] = n
LN = {'mag-fore-P': '彈藥庫-前左', 'mag-fore-S': '彈藥庫-前右', 'mag-aft': '彈藥庫-後'}
for nm, n in tot.items():
    run(('op', 'work'), ('sub', 'meta'), ('work', ASM), ('persona', PER), ('part', 'link'), ('name', LN[nm]), ('meta', json.dumps({'powder_lb': n * 100})))
print('桶', tot)

# ── 鋼索（靜索：上焦油的鋼索色）──
ROPES = [
    ('main-shroud-S', '主桅/shroud-S', '船殼/chain-main-S', 'standing/shrouds'), ('main-shroud-P', '主桅/shroud-P', '船殼/chain-main-P', 'standing/shrouds'),
    ('main-backstay-S', '主桅/pole-head', '船殼/backstay-S', 'standing/stays'), ('main-backstay-P', '主桅/pole-head', '船殼/backstay-P', 'standing/stays'),
    ('fore-shroud-S', '前桅/shroud-S', '船殼/chain-fore-S', 'standing/shrouds'), ('fore-shroud-P', '前桅/shroud-P', '船殼/chain-fore-P', 'standing/shrouds'),
    ('forestay', '前桅/pole-head', '船殼/stem-head', 'standing/stays'), ('triatic', '主桅/pole-head', '前桅/pole-head', 'standing/stays'),
]
have = listed(ASM, 'ropes.json', 'ropes')
for nm, a_, b_, grp in ROPES:
    a = [('op', 'work'), ('sub', 'rope'), ('work', ASM), ('persona', PER), ('name', nm), ('from', a_), ('to', b_), ('slack', '1.0'), ('thickness', '0.9'), ('color', '#2b2620'), ('group', grp)]
    if nm in have: a.append(('overwrite', '1'))
    run(*a); print('✓ 繩', nm)
# ── 黃龍旗（主桅斜桁頂；1889 年起的長方形，3 × 4.5 m）──
gx, gz = int(math.floor(gp[0])) + 1, int(math.floor(gp[2])) - 1
corners = '主桅/gaff-peak|%g,%g,%g|%g,%g,%g|%g,%g,%g' % (gx - 45, YC + 0.5, gz + 0.5, gx - 45, YC + 0.5, gz - 29.5, gx + 0.5, YC + 0.5, gz - 29.5)
a = [('op', 'work'), ('sub', 'sail'), ('work', ASM), ('persona', PER), ('name', 'ensign'), ('corners', corners), ('corner_names', 'head|fly-top|fly-foot|foot'),
     ('bind', '3'), ('free', '1,2'), ('color', '#f2d22a'), ('texture', os.path.join(pout, 'flag_dragon.png').replace(os.sep, '/'))]
if 'ensign' in listed(ASM, 'sails.json', 'sails'): a.append(('overwrite', '1'))
run(*a)
run(('op', 'work'), ('sub', 'meta'), ('work', ASM), ('persona', PER), ('part', 'sail'), ('name', 'ensign'), ('meta', json.dumps({'kind': 'flag', 'flag': 'ensign', 'mast': 'main'})))
run(('op', 'work'), ('sub', 'wind'), ('work', ASM), ('persona', PER), ('wind', '-4,1.5,0'))
print('✓ 旗')
# ── 預覽 preset ──
def preset(nm, note, **kw):
    run(*([('op', 'work'), ('sub', 'preset'), ('work', ASM), ('persona', PER), ('name', nm), ('note', note)] + list(kw.items())))
preset('藏船殼看裡面', '拿掉外板與裝甲帶：看甲板、機艙、鍋爐、彈藥庫、梯子', hide_links='船殼,裝甲帶')
preset('只看動力', '鍋爐、煙囪、主機、軸', links='鍋爐-後,鍋爐-後-鏡像,鍋爐-前,鍋爐-前-鏡像,煙囪-後,煙囪-前,主機,主機-鏡像,軸,軸-鏡像', hide_links='self')
preset('只看主砲', '兩座露砲台、砲塔、飛橋甲板', links='露砲台,露砲台平台,砲塔-S,砲塔-P,甲板-main', hide_links='self')
print('done')

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
    if 'render' in om and 'render' not in (meta or {}): keep['render'] = om['render']      # 別人加的渲染方式照留（ame 2026-10-21：火藥桶 render=lathe）
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


def model(work, nm, src, at, pivot, rot, sc, meta, mirror='', note=''):
    meta = kept(work, 'models.json', 'models', nm, meta)
    a = [('op', 'work'), ('sub', 'model'), ('work', work), ('persona', PER), ('name', nm), ('source_work', src),
         ('at', '%.2f,%.2f,%.2f' % tuple(at)), ('pivot', '%.2f,%.2f,%.2f' % tuple(pivot)), ('rotate', '%g,%g,%g' % tuple(rot)),
         ('scale', '%g,%g,%g' % ((sc,) * 3 if np.isscalar(sc) else tuple(sc))), ('meta', json.dumps(meta, ensure_ascii=False))]
    if mirror: a.append(('mirror', mirror))
    if note: a.append(('note', note))
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
    ('船殼', W, {'kind': 'ship', 'waterline_z': M['plan']['z_waterline'], 'material': 'iron_hull', 'render': 'smooth'}, ''),   # iron_hull：鐵外板＋肋骨內襯的混合層（全鐵 ⇒ 9,215 t）
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
    ('海圖室', W + '-chart-house', {'material': 'iron_plate', 'render': 'smooth'}, ''),   # 鐵（薄鋼板，遊戲 matMap iron*0.125）＋平滑（Tim 2026-10-21「海圖室改成鐵的吧」）；牆 2 格厚
    ('煙囪-後', W + '-funnel-aft', dict(IRON, kind='funnel'), ''),
    ('煙囪-前', W + '-funnel-fwd', dict(IRON, kind='funnel'), ''),
    ('軸', W + '-shaft', dict(IRON, kind='shaft'), ''),
    ('軸-鏡像', W + '-shaft', dict(IRON, kind='shaft'), 'y'),
    ('主桅', W + '-mast-main', None, ''),
    ('前桅', W + '-mast-fore', None, ''),
    ('通風筒', W + '-vents', None, ''),
    ('艇架', W + '-skids', None, ''),
    ('彈藥庫-前左', W + '-mag-fore-p', {'kind': 'magazine', 'pos': 'fore', 'hoist': '梯子/barbette-P'}, ''),
    ('彈藥庫-前右', W + '-mag-fore-s', {'kind': 'magazine', 'pos': 'fore', 'hoist': '梯子/barbette-S'}, ''),   # 艏 15 cm 改由揚弾機吊（2026-10-23）⇒ 不再從 turret15-fwd 艙口吊
    ('彈藥庫-後', W + '-mag-aft', {'kind': 'magazine', 'pos': 'aft'}, ''),   # 艉 15 cm 改由揚弾機吊（2026-10-23）⇒ 不再從 turret15-aft 艙口吊；艉樓的 37 mm 照一般的取用點
    ('揚弾筒-艉', W + '-hoist-aft', {'kind': 'hoist', 'guns': 'gun-13', 'material': 'iron', 'render': 'smooth'}, ''),   # 造船規格 §9.15；gun-13 ＝ 砲塔-艉/砲
    ('揚弾筒-艏', W + '-hoist-fwd', {'kind': 'hoist', 'guns': 'gun-14', 'material': 'iron', 'render': 'smooth'}, ''),   # gun-14 ＝ 砲塔-艏/砲
    ('艙壁', W + '-bulkheads', None, ''),
    ('梯子', W + '-ladders', {'kind': 'ladders', 'poop-break-P.decks': 'main,poop', 'poop-break-S.decks': 'main,poop', 'fc-break-a.decks': 'main,forecastle', 'fc-break-b.decks': 'main,forecastle'}, ''),
]
for old in ('甲板-engine',):                                               # 改過名、拿掉的關聯（機艙地板 2026-10-21 不當甲板：沒有砲的層也會被要求火藥取用點）
    if old in listed(ASM, 'links.json', 'links'):
        run(('op', 'work'), ('sub', 'unlink'), ('work', ASM), ('persona', PER), ('name', old)); print('✓ 拿掉關聯', old)
for nm, src, meta, mir in LINKS:
    link(ASM, nm, src, meta, mirror=mir)
# 鍋爐、主機：自帶格子的外部模型（TASK-0793，ame 2026-10-21：關聯換成模型 ⇒ 可換零件的掛點）—— 跟 ame 那一次同一個擺法：整船的框、at＝pivot；鏡像那一份繞 y 110.5 翻
DRV = [('鍋爐-後', W + '-boilers-aft', {'kind': 'boiler', 'boilers': 2, 'funnel': '煙囪-後', 'material': 'boiler', 'render': 'smooth'}),
       ('鍋爐-前', W + '-boilers-fwd', {'kind': 'boiler', 'boilers': 2, 'funnel': '煙囪-前', 'material': 'boiler', 'render': 'smooth'}),
       ('主機', W + '-engine', dict(ENG, propeller='螺旋槳-S'))]
for nm, src, meta in DRV:
    for suf, mir in (('', ''), ('-鏡像', 'y')):
        if nm + suf in listed(ASM, 'links.json', 'links'):
            run(('op', 'work'), ('sub', 'unlink'), ('work', ASM), ('persona', PER), ('name', nm + suf)); print('✓ 拿掉關聯（換成模型）', nm + suf)
        m_ = dict(meta, propeller='螺旋槳-P') if nm == '主機' and mir else meta
        p_ = [0, YC + 0.5, 0] if mir else [0, 0, 0]
        model(ASM, nm + suf, src, p_, p_, [0, 0, 0], 1, m_, mirror=mir, note='TASK-0793：關聯換成自帶格子的模型（ame 2026-10-21）')

# ── 固定點 ──
for L in A['ladders']:
    for k in ('foot', 'lo', 'hi', 'head'): anchor(W + '-ladders', L['name'] + '.' + k, L[k])
for H in A['hoists']:
    for k in ('bottom', 'top'): anchor(W + '-hoist-' + H['name'], k, H[k])
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
# 側支索（2026-10-21：每根桅每舷三根，上端在桅樓邊下面、下端在舷牆頂；前後兩根之間是繩梯）：S1 最前
CHAIN = {'main': 214, 'fore': 712}; SHR_DX = (10, 0, -10); RIM_DX = (6, 0, -6)
ROPE_FOOT = {'backstay-S': side_cell(150, zu + 1, 1), 'backstay-P': side_cell(150, zu + 1, -1)}
for mn, cx_ in CHAIN.items():
    for s, sg in (('S', 1), ('P', -1)):
        for k, dx in enumerate(SHR_DX): ROPE_FOOT['chain-%s-%s%d' % (mn, s, k + 1)] = side_cell(cx_ + dx, zu + 1, sg)
zs = zu + 1; xs_ = np.nonzero(hull[:, YC, zs])[0]
ROPE_FOOT['stem-head'] = [int(xs_.max()), YC, zs]
OLD_ROPES = ('main-shroud-S', 'main-shroud-P', 'fore-shroud-S', 'fore-shroud-P')   # 一舷一根的舊側支索（2026-10-21 換成三根＋繩梯）
for nm in OLD_ROPES:
    if nm in listed(ASM, 'ropes.json', 'ropes'): run(('op', 'work'), ('sub', 'unrope'), ('work', ASM), ('persona', PER), ('name', nm)); print('✓ 拿掉繩', nm)
for wid, nm in [(W, 'chain-%s-%s' % (m_, s)) for m_ in CHAIN for s in 'SP'] + [(W + '-mast-' + m_, 'shroud-' + s) for m_ in CHAIN for s in 'SP']:
    if nm in listed(wid, 'anchors.json', 'anchors'): run(('op', 'work'), ('sub', 'unanchor'), ('work', wid), ('persona', PER), ('name', nm)); print('✓ 拿掉固定點', wid, nm)
for k, v in ROPE_FOOT.items(): anchor(W, k, v)
MS = M['masts']
for mn, wid in (('main', W + '-mast-main'), ('fore', W + '-mast-fore')):
    mx = MS[mn]['x']; tz = MS[mn]['top']; rr_ = MS[mn]['r']
    for s, sg in (('S', 1), ('P', -1)):
        for k, dx in enumerate(RIM_DX): anchor(wid, 'shroud-%s%d' % (s, k + 1), [mx + dx, YC + sg * (rr_ + 1), tz - 1])   # 桅樓圓台邊的正下方外一格
    anchor(wid, 'pole-head', [mx, YC, MS[mn]['pole_top'] - 4])
# 信號桁（帆桁模型、meta kind=yard）：遊戲照帆桁的 mast 認桅（10_ship.js findMasts）⇒ 桅頂掛陣營旗（77_colours.js）、桅身可以被打斷；yard=signal ⇒ 不追風（30_rig_physics.js）
for mn, wid in (('main', W + '-mast-main'), ('fore', W + '-mast-fore')):
    YG = PM['yard-' + mn]; pv_ = YG['anchors']['pivot']; L_m = YG['frame'][1] * 0.1
    model(wid, 'yard-signal', W + '-yard-' + mn, [MS[mn]['x'] + 0.5, YC + 0.5, MS[mn]['yard_z'] + 0.5], [pv_[0] + 0.5, pv_[1] + 0.5, pv_[2] + 0.5], [0, 0, 0], 1,
          {'kind': 'yard', 'mast': mn, 'yard': 'signal', 'length_ft': round(L_m / 0.3048, 1), 'diameter_in': 4, 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0})
gp = MS['gaff_peak']
anchor(W + '-mast-main', 'gaff-peak', [int(math.floor(gp[0])) + 1, YC, int(math.floor(gp[2])) - 1])

# 通用部件的固定點（砲：muzzle 內膛那一格、breech、trunnion；37 mm：pivot ＝ 立柱中心）
for key, wid in (('gun305', W + '-gun-krupp305'), ('gun150', W + '-gun-krupp150'), ('gun37', W + '-gun-hotchkiss37'),
                 ('yard-main', W + '-yard-main'), ('yard-fore', W + '-yard-fore'), ('helm', W + '-helm')):
    for k, v in PM[key]['anchors'].items(): anchor(wid, k, v)
# ── 砲塔層 ──
TMG = PM['turret-main-shell']['geom']; CXM = TMG['CX']
G305 = PM['gun305']['anchors']; piv305 = [G305['trunnion'][0] + 0.5, G305['trunnion'][1] + 0.5, 0]
TM = P['turret_main']
for b in P['barbettes']:
    side = b['name']; wid = W + '-turret-' + side.lower(); sg = 1 if b['dy'] > 0 else -1
    link(wid, '殼', W + '-turret-main-shell', {'material': 'iron', 'render': 'smooth'}, turn=0 if sg > 0 else 180)      # 牆 2 格厚 ⇒ 平滑＋金屬反光（Tim 2026-10-21）
    link(wid, '頂', W + '-turret-main-top', {'material': 'iron_plate', 'render': 'smooth'}, turn=0 if sg > 0 else 180)  # 頂 2 格厚 ⇒ 平滑（Tim 2026-10-21「砲塔蓋 是金屬的嗎」）；iron_plate：遊戲照 matMap 換成 iron*0.125（2 格裡一吋鋼板，實心鐵會多 360 t）
    link(wid, '轉盤', W + '-turret-main-table', {'material': 'iron', 'render': 'voxel'}, turn=0 if sg > 0 else 180)    # 轉盤 1 格厚 ⇒ 方塊（平滑會被平均掉）
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
    link(wid, '殼', W + '-turret15-shell', {'material': 'iron', 'render': 'smooth'}, turn=270 if f > 0 else 90)
    link(wid, '頂', W + '-turret15-roof', {'material': 'iron_plate', 'render': 'smooth'}, turn=270 if f > 0 else 90)
    model(wid, '砲', W + '-gun-krupp150', [CX15 + 0.5 + f * T15['gun_fwd'], CX15 + 0.5, 0], piv150, [0, 0, -90 if f > 0 else 90], 0.5, {'kind': 'gun', 'gun': '150k', 'safe': 1})
    anchor(wid, 'pivot', [CX15, CX15, 0]); anchor(wid, 'front', [CX15 + f * CX15, CX15, 0])
    ar = ARC['turret15-' + t['name']]
    link(ASM, '砲塔-' + ('艉' if f < 0 else '艏'), wid, {'kind': 'turret', 'arc': '%d,%d' % tuple(ar['arc']), 'fire': '%d,%d' % tuple(ar['fire']), 'rate': 15},
         at=(t['x'] - CX15, YC - CX15, T15['z0']))

# ── 中甲板艙房（gen_rooms.py；造船規格 §9.2）：關聯在 下甲板 那件作品裡 ⇒ 艙房屬於下甲板那一層；右舷一排照原樣＋mirror=y、中線一件 ──
RM = json.load(open(os.path.join(out, 'rooms_meta.json'), encoding='utf-8'))['rooms']
for which, wid in (('side', W + '-rooms-lower-side'), ('mid', W + '-rooms-lower-mid')):
    for r in RM[which]:
        anchor(wid, r['name'] + '.min', r['min']); anchor(wid, r['name'] + '.max', r['max'])
link(W + '-deck-lower', '艙房', W + '-rooms-lower-side', {'kind': 'rooms'})
link(W + '-deck-lower', '艙房-鏡像', W + '-rooms-lower-side', {'kind': 'rooms'}, mirror='y')
link(W + '-deck-lower', '艙房-中', W + '-rooms-lower-mid', {'kind': 'rooms'})

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
# 舵輪：自己的單輪（2026-10-21 換掉憲法號的雙輪 —— 那件的兩個輪子沒接到中間的支架，6 連通 3 塊，Tim：「中間是浮空的」）。
#   軸前端插進鐵立柱的齒輪箱後面（立柱 x helm_x..+2、齒輪箱 helm_x−1..+3、z WH1+10..+13 ⇒ 軸心 z WH1+12）；模型的軸長 13.5×0.2 ＝ 2.7 格
HG = PM['helm']['anchors']; hpv = [HG['spin-a'][0] + 0.5, HG['spin-a'][1] + 0.5, HG['spin-a'][2] + 0.5]
hx_ = ch['helm_x'] - 1 + 0.6 - (PM['helm']['frame'][0] - hpv[0]) * 0.2
model(W + '-chart-house', '舵輪', W + '-helm', [hx_, YC + 0.5, ch['z'] + 12], hpv, [0, 0, 0], 0.2,
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
MLINK = {'main': '主桅', 'fore': '前桅'}
ROPES = [('%s-shroud-%s%d' % (mn, s, k), '%s/shroud-%s%d' % (MLINK[mn], s, k), '船殼/chain-%s-%s%d' % (mn, s, k), 'standing/shrouds', '0.8')
         for mn in CHAIN for s in 'SP' for k in (1, 2, 3)]
ROPES += [
    ('main-backstay-S', '主桅/pole-head', '船殼/backstay-S', 'standing/stays', '0.9'), ('main-backstay-P', '主桅/pole-head', '船殼/backstay-P', 'standing/stays', '0.9'),
    ('forestay', '前桅/pole-head', '船殼/stem-head', 'standing/stays', '0.9'), ('triatic', '主桅/pole-head', '前桅/pole-head', 'standing/stays', '0.9'),
]
have = listed(ASM, 'ropes.json', 'ropes')
for nm, a_, b_, grp, th in ROPES:
    a = [('op', 'work'), ('sub', 'rope'), ('work', ASM), ('persona', PER), ('name', nm), ('from', a_), ('to', b_), ('slack', '1.0'), ('thickness', th), ('color', '#2b2620'), ('group', grp)]
    if nm in have: a.append(('overwrite', '1'))
    run(*a); print('✓ 繩', nm)
# ── 繩梯（橫繩組 climb=1，造船規格 §6）：側支索最前、最後兩根之間每 4 格一道；foot ＝ 舷牆內第一格站得住的甲板再往內 2 格、head ＝ 桅樓圓台上這一舷的開口內 ──
allc = own > 0


def stand(x, y, z): return bool(allc[x, y, z - 1]) and not allc[x, y, z:z + 7].any()


ROPES_F = os.path.join(WORKS, ASM, 'ropes.json')
have_rl = set()
if os.path.exists(ROPES_F):
    for k_, v_ in json.load(open(ROPES_F, encoding='utf-8')).items():
        if isinstance(v_, list) and 'ratline' in k_: have_rl |= {x.get('name') for x in v_ if isinstance(x, dict)}
for mn in CHAIN:
    mx = MS[mn]['x']; tz = MS[mn]['top']; rr_ = MS[mn]['r']
    for s, sg in (('S', 1), ('P', -1)):
        x_ = CHAIN[mn]; y_ = ROPE_FOOT['chain-%s-%s2' % (mn, s)][1]
        while not stand(x_, y_, zu + 1): y_ -= sg
        foot = [x_, y_ - 2 * sg, zu + 1]
        head = [mx, YC + sg * (rr_ - 2), tz + 1]
        assert stand(*foot) and stand(*head), (mn, s, foot, head)
        nm = '%s-lower-%s' % (mn, s)
        a = [('op', 'work'), ('sub', 'ratlines'), ('work', ASM), ('persona', PER), ('name', nm), ('rope_a', '%s-shroud-%s1' % (mn, s)), ('rope_b', '%s-shroud-%s3' % (mn, s)),
             ('step', '4'), ('start', '7'), ('stop', '6'), ('min_span', '5'), ('thickness', '0.3'), ('color', '#2b2620'), ('group', 'ratlines/lower'),
             ('climb', '1'), ('foot', '%d,%d,%d' % tuple(foot)), ('head', '%d,%d,%d' % tuple(head))]
        if nm in have_rl: a.append(('overwrite', '1'))
        run(*a); print('✓ 繩梯', nm, foot, head)
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
preset('只看動力', '煙囪、軸（鍋爐、主機是模型 ⇒ 照常畫；TASK-0793）', links='煙囪-後,煙囪-前,軸,軸-鏡像', hide_links='self')
preset('只看主砲', '兩座露砲台、砲塔、飛橋甲板', links='露砲台,露砲台平台,砲塔-S,砲塔-P,甲板-main', hide_links='self')
print('done')

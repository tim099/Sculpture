# 建子作品（沒有才建）＋把格子同步成產生程式的清單（刻掉多的與換色的、補上缺的；重跑只動差的那幾格）。
# 用法：python -I -X utf8 -B apply_build.py <gen_dingyuan 輸出> <gen_parts 輸出> [部件…]
import sys, os, json, subprocess, shutil, tempfile
out, pout = sys.argv[1], sys.argv[2]; ONLY = set(sys.argv[3:])
S = shutil.which('senate'); W = 'trailhead-dingyuan-01m'; PER = 'trailhead'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1200:]); sys.exit(1)
    return p.stdout


def fwd(p): return p.replace(os.sep, '/')


HULL = '960,221,390'
def fr(k): return ','.join(str(v) for v in PM[k]['frame'])
# 部件 → (作品 ID, 名稱, 清單檔, 尺寸, 一格幾公尺)
PARTS = [
    ('hull', W, '定遠號 船殼', 'part_hull.txt', HULL, 0.1),
    ('belt', W + '-belt', '定遠號 城堡裝甲帶（14 in 複合裝甲）', 'part_belt.txt', HULL, 0.1),
    ('barbettes', W + '-barbettes', '定遠號 露砲台裝甲圈（兩座、12 in）', 'part_barbettes.txt', HULL, 0.1),
    ('barbette-platforms', W + '-barbette-platforms', '定遠號 露砲台中間的固定平台與撐柱', 'part_barbette-platforms.txt', HULL, 0.1),
    ('armour-deck', W + '-armour-deck', '定遠號 城堡上的裝甲甲板（3 in）', 'part_armour-deck.txt', HULL, 0.1),
    ('deck-lower', W + '-deck-lower', '定遠號 下甲板', 'part_deck-lower.txt', HULL, 0.1),
    ('deck-main', W + '-deck-main', '定遠號 主甲板（舯部露天）', 'part_deck-main.txt', HULL, 0.1),
    ('deck-poop', W + '-deck-poop', '定遠號 艉樓甲板', 'part_deck-poop.txt', HULL, 0.1),
    ('deck-fc', W + '-deck-fc', '定遠號 艏樓甲板', 'part_deck-fc.txt', HULL, 0.1),
    ('deck-hurricane', W + '-deck-hurricane', '定遠號 飛橋甲板（蓋在兩座露砲台上）', 'part_deck-hurricane.txt', HULL, 0.1),
    ('superstructure', W + '-superstructure', '定遠號 艉樓、艏樓的前後壁', 'part_superstructure.txt', HULL, 0.1),
    ('rails', W + '-rails', '定遠號 艉樓欄杆', 'part_rails.txt', HULL, 0.1),
    ('conning', W + '-conning', '定遠號 司令塔（8 in）', 'part_conning.txt', HULL, 0.1),
    ('chart-house', W + '-chart-house', '定遠號 海圖室', 'part_chart-house.txt', HULL, 0.1),
    ('funnel-aft', W + '-funnel-aft', '定遠號 後煙囪（含甲板下直煙道）', 'part_funnel-aft.txt', HULL, 0.1),
    ('funnel-fwd', W + '-funnel-fwd', '定遠號 前煙囪（含甲板下直煙道）', 'part_funnel-fwd.txt', HULL, 0.1),
    ('boilers-aft', W + '-boilers-aft', '定遠號 1、2 號鍋爐間（右舷兩座＋煙箱；左舷鏡像）', 'part_boilers-aft.txt', HULL, 0.1),
    ('boilers-fwd', W + '-boilers-fwd', '定遠號 3、4 號鍋爐間（右舷兩座＋煙箱；左舷鏡像）', 'part_boilers-fwd.txt', HULL, 0.1),
    ('engine', W + '-engine', '定遠號 臥式三缸主機（右舷；左舷鏡像）', 'part_engine.txt', HULL, 0.1),
    ('shaft', W + '-shaft', '定遠號 螺旋槳軸（右舷；左舷鏡像）', 'part_shaft.txt', HULL, 0.1),
    ('mast-main', W + '-mast-main', '定遠號 主桅（戰鬥桅、斜桁、兩根吊艇桿）', 'part_mast-main.txt', HULL, 0.1),
    ('mast-fore', W + '-mast-fore', '定遠號 前桅（戰鬥桅、下平台）', 'part_mast-fore.txt', HULL, 0.1),
    ('vents', W + '-vents', '定遠號 通風筒', 'part_vents.txt', HULL, 0.1),
    ('skids', W + '-skids', '定遠號 艇架（魚雷艇、艉樓小艇）', 'part_skids.txt', HULL, 0.1),
    ('mag-fore-P', W + '-mag-fore-p', '定遠號 前彈藥庫・左（吊左舷露砲台）', 'part_mag-fore-P.txt', HULL, 0.1),
    ('mag-fore-S', W + '-mag-fore-s', '定遠號 前彈藥庫・右（吊右舷露砲台、艏 15 cm 砲）', 'part_mag-fore-S.txt', HULL, 0.1),
    ('mag-aft', W + '-mag-aft', '定遠號 後彈藥庫（吊艉 15 cm 砲）', 'part_mag-aft.txt', HULL, 0.1),
    ('floor', W + '-floor', '定遠號 機艙與鍋爐艙的地板', 'part_floor.txt', HULL, 0.1),
    ('bulkheads', W + '-bulkheads', '定遠號 艙底的水密艙壁', 'part_bulkheads.txt', HULL, 0.1),
    ('ladders', W + '-ladders', '定遠號 梯子', 'part_ladders.txt', HULL, 0.1),
    ('rooms-lower-side', W + '-rooms-lower-side', '定遠號 中甲板艙房・右舷一排（軍官艙、艏艙；左舷鏡像）', 'part_rooms-lower-side.txt', HULL, 0.1),
    ('rooms-lower-mid', W + '-rooms-lower-mid', '定遠號 中甲板艙房・中線（艦長套房、餐廳、配膳室、病房、藥房）', 'part_rooms-lower-mid.txt', HULL, 0.1),
    ('rudder', W + '-rudder', '定遠號 舵（外部模型的來源，整船的框）', 'part_rudder.txt', HULL, 0.1),
    ('screw-s', W + '-screw-s', '定遠號 右舷螺旋槳（四葉 3 m、右旋；外部模型的來源，整船的框）', 'part_screw-s.txt', HULL, 0.1),
    ('screw-p', W + '-screw-p', '定遠號 左舷螺旋槳（四葉 3 m、左旋；外部模型的來源，整船的框）', 'part_screw-p.txt', HULL, 0.1),
    # 通用部件與砲塔（P：parts 輸出）
    ('gun305', W + '-gun-krupp305', '30.5 cm 克虜伯後膛砲 MRK L/25＋滑架（gun 305k，通用部件，0.05 m）', 'P:gun305.txt', fr('gun305'), 0.05),
    ('gun150', W + '-gun-krupp150', '15 cm 克虜伯後膛砲 MRK L/35＋滑架（gun 150k，通用部件，0.05 m）', 'P:gun150.txt', fr('gun150'), 0.05),
    ('gun37', W + '-gun-hotchkiss37', '37 mm 哈乞開斯五管轉膛砲＋立柱座（gun h37，通用部件，0.02 m）', 'P:gun37.txt', fr('gun37'), 0.02),
    ('boat-torpedo', W + '-boat-torpedo', '二等魚雷艇（boat torpedo、18.5 m，通用部件，0.1 m）', 'P:torpedo-boat.txt', fr('torpedo-boat'), 0.1),
    ('turret-main-shell', W + '-turret-main-shell', '定遠號 主砲塔殼・砲罩的牆（平滑，前方 +y）', 'P:turret-main-shell.txt', fr('turret-main-shell'), 0.1),
    ('turret-main-top', W + '-turret-main-top', '定遠號 主砲塔殼・頂（2 格厚、平滑，前方 +y）', 'P:turret-main-top.txt', fr('turret-main-top'), 0.1),
    ('turret-main-table', W + '-turret-main-table', '定遠號 主砲塔殼・轉盤（1 格厚、方塊）', 'P:turret-main-table.txt', fr('turret-main-table'), 0.1),
    ('turret15-shell', W + '-turret15-shell', '定遠號 15 cm 砲塔殼・圓筒（平滑，前方 +y）', 'P:turret15-shell.txt', fr('turret15-shell'), 0.1),
    ('turret15-roof', W + '-turret15-roof', '定遠號 15 cm 砲塔殼・頂（2 格厚、平滑）', 'P:turret15-roof.txt', fr('turret15-roof'), 0.1),
    ('yard-main', W + '-yard-main', '定遠號 主桅信號桁（帆桁模型的來源，沿 y）', 'P:yard-main.txt', fr('yard-main'), 0.1),
    ('yard-fore', W + '-yard-fore', '定遠號 前桅信號桁（帆桁模型的來源，沿 y）', 'P:yard-fore.txt', fr('yard-fore'), 0.1),
    ('helm', W + '-helm', '定遠號 舵輪（單輪、黃銅輪轂；外部模型的來源，0.02 m）', 'P:helm.txt', fr('helm'), 0.02),
    ('turret-S', W + '-turret-s', '定遠號 右舷主砲塔（砲塔層：殼＋兩門 30.5 cm）', None, fr('turret-main-shell'), 0.1),
    ('turret-P', W + '-turret-p', '定遠號 左舷主砲塔（砲塔層：殼＋兩門 30.5 cm）', None, fr('turret-main-shell'), 0.1),
    ('turret15-aft', W + '-turret15-aft', '定遠號 艉 15 cm 砲塔（砲塔層）', None, fr('turret15-shell'), 0.1),
    ('turret15-fwd', W + '-turret15-fwd', '定遠號 艏 15 cm 砲塔（砲塔層）', None, fr('turret15-shell'), 0.1),
]
ASM = (W + '-assembly', '定遠號')


def exists(wid): return os.path.exists(os.path.join(WORKS, wid, 'work.json'))


def ensure(wid, title, size, mpv, tags):
    if not exists(wid):
        run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('parent_work', W), ('size', size), ('tags', tags))
        print('＋ 建立', wid)
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('meters_per_voxel', str(mpv)), ('size', size), ('tags', tags), ('title', title))


def load(f):
    d = {}
    for l in open(f, encoding='utf-8'):
        if l[:1].isdigit():
            a = l.split(','); d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


def sync(wid, listfile):
    tmp = tempfile.mkdtemp(prefix='dsync_'); cur = fwd(os.path.join(tmp, 'cur.txt'))
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', cur), ('links', 'none'))
    old = load(cur) if os.path.exists(cur) else {}
    new = load(listfile)
    rm = [k for k, c in old.items() if new.get(k) != c]
    add = [k for k, c in new.items() if old.get(k) != c]
    print('%s：現在 %d、新的 %d ⇒ 刻 %d、補 %d' % (wid, len(old), len(new), len(rm), len(add)))
    for name, lst, op in (('rm', rm, 'carvevox'), ('add', add, 'stampvox')):
        for i in range(0, len(lst), 900000):
            part = lst[i:i + 900000]; fn = fwd(os.path.join(tmp, '%s%d.txt' % (name, i)))
            with open(fn, 'w') as f:
                f.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], old[k] if op == 'carvevox' else new[k]) for k in part) + '\n')
            o = run(('op', op), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(part))), ('share', '0'))
            got = [l for l in o.splitlines() if 'placed' in l or 'carved' in l][:1]
            print('  %s %d ✓ %s' % (op, len(part), got[0].strip() if got else ''))


run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', W), ('meters_per_voxel', '0.1'), ('size', HULL), ('tags', 'sub'), ('title', '定遠號 船殼'))
if not exists(ASM[0]):
    run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', ASM[0]), ('title', ASM[1]), ('parent_work', W), ('size', HULL))
    print('＋ 建立', ASM[0])
run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', ASM[0]), ('meters_per_voxel', '0.1'), ('size', HULL), ('tags', ''), ('title', ASM[1]))
for key, wid, title, lf, size, mpv in PARTS:
    if ONLY and key not in ONLY: continue
    if wid != W: ensure(wid, title, size, mpv, 'sub')
    if lf: sync(wid, os.path.join(pout, lf[2:]) if lf.startswith('P:') else os.path.join(out, lf))
print('done')

# 建子作品（沒有才建）＋把格子同步成產生程式的清單（刻掉多的與換色的、補上缺的；重跑只動差的那幾格）。
# 用法：python -I -X utf8 -B apply_build.py <gen_matsushima 輸出> <gen_parts 輸出> [部件…]
# 寫法照定遠號的 apply_build.py（trailhead）。
import sys, os, json, subprocess, shutil, tempfile
out, pout = sys.argv[1], sys.argv[2]; ONLY = set(sys.argv[3:])
S = shutil.which('senate'); W = 'ridge-001-matsushima-01m'; PER = 'ridge-001'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
PM = json.load(open(os.path.join(pout, 'parts_meta.json'), encoding='utf-8'))


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1200:]); sys.exit(1)
    return p.stdout


def fwd(p): return p.replace(os.sep, '/')


HULL = '1004,181,490'
def fr(k): return ','.join(str(v) for v in PM[k]['frame'])
# 部件 → (作品 ID, 名稱, 清單檔, 尺寸, 一格幾公尺)
PARTS = [
    ('hull', W, '松島號 船殼', 'part_hull.txt', HULL, 0.1),
    ('deck-lower', W + '-deck-lower', '松島號 防護甲板（2 in，走路的那一層）', 'part_deck-lower.txt', HULL, 0.1),
    ('deck-middle', W + '-deck-middle', '松島號 中甲板（12 cm 砲列）', 'part_deck-middle.txt', HULL, 0.1),
    ('deck-upper', W + '-deck-upper', '松島號 上甲板（後段露天：主砲露砲台）', 'part_deck-upper.txt', HULL, 0.1),
    ('deck-fc', W + '-deck-fc', '松島號 船首樓甲板', 'part_deck-fc.txt', HULL, 0.1),
    ('bridge', W + '-bridge', '松島號 艦橋（兩翼）', 'part_bridge.txt', HULL, 0.1),
    ('superstructure', W + '-superstructure', '松島號 船首樓後壁與煙囪罩', 'part_superstructure.txt', HULL, 0.1),
    ('rails', W + '-rails', '松島號 欄杆', 'part_rails.txt', HULL, 0.1),
    ('conning', W + '-conning', '松島號 司令塔（125 mm）', 'part_conning.txt', HULL, 0.1),
    ('chart-house', W + '-chart-house', '松島號 海圖室', 'part_chart-house.txt', HULL, 0.1),
    ('funnel', W + '-funnel', '松島號 煙囪（含甲板下直煙道）', 'part_funnel.txt', HULL, 0.1),
    ('boilers', W + '-boilers', '松島號 圓筒鍋爐（右舷三座＋煙箱；左舷鏡像）', 'part_boilers.txt', HULL, 0.1),
    ('engine', W + '-engine', '松島號 臥式三段膨脹主機（右舷；左舷鏡像）', 'part_engine.txt', HULL, 0.1),
    ('shaft', W + '-shaft', '松島號 螺旋槳軸（右舷；左舷鏡像）', 'part_shaft.txt', HULL, 0.1),
    ('barbette', W + '-barbette', '松島號 主砲露砲台（300 mm）', 'part_barbette.txt', HULL, 0.1),
    ('hoist', W + '-hoist', '松島號 主砲的揚弾筒（轉軸上、防護甲板 → 轉盤中間；裝甲 0.3 m；kind=hoist）', 'part_hoist.txt', HULL, 0.1),
    ('barbette-posts', W + '-barbette-posts', '松島號 露砲台裡的撐柱', 'part_barbette-posts.txt', HULL, 0.1),
    ('bridge-posts', W + '-bridge-posts', '松島號 艦橋的撐柱與撐臂', 'part_bridge-posts.txt', HULL, 0.1),
    ('mast', W + '-mast', '松島號 軍用桅（兩層桅樓、信號桁、斜桁、吊艇桿）', 'part_mast.txt', HULL, 0.1),
    ('top-lower', W + '-top-lower', '松島號 下桅樓的地板（kind=deck）', 'part_top-lower.txt', HULL, 0.1),
    ('top-upper', W + '-top-upper', '松島號 上桅樓的地板（kind=deck）', 'part_top-upper.txt', HULL, 0.1),
    ('vents', W + '-vents', '松島號 通風筒', 'part_vents.txt', HULL, 0.1),
    ('skids', W + '-skids', '松島號 艇架墊木', 'part_skids.txt', HULL, 0.1),
    ('mag-aft', W + '-mag-aft', '松島號 後彈藥庫（主砲）', 'part_mag-aft.txt', HULL, 0.1),
    ('mag-fore', W + '-mag-fore', '松島號 前彈藥庫（12 cm 與速射砲）', 'part_mag-fore.txt', HULL, 0.1),
    ('floor', W + '-floor', '松島號 機艙與鍋爐艙的地板', 'part_floor.txt', HULL, 0.1),
    ('bulkheads', W + '-bulkheads', '松島號 艙底的水密艙壁', 'part_bulkheads.txt', HULL, 0.1),
    ('ladders', W + '-ladders', '松島號 梯子', 'part_ladders.txt', HULL, 0.1),
    ('rooms-lower', W + '-rooms-lower', '松島號 防護甲板上的艙房（右舷；左舷鏡像）', 'part_rooms-lower.txt', HULL, 0.1),   # gen_rooms.py
    ('rooms-middle', W + '-rooms-middle', '松島號 中甲板的艙房（右舷；左舷鏡像）', 'part_rooms-middle.txt', HULL, 0.1),
    ('rooms-upper', W + '-rooms-upper', '松島號 船首樓底下的艙房（右舷；左舷鏡像）', 'part_rooms-upper.txt', HULL, 0.1),
    ('rudder', W + '-rudder', '松島號 舵（外部模型的來源，整船的框）', 'part_rudder.txt', HULL, 0.1),
    ('screw-s', W + '-screw-s', '松島號 右舷螺旋槳（四葉 3.2 m、內旋 ⇒ 左旋；外部模型的來源，整船的框）', 'part_screw-s.txt', HULL, 0.1),
    ('screw-p', W + '-screw-p', '松島號 左舷螺旋槳（四葉 3.2 m、內旋 ⇒ 右旋；外部模型的來源，整船的框）', 'part_screw-p.txt', HULL, 0.1),
    # 通用部件與砲塔（P：parts 輸出）
    ('gun320', W + '-gun-canet320', '32 cm Canet 砲（1890 年式、38 倍徑）＋液壓搖架與斜滑座（gun 320c，通用部件，0.05 m）', 'P:gun320.txt', fr('gun320'), 0.05),
    ('gun120', W + '-gun-armstrong120', '12 cm Armstrong 速射砲（40 倍徑）＋中心樞軸座與砲盾（gun 120a，通用部件，0.05 m）', 'P:gun120.txt', fr('gun120'), 0.05),
    ('gun57', W + '-gun-hotchkiss57', '57 mm 哈乞開斯 6 磅速射砲＋立柱座（gun h57，通用部件，0.02 m）', 'P:gun57.txt', fr('gun57'), 0.02),
    ('gun47', W + '-gun-hotchkiss47', '47 mm 哈乞開斯 3 磅速射砲＋立柱座（gun h47，通用部件，0.02 m）', 'P:gun47.txt', fr('gun47'), 0.02),
    ('turret-main-shell', W + '-turret-main-shell', '松島號 主砲的轉盤與砲罩（100 mm，前方 +y）', 'P:turret-main-shell.txt', fr('turret-main-shell'), 0.1),
    ('turret-main', W + '-turret-main', '松島號 主砲塔（砲塔層：轉盤與砲罩＋32 cm Canet）', None, fr('turret-main-shell'), 0.1),
]
ASM = (W + '-assembly', '松島號')


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
    tmp = tempfile.mkdtemp(prefix='msync_'); cur = fwd(os.path.join(tmp, 'cur.txt'))
    run(('op', 'export'), ('format', 'list'), ('work', wid), ('out', cur), ('links', 'none'))
    old = load(cur) if os.path.exists(cur) else {}
    new = load(listfile)
    rm = [k for k, c in old.items() if new.get(k) != c]
    add = [k for k, c in new.items() if old.get(k) != c]
    print('%s：現在 %d、新的 %d ⇒ 刻 %d、補 %d' % (wid, len(old), len(new), len(rm), len(add)), flush=True)
    for name, lst, op in (('rm', rm, 'carvevox'), ('add', add, 'stampvox')):
        for i in range(0, len(lst), 900000):
            part = lst[i:i + 900000]; fn = fwd(os.path.join(tmp, '%s%d.txt' % (name, i)))
            with open(fn, 'w') as f:
                f.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], old[k] if op == 'carvevox' else new[k]) for k in part) + '\n')
            o = run(('op', op), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(part))), ('share', '0'))
            got = [l for l in o.splitlines() if 'placed' in l or 'carved' in l][:1]
            print('  %s %d ✓ %s' % (op, len(part), got[0].strip() if got else ''), flush=True)
    shutil.rmtree(tmp, ignore_errors=True)


run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', W), ('meters_per_voxel', '0.1'), ('size', HULL), ('tags', 'sub'), ('title', '松島號 船殼'))
if not exists(ASM[0]):
    run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', ASM[0]), ('title', ASM[1]), ('parent_work', W), ('size', HULL))
    print('＋ 建立', ASM[0])
run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', ASM[0]), ('meters_per_voxel', '0.1'), ('size', HULL), ('tags', ''), ('title', ASM[1]))
for key, wid, title, lf, size, mpv in PARTS:
    if ONLY and key not in ONLY: continue
    if wid != W: ensure(wid, title, size, mpv, 'sub')
    if lf: sync(wid, os.path.join(pout, lf[2:]) if lf.startswith('P:') else os.path.join(out, lf))
print('done')

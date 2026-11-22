# 明鄭一號大鳥船 新圖紙 09（TASK-1316 步驟 10）：水線下火藥庫（＋16 火藥桶）、上戰棚貨艙口蓋、尾樓艙門、明鄭戰船廚房灶、杉板小艇、絞盤、羅經櫃與 3 盞船燈
#   用法：python -I -X utf8 draft_gear.py <design 資料夾> [--probe=shift_galley=+12]
import json, math, os, sys, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_decks as DD

sys.path.insert(0, os.path.join(HERE, 'tools'))
from wio import export_list

sys.stdout.reconfigure(encoding='utf-8')


def load_vox(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def transform_pts(vox_arr, pivot, at, rot_deg, scale):
    """將局部格轉到組裝件世界座標（先減 pivot 再縮放、再 Z 旋轉，最後加 at）。"""
    rz = rot_deg[2] if isinstance(rot_deg, (list, tuple)) else float(rot_deg)
    sc = np.array(scale, float) if isinstance(scale, (list, tuple)) else np.array([scale, scale, scale], float)
    pts = (vox_arr[:, :3].astype(float) + 0.5 - np.array(pivot, float)) * sc
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    x_new = at[0] + pts[:, 0] * c - pts[:, 1] * s
    y_new = at[1] + pts[:, 0] * s + pts[:, 1] * c
    z_new = at[2] + pts[:, 2]
    return np.stack([x_new, y_new, z_new], axis=1)


def main():
    design = os.path.abspath(HERE)
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = os.path.abspath(a)

    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    hull_id = plan['guns_build']['hull']

    zmax = int(math.ceil(L.top_max)) + 20
    x0 = int(math.floor(L.xa_min)) - 12
    x1 = int(math.ceil(L.xf_max)) + 16
    half = int(math.ceil(L.B)) + 10
    ylo = L.YC - half
    yhi = L.YC + half
    shape = (x1 - x0 + 1, yhi - ylo + 1, zmax + 1)

    wall_col, _ = DD.load_carved_shell(design, plan, L, x0, ylo, shape)
    sw_c = load_vox(os.path.join(design, 'masks', 'guns', 'swivel_rail_carve.vox.txt'))
    if sw_c.size:
        wall_col[sw_c[:, 0] - x0, sw_c[:, 1] - ylo, sw_c[:, 2]] = 0
    world_occ = wall_col > 0

    for folder in ('decks', 'ladders', 'rooms', 'deco', 'masts'):
        pdir = os.path.join(design, 'masks', folder)
        if not os.path.isdir(pdir):
            continue
        for fn in os.listdir(pdir):
            if not fn.endswith('.vox.txt'):
                continue
            if folder == 'masts' and not fn.startswith('mast-'):
                continue
            arr = load_vox(os.path.join(pdir, fn))
            if arr.size:
                xi, yi, zi = arr[:, 0] - x0, arr[:, 1] - ylo, arr[:, 2]
                m = (xi >= 0) & (xi < shape[0]) & (yi >= 0) & (yi < shape[1]) & (zi >= 0) & (zi < shape[2])
                world_occ[xi[m], yi[m], zi[m]] = True

    # 也把所有 30 門砲體素計入保留障礙，保證物件與火砲零碰撞
    guns = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))
    gun_local_cache = {}
    for g in guns:
        src = g['source']
        if src not in gun_local_cache:
            mp = os.path.join(design, 'masks', 'guns', f'{src}.vox.txt')
            gun_local_cache[src] = load_vox(mp) if os.path.exists(mp) else export_list(src, links='none')
        pts = transform_pts(gun_local_cache[src], g['pivot'], g['at'], g['rotate'], g['scale'])
        ix = np.floor(pts[:, 0]).astype(int) - x0
        iy = np.floor(pts[:, 1]).astype(int) - ylo
        iz = np.floor(pts[:, 2]).astype(int)
        m = (ix >= 0) & (ix < shape[0]) & (iy >= 0) & (iy < shape[1]) & (iz >= 0) & (iz < shape[2])
        world_occ[ix[m], iy[m], iz[m]] = True

    def check_hits(pts_world):
        ix = np.floor(pts_world[:, 0]).astype(int) - x0
        iy = np.floor(pts_world[:, 1]).astype(int) - ylo
        iz = np.floor(pts_world[:, 2]).astype(int)
        m = (ix >= 0) & (ix < shape[0]) & (iy >= 0) & (iy < shape[1]) & (iz >= 0) & (iz < shape[2])
        return int(world_occ[ix[m], iy[m], iz[m]].sum()) + int((~m).sum())

    # ── 1. 水線下火藥庫 (x=208..219, y=133..153..160 順船殼外張，z=12..37 仍低於 waterline=42，不擋中線 y=126..130 通路) ──
    COPPER, PINE, OAK = 168, 177, 136
    mag_cells = {}
    mx0, mx1, mz0, mz1 = 208, 219, 12, 37
    # 內側隔牆在 y=133；外側貼船殼外緣或到 y=160；門口開在 y=133, x=211..215, z=13..27
    for zw in range(mz0, mz1 + 1):
        # 依高度 z 隨船寬擴張外側牆界 y_out_z（查 hull_occ 在 x=214 的最內船殼格）
        y_hull_in = min(int(np.nonzero(world_occ[xw - x0, YC - ylo:, zw])[0].min()) + YC for xw in range(mx0, mx1 + 1) if world_occ[xw - x0, YC - ylo:, zw].any())
        my0, my1 = 133, min(158, y_hull_in - 1)
        for xw in range(mx0, mx1 + 1):
            for yw in range(my0, my1 + 1):
                if world_occ[xw - x0, yw - ylo, zw]:
                    continue
                is_floor = (zw == mz0)
                is_roof = (zw == mz1)
                is_wall = (xw in (mx0, mx1)) or (yw in (my0, my1))
                is_door = (yw == my0) and (211 <= xw <= 215) and (mz0 + 1 <= zw <= 27)
                if is_door:
                    continue
                if is_floor:
                    mag_cells[(xw, yw, zw)] = PINE
                elif is_roof:
                    mag_cells[(xw, yw, zw)] = OAK if (xw in (mx0, mx1) or yw in (my0, my1) or (xw % 3 == 0)) else COPPER
                elif is_wall:
                    mag_cells[(xw, yw, zw)] = OAK if (zw in (mz0 + 1, mz1 - 1) or (xw in (mx0, mx1) and yw in (my0, my1))) else COPPER

    # 兩層木架（z=20 與 z=28）供 4 + 6 + 6 = 16 桶互不重疊且不碰牆（桶寬 4.4 格, 高 5.4 格）
    for zw_shelf, y_s0, y_s1 in ((20, 141, 156), (28, 141, 157)):
        for xw in range(mx0 + 1, mx1):
            for yw in range(y_s0, y_s1 + 1):
                if not world_occ[xw - x0, yw - ylo, zw_shelf]:
                    mag_cells[(xw, yw, zw_shelf)] = OAK
        for xw in (mx0 + 1, mx1 - 1):
            mag_cells[(xw, y_s0, zw_shelf - 1)] = OAK

    mag_arr = np.array([[x, y, z, c] for (x, y, z), c in sorted(mag_cells.items())], dtype=np.int32)
    mag_world_occ = world_occ.copy()
    mag_world_occ[mag_arr[:, 0] - x0, mag_arr[:, 1] - ylo, mag_arr[:, 2]] = True
    mag_cav = ndimage.binary_fill_holes(mag_world_occ) & ~mag_world_occ
    labc, nc = ndimage.label(mag_cav)
    for ci in range(1, nc + 1):
        pts = np.argwhere(labc == ci)
        if len(pts) <= 200:
            for px, py, pz in pts:
                mag_cells[(int(px) + x0, int(py) + ylo, int(pz))] = 136
    mag_arr = np.array([[x, y, z, c] for (x, y, z), c in sorted(mag_cells.items())], dtype=np.int32)
    mag_world_occ = world_occ.copy()
    mag_world_occ[mag_arr[:, 0] - x0, mag_arr[:, 1] - ylo, mag_arr[:, 2]] = True
    mag_cav = ndimage.binary_fill_holes(mag_world_occ) & ~mag_world_occ
    mag_cav_count = int(mag_cav.sum())
    assert mag_cav_count == 0, f'Expected 0 magazine cavities, got {mag_cav_count}'

    barrel_vox = export_list('basecamp-frigate-constitution-01m-powder-barrel', links='none')
    barrel_models = []
    barrel_hits = 0
    # 4 桶於底板 z=13 + 6 桶於二層架 z=21 + 6 桶於三層架 z=29 = 16 桶（間距 >= 4.8 格 > 桶寬 4.4 格）
    barrel_coords = (
        [(bx, by, 13.0) for bx in (211.2, 216.2) for by in (139.0, 144.0)] +
        [(bx, by, 21.0) for bx in (211.2, 216.2) for by in (143.5, 148.5, 153.5)] +
        [(bx, by, 29.0) for bx in (211.2, 216.2) for by in (143.5, 148.5, 153.5)]
    )
    for b_idx, (bx, by, bz) in enumerate(barrel_coords, 1):
        at_b = [bx, by, bz]
        pts_b = transform_pts(barrel_vox, [11.0, 11.0, 0.0], at_b, 0.0, 0.2)
        ix = np.floor(pts_b[:, 0]).astype(int) - x0
        iy = np.floor(pts_b[:, 1]).astype(int) - ylo
        iz = np.floor(pts_b[:, 2]).astype(int)
        barrel_hits += int(mag_world_occ[ix, iy, iz].sum())
        barrel_models.append({
            'name': f'桶-{b_idx:02d}',
            'source': 'basecamp-frigate-constitution-01m-powder-barrel',
            'at': at_b, 'pivot': [11.0, 11.0, 0.0], 'rotate': [0.0, 0.0, 0.0], 'scale': 0.2,
            'meta': {'kind': 'powder', 'powder_lb': 100},
        })

    mag_spec = {
        'work': f'{hull_id}-magazine',
        'link': '火藥庫',
        'title': '明鄭一號大鳥船 水線下火藥庫（0.1 m）',
        'cells': len(mag_cells),
        'anchors': {'blast': [213, 142, 18], 'door': [213, 133, 13]},
        'barrels': barrel_models,
        'meta': {'kind': 'magazine', 'pos': 'aft'},
        'cavities': mag_cav_count,
        'barrel_hits': barrel_hits,
    }

    # ── 2. 貨艙口蓋（cargo-hatch：蓋於上戰棚貨艙口 x=260..274, y=122..134, z=72；hinge-a/b 朝上掀開）──
    hatch_w, hatch_l = 15, 13
    hatch_cells = {}
    for lx in range(hatch_w):
        for ly in range(hatch_l):
            is_rim = (lx in (0, hatch_w - 1) or ly in (0, hatch_l - 1))
            is_seam = (lx in (5, 9) or ly == 6)
            hatch_cells[(lx, ly, 0)] = OAK if (is_rim or is_seam) else 177
            if is_rim:
                hatch_cells[(lx, ly, 1)] = OAK
    hatch_spec = {
        'work': f'{hull_id}-cargo-hatch',
        'title': '明鄭一號大鳥船 貨艙口蓋（0.1 m）',
        'size': [hatch_w, hatch_l, 2],
        'anchors': {'hinge-a': [0, 12, 0], 'hinge-b': [0, 0, 0]},
        'mount': {
            'host': f'{hull_id}-deck-upper',
            'name': '貨艙口',
            'at': [260.0, 122.0, 72.0],
            'pivot': [0.0, 0.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 1.0,
            'meta': {'kind': 'door', 'open': 'up'},
        },
    }

    # ── 3. 甲板裝備外部模型（貼緊甲板與艙壁，嚴查零碰撞＋腳底實心）──
    ext_items = [
        # (a) 尾樓斷牆直立艙門（x=134 緊貼 x=132，y=123..134 遮蓋 y=124..132 門洞, z=70..88 壓 z=87 橫樑）
        {
            'host': f'{hull_id}-deck-upper',
            'name': '艙門-尾樓',
            'source': 'gura-pinas-01m-door',
            'at': [134.0, 123.0, 70.0],
            'pivot': [1.0, 0.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': [0.5, 0.7857, 0.5625],
            'meta': {'kind': 'door', 'open': 'side'},
        },
        # (b) 廚房灶（kaguya-gloire-01m-galley，scale 0.5 ⇒ 2.2×1.6×2.2 m；x=296 置中上戰棚；probe 往後 -24 撞進貨艙／小艇）
        {
            'host': f'{hull_id}-deck-upper',
            'name': '廚房',
            'source': 'kaguya-gloire-01m-galley',
            'at': [296.0 + (-24.0 if probe == 'shift_galley=-24' else 0.0), 128.5, 70.0],
            'pivot': [22.0, 16.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.5,
            'meta': {'kind': 'galley'},
        },
        # (c) 杉板小艇（basecamp-ember-01m-boat，scale 0.35 ⇒ 6.3×1.8×0.95 m；置於主桅後 x=174..237）
        {
            'host': f'{hull_id}-deck-upper',
            'name': '小艇',
            'source': 'basecamp-ember-01m-boat',
            'at': [204.0, 128.5, 70.0],
            'pivot': [90.0, 26.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.35,
            'meta': {'kind': 'boat', 'boat': 'sampan'},
        },
        # (d) 絞盤（basecamp-ember-01m-capstan，0.02 m scale 0.2 ⇒ 置於前戰棚 x=320）
        {
            'host': f'{hull_id}-deck-upper',
            'name': '絞盤',
            'source': 'basecamp-ember-01m-capstan',
            'at': [320.0, 128.5, 70.0],
            'pivot': [40.0, 40.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.2,
            'meta': {'kind': 'capstan'},
        },
        # (e) 羅經櫃（summit-night-falcon-01m-binnacle，0.02 m scale 0.2 ⇒ 置於尾樓甲板舵柄前 x=87, z=92）
        {
            'host': f'{hull_id}-deck-poop',
            'name': '羅經櫃',
            'source': 'summit-night-falcon-01m-binnacle',
            'at': [87.0, 128.5, 92.0],
            'pivot': [9.0, 13.0, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.2,
            'meta': {'kind': 'binnacle'},
        },
        # (f) 三盞船燈（雙尾樓角燈站實尾樓甲板 z=92 且頂高 110 < 尾帆下桁 116.5＋前艏樓甲板燈 z=70）
        {
            'host': f'{hull_id}-deck-poop',
            'name': '艉燈-S',
            'source': 'gura-tridente-01m-lantern',
            'at': [65.5, 146.5, 92.0],
            'pivot': [8.5, 8.5, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.5,
            'meta': {'kind': 'light'},
        },
        {
            'host': f'{hull_id}-deck-poop',
            'name': '艉燈-P',
            'source': 'gura-tridente-01m-lantern',
            'at': [65.5, 110.5, 92.0],
            'pivot': [8.5, 8.5, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.5,
            'meta': {'kind': 'light'},
        },
        {
            'host': f'{hull_id}-deck-upper',
            'name': '艏燈',
            'source': 'gura-tridente-01m-lantern',
            'at': [412.5, 128.5, 70.0],
            'pivot': [8.5, 8.5, 0.0],
            'rotate': [0.0, 0.0, 0.0],
            'scale': 0.5,
            'meta': {'kind': 'light'},
        },
    ]

    item_report = {}
    ext_hits_total = 0
    for it in ext_items:
        src = it['source']
        vox = export_list(src, links='none')
        pts = transform_pts(vox, it['pivot'], it['at'], it['rotate'], it['scale'])
        hits = check_hits(pts)
        # 檢查底面最低一格下一格有支撐
        zmin_w = float(pts[:, 2].min())
        bot = pts[pts[:, 2] <= zmin_w + 0.6]
        bx = np.floor(bot[:, 0]).astype(int) - x0
        by = np.floor(bot[:, 1]).astype(int) - ylo
        bz_sup = int(math.floor(zmin_w)) - 1
        sup = float(world_occ[bx, by, bz_sup].mean()) if len(bx) else 1.0
        ext_hits_total += hits
        item_report[it['name']] = {
            'hits': hits,
            'support': round(sup, 3),
            'min_xyz': [round(float(pts[:, i].min()), 2) for i in range(3)],
            'max_xyz': [round(float(pts[:, i].max()), 2) for i in range(3)],
        }

    # 也檢查貨艙口蓋（僅 z=72..73）不撞其他物件
    hatch_pts = np.array([[260.0 + x + 0.5, 122.0 + y + 0.5, 72.0 + z + 0.5] for (x, y, z) in hatch_cells], float)
    hatch_hits = check_hits(hatch_pts)

    summary = {
        'magazine_cells': mag_spec['cells'],
        'magazine_cavities': mag_cav_count,
        'barrel_count': len(barrel_models),
        'barrel_hits': barrel_hits,
        'cargo_hatch_hits': hatch_hits,
        'ext_hits_total': ext_hits_total,
        'items': item_report,
    }
    if probe:
        summary['probe'] = probe
        print(json.dumps(summary, ensure_ascii=False))
        return

    assert mag_cav_count == 0, f'magazine cavities: {mag_cav_count}'
    assert barrel_hits == 0, f'barrel hits: {barrel_hits}'
    assert hatch_hits == 0, f'hatch hits: {hatch_hits}'
    assert ext_hits_total == 0, f'ext hits: {item_report}'

    og = os.path.join(design, 'masks', 'gear')
    os.makedirs(og, exist_ok=True)
    with open(os.path.join(og, 'magazine.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 明鄭一號大鳥船 火藥庫\n')
        for (x, y, z), c in sorted(mag_cells.items()):
            f.write(f'{x},{y},{z},{c}\n')
    with open(os.path.join(og, 'cargo_hatch.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 明鄭一號大鳥船 貨艙口蓋\n')
        for (x, y, z), c in sorted(hatch_cells.items()):
            f.write(f'{x},{y},{z},{c}\n')

    gear_spec = {
        'magazine': mag_spec,
        'cargo_hatch': hatch_spec,
        'ext_items': ext_items,
    }
    gs_p = os.path.join(design, 'gear_spec.json')
    with open(gs_p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(gear_spec, f, ensure_ascii=False, indent=1)
    summary['spec_sha256'] = hashlib.sha256(open(gs_p, 'rb').read()).hexdigest()

    # 出圖 sheet08_gear_v1.png
    im = Image.new('RGB', (shape[0] + 100, (shape[1] + 20) * 2 + 50), (248, 246, 238))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '明鄭一號大鳥船 新圖紙 09：底艙水線下火藥庫（上）與上戰棚／尾樓甲板裝備（下）', fill=(0, 0, 0), font=DL.font(14))
    for ridx, z_ref in enumerate((12, 70)):
        oy = 50 + ridx * (shape[1] + 20)
        for xi_ in range(shape[0]):
            for yi_ in range(shape[1]):
                if wall_col[xi_, yi_, z_ref + 2] > 0:
                    d.point((30 + xi_, oy + yi_), fill=(120, 90, 60))
    # 畫火藥庫 & 裝備框
    for (x, y, z), c in mag_cells.items():
        if z == 14:
            d.point((30 + x - x0, 50 + y - ylo), fill=DL.rgb(c))
    oy2 = 50 + shape[1] + 20
    for name, rep in item_report.items():
        xlo_r, ylo_r = int(rep['min_xyz'][0]) - x0 + 30, int(rep['min_xyz'][1]) - ylo + oy2
        xhi_r, yhi_r = int(rep['max_xyz'][0]) - x0 + 30, int(rep['max_xyz'][1]) - ylo + oy2
        d.rectangle((xlo_r, ylo_r, xhi_r, yhi_r), outline=(30, 90, 180), width=2)
    im.save(os.path.join(design, 'sheet08_gear_v1.png'))

    with open(os.path.join(design, 'verify_gear.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()

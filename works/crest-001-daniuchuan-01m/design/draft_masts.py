# 明鄭一號大鳥船 新圖紙 06（TASK-1316 步驟 7）：三桅（前／大／尾）、6 根 yard=course 主下帆桁與 22 根弧形實體竹篾（Ship_Masts ＋ Ship_Battens）
#   用法：python -I -X utf8 draft_masts.py <design 資料夾> [--probe=shift_mast_fore=-3 | --probe=short_batten]
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_decks as DD

sys.stdout.reconfigure(encoding='utf-8')

ROACH = (0.16, 0.05)  # [aft leech bulge, fore luff bulge]
TIP_MARGIN = 1.6      # 竹篾兩端突出帆邊至少 >= 1.5 格


def lerp(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def roach_row(corners, roach, v):
    # corners = [aft_top, fore_top, fore_bot, aft_bot]
    a = lerp(corners[0], corners[3], v)
    b = lerp(corners[1], corners[2], v)
    bulge = 0.0 if v in (0.0, 1.0) else math.sin(math.pi * (v ** 0.85))
    return lerp(a, b, -bulge * roach[0]), lerp(a, b, 1.0 + bulge * roach[1])


def mast_axis(spec, z):
    return float(spec['x']) + (float(z) - float(spec['heel_z'])) * math.tan(math.radians(float(spec['rake_deg'])))


def main():
    design = HERE
    probe = None
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            probe = a.split('=', 1)[1]
        elif not a.startswith('--'):
            design = a

    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    C = {k: DL.V(v) for k, v in plan['hull_build']['colors'].items()}
    WOOD, TRIM, RED, GOLD = C['hull'], C['trim'], C['red'], C['gold']

    # 座標空間：與船殼／甲板共用 512×256×512
    # 讀入船殼＋甲板佔位以驗證桅桿穿孔零重疊
    zmax = int(math.ceil(L.top_max)) + 16
    x0 = int(math.floor(L.xa_min)) - 12
    x1 = int(math.ceil(L.xf_max)) + 16
    half = int(math.ceil(L.B)) + 10
    ylo = L.YC - half
    yhi = L.YC + half
    shape = (x1 - x0 + 1, yhi - ylo + 1, zmax + 1)
    wall_col, _ = DD.load_carved_shell(design, plan, L, x0, ylo, shape)
    base_occ = wall_col > 0
    for folder in ('decks', 'ladders', 'rooms'):
        pdir = os.path.join(design, 'masks', folder)
        if os.path.isdir(pdir):
            for fn in os.listdir(pdir):
                if fn.endswith('.vox.txt'):
                    arr = np.loadtxt(os.path.join(pdir, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
                    if arr.size:
                        xi, yi, zi = arr[:, 0] - x0, arr[:, 1] - ylo, arr[:, 2]
                        m = (xi >= 0) & (xi < shape[0]) & (yi >= 0) & (yi < shape[1]) & (zi >= 0) & (zi < shape[2])
                        base_occ[xi[m], yi[m], zi[m]] = True

    # ── 1. 三根桅子作品體素（與桅孔及甲板零重疊）──
    masts_spec = {
        'fore': {
            'name': '前桅', 'set': 2, 'battens': 7,
            'x': 374, 'rake_deg': 5.0, 'heel_z': 12, 'len': 238, 'r': [2.6, 1.4],
            'upper': {'z': 228.5, 'aft_len': 56, 'fore_len': 20, 'pitch_deg': 15.0},
            'lower': {'z': 94.5, 'aft_len': 72, 'fore_len': 25, 'pitch_deg': 0.0},
        },
        'main': {
            'name': '主桅', 'set': 1, 'battens': 9,
            'x': 246, 'rake_deg': -2.0, 'heel_z': 12, 'len': 310, 'r': [3.6, 1.8],
            'upper': {'z': 296.5, 'aft_len': 74, 'fore_len': 26, 'pitch_deg': 16.0},
            'lower': {'z': 112.5, 'aft_len': 96, 'fore_len': 34, 'pitch_deg': 0.0},
        },
        'mizzen': {
            'name': '尾桅', 'set': 3, 'battens': 6,
            'x': 96, 'rake_deg': -4.0, 'heel_z': 48, 'len': 166, 'r': [2.2, 1.1],
            'upper': {'z': 198.5, 'aft_len': 36, 'fore_len': 13, 'pitch_deg': 15.0},
            'lower': {'z': 116.5, 'aft_len': 46, 'fore_len': 17, 'pitch_deg': 0.0},
        },
    }

    if probe == 'shift_mast_fore=-3':
        masts_spec['fore']['x'] -= 3

    mast_cells = {}
    mast_anchors = {}
    mast_overlaps = {}

    for mk, sp in masts_spec.items():
        pts = {}
        z0 = int(sp['heel_z'])
        z1 = z0 + int(sp['len']) - 1
        r0, r1 = sp['r']
        ov = 0
        for zw in range(z0, z1 + 1):
            t = (zw - z0) / max(sp['len'] - 1, 1)
            r = r0 + (r1 - r0) * t
            cx = mast_axis(sp, zw + 0.5)
            # 桅箍、頂帽上色
            is_band = (zw % 28 in (0, 1))
            is_cap = (zw >= z1 - 4)
            col = RED if zw >= z1 - 2 else (GOLD if is_cap else (TRIM if is_band else WOOD))
            r_box = int(math.ceil(r + 0.5))
            for dx in range(-r_box, r_box + 1):
                xw = int(math.floor(cx)) + dx
                for dy in range(-r_box, r_box + 1):
                    yw = YC + dy
                    if (xw + 0.5 - cx) ** 2 + (yw + 0.5 - (YC + 0.5)) ** 2 <= r * r:
                        xi, yi = xw - x0, yw - ylo
                        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= zw < shape[2] and base_occ[xi, yi, zw]:
                            ov += 1
                        pts[(xw, yw, zw)] = col
        # 桅盤架（hound trestletree 小托樑，位於 upper 上方 2 格作滑輪與支索固定）
        zh = int(round(sp['upper']['z'])) + 4
        hx = int(round(mast_axis(sp, zh)))
        for dx in range(-2, 3):
            for dy in (-2, -1, 1, 2):
                pts.setdefault((hx + dx, YC + dy, zh), TRIM)

        mast_cells[mk] = pts
        mast_overlaps[mk] = ov

        tx = int(round(mast_axis(sp, z1)))
        ux = int(round(mast_axis(sp, sp['upper']['z'])))
        lx = int(round(mast_axis(sp, sp['lower']['z'])))
        mast_anchors[mk] = {
            'heel': [int(sp['x']), YC, z0],
            'hound': [hx, YC, zh],
            'top': [tx, YC, z1 - 1],
            'cap': [tx, YC, z1],
            'yard-upper': [ux, YC, int(round(sp['upper']['z']))],
            'yard-lower': [lx, YC, int(round(sp['lower']['z']))],
        }

    # ── 2. 帆桁模板 (yard-upper / yard-lower) 與竹篾模板 (batten-*) ──
    hull_id = plan['guns_build']['hull']
    yard_templates = {}
    batten_templates = {}
    placements = {}
    envelopes = []

    for mk, sp in masts_spec.items():
        # 每根桅用下桁幾何為模板（length = aft_len + fore_len），上桁透過 scale=(ratio_x, 1, 1) 與 rotate=(0, pitch, 0) 共用或各自建
        # 各自建立 upper 與 lower 模板，讓轉軸、arm-P/S、earing-aft/fore、sling、pivot 全無縮放歪斜
        frames = {}
        for pos in ('upper', 'lower'):
            u_sp = sp[pos]
            aft_l, fore_l = int(u_sp['aft_len']), int(u_sp['fore_len'])
            span = aft_l + fore_l
            # 局部格：x = 2 .. span+2 (寬 2×2 橫截面 y in (1,2), z in (2,3))，留前後各 2 格餘裕
            piv_x = 2 + aft_l
            sz = (span + 5, 4, 5)
            y_vox = {}
            for lx in range(2, span + 3):
                is_band = ((lx - piv_x) % 16 == 0)
                col = GOLD if lx in (2, span + 2) else (TRIM if is_band else WOOD)
                for ly in (1, 2):
                    for lz in (2, 3):
                        y_vox[(lx, ly, lz)] = col
            w_id = f'{hull_id}-yard-{mk}-{pos}'
            y_anc = {
                'arm-P': [2, 1, 2],
                'arm-S': [span + 2, 1, 2],
                'earing-aft': [2, 1, 2],
                'earing-fore': [span + 2, 1, 2],
                'sling': [piv_x, 1, 2],
                'pivot': [piv_x, 1, 2],
            }
            yard_templates[f'{mk}-{pos}'] = {
                'work': w_id, 'title': f'明鄭一號大鳥船 {sp["name"]}{"上" if pos=="upper" else "下"}桁（0.1 m）',
                'size': list(sz), 'voxels': y_vox, 'anchors': y_anc, 'span': span, 'aft_len': aft_l, 'fore_len': fore_l,
            }

            at_z = float(u_sp['z'])
            at_x = mast_axis(sp, at_z)
            at_pos = [round(at_x, 3), YC + 0.5, round(at_z, 3)]
            piv_f = [float(piv_x) + 0.5, 1.5, 2.5]
            pitch = float(u_sp['pitch_deg'])
            # rotate=(0, +pitch, 0): dx>0 -> z - dx*sin(pitch)（艏降），dx<0 -> z + |dx|*sin(pitch)（艉升）
            c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
            e_aft = [at_pos[0] + (-aft_l) * c, at_pos[1], at_pos[2] - (-aft_l) * s]
            e_fore = [at_pos[0] + fore_l * c, at_pos[1], at_pos[2] - fore_l * s]
            frames[pos] = {
                'label': f'yard-{pos}', 'work': w_id, 'at': at_pos, 'pivot': piv_f,
                'rotate': [0.0, pitch, 0.0], 'scale': [1.0, 1.0, 1.0],
                'ends': [e_aft, e_fore],
                'meta': {
                    'kind': 'yard', 'mast': mk, 'yard': 'course', 'sail': f'{mk}-junk',
                    'length_ft': round(span * 0.1 / 0.3048, 2), 'diameter_in': 10 if pos == 'lower' else 8,
                    'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0,
                },
            }

        # 竹篾模板（batten-{mk}，0.1 m/格，material=bamboo，render=pole）
        aft_base = int(sp['lower']['aft_len']) + 4
        fore_base = int(sp['lower']['fore_len']) + 4
        bat_len = aft_base + fore_base
        bat_piv_x = 2 + aft_base
        bat_vox = {}
        for lx in range(2, bat_len + 3):
            bat_vox[(lx, 2, 2)] = 104 if (lx % 12 == 0) else 177  # 竹節點著深色、竹身淡黃木色
        bat_w_id = f'{hull_id}-batten-{mk}'
        batten_templates[mk] = {
            'work': bat_w_id,
            'title': f'明鄭一號大鳥船 {sp["name"]}硬篷竹篾（0.1 m；material=bamboo）',
            'size': [bat_len + 5, 5, 5],
            'voxels': bat_vox,
            'anchors': {'pivot': [bat_piv_x, 2, 2], 'arm-P': [2, 2, 2], 'arm-S': [bat_len + 2, 2, 2]},
            'left_span': float(aft_base),
            'right_span': float(fore_base),
            'pivot': [float(bat_piv_x) + 0.5, 2.5, 2.5],
        }

        corners = (*frames['upper']['ends'], *reversed(frames['lower']['ends']))
        count = int(sp['battens'])
        lower_width = math.dist(*frames['lower']['ends'])
        rods = []
        for m in range(1, count + 1):
            v = m / (count + 1)
            left, right = roach_row(corners, ROACH, v)
            z_est = 0.5 * (left[2] + right[2])
            mx_z = mast_axis(sp, z_est)
            u = (mx_z - left[0]) / max(right[0] - left[0], 1e-6)
            at_pt = lerp(left, right, u)
            pitch_rod = -math.degrees(math.atan2(right[2] - left[2], right[0] - left[0]))
            open_l = math.dist(at_pt, left)
            open_r = math.dist(at_pt, right)
            l_sp = float(aft_base)
            r_sp = float(fore_base)
            # 同時滿足張帆扇弧 roach 與收帆縮寬到下桁時的雙重突出 ≥ 1.5 格
            sc_x = max((max(open_l, u * lower_width) + TIP_MARGIN) / l_sp,
                       (max(open_r, (1.0 - u) * lower_width) + TIP_MARGIN) / r_sp)
            if probe == 'short_batten' and mk == 'main' and m == 1:
                sc_x = 0.55  # 故意縮短竹篾作為反證測試
            ov_l = l_sp * sc_x - open_l
            ov_r = r_sp * sc_x - open_r
            rods.append({
                'label': f'batten-{m:02d}',
                'work': bat_w_id,
                'at': [round(x, 3) for x in at_pt],
                'pivot': batten_templates[mk]['pivot'],
                'rotate': [0.0, round(pitch_rod, 3), 0.0],
                'scale': [round(sc_x, 4), 1.0, 1.0],
                'overhang': [round(ov_l, 3), round(ov_r, 3)],
                'span': [round(l_sp * sc_x, 3), round(r_sp * sc_x, 3)],
                'meta': {
                    'kind': 'yard', 'yard': 'batten', 'batten': m, 'mast': mk, 'sail': f'{mk}-junk',
                    'material': 'bamboo', 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0,
                    'length_ft': round((l_sp + r_sp) * sc_x * 0.1 / 0.3048, 2), 'diameter_in': 4,
                },
            })

        # 計算縱向包絡（含 roach 曲線＋所有竹篾端點）以驗各桅間淨距 ≥ 4 格
        xs_env = [pt[0] for i in range(101) for pt in roach_row(corners, ROACH, i / 100.0)]
        for rd in rods:
            cx_r = rd['at'][0]
            cos_r = math.cos(math.radians(rd['rotate'][1]))
            xs_env.extend((cx_r - rd['span'][0] * cos_r, cx_r + rd['span'][1] * cos_r))
        envelopes.append((mk, min(xs_env), max(xs_env)))

        # 計算帆面積（梯形基礎 + 拱腹）
        h_mid = frames['upper']['at'][2] - frames['lower']['at'][2]
        w_up = math.dist(*frames['upper']['ends'])
        w_lo = math.dist(*frames['lower']['ends'])
        area_m2 = round((0.5 * (w_up + w_lo) * h_mid) * 0.01 * 1.10, 1)

        placements[mk] = {
            'mast_name': sp['name'],
            'sail': f'{mk}-junk',
            'set': sp['set'],
            'battens': count,
            'roach': list(ROACH),
            'area_m2': area_m2,
            'corners': corners,
            'frames': frames,
            'rods': rods,
        }

    # 計算相鄰兩帆包絡縱向間距（fore 最小 x - main 最大 x；main 最小 x - mizzen 最大 x）
    gaps = [envelopes[i][1] - envelopes[i + 1][2] for i in range(len(envelopes) - 1)]
    min_overhang = min(min(rd['overhang']) for pl in placements.values() for rd in pl['rods'])

    summary = {
        'mast_overlaps_with_hull_decks': mast_overlaps,
        'mast_cells': {mk: len(v) for mk, v in mast_cells.items()},
        'total_yards_course': sum(len(pl['frames']) for pl in placements.values()),
        'total_battens': sum(len(pl['rods']) for pl in placements.values()),
        'min_batten_overhang_cells': round(min_overhang, 3),
        'longitudinal_gaps_cells': [round(g, 2) for g in gaps],
        'envelopes_x': {mk: [round(x_lo, 2), round(x_hi, 2)] for mk, x_lo, x_hi in envelopes},
        'sail_area_m2': {mk: pl['area_m2'] for mk, pl in placements.items()},
        'total_sail_area_m2': round(sum(pl['area_m2'] for pl in placements.values()), 1),
    }

    if probe:
        summary['probe'] = probe
        print(json.dumps(summary, ensure_ascii=False))
        return

    assert max(mast_overlaps.values()) == 0, f'mast overlap: {mast_overlaps}'
    assert min_overhang >= 1.5, f'batten overhang too small: {min_overhang}'
    assert min(gaps) >= 4.0, f'sail gaps too tight: {gaps}'

    # ── 3. 寫出所有清單與 placements ──
    om = os.path.join(design, 'masks', 'masts')
    os.makedirs(om, exist_ok=True)
    for fn in os.listdir(om):
        if fn.endswith('.vox.txt'):
            os.remove(os.path.join(om, fn))

    def dump_dict(path, pts_dict, head):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for (x, y, z), c in sorted(pts_dict.items()):
                f.write(f'{x},{y},{z},{c}\n')
        return [len(pts_dict), hashlib.sha256(open(path, 'rb').read()).hexdigest()]

    lists = {}
    for mk, pts in mast_cells.items():
        lists[f'mast-{mk}'] = dump_dict(os.path.join(om, f'mast-{mk}.vox.txt'), pts, f'# 明鄭一號大鳥船 {mk} 桅\n')
    for k, tpl in yard_templates.items():
        lists[f'yard-{k}'] = dump_dict(os.path.join(om, f'yard-{k}.vox.txt'), tpl['voxels'], f'# {tpl["title"]}\n')
    for mk, tpl in batten_templates.items():
        lists[f'batten-{mk}'] = dump_dict(os.path.join(om, f'batten-{mk}.vox.txt'), tpl['voxels'], f'# {tpl["title"]}\n')

    masts_spec_out = {
        'masts': {
            mk: {
                'work': f'{hull_id}-mast-{mk}',
                'link': masts_spec[mk]['name'],
                'title': f'明鄭一號大鳥船 {masts_spec[mk]["name"]}（0.1 m）',
                'mask': f'mast-{mk}.vox.txt',
                'anchors': mast_anchors[mk],
                'meta': {'kind': 'mast', 'mast': mk},
            } for mk in masts_spec
        },
        'yard_templates': {
            k: {**v, 'voxels': len(v['voxels']), 'mask': f'yard-{k}.vox.txt'}
            for k, v in yard_templates.items()
        },
        'batten_templates': {
            mk: {**v, 'voxels': len(v['voxels']), 'mask': f'batten-{mk}.vox.txt'}
            for mk, v in batten_templates.items()
        },
        'placements': placements,
    }
    with open(os.path.join(design, 'masts_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(masts_spec_out, f, ensure_ascii=False, indent=1)

    # 出圖 sheet06_masts_v1.png
    Hmax = 340
    im = Image.new('RGB', (shape[0] + 120, Hmax + 40), (248, 246, 238))
    d = ImageDraw.Draw(im)
    d.text((20, 12), '明鄭一號大鳥船 新圖紙 06：三桅、6 根 yard=course 橫桁與 22 根弧形竹篾 (Roach)', fill=(0, 0, 0), font=DL.font(15))
    ox = 30 - x0
    oy_bot = Hmax + 10
    # 畫船殼剪影
    for xi_ in range(shape[0]):
        for zi_ in range(shape[2]):
            if wall_col[xi_, :, zi_].any():
                d.point((xi_ + 30, oy_bot - zi_), fill=(182, 145, 85))
    # 畫三桅
    for mk, pts in mast_cells.items():
        for (xw, yw, zw), c in pts.items():
            if 0 <= xw + ox < im.width and 0 <= oy_bot - zw < im.height:
                d.point((xw + ox, oy_bot - zw), fill=DL.rgb(c))
    # 畫帆緣 roach、竹篾與帆桁
    for mk, pl in placements.items():
        # 帆面弧線
        for i in range(100):
            la, ra = roach_row(pl['corners'], ROACH, i / 100.0)
            lb, rb = roach_row(pl['corners'], ROACH, (i + 1) / 100.0)
            d.line((la[0] + ox, oy_bot - la[2], lb[0] + ox, oy_bot - lb[2]), fill=(195, 160, 100), width=1)
            d.line((ra[0] + ox, oy_bot - ra[2], rb[0] + ox, oy_bot - rb[2]), fill=(195, 160, 100), width=1)
        for pos in ('upper', 'lower'):
            e0, e1 = pl['frames'][pos]['ends']
            d.line((e0[0] + ox, oy_bot - e0[2], e1[0] + ox, oy_bot - e1[2]), fill=(90, 50, 20), width=3)
        for rd in pl['rods']:
            cx_r, cz_r = rd['at'][0], rd['at'][2]
            pr = math.radians(rd['rotate'][1])
            c, s = math.cos(pr), math.sin(pr)
            p_aft = (cx_r - rd['span'][0] * c + ox, oy_bot - (cz_r + rd['span'][0] * s))
            p_fore = (cx_r + rd['span'][1] * c + ox, oy_bot - (cz_r - rd['span'][1] * s))
            d.line((*p_aft, *p_fore), fill=(210, 110, 20), width=2)
    im.save(os.path.join(design, 'sheet06_masts_v1.png'))

    summary['lists'] = lists
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

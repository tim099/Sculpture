# 福建趕繒船 新圖紙 08（TASK-1314 步驟 10）：彈藥庫、火藥桶 ×4、主艙蓋、舵艙門、廚房大灶、小艇、絞盤、羅經櫃、尾燈
#   出處：kaguya-shachuan-01m/design/draft_gear.py ＋ meadow-tungning-trader-01m/design/gear.py（適配趕繒船尺寸與甲板動線）
#   用法：python -I -X utf8 draft_gear.py <design 資料夾> [--probe=shift=boat:-10|shift_hatch=cargo-hatch:2]
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
from wio import export_list

HULL = 'kotoko-ganzengchuan-01m'
ASM = HULL + '-assembly'


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def src_cells(work):
    return export_list(work, links='none')[:, :3].astype(float)


def parts_boxes():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts',
                        '--arg', f'work={ASM}', '--arg', f'out={out}'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
        P = json.load(open(out, encoding='utf-8'))
    return {m['path']: m['box'] for m in P['models']}


def corners(cells):
    o = np.array([[0.5, 0.5, 0.5]] + [[(0.2, 0.8)[k & 1], (0.2, 0.8)[(k >> 1) & 1], (0.2, 0.8)[(k >> 2) & 1]] for k in range(8)])
    return (cells[:, None, :] + o[None]).reshape(-1, 3)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
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

    A = export_list(ASM, links='all')
    occ = set(map(tuple, A[:, :3].astype(int).tolist()))
    boxes = parts_boxes()

    # ── 1. 底艙艉端彈藥庫襯牆（x=111 貼齊 x=112 第一隔艙壁，留 y=94..98 z=9..25 中央門洞防閉腔與卡路）──
    zf = int(plan['decks']['hold']['floor'])  # 9
    z_beam_bot = int(plan['decks']['main']['floor']) - 3  # 32（樑底下一格 32）
    x_fwd = 111
    wall = {}
    for z in range(zf, z_beam_bot):
        h = float(L.hb(np.array([x_fwd + 0.5]), np.array([z + 0.5]))[0])
        if h < 0:
            continue
        for y in range(YC - int(h), YC + int(h) + 1):
            if (x_fwd, y, z) in occ:
                continue
            if abs(y - YC) <= 2 and z < zf + 17:
                continue
            wall[(x_fwd, y, z)] = 168  # 銅皮防火襯壁

    # 量測底艙彈藥庫空間（x=92..110, z=9..24）求 blast 重心固定點
    air = [(x, y, z) for x in range(94, 110) for z in range(zf, zf + 13)
           for y in range(YC - 16, YC + 17)
           if (x, y, z) not in occ and float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0]) - 3 >= abs(y - YC)]
    c_air = np.array(air, float).mean(0)
    blast = min(air, key=lambda p: (p[0] - c_air[0]) ** 2 + (p[1] - c_air[1]) ** 2 + (p[2] - c_air[2]) ** 2)
    mag_anchors = {'blast': [int(blast[0]), int(blast[1]), int(blast[2])], 'door': [x_fwd, YC, zf]}

    # ── 2. 主艙口格柵木蓋（cargo-hatch，0.05 m 子作品，30×26×3 -> scale 0.5 壓蓋 x=207..221, y=90..102 圍板頂 z=37）──
    hatch_spec = {'name': '貨艙蓋', 'work_suffix': 'cargo-hatch', 'title': '福建趕繒船 主艙口格柵蓋（0.05 m）',
                  'host': 'deck-main', 'host_link': '甲板-main', 'at': [207, 90, 37], 'open': [15, 13], 'coaming_top': 36}
    NX, NY, NZ = hatch_spec['open'][0] * 2, hatch_spec['open'][1] * 2, 3  # 30×26×3
    h_cells = {}
    for lx in range(NX):
        for ly in range(NY):
            is_edge = lx in (0, 1, NX - 2, NX - 1) or ly in (0, 1, NY - 2, NY - 1)
            if is_edge:
                for lz in (0, 1, 2):
                    h_cells[(lx, ly, lz)] = 104
            else:
                if ly % 2 == 0:
                    h_cells[(lx, ly, 1)] = 177
                if lx % 2 == 0:
                    h_cells[(lx, ly, 2)] = 177
                if ly in (NY // 2 - 1, NY // 2) or lx in (NX // 2 - 1, NX // 2):
                    h_cells[(lx, ly, 0)] = 104
                    h_cells[(lx, ly, 1)] = 104
    h_at = list(hatch_spec['at'])
    if probe and probe.startswith('shift_hatch='):
        nm, dv = probe.split('=', 1)[1].rsplit(':', 1)
        if nm == hatch_spec['work_suffix']:
            h_at[0] += int(dv)
    wc = {(h_at[0] + lx // 2, h_at[1] + ly // 2, h_at[2] + lz // 2) for lx, ly, lz in h_cells}
    hatch_hit = len(wc & occ)
    ring = [(x, y, hatch_spec['coaming_top']) for x in range(207, 222) for y in (90, 102)] + \
           [(x, y, hatch_spec['coaming_top']) for x in (207, 221) for y in range(91, 102)]
    hatch_ring_solid = sum(1 for k in ring if k in occ)
    hatch_open_below = sum(1 for x in range(208, 221) for y in range(91, 102) if (x, y, 34) not in occ)

    # ── 3. 所有外部模型清冊（4 火藥桶＋舵艙門＋廚房大灶＋小艇＋絞盤＋羅經櫃＋2 尾燈）──
    models = []
    # (a) 4 具火藥桶（掛彈藥庫）
    for i, (px, py) in enumerate(((99.5, 89.5), (99.5, 103.5), (105.5, 89.5), (105.5, 103.5)), 1):
        models.append({'name': f'桶-{i:02d}', 'host': 'magazine', 'host_link': '彈藥庫',
                       'source_work': 'basecamp-frigate-constitution-01m-powder-barrel',
                       'at': [px, py, float(zf)], 'pivot': [11.0, 11.0, 0.0], 'scale': 0.2,
                       'meta': {'kind': 'powder', 'powder_lb': 100}})

    # (b) 舵艙門（掛甲板-main，複用藍鯊號通用門，x=113 貼 x=112 隔艙門框 y=92..100 z=35..51，門洞 112 格）
    models.append({'name': '舵艙門', 'host': 'deck-main', 'host_link': '甲板-main',
                   'source_work': 'gura-pinas-01m-door',
                   'at': [113.0, 92.0, 35.0], 'pivot': [0.0, 0.0, 0.0],
                   'scale': [0.5, 0.6429, 0.5313],
                   'meta': {'kind': 'door', 'open': 'side', 'open_deg': 100}})

    # (c) 廚房大灶（掛甲板-main 左舷開放空位 x=146..159, y=79..88, z=35，避開砲門 #1/#2 與梯井）
    models.append({'name': '廚房大灶', 'host': 'deck-main', 'host_link': '甲板-main',
                   'source_work': 'kaguya-gloire-01m-galley',
                   'at': [152.5, 83.5, 35.0], 'pivot': [22.0, 16.0, 0.0], 'scale': 0.3,
                   'meta': {'kind': 'galley'}})

    # (d) 艦載舢舨（掛甲板-main 前腰中線 x=224.7..264.3, y=90.8..102.2, z=35，兩舷留 2.7 m 走道）
    models.append({'name': '舢舨', 'host': 'deck-main', 'host_link': '甲板-main',
                   'source_work': 'basecamp-ember-01m-boat',
                   'at': [244.5, 96.5, 35.0], 'pivot': [90.0, 26.0, 0.0], 'scale': 0.22,
                   'meta': {'kind': 'boat', 'boat': 'cutter', 'length_m': 4}})

    # (e) 主絞盤（掛甲板-main 後段 x=123.5..133.5, y=91.5..101.5, z=35，避開舵艙門與下艙梯）
    models.append({'name': '絞盤', 'host': 'deck-main', 'host_link': '甲板-main',
                   'source_work': 'basecamp-ember-01m-capstan',
                   'at': [128.5, 96.5, 35.0], 'pivot': [40.0, 40.0, 0.0], 'scale': 0.14,
                   'meta': {'kind': 'capstan'}})

    # (f) 羅經櫃（掛甲板-poop x=93.5, y=96.5, z=54，避開步驟 11 舵柄區 x<=82 與兩舷迴旋砲 x=86）
    models.append({'name': '羅經櫃', 'host': 'deck-poop', 'host_link': '甲板-poop',
                   'source_work': 'summit-night-falcon-01m-binnacle',
                   'at': [93.5, 96.5, 54.0], 'pivot': [9.0, 13.0, 0.0], 'scale': 0.2,
                   'meta': {'kind': 'binnacle'}})

    # (g) 雙尾舷燈（掛甲板-poop，立於尾樓望樓金欄兩端角柱頂 (70.5, 76.5/116.5, 73.0)）
    for snm, yw in (('尾燈-P', 76.5), ('尾燈-S', 116.5)):
        models.append({'name': snm, 'host': 'deck-poop', 'host_link': '甲板-poop',
                       'source_work': 'gura-tridente-01m-lantern',
                       'at': [70.5, yw, 73.0], 'pivot': [8.5, 8.5, 0.0], 'scale': 0.3,
                       'meta': {'kind': 'light', 'light_color': '#ffae52'}})

    # 對全部模型做格心＋八角碰撞檢查、與砲模型外框互斥檢查、底面支承檢查
    own_paths = {m['host_link'] + '/' + m['name'] for m in models} | {hatch_spec['host_link'] + '/' + hatch_spec['name']}
    other_boxes = {p: b for p, b in boxes.items() if p not in own_paths}

    cache = {}
    rows, bad = [], []
    for m in models:
        w = m['source_work']
        if w not in cache:
            cache[w] = corners(src_cells(w))
        P0 = cache[w]
        piv = np.array(m['pivot'], float)
        sc = np.array(m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3, float)
        at = np.array(m['at'], float)
        if probe and probe.startswith('shift='):
            nm, dv = probe.split('=', 1)[1].rsplit(':', 1)
            if m['name'] == nm or m['source_work'].endswith('-' + nm):
                at[0] += float(dv)
        Pw = (P0 - piv) * sc + at
        hit = sum(1 for p in np.floor(Pw).astype(int).tolist() if tuple(p) in occ or tuple(p) in wall or tuple(p) in wc)
        lo, hi = Pw.min(0), Pw.max(0)
        box_hit = [p for p, b in other_boxes.items()
                   if not (hi[0] <= b[0] or lo[0] >= b[3] or hi[1] <= b[1] or lo[1] >= b[4] or hi[2] <= b[2] or lo[2] >= b[5])]
        bot = Pw[Pw[:, 2] <= lo[2] + 0.25]
        sup = float(np.mean([any(tuple(np.floor(p - [0, 0, 1]).astype(int)) in S for S in (occ, wall, wc)) for p in bot]))
        row = {'name': m['name'], 'host': m['host'], 'hit_samples': hit, 'other_box_overlap': box_hit,
               'support': round(sup, 3), 'box': [round(float(v), 2) for v in list(lo) + list(hi)]}
        rows.append(row)
        if hit or box_hit or sup < 0.5:
            bad.append(row)

    # 檢查模型間彼此不重疊（box 互斥）
    for i in range(len(rows)):
        bi = rows[i]['box']
        for j in range(i + 1, len(rows)):
            bj = rows[j]['box']
            if not (bi[3] <= bj[0] or bi[0] >= bj[3] or bi[4] <= bj[1] or bi[1] >= bj[4] or bi[5] <= bj[2] or bi[2] >= bj[5]):
                bad.append({'pair_overlap': [rows[i]['name'], rows[j]['name']]})

    hatch_bad = (hatch_hit > 0 or hatch_ring_solid < len(ring) or hatch_open_below == 0)

    if probe:
        print(json.dumps({'probe': probe, 'bad': bad, 'hatch_hit': hatch_hit}, ensure_ascii=False))
        return

    assert not bad and not hatch_bad, f'檢查未過：{bad=} {hatch_hit=} {hatch_ring_solid}/{len(ring)}'

    od = os.path.join(design, 'masks', 'gear')
    os.makedirs(od, exist_ok=True)
    p_mag = os.path.join(od, 'magazine.vox.txt')
    with open(p_mag, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 10：底艙彈藥庫銅襯壁（x=111 貼齊 x=112 隔艙壁、留中門洞 y=94..98）x,y,z,color\n')
        for k in sorted(wall):
            f.write(f'{k[0]},{k[1]},{k[2]},{wall[k]}\n')

    p_hat = os.path.join(od, 'cargo_hatch.vox.txt')
    with open(p_hat, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 福建趕繒船 步驟 10：主艙口木格柵艙蓋（0.05 m 30×26×3）x,y,z,color\n')
        for k in sorted(h_cells):
            f.write(f'{k[0]},{k[1]},{k[2]},{h_cells[k]}\n')

    # hoist 指明通往三層火砲甲板的所有梯子
    mag_meta = {
        'kind': 'magazine',
        'pos': 'aft',
        'powder_lb': 100 * sum(1 for m in models if m['meta'].get('kind') == 'powder'),
        'hoist': '甲板-main/梯子#hold,甲板-poop/梯子#poop,甲板-fore/梯子#fore',
    }
    hatch_info = {
        'work': f'{HULL}-cargo-hatch',
        'title': hatch_spec['title'],
        'name': hatch_spec['name'],
        'host': hatch_spec['host'],
        'size': [NX, NY, NZ],
        'cells': len(h_cells),
        'vox_file': 'masks/gear/cargo_hatch.vox.txt',
        'at': [float(v) for v in hatch_spec['at']],
        'pivot': [0.0, 0.0, 0.0],
        'scale': 0.5,
        'anchors': {'hinge-a': [0, 0, 0], 'hinge-b': [NX - 1, 0, 0]},
        'meta': {'kind': 'door', 'open': 'up', 'open_deg': 100},
    }

    placement = {
        'magazine_wall_cells': len(wall),
        'magazine_anchors': mag_anchors,
        'magazine_meta': mag_meta,
        'hatch': hatch_info,
        'models': models,
    }
    verify = {
        'magazine_wall_cells': len(wall),
        'magazine_air_cells': len(air),
        'powder_barrels': 4,
        'powder_lb': mag_meta['powder_lb'],
        'hatch': {'cells': len(h_cells), 'hit_occ': hatch_hit, 'coaming_solid': f'{hatch_ring_solid}/{len(ring)}', 'open_below': hatch_open_below},
        'models': rows,
        'bad': bad,
        'sha256': {'magazine': sha256_file(p_mag), 'cargo_hatch': sha256_file(p_hat)},
    }
    with open(os.path.join(design, 'gear_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(placement, f, ensure_ascii=False, indent=2)
    with open(os.path.join(design, 'verify_gear.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(verify, f, ensure_ascii=False, indent=2)
    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

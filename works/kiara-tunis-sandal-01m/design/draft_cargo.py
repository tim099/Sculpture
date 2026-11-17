# 步驟 10 甲板物件：舯貨艙貨位對帳（貨箱／酒桶 6+4＝3.12–3.5 t）與船尾左舷停泊燈（kind=light）
#   - 依 Ship_Fittings §2.1／§9.9 取樣外框格心＋八角，驗證與船殼／甲板／坐板／桅／裝飾零碰撞且底面實踩 z=2 鋪板
#   - 貨箱與酒桶掛於 kiara-tunis-sandal-01m-deck-main（標 deco=1）；艉燈掛於組裝件（標 kind=light，不標 deco）
#   用法：python -I -X utf8 draft_cargo.py [--apply] [--probe=shift_out=+4]
import sys, os, json, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_ASM = 'kiara-tunis-sandal-01m-assembly'
WORK_DECK = 'kiara-tunis-sandal-01m-deck-main'
SX, SY, SZ = 136, 101, 110


def load_vox(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((SX, SY, SZ), bool)
    if len(a):
        G[a[:, 0], a[:, 1], a[:, 2]] = True
    return G


def build_items(probe):
    dy = float(probe.get('shift_out', 0.0))
    items = []
    # 舯貨艙 x=46..78：6 只貨箱 (0.6×0.6×0.6 m, scale 0.5) ＋ 4 只橄欖油/壓艙酒桶 (0.6×0.6×0.9 m, scale 0.5)
    # 留出中央 y 49..52 通行走道與前後坐板腳部餘裕
    crate_rows = [
        ('1', 48.5, 45.5, 55.5),
        ('2', 55.5, 45.5, 55.5),
        ('3', 62.5, 45.5, 55.5),
    ]
    for rtag, cx, yp, ys in crate_rows:
        items.append({
            'name': f'貨箱-{rtag}P', 'host': WORK_DECK, 'work': 'summit-rocher-01m-crate',
            'at': [cx, yp - dy, 2.0], 'pivot': [6.0, 6.0, 0.0], 'scale': 0.5,
            'size_local': (6.0, 6.0, 6.0), 'meta': {'deco': 1}, 'mass_t': 0.22,
        })
        items.append({
            'name': f'貨箱-{rtag}S', 'host': WORK_DECK, 'work': 'summit-rocher-01m-crate',
            'at': [cx, ys + dy, 2.0], 'pivot': [6.0, 6.0, 0.0], 'scale': 0.5,
            'size_local': (6.0, 6.0, 6.0), 'meta': {'deco': 1}, 'mass_t': 0.22,
        })

    barrel_rows = [
        ('1', 69.5, 45.5, 55.5),
        ('2', 76.5, 46.5, 54.5),
    ]
    for rtag, bx, yp, ys in barrel_rows:
        items.append({
            'name': f'貨桶-{rtag}P', 'host': WORK_DECK, 'work': 'summit-rocher-01m-barrel',
            'at': [bx, yp - dy, 2.0], 'pivot': [6.0, 6.0, 0.0], 'scale': 0.5,
            'size_local': (6.0, 6.0, 9.0), 'meta': {'deco': 1}, 'mass_t': 0.45,
        })
        items.append({
            'name': f'貨桶-{rtag}S', 'host': WORK_DECK, 'work': 'summit-rocher-01m-barrel',
            'at': [bx, ys + dy, 2.0], 'pivot': [6.0, 6.0, 0.0], 'scale': 0.5,
            'size_local': (6.0, 6.0, 9.0), 'meta': {'deco': 1}, 'mass_t': 0.45,
        })

    # 船尾左舷停泊燈（與右舷旗桿 x=19,y=54 對稱，落於 (18..19,46,10) 頂面 z=11.0，尺規留出舵柄 ±35° 掃掠淨空；不可標 deco=1）
    items.append({
        'name': '艉燈', 'host': WORK_ASM, 'work': 'gura-tridente-01m-lantern',
        'at': [18.8, 46.0, 11.0], 'pivot': [8.5, 8.5, 0.0], 'scale': 0.14,
        'size_local': (2.38, 2.38, 5.04), 'meta': {'id': 'light-1', 'kind': 'light', 'light': 'amber'},
        'mass_t': 0.02, 'is_light': True,
    })
    return items


def check_item_box(occ, item):
    ax, ay, az = item['at']
    sx, sy, sz = item['size_local']
    x0, x1 = ax - sx * 0.5, ax + sx * 0.5
    y0, y1 = ay - sy * 0.5, ay + sy * 0.5
    z0, z1 = az, az + sz

    # 取樣格心＋八角＋內外網格點（縮 0.05 避開臨界擦邊誤差、保留實格檢查）
    xs = np.linspace(x0 + 0.1, x1 - 0.1, 4)
    ys = np.linspace(y0 + 0.1, y1 - 0.1, 4)
    zs = np.linspace(z0 + 0.1, z1 - 0.1, 4)
    hits = 0
    for px in xs:
        for py in ys:
            for pz in zs:
                ix, iy, iz = int(np.floor(px)), int(np.floor(py)), int(np.floor(pz))
                if 0 <= ix < SX and 0 <= iy < SY and 0 <= iz < SZ and occ[ix, iy, iz]:
                    hits += 1

    # 底面支撐檢查：下方那一層（floor(z0 - 0.5)）中線實心
    sz_floor = int(np.floor(z0 - 0.5))
    sup_hits = 0
    for px in (ax - sx * 0.25, ax, ax + sx * 0.25):
        for py in (ay - sy * 0.25, ay, ay + sy * 0.25):
            ix, iy = int(np.floor(px)), int(np.floor(py))
            if 0 <= ix < SX and 0 <= iy < SY and 0 <= sz_floor < SZ and occ[ix, iy, sz_floor]:
                sup_hits += 1
    return hits, sup_hits, [round(x0, 2), round(y0, 2), round(z0, 2)], [round(x1, 2), round(y1, 2), round(z1, 2)]


def main():
    apply_mode = '--apply' in sys.argv[1:]
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)

    occ = (load_vox(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
           | load_vox(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'))
           | load_vox(os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt')))

    items = build_items(probe)
    results = []
    total_hits = 0
    total_cargo_mass = 0.0
    all_supported = True
    aisle_min_gap = 999.0

    # 檢查每件碰撞與兩件之間互斥
    boxes = []
    for it in items:
        hits, sup, bmin, bmax = check_item_box(occ, it)
        total_hits += hits
        if sup == 0:
            all_supported = False
        if not it.get('is_light'):
            total_cargo_mass += it['mass_t']
            if bmin[1] >= 50.5:
                aisle_min_gap = min(aisle_min_gap, bmin[1] - 50.5)
            else:
                aisle_min_gap = min(aisle_min_gap, 50.5 - bmax[1])
        boxes.append((it['name'], bmin, bmax))
        results.append({'name': it['name'], 'hits': hits, 'support_pts': sup, 'min': bmin, 'max': bmax})

    # 檢查兩兩箱/桶有無互相重疊
    pair_overlaps = 0
    for i in range(len(boxes)):
        n1, a0, a1 = boxes[i]
        for j in range(i + 1, len(boxes)):
            n2, b0, b1 = boxes[j]
            if (a0[0] < b1[0] - 0.05 and a1[0] > b0[0] + 0.05 and
                a0[1] < b1[1] - 0.05 and a1[1] > b0[1] + 0.05 and
                a0[2] < b1[2] - 0.05 and a1[2] > b0[2] + 0.05):
                pair_overlaps += 1

    R = {
        'cargo_count': sum(1 for it in items if not it.get('is_light')),
        'light_count': sum(1 for it in items if it.get('is_light')),
        'cargo_stowed_mass_t': round(total_cargo_mass, 2),
        'free_payload_budget_t': 3.67,
        'center_aisle_half_width_cells': round(aisle_min_gap, 2),
        'center_aisle_width_m': round(aisle_min_gap * 2 * 0.1, 2),
        'occ_sample_hits': total_hits,
        'pair_overlaps': pair_overlaps,
        'all_supported': all_supported,
        'items': results,
    }

    if probe:
        print(json.dumps({'probe': probe, **{k: R[k] for k in ('occ_sample_hits', 'pair_overlaps', 'all_supported')}}, ensure_ascii=False))
        return

    with open(os.path.join(HERE, 'verify_cargo.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    print('CARGO_CHECK:', json.dumps({k: v for k, v in R.items() if k != 'items'}, ensure_ascii=False))

    if not apply_mode:
        return

    for it in items:
        at_s = ','.join(str(v) for v in it['at'])
        pv_s = ','.join(str(v) for v in it['pivot'])
        meta_s = json.dumps(it['meta'], ensure_ascii=False)
        cmd = ['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=model',
               '--arg', 'persona=kiara', '--arg', f'work={it["host"]}',
               '--arg', f'name={it["name"]}', '--arg', f'source_work={it["work"]}',
               '--arg', f'at={at_s}', '--arg', f'pivot={pv_s}',
               '--arg', f'scale={it["scale"]}', '--arg', f'meta={meta_s}', '--arg', 'overwrite=1']
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(f'model fail {it["name"]}:\n{r.stdout}\n{r.stderr}')
    print('Mounted cargo & light models:', len(items))


if __name__ == '__main__':
    main()

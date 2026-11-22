# 明鄭一號大鳥船 新圖紙 08（TASK-1316 步驟 9）：砲具（船殼牆環、甲板尾索環）與 24 門輪式砲 120 條砲索
import json, math, os, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_decks as DD

sys.stdout.reconfigure(encoding='utf-8')


def main():
    design = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else HERE)
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    GF = plan['gunfittings_build']
    YC = L.YC

    zmax = int(math.ceil(L.top_max)) + 16
    x0 = int(math.floor(L.xa_min)) - 12
    x1 = int(math.ceil(L.xf_max)) + 16
    half = int(math.ceil(L.B)) + 10
    ylo = L.YC - half
    yhi = L.YC + half
    shape = (x1 - x0 + 1, yhi - ylo + 1, zmax + 1)

    wall_col, _ = DD.load_carved_shell(design, plan, L, x0, ylo, shape)
    hull_occ = wall_col > 0
    # 同步迴旋砲切口
    sw_c = np.loadtxt(os.path.join(design, 'masks', 'guns', 'swivel_rail_carve.vox.txt'), delimiter=',', comments='#', dtype=int, encoding='utf-8')
    if sw_c.size:
        hull_occ[sw_c[:, 0] - x0, sw_c[:, 1] - ylo, sw_c[:, 2]] = False

    world_occ = hull_occ.copy()
    for folder in ('decks', 'ladders', 'rooms', 'deco', 'masts'):
        pdir = os.path.join(design, 'masks', folder)
        if not os.path.isdir(pdir):
            continue
        for fn in os.listdir(pdir):
            if not fn.endswith('.vox.txt'):
                continue
            if folder == 'masts' and not fn.startswith('mast-'):
                continue
            arr = np.loadtxt(os.path.join(pdir, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
            if arr.size:
                xi, yi, zi = arr[:, 0] - x0, arr[:, 1] - ylo, arr[:, 2]
                m = (xi >= 0) & (xi < shape[0]) & (yi >= 0) & (yi < shape[1]) & (zi >= 0) & (zi < shape[2])
                world_occ[xi[m], yi[m], zi[m]] = True

    guns = json.load(open(os.path.join(design, 'guns_placement.json'), encoding='utf-8'))
    gf_cells = {}
    gf_anchors = {}
    ropes = []
    DECK_LINK = {'main': '甲板-main', 'upper': '甲板-upper', 'poop': '甲板-poop'}
    COL = int(GF['ring']['color'])

    def place_free(xw, yw, zw):
        xi, yi = xw - x0, yw - ylo
        if 0 <= xi < shape[0] and 0 <= yi < shape[1] and 0 <= zw < shape[2]:
            return (not world_occ[xi, yi, zw]) and ((xw, yw, zw) not in gf_cells)
        return False

    for g in guns:
        if g['type'] == 'pierrier':
            continue
        nm = g['name']
        dk = g['deck']
        z_floor = int(plan['decks'][dk]['floor'])
        sign = 1 if g['side'] == 'S' else -1
        bx, by, bz = g['breech_world']
        tx, ty, tz = g['train_world']
        z_eye = int(round(g['eye_aft_world'][2]))
        gx = int(round(g['at'][0]))

        # 1) 兩枚舷壁砲環（分別位於砲口中心兩側 offset，貼著船殼內側牆面、高於甲板 ≥ 3 格）
        wall_names = {}
        for side_dx, lbl in ((-1, 'aft'), (1, 'fwd')):
            found_w = None
            for off in GF['ring']['offset']:
                xw = gx + side_dx * int(off)
                if not (0 <= xw - x0 < shape[0]):
                    continue
                # 由船舯往外側掃該側 hull_occ 最內緣，並放於其內側相鄰 1 格
                ys = np.nonzero(hull_occ[xw - x0, :, z_eye])[0]
                if not len(ys):
                    ys = np.nonzero(hull_occ[xw - x0, :, z_floor + 2])[0]
                if not len(ys):
                    continue
                # 取靠近 YC 但大於半寬的一側內面
                if sign > 0:
                    y_cand = int(ys[ys + ylo > YC + 8].min()) + ylo - 1
                else:
                    y_cand = int(ys[ys + ylo < YC - 8].max()) + ylo + 1
                for dz_try in (0, 1, -1):
                    zt = max(z_floor + 2, z_eye + dz_try)
                    if place_free(xw, y_cand, zt):
                        found_w = (xw, y_cand, zt)
                        break
                if found_w:
                    break
            assert found_w is not None, f'無法放舷壁環：{nm}-{lbl}'
            an_nm = f'gf-{nm}-{lbl}'
            gf_cells[found_w] = COL
            gf_anchors[an_nm] = list(found_w)
            wall_names[lbl] = an_nm

        # 2) 1 枚甲板尾索環（砲尾正後方沿 -sign * back 放於甲板上 z=z_floor）
        found_d = None
        for bk in GF['deck_ring']['back']:
            yw_t = int(math.floor(ty)) - sign * int(bk)
            for lat in GF['deck_ring']['lat']:
                xw_t = int(math.floor(tx)) + int(lat)
                xi, yi = xw_t - x0, yw_t - ylo
                if 0 <= xi < shape[0] and 0 <= yi < shape[1]:
                    if world_occ[xi, yi, z_floor - 1] and place_free(xw_t, yw_t, z_floor):
                        found_d = (xw_t, yw_t, z_floor)
                        break
            if found_d:
                break
        assert found_d is not None, f'無法放甲板環：{nm}'
        an_deck = f'gf-{nm}-deck'
        gf_cells[found_d] = COL
        gf_anchors[an_deck] = list(found_d)

        # 3) 該門砲的 5 條砲索（2 breeching, 2 tackle, 1 train）
        lk = DECK_LINK[dk]
        gf_lk = GF['link']
        rp_b = GF['ropes']['breeching']
        rp_t = GF['ropes']['tackle']
        rp_tr = GF['ropes']['train']
        for lbl, eye_k in (('aft', 'eye-aft'), ('fwd', 'eye-fwd')):
            ropes.append({
                'name': f'gun-{nm}-breech-{lbl}',
                'from': f'{gf_lk}/{wall_names[lbl]}',
                'to': f'model:{lk}/{nm}/breech',
                'slack': rp_b['slack'], 'thickness': rp_b['thickness'], 'color': rp_b['color'], 'group': rp_b['group'],
                'meta': {'kind': 'gun'},
            })
            ropes.append({
                'name': f'gun-{nm}-tackle-{lbl}',
                'from': f'{gf_lk}/{wall_names[lbl]}',
                'to': f'model:{lk}/{nm}/{eye_k}',
                'slack': rp_t['slack'], 'thickness': rp_t['thickness'], 'color': rp_t['color'], 'group': rp_t['group'],
                'meta': {'kind': 'gun'},
            })
        ropes.append({
            'name': f'gun-{nm}-train',
            'from': f'model:{lk}/{nm}/train',
            'to': f'{gf_lk}/{an_deck}',
            'slack': rp_tr['slack'], 'thickness': rp_tr['thickness'], 'color': rp_tr['color'], 'group': rp_tr['group'],
            'meta': {'kind': 'gun'},
        })

    # 檢查鏡像對稱性與輸出
    gf_set = set(gf_cells.keys())
    mirror_diff = sum(1 for (x, y, z) in gf_set if (x, 2 * YC - y, z) not in gf_set)
    ov = sum(1 for (x, y, z) in gf_set if world_occ[x - x0, y - ylo, z])
    assert ov == 0, f'gunfittings overlap: {ov}'

    gdir = os.path.join(design, 'masks', 'guns')
    os.makedirs(gdir, exist_ok=True)
    gp = os.path.join(gdir, 'gunfittings.vox.txt')
    with open(gp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 步驟 9 砲具（舷壁環與甲板尾索環）\n')
        for (x, y, z), c in sorted(gf_cells.items()):
            f.write(f'{x},{y},{z},{c}\n')

    spec = {
        'work': GF['work'],
        'link': GF['link'],
        'title': GF['title'],
        'cells': len(gf_cells),
        'anchors': gf_anchors,
        'ropes': ropes,
        'mirror_diff': mirror_diff,
        'vox_sha256': hashlib.sha256(open(gp, 'rb').read()).hexdigest(),
    }
    sp_p = os.path.join(design, 'gunfittings_spec.json')
    with open(sp_p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    print(json.dumps({
        'gunfittings_cells': len(gf_cells),
        'anchors': len(gf_anchors),
        'ropes': len(ropes),
        'overlap': ov,
        'mirror_diff': mirror_diff,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()

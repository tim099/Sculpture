# 光榮號 階段十 機艙：主機（HRCR 臥式雙缸）、會轉的曲柄、螺旋槳軸、八座鍋爐與煙道 —— plan.json engine。
#   抄自拿破崙號 kotoko-napoleon-01m/design/draft_engine.py（kotoko）；光榮號改：
#     主機換成臥式回行連桿（缸在左舷、十字頭與導軌在右舷、連桿回到軸上的曲柄；曲軸 ＝ 螺旋槳軸、沒有齒輪）；
#     曲柄一開始就是獨立的一件（之後當會轉的外部模型，拿破崙號是事後 split_gears 拆的）；鍋爐一組八座、沿中線一條燒火通道、兩舷各四座；
#     煙道收到唯一那根煙囪（x 563、半徑 13、煙囪底 z 89）。
#   現況 ＝ 組裝件 links=all（藏本階段的關聯 ⇒ 落格之後重跑讀到的還是同一份），z < 120。
#   只放在船殼裡面的空氣（每個 (x, z) 從中線往兩舷走到第一格實心為止）；落在現況實心上的不放（照實數）。
#   輸出：masks/engine/{engine,crank,shaft,boilers}.vox.txt（子作品座標；crank 用整船的框 ⇒ 世界座標）、engine_placement.json、verify_engine.json、sheet07_engine_v1.png
#   用法：python -I -X utf8 draft_engine.py <design> [--probe=nometa|shift:<件>:<dz>]
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_io
import mio

NX, NY, NZ = 1200, 400, 120
YC = 200
HIDE = '機艙-主機,機艙-鍋爐,螺旋槳軸,甲板-engine,甲板-lower/梯子-機艙'   # 後兩條是地板、梯子（在本件之後）
X0, X1 = 160, 670


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
    plan = plan_io.load(D)
    E = plan['engine']
    C = E['colors']
    try:
        A = mio.export_list(mio.ASM, 'all', ('hide_links=' + HIDE,))
    except SystemExit:
        A = mio.export_list(mio.ASM, 'all')                              # 還沒落格：那幾條關聯不存在
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True

    inside = np.zeros((NX, NY, NZ), bool)
    for x in range(X0, X1):
        for z in range(NZ):
            if occ[x, YC, z]:
                continue
            ys = np.nonzero(occ[x, YC:, z])[0]
            yn = np.nonzero(occ[x, :YC + 1, z][::-1])[0]
            if not len(ys) or not len(yn):
                continue
            inside[x, YC - yn[0] + 1:YC + ys[0], z] = True

    parts = {k: {} for k in ('engine', 'crank', 'shaft', 'boilers')}
    skipped = {k: 0 for k in parts}

    def put(k, x, y, z, c):
        if not (0 <= x < NX and 0 <= y < NY and 0 <= z < NZ) or not inside[x, y, z]:
            skipped[k] += 1
            return
        parts[k][(x, y, z)] = c

    SH = E['shaft']
    sz, sr = SH['z'], SH['r']
    on_shaft = lambda y, z: (y - YC) ** 2 + (z - sz) ** 2 <= sr ** 2

    # ── 主機（HRCR）──
    G = E['engine']
    ex0, ex1 = G['x']
    for x in range(ex0, ex1 + 1):                                        # 底座：船底到 bed_top（跟機艙地板同高 ⇒ 站得上去）
        for y in range(YC - 45, YC + 46):
            for z in range(0, G['bed_top'] + 1):
                if inside[x, y, z]:
                    parts['engine'][(x, y, z)] = C['steel']
    cy = G['cyl']
    r = cy['r']
    for cx in cy['xs']:
        for x in range(cx - r, cx + r + 1):                              # 缸（缸軸沿 y，臥在左舷）；外端蓋一圈黃銅
            for z in range(cy['z'] - r, cy['z'] + r + 1):
                d2 = (x - cx) ** 2 + (z - cy['z']) ** 2
                if d2 > r ** 2:
                    continue
                for y in range(cy['y'][0], cy['y'][1] + 1):
                    put('engine', x, y, z, C['brass'] if y == cy['y'][0] and d2 >= (r - 1) ** 2 else C['iron'])
        ch = cy['chest']                                                 # 汽門箱：貼著缸頂往上到 z 55，頂面黃銅
        ztop = cy['z'] + r + ch['h']
        for x in range(cx - ch['half_x'], cx + ch['half_x'] + 1):
            zs = cy['z'] + int(math.floor(math.sqrt(r ** 2 - (x - cx) ** 2)))
            for y in range(ch['y'][0], ch['y'][1] + 1):
                for z in range(zs + 1, ztop + 1):
                    put('engine', x, y, z, C['brass'] if z == ztop else C['iron'])
        sp = cy['support']                                               # 缸座：船底到缸底
        for x in range(cx - sp['half_x'], cx + sp['half_x'] + 1):
            zb = cy['z'] - int(math.floor(math.sqrt(r ** 2 - (x - cx) ** 2)))
            for y in range(sp['y'][0], sp['y'][1] + 1):
                for z in range(G['bed_top'] + 1, zb):
                    put('engine', x, y, z, C['steel'])
                for z in range(0, G['bed_top'] + 1):
                    if inside[x, y, z]:
                        parts['engine'][(x, y, z)] = C['steel']
        cross = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
        for dz in (-G['rods']['dz'], G['rods']['dz']):                   # 活塞桿：每缸兩根，從缸的右舷端跨過軸的上下到十字頭
            for y in range(cy['y'][1] + 1, G['crosshead']['y'][0]):
                for ddx, ddz in cross:
                    put('engine', cx + ddx, y, cy['z'] + dz + ddz, C['steel'])
        xh = G['crosshead']                                              # 十字頭
        for x in range(cx - xh['half_x'], cx + xh['half_x'] + 1):
            for y in range(xh['y'][0], xh['y'][1] + 1):
                for z in range(xh['z'][0], xh['z'][1] + 1):
                    put('engine', x, y, z, C['steel'])
        gd = G['guide']                                                  # 導軌架：從船底到十字頭頂上
        for x in range(cx - gd['half_x'], cx + gd['half_x'] + 1):
            for y in range(gd['y'][0], gd['y'][1] + 1):
                for z in range(0, gd['z_top'] + 1):
                    put('engine', x, y, z, C['iron'])
        cr = G['conrod']                                                 # 連桿：十字頭「回」到曲柄（停在曲柄銷外一格；曲柄會轉，連桿不轉 —— 只是畫面）
        for y in range(cr['y'][0], cr['y'][1] + 1):
            for ddx, ddz in cross:
                put('engine', cx + ddx, y, sz + ddz, C['steel'])
    for px in G['pedestals_x']:                                          # 主軸承座：地板到軸底下
        for x in range(px - 1, px + 2):
            for y in range(YC - 5, YC + 6):
                for z in range(G['bed_top'] + 1, sz - sr):
                    put('engine', x, y, z, C['iron'])

    # ── 曲柄（會轉的外部模型；整船的框）：每缸一組 ＝ 兩片曲臂＋曲柄銷，停在 +y（朝十字頭）──
    K = G['crank']
    for cx in K['xs']:
        for x in list(range(cx - K['half_x'], cx - K['half_x'] + K['web_t'])) + list(range(cx + K['half_x'] - K['web_t'] + 1, cx + K['half_x'] + 1)):
            for y in range(YC - K['web_half'], YC + K['throw'] + K['web_half'] + 1):
                for z in range(sz - K['web_half'], sz + K['web_half'] + 1):
                    if not on_shaft(y, z):
                        put('crank', x, y, z, C['steel'])
        for x in range(cx - K['half_x'] + K['web_t'], cx + K['half_x'] - K['web_t'] + 1):
            for y in range(YC + K['throw'] - K['pin_r'], YC + K['throw'] + K['pin_r'] + 1):
                for z in range(sz - K['pin_r'], sz + K['pin_r'] + 1):
                    if (y - YC - K['throw']) ** 2 + (z - sz) ** 2 <= K['pin_r'] ** 2:
                        put('crank', x, y, z, C['brass'])
    for p in parts['crank']:
        parts['engine'].pop(p, None)

    # ── 螺旋槳軸（曲軸那一段也是它）──
    for x in range(SH['x'][0], SH['x'][1] + 1):
        for y in range(YC - sr, YC + sr + 1):
            for z in range(sz - sr, sz + sr + 1):
                if on_shaft(y, z):
                    parts['engine'].pop((x, y, z), None)
                    put('shaft', x, y, z, C['steel'])
    for px in range(SH['plummer_from'], ex0 - 5, SH['plummer_every']):    # 軸承座：船底到軸底下
        for x in range(px, px + 3):
            for y in range(YC - 3, YC + 4):
                for z in range(0, sz - sr):
                    if inside[x, y, z]:
                        parts['shaft'][(x, y, z)] = C['iron']

    # ── 鍋爐一組八座（兩舷各四、爐門朝中線的燒火通道）與煙道 ──
    BO = E['boilers']
    P = parts['boilers']
    an_b = {}
    bi = 0
    w = BO['width']
    for s in (-1, 1):
        y_in = BO['y_in'] if s < 0 else 2 * YC - BO['y_in']               # 爐門那一面（P 188、S 212）
        y0, y1 = (y_in - w, y_in - 1) if s < 0 else (y_in + 1, y_in + w)
        door_y = y1 if s < 0 else y0
        for (x0, x1) in BO['xs']:
            for x in range(x0, x1 + 1):
                for y in range(y0, y1 + 1):
                    u = (y - y0) / float(y1 - y0)
                    ztop = BO['z'][1] - int(round(BO['crown'] * (2 * u - 1) ** 2))
                    for z in range(BO['z'][0], ztop + 1):
                        c = C['iron']
                        if y == door_y:
                            for xd in ((x0 + x1) / 2.0 - 6, (x0 + x1) / 2.0 + 6):   # 每座兩個爐門：火色、鐵框
                                if abs(x - xd) <= 2.5 and 17 <= z <= 23:
                                    c = C['fire'] if abs(x - xd) <= 1.5 and 18 <= z <= 22 else C['steel']
                        put('boilers', x, y, z, c)
            for x in range(x0 + 2, x1 - 1):                              # 鍋爐座：鍋爐底下到船底（磚）
                for y in range(y0 + 2, y1 - 1):
                    for z in range(0, BO['z'][0]):
                        if inside[x, y, z]:
                            P[(x, y, z)] = C['brick']
            bi += 1
            xc = (x0 + x1) // 2
            an_b['boiler-%d' % bi] = [xc, (y0 + y1) // 2, (BO['z'][0] + BO['z'][1]) // 2]
            an_b['stoke-%d' % bi] = [xc, door_y - 4 * s, BO['z'][0]]       # 爐門前往燒火通道 4 格、鍋爐底那一層（機艙地板上第一格空氣）
    gx0, gx1 = BO['xs'][0][0], BO['xs'][-1][1]
    gay = YC - (BO['y_in'] - w)                                           # 整組半寬（y 157–243 ⇒ 43）
    cx0, fx = (gx0 + gx1) / 2.0, float(BO['funnel_x'])
    zu0, zu1 = BO['uptake_z']

    def shape(z):
        t = (z - zu0) / float(zu1 - zu0)
        return cx0 + (fx - cx0) * t, (gx1 - gx0) / 2.0 + (BO['funnel_r'] - (gx1 - gx0) / 2.0) * t, gay + (BO['funnel_r'] - gay) * t, 8 + (2 - 8) * t
    SH_ = {z: shape(z) for z in range(zu0 - 1, zu1 + 2)}

    def inn(x, y, z):
        if z < zu0 or z > zu1:
            return False
        cxz, ax, ay, pw = SH_[z]
        return (abs(x + 0.5 - cxz) / ax) ** pw + (abs(y - YC) / ay) ** pw <= 1

    def ring(x, y, z):
        return inn(x, y, z) and not (inn(x + 1, y, z) and inn(x - 1, y, z) and inn(x, y + 1, z) and inn(x, y - 1, z))
    for z in range(zu0, zu1 + 1):
        cxz, ax, ay, pw = SH_[z]
        for x in range(int(cxz - ax) - 1, int(cxz + ax) + 2):
            for y in range(int(YC - ay) - 1, int(YC + ay) + 2):
                if not inn(x, y, z):
                    continue
                edge = ring(x, y, z)
                side = z < zu1 and (not inn(x, y, z + 1) or ring(x, y, z + 1))
                if z == zu0 or edge or side:
                    put('boilers', x, y, z, C['iron'])
    an_b['uptake'] = [int(round(cx0)), YC, zu0]

    # ── 封小空腔：本階段新夾出來、≤ 20 格的 ⇒ 填進鍋爐件（煙道頂跟煙囪壁、樑之間的縫）；更大的照實報 ──
    U0 = occ[X0:X1].copy(); U1 = U0.copy()
    for Pp in parts.values():
        for (x, y, z) in Pp:
            U1[x - X0, y, z] = True
    newcav = (ndimage.binary_fill_holes(U1) & ~U1) & ~(ndimage.binary_fill_holes(U0) & ~U0)
    labc, nc = ndimage.label(newcav)
    sealed, big_cav = [], []
    for i in range(1, nc + 1):
        q = np.argwhere(labc == i)
        if len(q) > 20:
            big_cav.append([int(q[0][0]) + X0, int(q[0][1]), int(q[0][2]), int(len(q))])
            continue
        for (x, y, z) in q:
            P[(int(x) + X0, int(y), int(z))] = C['iron']
        sealed.append([int(q[0][0]) + X0, int(q[0][1]), int(q[0][2]), int(len(q))])

    if probe and probe.startswith('shift:'):
        _, k, dz = probe.split(':')
        parts[k] = {(x, y, z + int(dz)): c for (x, y, z), c in parts[k].items()}

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_outside': skipped}
    allc = {}
    over_parts = 0
    for k, Pp in parts.items():
        for p in Pp:
            if p in allc:
                over_parts += 1
            allc[p] = k
    over_base = {k: sum(1 for p in Pp if occ[p]) for k, Pp in parts.items()}
    U = occ[X0:X1].copy(); Ub = U.copy()
    for (x, y, z) in allc:
        U[x - X0, y, z] = True
    lab, _ = ndimage.label(U)
    base_l = set(np.unique(lab[Ub]).tolist()) - {0}
    floating = {k: sum(1 for (x, y, z) in Pp if lab[x - X0, y, z] not in base_l) for k, Pp in parts.items()}
    FLT = [(x, y, z) for (x, y, z) in allc if lab[x - X0, y, z] not in base_l]
    holes = int((ndimage.binary_fill_holes(U) & ~U).sum() - (ndimage.binary_fill_holes(Ub) & ~Ub).sum())
    asym = {k: sum(1 for (x, y, z), c in Pp.items() if Pp.get((x, 2 * YC - y, z)) != c) for k, Pp in parts.items()}
    # 軸線不斷：aft 那一頭（船殼借格）到 fwd，軸心那一列每一格要嘛是軸、要嘛是現況實心（deadwood）
    gap = [x for x in range(SH['x'][0], SH['x'][1] + 1) if (x, YC, sz) not in parts['shaft'] and not occ[x, YC, sz]]

    os.makedirs(os.path.join(D, 'masks', 'engine'), exist_ok=True)
    place = {}
    KM = E['crank_model']
    works = {'engine': (E['engine'].get('work', 'kaguya-gloire-01m-engine'), '機艙-主機', '光榮號 主機（HRCR 臥式雙缸、直接驅動、2,500 ihp；0.1 m）', G['meta']),
             'crank': (KM['work'], KM['model'], '光榮號 主機的曲柄（會轉的外部模型；0.1 m、整船的框）', KM['meta']),
             'shaft': (SH['work'], SH['link'], '光榮號 螺旋槳軸與軸承座（0.1 m）', SH['meta']),
             'boilers': (BO['work'], BO['link'], '光榮號 鍋爐 8 座與煙道（0.1 m）', BO['meta'])}
    ck = K['xs']
    anchors = {'engine': {'core': [(ex0 + ex1) // 2, YC, sz],
                          'cyl-1': [cy['xs'][0], (cy['y'][0] + cy['y'][1]) // 2, cy['z']], 'cyl-2': [cy['xs'][1], (cy['y'][0] + cy['y'][1]) // 2, cy['z']],
                          # 站位：機匠站兩缸之間的地板上（左舷看缸、右舷看十字頭）—— 要幾個人由遊戲那側定
                          'tend-1': [(ck[0] + ck[1]) // 2, 185, G['bed_top'] + 1], 'tend-2': [(ck[0] + ck[1]) // 2, 215, G['bed_top'] + 1]},
               'crank': {'spin-a': [ck[0] - K['half_x'], YC, sz], 'spin-b': [ck[1] + K['half_x'], YC, sz]},
               'shaft': {'aft': [SH['x'][0], YC, sz], 'fwd': [SH['x'][1], YC, sz]},
               'boilers': an_b}
    for k, Pp in parts.items():
        if k == 'crank':
            org, size = [0, 0, 0], [1200, 400, 800]                      # 整船的框（同螺旋槳、拿破崙號的齒輪）：at ＝ pivot ＝ 轉軸格心
        else:
            org, size = mio.bbox(Pp)
            for v in anchors[k].values():
                for i in range(3):
                    if v[i] < org[i]:
                        size[i] += org[i] - v[i]; org[i] = v[i]
                    if v[i] >= org[i] + size[i]:
                        size[i] = v[i] - org[i] + 1
        n, h = mio.write_local(os.path.join(D, 'masks', 'engine', k + '.vox.txt'), Pp, org, '# 光榮號 %s（draft_engine.py；子作品座標，原點 ＝ 組裝件 %s）\n' % (k, org))
        an_local = {nm: [v[i] - org[i] for i in range(3)] for nm, v in anchors[k].items()}
        bad_an = [nm for nm, v in anchors[k].items() if not all(0 <= v[i] - org[i] < size[i] for i in range(3))]
        wk, link, title, meta = works[k]
        if probe == 'nometa' and k == 'engine':
            meta = {kk: vv for kk, vv in meta.items() if kk != 'kind'}
        place[k] = {'work': wk, 'link': link, 'title': title, 'at': org, 'size': size, 'cells': n, 'sha256': h, 'meta': meta, 'anchors': an_local, 'anchors_world': anchors[k]}
        if k == 'crank':
            pv = [ck[0] + 0.5 + (ck[1] - ck[0]) / 2.0, YC + 0.5, sz + 0.5]
            place[k].update({'model': True, 'host': KM['host'], 'pivot': pv, 'model_at': pv})
        near = {nm: sum(1 for (x, y, z) in Pp if (x - v[0]) ** 2 + (y - v[1]) ** 2 + (z - v[2]) ** 2 <= 64) for nm, v in anchors[k].items()}
        by = {}
        for c in Pp.values():
            by[str(c)] = by.get(str(c), 0) + 1
        R['parts'][k] = {'cells': n, 'colors': dict(sorted(by.items())), 'box': [org, size], 'overlap_base': over_base[k], 'floating': floating[k],
                         'asym': asym[k], 'anchor_out_of_box': bad_an, 'near_anchor_cells_r8': near}
    R['overlap_between_parts'] = over_parts
    R['new_cavities'] = holes
    R['sealed'] = sealed
    R['big_new_cavities'] = big_cav
    R['floating_box'] = (np.array(FLT).min(0).tolist(), np.array(FLT).max(0).tolist()) if FLT else None
    R['shaft_line_gaps'] = gap
    if probe:
        print('probe', probe, json.dumps({k: {kk: v[kk] for kk in ('cells', 'overlap_base', 'floating', 'asym')} for k, v in R['parts'].items()}, ensure_ascii=False),
              'meta', place['engine']['meta'])
        return
    for nm, obj in (('engine_placement.json', place), ('verify_engine.json', R)):
        with open(os.path.join(D, nm), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write('\n')
    sheet(D, occ, parts, anchors)
    print(json.dumps(R, ensure_ascii=False))


def sheet(D, occ, parts, anchors):
    """圖紙：上 ＝ 側面（x–z，中線剖面＋本階段每件的投影），下 ＝ 俯視（x–y，z 0–88 投影）。2 px／格。"""
    from PIL import Image, ImageDraw
    from draft_lines import font
    x0, x1, k = 160, 670, 2
    W = (x1 - x0) * k
    img = Image.new('RGB', (W + 40, 120 * k + 200 * k + 80), (250, 248, 240))
    d = ImageDraw.Draw(img)
    col = {'engine': (60, 60, 70), 'crank': (200, 170, 60), 'shaft': (120, 120, 130), 'boilers': (170, 70, 40)}
    oy1, oy2 = 30, 30 + 120 * k + 30
    sec = occ[x0:x1, YC, :]
    for (xx, zz) in np.argwhere(sec):
        d.rectangle([20 + xx * k, oy1 + (119 - zz) * k, 20 + xx * k + k - 1, oy1 + (119 - zz) * k + k - 1], fill=(200, 195, 185))
    top = occ[x0:x1, 100:300, :89].any(2)
    for (xx, yy) in np.argwhere(top):
        d.point([20 + xx * k, oy2 + yy * k], fill=(205, 200, 190))
    for nm in ('boilers', 'shaft', 'engine', 'crank'):
        for (x, y, z) in parts[nm]:
            d.rectangle([20 + (x - x0) * k, oy1 + (119 - z) * k, 20 + (x - x0) * k + k - 1, oy1 + (119 - z) * k + k - 1], fill=col[nm])
            if 100 <= y < 300:
                d.rectangle([20 + (x - x0) * k, oy2 + (y - 100) * k, 20 + (x - x0) * k + k - 1, oy2 + (y - 100) * k + k - 1], fill=col[nm])
    for nm, an in anchors.items():
        for a, v in an.items():
            px, pz = 20 + (v[0] - x0) * k, oy1 + (119 - v[2]) * k
            d.ellipse([px - 3, pz - 3, px + 3, pz + 3], outline=(0, 120, 200), width=2)
            py = oy2 + (v[1] - 100) * k
            d.ellipse([px - 3, py - 3, px + 3, py + 3], outline=(0, 120, 200), width=2)
    d.text((20, 8), '光榮號 機艙 sheet07 v1 —— 上：中線側面（x %d–%d、z 0–119）；下：俯視（y 100–299）；藍圈 ＝ 固定點' % (x0, x1), fill=(0, 0, 0), font=font(16))
    img.save(os.path.join(D, 'sheet07_engine_v1.png'))


if __name__ == '__main__':
    main()

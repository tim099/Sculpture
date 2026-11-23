# 海鷗號 新圖紙 05（TASK-0024 步驟 7）：桅與三角帆桁
#   出處：星辰號 claude-baghlah-01m/design/draft_masts.py（它出自收穫號 calli-cosecha-01m/design/draft_masts.py：三角帆桁在自己的框裡就做成斜的、
#         模型 rotate 0；foc 桿「不碰任何格的最小仰角」解法出自塔爾塔納）——改寫給海鷗號：桅的軸與截面改用 rig.py（前桅往前傾 8°，跟甲板桅孔同一支），
#         沒有錨纜橫樑、沒有第三段帆桁；船頭那根桿（tack spar）腳躺在船頭平台上。
#   輸入：plan.json（layout.masts、rig_build）、前面每一步的設計清單（船殼 hull_01 ＋ 步驟 6 換色、甲板、艏柱頭）——不讀作品 ⇒ 落格之後重跑一樣。
#   輸出：masks/masts/{main,fore,tack_spar}.vox.txt（子作品、at 0,0,0、整船的框）、masks/yards/lateen-{main,fore}.vox.txt（帆桁子作品，自己的框）、
#         yards_lateen.json（框、固定點）、yards_placement.json（模型放在桅的子作品裡：at／pivot／rotate／scale／meta）、verify_masts.json、sheet05_masts_v1.png
#   用法：python -I -X utf8 draft_masts.py [--probe=pivot=main:-40] [--probe=hole=fore]
#     反向對照（不寫檔）：帆桁吊點上下挪 ⇒「匯入檢查那一段」的桅格數、跟船的距離要變；拿掉一根桅的格 ⇒ 桅孔要報空。
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import rig

sys.stdout.reconfigure(encoding='utf-8')
CELL = 0.1
AX, AY, AZ = 190, 161, 180                 # 組裝件與桅子作品的框


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def load(fn):
    p = os.path.join(HERE, fn)
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def ship_cells():
    occ = {}
    for fn in ('masks/hull/hull_01.vox.txt', 'masks/step6/hull_paint.vox.txt', 'masks/decks/deck_main.vox.txt', 'masks/deco/stem_head.vox.txt'):
        occ.update(load(fn))
    return occ


def main():
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe'))
    plan = HL.load_plan(HERE)
    YC = plan['space']['yc']
    RB = {k: V(v) for k, v in plan['rig_build'].items() if k != 'src'}
    C = RB['colors']
    MH = RB['masthead']
    rows = rig.mast_rows(plan)
    occ = ship_cells()
    deck = load('masks/decks/deck_main.vox.txt')
    parts, skipped, trimmed = {}, {}, {}

    def put(part, k, c):
        if k in occ:
            skipped[part] = skipped.get(part, 0) + 1
            return
        parts.setdefault(part, {})[k] = c

    # ── 桅：rig.py 的截面（跟甲板桅孔同一支）；頂上 h 格見方 3×3、滑輪槽、黑帽 ──
    for key, row in rows.items():
        part = 'mast-' + key
        if probe.get('hole') == key:
            parts[part] = {}
            continue
        for z in range(row['heel_z'], row['top_z']):
            if z < row['top_z'] - MH['h']:
                for k in rig.section(row, z, YC):
                    put(part, k, C['mast'])
            else:
                xc = int(math.floor(rig.axis_x(row, z)))
                for dx in range(-MH['half'], MH['half'] + 1):
                    for dy in range(-MH['half'], MH['half'] + 1):
                        c = C['mast']
                        if dy == 0 and row['top_z'] - 1 - z in MH['sheave']:
                            c = C['sheave']
                        if z >= row['top_z'] - MH['cap_h']:
                            c = C['cap']
                        put(part, (xc + dx, YC + dy, z), c)
        cl = parts.get(part, {})
        if cl:
            G = np.zeros((AX, AY, AZ), bool)
            for k in cl:
                G[k] = True
            lab, n = ndimage.label(G)
            if n > 1:
                big = int(np.argmax(np.bincount(lab.ravel())[1:])) + 1
                drop = [k for k in cl if lab[k] != big]
                for k in drop:
                    del cl[k]
                trimmed[part] = len(drop)

    # ── 船頭那根桿（tack spar）：腳躺在船頭平台上、偏右舷；仰角解「不碰任何格」的最小角 ──
    T = RB['tack_spar']
    Lt = T['len_m'] / CELL
    hx, hdy, hz = T['heel']
    X0, Yt, Z0 = hx + 0.0, YC + hdy, hz + T['r0']
    others = set(occ) | {k for p in parts.values() for k in p}

    def spar(alpha):
        a = math.radians(alpha)
        u = (math.cos(a), math.sin(a))
        cells = {}
        for x in range(int(X0) - 2, int(X0 + Lt) + 3):
            for z in range(int(Z0) - 3, int(Z0 + Lt * u[1]) + 4):
                px, pz = x + 0.5 - X0, z + 0.5 - Z0
                t = px * u[0] + pz * u[1]
                if t < 0 or t > Lt:
                    continue
                r = T['r0'] + (T['r1'] - T['r0']) * t / Lt
                d2 = (px - t * u[0]) ** 2 + (pz - t * u[1]) ** 2
                for dy in range(-2, 3):
                    if d2 + dy * dy <= r * r:
                        cells[(x, Yt + dy, z)] = t
        return cells

    alpha = None
    for k in range(0, 601):
        a_ = k * 0.05
        if not any(c in others for c in spar(a_)):
            alpha = round(a_, 2)
            break
    if alpha is None:
        raise SystemExit('✗ tack spar: 30° 以內找不到不碰格的仰角')
    sc = spar(alpha)
    rest = sorted({x for (x, y, z) in sc if (x, y, z - 1) in occ})
    fm = parts.get('mast-fore', {})
    touch = sorted({x for (x, y, z) in sc if (x, y - 1, z) in fm or (x, y + 1, z) in fm})
    lash_x = set()
    if rest:
        lash_x |= {rest[0], rest[-1]}
    if touch:
        lash_x |= {touch[len(touch) // 2]}
    for k, t in sc.items():
        put('tack-spar', k, C['lashing'] if k[0] in lash_x else C['yard'])
    tack_meta = {'alpha_deg': alpha, 'heel_axis': [X0, Yt + 0.5, Z0], 'rest_x': rest[:1] + rest[-1:], 'touch_fore_mast_x': touch[:1] + touch[-1:],
                 'tip': [round(X0 + Lt * math.cos(math.radians(alpha)), 1), Yt + 0.5, round(Z0 + Lt * math.sin(math.radians(alpha)), 1)]}

    # ── 三角帆桁（自己的框）：一根斜桿，前端低（x 大）、後端高 ──
    lat, place = {}, []
    for key in ('main', 'fore'):
        Y = RB['yards'][key]
        Lc = Y['len_m'] / CELL
        th = math.radians(Y['tilt_deg'])
        pad = 3
        W_ = int(math.ceil(Lc * math.cos(th))) + 2 * pad
        H_ = int(math.ceil(Lc * math.sin(th))) + 2 * pad
        yc = 3
        F = (W_ - pad, pad)
        A = (F[0] - Lc * math.cos(th), F[1] + Lc * math.sin(th))
        hs = Y['hoist_frac'] * Lc

        def radius(s):
            return Y['r_end'] + (Y['r_max'] - Y['r_end']) * max(0.0, 1 - abs(s - hs) / max(hs, Lc - hs))

        vx, vz = A[0] - F[0], A[1] - F[1]
        ln = math.hypot(vx, vz)
        cells = {}
        for x in range(0, W_):
            for z in range(0, H_):
                px, pz = x + 0.5 - F[0], z + 0.5 - F[1]
                t = (px * vx + pz * vz) / ln
                if t < -0.5 or t > ln + 0.5:
                    continue
                tc = min(max(t, 0.0), ln)
                d2 = (px - tc * vx / ln) ** 2 + (pz - tc * vz / ln) ** 2
                r = radius(tc)
                lash = abs(tc - hs) <= Y['lash_half'] and abs(tc - hs) > 1.5 and int(round(tc - hs)) % Y['lash_every'] == 0
                for dy in range(-3, 4):
                    if d2 + dy * dy <= r * r:
                        cells[(x, yc + dy, z)] = C['lashing'] if lash else C['yard']

        def near(s, top=False):
            px_, pz_ = F[0] + vx / ln * s, F[1] + vz / ln * s
            best = min((k for k in cells if k[1] == yc), key=lambda k: ((k[0] + 0.5 - px_) ** 2 + (k[2] + 0.5 - pz_) ** 2, k))
            if top:
                z = best[2]
                while (best[0], yc, z + 1) in cells:
                    z += 1
                best = (best[0], yc, z)
            return list(best)
        anchors = {'pivot': near(hs), 'sling': near(hs, True), 'fore': near(1.0), 'peak': near(Lc - 1.0)}
        for k_, s in enumerate(np.arange(8.0, Lc - 4, 8.0)):
            anchors['jackstay-%02d' % (k_ + 1)] = near(float(s), True)
        pv = anchors['pivot']
        row = rows[key]
        zp = row['top_z'] - Y['below_top']
        if probe.get('pivot', '').startswith(key + ':'):
            zp += int(probe['pivot'].split(':')[1])
        xm = int(math.floor(rig.axis_x(row, zp)))
        yw = YC + Y['y_off']
        off = (xm - pv[0], yw - pv[1], zp - pv[2])
        lat[key] = {'cells': cells, 'size': [W_, 7, H_], 'anchors': anchors, 'len_m': Y['len_m'], 'tilt_deg': Y['tilt_deg'],
                    'hoist_frac': Y['hoist_frac'], 'sail': Y['sail'], 'off': off}
        place.append({'name': 'yard-%s-lateen' % key, 'mast': key, 'host': 'mast-' + key, 'work': 'claude-felucca-01m-yard-%s' % key,
                      'at': [xm + 0.5, yw + 0.5, zp + 0.5], 'pivot': [pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5], 'rotate': [0, 0, 0], 'scale': [1, 1, 1],
                      'meta': {'kind': 'yard', 'mast': key, 'yard': 'gaff', 'rig': 'lateen', 'sail': Y['sail'], 'length_m': Y['len_m'],
                               'length_ft': round(Y['len_m'] / 0.3048, 1), 'diameter_in': round((2 * int(Y['r_max']) + 1) * CELL / 0.0254, 1),
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}})

    # ── 讀數 ──
    R = {'probe': probe or None, 'rows': rows, 'skipped_on_ship': skipped, 'heel_slivers_trimmed': trimmed, 'tack_spar': tack_meta, 'parts': {}, 'yards': {}}
    allp = {}
    for nm, cl in parts.items():
        if not cl:
            R['parts'][nm] = {'cells': 0}
            continue
        G = np.zeros((AX, AY, AZ), bool)
        for k in cl:
            G[k] = True
        _, n6 = ndimage.label(G)
        xs = [k[0] for k in cl]; zs = [k[2] for k in cl]
        R['parts'][nm] = {'cells': len(cl), 'components_6': int(n6), 'x': [min(xs), max(xs)], 'z': [min(zs), max(zs)],
                          'mirror_diff': None if nm == 'tack-spar' else sum(1 for (x, y, z), c in cl.items() if cl.get((x, 2 * YC - y, z)) != c),
                          'colours': {str(c): sum(1 for v in cl.values() if v == c) for c in sorted(set(cl.values()))}}
        for k in cl:
            allp[k] = allp.get(k, 0) + 1
    R['overlap_ship'] = sum(1 for k in allp if k in occ)
    R['overlap_between_parts'] = sum(1 for v in allp.values() if v > 1)
    # 桅孔：甲板上被拿掉的格（rig.py 的桅格、在甲板那一層）每一格都要是桅
    holes = {}
    for key in rows:
        mc = parts.get('mast-' + key, {})
        cut = [k for k in rig.mast_cells(plan, key, YC) if k[2] in (6, 9) and k not in deck and (k[0], k[1], k[2]) in rig_deck_region(plan, k)]
        holes[key] = {'hole_cells': len(cut), 'mast': sum(1 for k in cut if k in mc), 'empty': sum(1 for k in cut if k not in mc)}
    R['mast_holes'] = holes
    G = np.zeros((AX, AY, AZ), bool)
    for k in occ:
        G[k] = True
    for cl in parts.values():
        for k in cl:
            G[k] = True
    lab, ncomp = ndimage.label(G)
    R['ship_with_rig'] = {'cells': int(G.sum()), 'components_6': int(ncomp), 'cavities': int((ndimage.binary_fill_holes(G) & ~G).sum())}
    world_ship = set(occ) | set(allp)
    pts = np.array(sorted(world_ship), float)
    tree = cKDTree(pts)
    for key, l_ in lat.items():
        cl = l_['cells']
        W_, _, H_ = l_['size']
        G2 = np.zeros((W_, 7, H_), bool)
        for k in cl:
            G2[k] = True
        _, n6 = ndimage.label(G2)
        ox, oy, oz = l_['off']
        wc = {(x + ox, y + oy, z + oz) for (x, y, z) in cl}
        an_w = {n: [a[0] + ox, a[1] + oy, a[2] + oz] for n, a in l_['anchors'].items()}
        mast = parts.get('mast-' + key, {})
        pz = an_w['pivot'][2]
        band = [k for k in mast if pz - 40 <= k[2] <= pz - 10 and abs(k[1] - YC) <= 4]
        dmin, _ = tree.query(np.array(sorted(wc), float))
        fore, piv = an_w['fore'], an_w['pivot']
        xh = fore[0] - piv[0]
        R['yards'][key] = {'size': l_['size'], 'cells': len(cl), 'components_6': int(n6), 'anchors': len(l_['anchors']),
                           'overlap_world': sum(1 for k in wc if k in world_ship), 'min_gap_cells': round(float(dmin.min()) - 1, 2),
                           'world_x': [min(k[0] for k in wc), max(k[0] for k in wc)], 'world_z': [min(k[2] for k in wc), max(k[2] for k in wc)],
                           'world_y': [min(k[1] for k in wc), max(k[1] for k in wc)],
                           'pivot_world': piv, 'fore_world': fore, 'peak_world': an_w['peak'],
                           'mast_cells_in_shipcheck_band': len(band), 'band_z': [pz - 40, pz - 10],
                           'lateen_swing_deg': round(math.degrees(math.asin(min(1.0, 25.0 / xh))), 1) if xh > 0 else None,
                           'inside_assembly_box': all(0 <= k[0] < AX and 0 <= k[1] < AY and 0 <= k[2] < AZ for k in wc)}
    R['problems'] = (R['overlap_ship'] + R['overlap_between_parts'] + sum(v['empty'] for v in holes.values())
                     + sum(1 for v in R['parts'].values() if v.get('components_6', 1) != 1)
                     + (R['ship_with_rig']['components_6'] != 1) + R['ship_with_rig']['cavities']
                     + sum((v['components_6'] != 1) + v['overlap_world'] + (v['mast_cells_in_shipcheck_band'] == 0) + (not v['inside_assembly_box']) for v in R['yards'].values()))
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'mast_holes', 'problems')} | {'yards': {k: {kk: v[kk] for kk in ('pivot_world', 'band_z', 'mast_cells_in_shipcheck_band', 'min_gap_cells')} for k, v in R['yards'].items()}}, ensure_ascii=False))
        return

    def dump(path, cl, head):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(head)
            for (x, y, z), c in sorted(cl.items()):
                fh.write('%d,%d,%d,%d\n' % (x, y, z, c))
        return hashlib.sha256(open(path, 'rb').read()).hexdigest()

    sha = {}
    for nm, fn in (('mast-main', 'main'), ('mast-fore', 'fore'), ('tack-spar', 'tack_spar')):
        sha['masts/' + fn] = dump(os.path.join(HERE, 'masks', 'masts', fn + '.vox.txt'), parts[nm], '# 海鷗號 步驟 7：%s（at 0,0,0、框 %d×%d×%d）\n' % (nm, AX, AY, AZ))
    for key, l_ in lat.items():
        sha['yards/lateen-' + key] = dump(os.path.join(HERE, 'masks', 'yards', 'lateen-%s.vox.txt' % key), l_['cells'],
                                          '# 海鷗號 步驟 7：%s 三角帆桁（自己的框 %s）\n' % (key, l_['size']))
    R['sha256'] = sha
    with open(os.path.join(HERE, 'yards_lateen.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump({k: {kk: v[kk] for kk in ('size', 'anchors', 'len_m', 'tilt_deg', 'hoist_frac', 'sail')} for k, v in lat.items()}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(place, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)

    # ── 圖紙 05：側面（全船＋桅＋帆桁＋桿） ──
    s = 5
    img = Image.new('RGB', (AX * s + 80, AZ * s + 120), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), 'al-Nawras - new sheet 05: masts (main x 84 upright, fore x 136 raked 8 deg fwd), lateen yards 15.0 / 10.5 m at 40 deg, tack spar   0.1 m/cell', fill=(20, 20, 40), font=f)
    oy = 40 + AZ * s
    side = {}
    for k, c in occ.items():
        if k[1] >= YC and (k[0], k[2]) not in side:
            side[(k[0], k[2])] = c
    for cl in parts.values():
        for k, c in cl.items():
            side[(k[0], k[2])] = c
    for key, l_ in lat.items():
        ox, oy_, oz = l_['off']
        for (x, y, z), c in l_['cells'].items():
            side[(x + ox, z + oz)] = c
    for (x, z), c in side.items():
        d.rectangle([40 + x * s, oy - (z + 1) * s, 40 + x * s + s - 1, oy - z * s - 1], fill=rgb(c))
    wl = plan['waterline']['z']
    d.line([40, oy - (wl + 1) * s, 40 + AX * s, oy - (wl + 1) * s], fill=(40, 110, 200))
    for x in range(0, AX + 1, 10):
        d.text((40 + x * s - 6, oy + 6), str(x), fill=(80, 80, 80), font=f)
    for key, v in R['yards'].items():
        p = v['pivot_world']
        d.ellipse([40 + p[0] * s - 4, oy - p[2] * s - 4, 40 + p[0] * s + 4, oy - p[2] * s + 4], outline=(200, 30, 30), width=2)
        d.text((40 + p[0] * s + 8, oy - p[2] * s - 6), '%s pivot (%d,%d)' % (key, p[0], p[2]), fill=(200, 30, 30), font=f)
    img.save(os.path.join(HERE, 'sheet05_masts_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('rows',)}, ensure_ascii=False))


def rig_deck_region(plan, k):
    """桅孔只算「甲板在那裡本來會鋪」的格：(x, y, z) 在艙底板或平台的範圍裡。"""
    lay = {kk: V(v) for kk, v in plan['layout'].items() if kk != 'src'}
    x, y, z = k
    ok = False
    if z == lay['floor']['board_z'] and lay['floor']['x0'] <= x <= lay['floor']['x1']:
        ok = True
    if z == lay['benches']['seat_z']:
        b = lay['benches']
        ok = ok or any(b['x0'] + i * b['pitch'] <= x < b['x0'] + i * b['pitch'] + b['w'] for i in range(b['n']))
        for key in ('bow_platform', 'stern_platform'):
            ok = ok or (lay[key]['board_z'] == z and lay[key]['x0'] <= x <= lay[key]['x1'])
    return {k} if ok else set()


if __name__ == '__main__':
    main()

# 蓬特號 新圖紙 03（TASK-0754）：帆裝 —— 桅（桅頂兩排導索孔）、上下帆桁（各一件子作品、模型掛在桅子作品裡）、寬矮方帆、
#   16 條吊索（W12）、後支索、內外前支索、轉帆索、升降索、hogging truss 粗繩
#   ⇒ masks/rig/{mast,yard_upper,yard_lower}.vox.txt、rig_plan.json（帆桁、固定點、帆、繩、meta）、verify_rig.json、sheet03_rig_v1.png
#   用法：python -I -X utf8 draft_rig.py
#   · 佔用照船殼與甲板清單（＝ 作品，前兩階段 delta_apply 讀回差 0）。只讀，不碰作品。
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import rgb, font, SX, SY, SZ, V
from draft_deck import load_list

sys.stdout.reconfigure(encoding='utf-8')


def lst(name):
    return np.loadtxt(os.path.join(HERE, 'masks', name), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def main():
    plan = HL.load_plan()
    K = {k: V(v) for k, v in plan['rig'].items()}
    C = K['colors']
    YC = plan['space']['yc']
    occ = load_list(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt')) > 0
    deck = {}
    for nm in ('deck_main', 'deck_hold', 'platform_aft', 'platform_fwd', 'crutches', 'ladders'):
        a = lst('deck/%s.vox.txt' % nm)
        deck[nm] = a
        occ[a[:, 0], a[:, 1], a[:, 2]] = True
    dz = V(plan['deck']['deck_z']) + 1                       # 甲板站的那一格
    R, out = {}, {'yards': {}, 'anchors': [], 'sails': [], 'ropes': []}

    # ───── 桅 ─────
    mx, mz0, mz1 = K['mast_x'], K['mast_base_z'], K['mast_top_z']
    r0, r1, r2 = K['mast_r']
    cx, cy = mx + 0.5, YC + 0.5
    zmid = (dz + mz1) / 2

    def mr(z):
        if z <= dz:
            return r0
        if z <= zmid:
            return r0 + (r1 - r0) * (z - dz) / (zmid - dz)
        return r1 + (r2 - r1) * (z - zmid) / (mz1 - zmid)
    mast = {}
    for z in range(mz0, mz1 + 1):
        r = mr(z + 0.5)
        for x in range(mx - 4, mx + 5):
            for y in range(YC - 4, YC + 5):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    mast[(x, y, z)] = C['mast']
    # 桅頂兩排導索孔（W12：16 條吊索穿過兩條各 8 個導索孔的板）：左右舷各一條板，z mz1−7 … mz1
    fair = {}
    for side, s in (('P', -1), ('S', 1)):
        yy = YC + s * (int(math.ceil(r2)) + 1)
        for k in range(8):
            z = mz1 - 7 + k
            mast[(mx, yy, z)] = C['head']
            mast[(mx, YC + s * int(math.ceil(r2)), z)] = C['head']
            fair['fair-%s%d' % (side, k + 1)] = [mx, yy, z]
    hits = [p for p in mast if occ[p]]
    R['mast'] = {'cells': len(mast), 'z': [mz0, mz1], 'overlap_existing': len(hits)}
    for nm, at in fair.items():
        out['anchors'].append({'work': 'mast', 'name': nm, 'at': at})
    out['anchors'].append({'work': 'mast', 'name': 'cap', 'at': [mx, YC, mz1]})
    for side, s in (('P', -1), ('S', 1)):
        out['anchors'].append({'work': 'mast', 'name': 'halyard-' + side, 'at': [mx, YC + s * int(math.ceil(r2)), mz1]})

    # ───── 帆桁（一根一件子作品，沿 y 放、沒轉）─────
    for key in ('upper', 'lower'):
        Y = K[key]
        n = Y['len']
        c = (n + 1) // 2
        size = [5, n + 2, 5]
        cells = {}
        for j in range(1, n + 1):
            t = abs(j - c) / (n / 2)
            r = Y['r'][0] + (Y['r'][1] - Y['r'][0]) * t
            for dx in (-1, 0, 1):
                for dzz in (-1, 0, 1):
                    if dx * dx + dzz * dzz <= r * r + 1e-6:
                        cells[(2 + dx, j, 2 + dzz)] = C['yard']
        h = Y['sail_half']
        anchors = {'pivot': [2, c, 2], 'sling-P': [2, c - 3, 2], 'sling-S': [2, c + 3, 2], 'earing-P': [2, c - h, 2], 'earing-S': [2, c + h, 2],
                   'arm-P': [2, 1, 2], 'arm-S': [2, n, 2]}
        for i, f in enumerate(Y['lifts'], 1):
            d = int(round(f * (n / 2)))
            anchors['lift-P%d' % i] = [2, c - d, 2]
            anchors['lift-S%d' % i] = [2, c + d, 2]
        at = [K['yard_x'] + 0.5, YC + 0.5, Y['z'] + 0.5]
        piv = [2.5, c + 0.5, 2.5]
        # 世界座標的格（量碰撞用）
        wc = [(int(K['yard_x'] + (x - 2)), int(YC + (y - c)), int(Y['z'] + (z - 2))) for (x, y, z) in cells]
        hit = sum(1 for p in wc if 0 <= p[1] < SY and (occ[p] or p in mast))
        meta = {'kind': 'yard', 'mast': 'main', 'yard': 'course' if key == 'upper' else 'lower', 'sail': K['sail_name'],
                'length_m': round(n * 0.1, 1), 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}
        out['yards'][key] = {'size': size, 'anchors': anchors, 'at': at, 'pivot': piv, 'meta': meta, 'cells': len(cells)}
        R['yard_' + key] = {'cells': len(cells), 'world_y': [YC + 1 - c, YC + n - c], 'z': Y['z'], 'collide': hit}
        os.makedirs(os.path.join(HERE, 'masks', 'rig'), exist_ok=True)
        with open(os.path.join(HERE, 'masks', 'rig', 'yard_%s.vox.txt' % key), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 蓬特號 %s帆桁（draft_rig.py）x,y,z,color —— 子作品自己的座標\n' % ('上' if key == 'upper' else '下'))
            f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c_) for (x, y, z), c_ in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0]))) + '\n')
    with open(os.path.join(HERE, 'masks', 'rig', 'mast.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蓬特號 桅（draft_rig.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c_) for (x, y, z), c_ in sorted(mast.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1]))) + '\n')

    # ───── 船殼／平台／叉柱上的繩端固定點（照實際的格挑）─────
    def pick(arr, cond, key):
        c = [tuple(int(v) for v in r[:3]) for r in arr if cond(r)]
        return list(min(c, key=key)) if c else None
    pa, pf, cr = deck['platform_aft'], deck['platform_fwd'], deck['crutches']
    pz = V(plan['deck']['plat_z'])
    tdy = YC + V(plan['deck']['truss_dy'])
    anc = {
        ('platform-aft', 'backstay'): pick(pa, lambda r: r[1] == YC and r[2] == pz, lambda p: p[0]),
        ('platform-aft', 'truss-aft'): pick(pa, lambda r: r[1] == tdy and r[2] == pz, lambda p: abs(p[0] - 64)),
        ('platform-fwd', 'forestay-in'): pick(pf, lambda r: r[1] == YC and r[2] == pz, lambda p: abs(p[0] - 212)),
        ('platform-fwd', 'truss-fwd'): pick(pf, lambda r: r[1] == tdy and r[2] == pz, lambda p: abs(p[0] - 214)),
    }
    for (side, s) in (('P', -1), ('S', 1)):
        post = [tuple(int(v) for v in r[:3]) for r in pa if r[0] == V(plan['deck']['rudder_post_x']) and (r[1] - YC) * s > 0 and r[2] > pz]
        top = max(p[2] for p in post)
        anc[('platform-aft', 'brace-' + side)] = list(min([p for p in post if p[2] == top - 1], key=lambda p: abs(p[1] - YC)))
        anc[('platform-aft', 'brace-lo-' + side)] = list(min([p for p in post if p[2] == pz + 3], key=lambda p: abs(p[1] - YC)))
    for i, x in enumerate(V(plan['deck']['crutch_x']), 1):
        anc[('truss', 'fork-%d' % i)] = [x, tdy, V(plan['deck']['crutch_z'])]
    hl = lst('hull/hull.vox.txt')
    anc[('hull', 'forestay-out')] = pick(hl, lambda r: r[1] == YC, lambda p: (p[0] - 236) ** 2 + (p[2] - 37) ** 2)
    for (w, nm), at in anc.items():
        assert at is not None, nm
        out['anchors'].append({'work': w, 'name': nm, 'at': at})
    LINK = {'platform-aft': '平台-aft', 'platform-fwd': '平台-fwd', 'truss': 'truss叉柱', 'hull': '船殼', 'mast': '桅'}

    # ───── 帆 ─────
    sn = K['sail_name']
    out['sails'].append({'name': sn, 'corners': ['model:桅/yard-upper/earing-P', 'model:桅/yard-upper/earing-S', 'model:桅/yard-lower/earing-S', 'model:桅/yard-lower/earing-P'],
                         'corner_names': ['head-P', 'head-S', 'foot-S', 'foot-P'], 'bind': [0, 2], 'free': [], 'color': K['sail_color'],
                         'meta': {'kind': 'sail', 'mast': 'main', 'sail': 'course'}})
    # ───── 繩 ─────
    RC = K['rope']

    def rope(name, a, b, kind, group, slack=1.0, meta=None):
        col, th = RC[kind]
        out['ropes'].append({'name': name, 'from': a, 'to': b, 'slack': slack, 'thickness': th, 'color': col, 'group': group, 'meta': meta or {}})
    for side in ('P', 'S'):
        for i in range(1, 5):
            rope('lift-upper-%s%d' % (side, i), '桅/fair-%s%d' % (side, 4 + i), 'model:桅/yard-upper/lift-%s%d' % (side, i), 'lift', 'standing/lifts', meta={'kind': 'lift'})
            rope('lift-lower-%s%d' % (side, i), '桅/fair-%s%d' % (side, i), 'model:桅/yard-lower/lift-%s%d' % (side, i), 'lift', 'standing/lifts', meta={'kind': 'lift'})
        rope('brace-upper-' + side, 'model:桅/yard-upper/arm-' + side, '平台-aft/brace-' + side, 'brace', 'running/braces', 1.02, {'kind': 'brace'})
        rope('brace-lower-' + side, 'model:桅/yard-lower/arm-' + side, '平台-aft/brace-lo-' + side, 'brace', 'running/braces', 1.02, {'kind': 'brace'})
        rope('halyard-' + side, 'model:桅/yard-upper/sling-' + side, '桅/halyard-' + side, 'halyard', 'running/halyards', 1.0, {'kind': 'halyard'})
    rope('backstay', '桅/cap', '平台-aft/backstay', 'stay', 'standing/stays', meta={'kind': 'backstay'})
    rope('forestay-inner', '桅/cap', '平台-fwd/forestay-in', 'stay', 'standing/stays', meta={'kind': 'stay'})
    rope('forestay-outer', '桅/cap', '船殼/forestay-out', 'stay', 'standing/stays', meta={'kind': 'stay'})
    chain = ['平台-aft/truss-aft'] + ['truss叉柱/fork-%d' % i for i in range(1, 5)] + ['平台-fwd/truss-fwd']
    for i in range(len(chain) - 1):
        rope('truss-%d' % (i + 1), chain[i], chain[i + 1], 'truss', 'hull/truss')
    R['ropes'] = len(out['ropes'])
    R['anchors'] = {'%s/%s' % (a['work'], a['name']): a['at'] for a in out['anchors']}
    # 帆的大小（設計）
    U, Lw = K['upper'], K['lower']
    R['sail'] = {'head_m': 2 * U['sail_half'] * 0.1, 'foot_m': 2 * Lw['sail_half'] * 0.1, 'height_m': round((U['z'] - Lw['z']) * 0.1, 1),
                 'area_m2': round(0.5 * (2 * U['sail_half'] + 2 * Lw['sail_half']) * 0.1 * (U['z'] - Lw['z']) * 0.1, 1)}
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_rig.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # ───── 圖紙：側面＋正面（帆面）─────
    sc = 3
    W, H = SX * sc + SY * sc + 60, 140 * sc + 120
    im = Image.new('RGB', (W, H), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(22), font(15)
    d.text((20, 10), '蓬特號 新圖紙 03：帆裝（側面｜正面）—— 單桅、上下帆桁、寬矮方帆、16 條吊索、前後支索、truss', fill=(40, 30, 20), font=f)
    oy = 40 + 140 * sc
    G = load_list(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    for nm, a in deck.items():
        G[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    for p, c_ in mast.items():
        G[p] = c_
    occ2 = G > 0
    side = occ2.any(axis=1)
    top = np.where(occ2.any(axis=1), np.argmax(occ2, axis=1), 0)
    for x in range(SX):
        for z in range(140):
            if side[x, z]:
                c_ = G[x, top[x, z], z]
                d.rectangle([20 + x * sc, oy - (z + 1) * sc, 20 + x * sc + sc - 1, oy - z * sc - 1], fill=rgb(int(c_)))
    ox2 = 40 + SX * sc
    front = occ2.any(axis=0)
    for y in range(SY):
        for z in range(140):
            if front[y, z]:
                d.rectangle([ox2 + y * sc, oy - (z + 1) * sc, ox2 + y * sc + sc - 1, oy - z * sc - 1], fill=(150, 110, 70))
    for key in ('upper', 'lower'):
        Y = K[key]
        z = Y['z']
        d.line([20 + (K['yard_x'] - 1) * sc, oy - z * sc, 20 + (K['yard_x'] + 2) * sc, oy - z * sc], fill=(145, 72, 0), width=3)
        d.line([ox2 + (YC - Y['len'] // 2) * sc, oy - z * sc, ox2 + (YC + Y['len'] // 2) * sc, oy - z * sc], fill=(145, 72, 0), width=3)
    poly = [(ox2 + (YC - U['sail_half']) * sc, oy - U['z'] * sc), (ox2 + (YC + U['sail_half']) * sc, oy - U['z'] * sc),
            (ox2 + (YC + Lw['sail_half']) * sc, oy - Lw['z'] * sc), (ox2 + (YC - Lw['sail_half']) * sc, oy - Lw['z'] * sc)]
    d.polygon(poly, fill=(239, 230, 207), outline=(120, 100, 70))
    d.line([20 + K['yard_x'] * sc, oy - U['z'] * sc, 20 + K['yard_x'] * sc, oy - Lw['z'] * sc], fill=(200, 190, 160), width=3)
    A = {('%s' % LINK[a['work']]) + '/' + a['name']: a['at'] for a in out['anchors']}
    for r in out['ropes']:
        def pt(e):
            if e.startswith('model:'):
                k, nm = e.split('/')[1], e.split('/')[2]
                Y = out['yards']['upper' if k == 'yard-upper' else 'lower']
                a = Y['anchors'][nm]
                return [K['yard_x'] + a[0] - 2, YC + a[1] - Y['anchors']['pivot'][1], (K['upper'] if k == 'yard-upper' else K['lower'])['z'] + a[2] - 2]
            return A[e]
        p, q = pt(r['from']), pt(r['to'])
        col = (90, 70, 40)
        d.line([20 + p[0] * sc, oy - p[2] * sc, 20 + q[0] * sc, oy - q[2] * sc], fill=col, width=2 if 'truss' in r['name'] else 1)
        d.line([ox2 + p[1] * sc, oy - p[2] * sc, ox2 + q[1] * sc, oy - q[2] * sc], fill=col, width=2 if 'truss' in r['name'] else 1)
    wl = plan['waterline']['z']
    d.line([20, oy - wl * sc, W - 20, oy - wl * sc], fill=(30, 90, 200), width=2)
    d.text((20, H - 60), '帆 頂 %.1f m｜腳 %.1f m｜高 %.1f m｜%.1f m²（W12 實做：14.25／14.45 × 5.40 m、77.5 m²）｜繩 %d 條｜桅 %d 格（跟既有的格重疊 %d）｜帆桁碰撞 上 %d、下 %d' % (
        R['sail']['head_m'], R['sail']['foot_m'], R['sail']['height_m'], R['sail']['area_m2'], R['ropes'], R['mast']['cells'], R['mast']['overlap_existing'],
        R['yard_upper']['collide'], R['yard_lower']['collide']), fill=(40, 30, 20), font=fs)
    im.save(os.path.join(HERE, 'sheet03_rig_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k != 'anchors'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

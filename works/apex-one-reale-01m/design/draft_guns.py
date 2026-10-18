# 皇家號 新圖紙 04（TASK-0702）：砲 ⇒ 迴旋砲元件清單、砲的擺法 guns_placement.json、讀數 verify_guns.json、圖紙 sheet04
#   用法：python -I -X utf8 draft_guns.py [--probe=push=gun-8-S:+6]
#   · 只讀 plan.json、船殼／階段二／階段三的清單（＝ 作品）與砲元件的作品（CLI 匯出），不碰作品。
#   · 擺法：模型每一格的格心＋八個角都不落在船的實心格裡（造船規格 §4.2）；船頭的砲從砲口目標位置開始，先往上抬（甲板拱）、不行再往船尾退。
#   · 射線：砲口沿砲軸往外 N 格（每 0.5 格取樣）碰到船的實心幾次（自己的砲不算）。
#   · --probe：反向對照（只印讀數、⛔ 不寫檔）。push=<砲名>:<格> ⇒ 那門砲沿砲軸往船裡推幾格（不再搜尋），要報碰撞。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio

sys.stdout.reconfigure(encoding='utf-8')
YC = 160


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def ld(p):
    return np.loadtxt(os.path.join(HERE, p), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


# ───────── 迴旋砲元件（0.05 m／格）：砲管沿 +y、砲口在 y 大的那頭 ─────────
def pierrier_cells():
    cells = {}
    cx, az = 5.5, 9.5                         # 砲軸（x、z 的連續座標）
    for y in range(0, 38):
        for x in range(11):
            for z in range(13):
                dx, dz = x + 0.5 - cx, z + 0.5 - az
                r2 = dx * dx + dz * dz
                if 4 <= y <= 36:
                    ro = 2.6 if y <= 10 else (2.3 if y >= 33 else 2.0)      # 藥室、砲管、砲口加厚
                    if r2 <= ro * ro and not (y >= 31 and r2 <= 0.8 * 0.8):
                        cells[(x, y, z)] = 73
                elif y < 4 and r2 <= 0.9 * 0.9 and z >= 9:                  # 尾巴的把手
                    cells[(x, y, z + (1 if y < 2 else 0))] = 36
    for y in (17, 18, 19):                    # 叉架（兩臂＋底）＋插銷
        for z in range(5, 11):
            for x in (1, 2, 8, 9):
                cells[(x, y, z)] = 36
        for x in range(1, 10):
            for z in (5, 6):
                cells.setdefault((x, y, z), 36)
    for y in (17, 18, 19):
        for x in (4, 5, 6):
            for z in range(0, 5):
                cells[(x, y, z)] = 36
    anchors = {'muzzle': [5, 36, 9], 'breech': [5, 5, 9], 'cascabel': [5, 1, 10], 'pivot': [5, 18, 0]}
    assert (5, 36, 9) not in cells and (5, 5, 9) in cells and (5, 18, 0) in cells
    return cells, [11, 38, 13], anchors


def rotz(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.stack([v[..., 0] * c - v[..., 1] * s, v[..., 0] * s + v[..., 1] * c, v[..., 2]], axis=-1)


OFF = np.array([[0.5, 0.5, 0.5]] + [[a, b, c] for a in (0.001, 0.999) for b in (0.001, 0.999) for c in (0.001, 0.999)])


def world_points(src, scale, pivot, at, deg):
    pts = src[:, None, :3].astype(float) + OFF[None, :, :]          # (n, 9, 3)
    return np.asarray(at) + rotz(scale * (pts - np.asarray(pivot)), deg)


def collide(occ, src, scale, pivot, at, deg):
    w = np.floor(world_points(src, scale, pivot, at, deg)).astype(np.int64)
    k = (w[..., 0] * 1000 + w[..., 1]) * 1000 + w[..., 2]
    return int(np.isin(k, occ).any(axis=1).sum())


def ray(occ, p0, d, n):
    hits = 0
    for t in np.arange(0.5, n, 0.5):
        q = np.floor(np.asarray(p0) + t * np.asarray(d)).astype(np.int64)
        if np.isin((q[0] * 1000 + q[1]) * 1000 + q[2], occ):
            hits += 1
    return hits


def anchor_world(a, scale, pivot, at, deg):
    return (np.asarray(at) + rotz(scale * (np.asarray(a, float) + 0.5 - np.asarray(pivot)), deg)).tolist()


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = v
    plan = HL.load_plan(HERE)
    G = V(plan['guns'])
    occ_l = [wio.load_lists(os.path.join(HERE, 'masks', 'hull'))]
    for nm in ('deck', 'apostis', 'rambade', 'eperon', 'stern', 'ladders'):
        occ_l.append(ld('masks/upper/%s.vox.txt' % nm))
    for nm in ('main', 'fore'):
        occ_l.append(ld('masks/masts/%s.vox.txt' % nm))
    allc = np.concatenate(occ_l)
    occ = np.unique(wio.key(allc))
    zmax, zlow = {}, {}                       # 每一柱最高的實心；z < 40 裡最高的（砲台底下的甲板面）
    for x, y, z, c in allc.tolist():
        if (x, y) not in zmax or z > zmax[(x, y)]:
            zmax[(x, y)] = z
        if z < 40 and ((x, y) not in zlow or z > zlow[(x, y)]):
            zlow[(x, y)] = z
    # 元件
    pc, psize, panc = pierrier_cells()
    comps = {}
    for k, c in G['components'].items():
        if c['source'] == 'self':
            src = np.array([[x, y, z, col] for (x, y, z), col in sorted(pc.items())])
            comps[k] = {'src': src, 'anchors': panc, 'size': psize}
        else:
            src = wio.export_list(c['source'], None)
            a = json.load(open(os.path.join(HERE, '..', '..', c['source'], 'anchors.json'), encoding='utf-8'))
            comps[k] = {'src': src, 'anchors': {q['name']: q['at'] for q in a['anchors']}, 'size': None}
    D = {k: V(v) for k, v in plan['layout'].items()}
    L = HL.Lines(plan)
    sh = lambda x: int(np.floor(L.sheer(np.array([x + 0.5]))[0]))
    rail_top = lambda x: sh(x) + int(D['rail_above_sheer'])
    out = []
    # 船頭 5 門
    for g in G['bow']:
        comp = comps[g['comp']]
        sc = g['scale']
        an = comp['anchors']
        piv = [an['breech'][0] + 0.5, 0.0, 0.0]
        deg = -90
        for side in ([1, -1] if g['dy'] else [1]):
            dy = g['dy'] * side
            name = g['name'] + ('' if not g['dy'] else ('-S' if side > 0 else '-P'))
            y = YC + dy + 0.5
            xm = g['muzzle_x']
            best = None
            push = probe.get('push', '')
            if push.startswith(name + ':'):
                d = float(push.split(':')[1])
                at = [xm - sc * (an['muzzle'][1] + 0.5) + d, y, zlow.get((int(xm) - 20, YC + dy), 28) + 1]
                best = (at, collide(occ, comp['src'], sc, piv, at, deg))
            else:
                for back in range(0, 40):
                    ax = xm - sc * (an['muzzle'][1] + 0.5) - back
                    zf = max(zlow.get((int(ax + sc * j), YC + dy + o), 0) for j in range(0, int(comp['src'][:, 1].max()) + 1, 4) for o in (-3, 0, 3))
                    for lift in range(0, 6):
                        at = [ax, y, zf + 1 + lift]
                        n = collide(occ, comp['src'], sc, piv, at, deg)
                        if n == 0:
                            best = (at, 0)
                            break
                    if best:
                        break
            at, n = best
            mz = anchor_world(an['muzzle'], sc, piv, at, deg)
            br = anchor_world(an['breech'], sc, piv, at, deg)
            out.append({'name': name, 'host': g['host'], 'comp': g['comp'], 'source': G['components'][g['comp']]['source'], 'scale': sc, 'pivot': piv,
                        'at': [round(v, 3) for v in at], 'rotate': [0, 0, deg], 'meta': {'kind': 'gun', 'gun': g['gun']},
                        'collide': n, 'muzzle': [round(v, 2) for v in mz], 'breech': [round(v, 2) for v in br],
                        'ray_hits': ray(occ, mz, [1, 0, 0], 40), 'below_solid': None})
    # 迴旋砲
    P = G['pierriers']
    comp = comps['pierrier']
    an = comp['anchors']
    piv = [an['pivot'][0] + 0.5, an['pivot'][1] + 0.5, 0.0]
    sc = P['scale']
    spots = []
    for x in P['side_x']:
        for side in (1, -1):
            spots.append(('pierrier-%d-%s' % (x, 'S' if side > 0 else 'P'), '舷外槳架', x, YC + side * (int(D['apostis_half']) - 1), rail_top(x), 0 if side > 0 else 180))
    for x in P.get('fwd_x', []):                                       # 槳架前端朝前（階段五：船頭 4 門從砲台搬下來）
        for side in (1, -1):
            spots.append(('pierrier-fwd-%d-%s' % (x, 'S' if side > 0 else 'P'), '舷外槳架', x, YC + side * (int(D['apostis_half']) - 1), rail_top(x), -90))
    rx1 = D['rambade_x'][1]
    for dy in P['bow_dy']:
        for side in (1, -1):
            yy = YC + side * dy
            spots.append(('pierrier-bow-%d-%s' % (dy, 'S' if side > 0 else 'P'), '甲板-rambade', rx1, yy, zmax[(rx1, yy)], -90))
    for name, host, x, y, ztop, deg in spots:
        at = [x + 0.5, y + 0.5, ztop + 1]
        push = probe.get('push', '')
        if push.startswith(name + ':'):
            at[2] -= float(push.split(':')[1])
        n = collide(occ, comp['src'], sc, piv, at, deg)
        mz = anchor_world(an['muzzle'], sc, piv, at, deg)
        br = anchor_world(an['breech'], sc, piv, at, deg)
        d = np.array(mz) - np.array(br)
        d = d / np.linalg.norm(d)
        k = (x * 1000 + y) * 1000 + ztop
        out.append({'name': name, 'host': host, 'comp': 'pierrier', 'source': G['components']['pierrier']['work'], 'scale': sc, 'pivot': piv,
                    'at': [round(v, 3) for v in at], 'rotate': [0, 0, deg],
                    'meta': {'kind': 'gun', 'gun': 'pierrier', 'mount': 'turret', 'arc': P['arc'], 'rate': P['rate']},
                    'collide': n, 'muzzle': [round(v, 2) for v in mz], 'breech': [round(v, 2) for v in br], 'ray_hits': ray(occ, mz, d.tolist(), 20),
                    'below_solid': bool(np.isin(k, occ))})
    # 砲與砲之間：外框不重疊
    R = {'guns': out, 'count': len(out), 'collide_total': sum(g['collide'] for g in out), 'ray_hits_total': sum(g['ray_hits'] for g in out),
         'pierrier_not_on_solid': sum(1 for g in out if g['below_solid'] is False)}
    if probe:
        print(json.dumps({'probe': probe, 'collide_total': R['collide_total'], 'ray_hits_total': R['ray_hits_total'],
                          'nonzero': {g['name']: [g['collide'], g['ray_hits']] for g in out if g['collide'] or g['ray_hits']}}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'guns'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'guns', 'pierrier.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 皇家號 迴旋砲 pierrier（draft_guns.py）x,y,z,color —— 0.05 m、框 %s、at 0,0,0\n' % psize)
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(pc.items())) + '\n')
    R['pierrier'] = {'size': psize, 'anchors': panc, 'cells': len(pc), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}
    with open(os.path.join(HERE, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'note': 'draft_guns.py 的結果；at ＝ 模型 pivot 的落點、rotate z', 'guns': out}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(allc, out, comps, os.path.join(HERE, 'sheet04_guns_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k != 'guns'}, ensure_ascii=False))
    for g in out:
        print('  %-22s at %s 碰撞 %d 射線 %d 砲口 %s' % (g['name'], g['at'], g['collide'], g['ray_hits'], g['muzzle']))


def sheet(allc, guns, comps, path):
    x0, x1, y0, y1 = 520, 700, 95, 226
    s = 6
    W, H = (x1 - x0) * s + 80, (y1 - y0) * s + 140
    img = Image.new('RGB', (W, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    d.text((40, 12), '皇家號 新圖紙 04：船頭的砲（俯視，船頭朝右；每格 6 px）', fill=(20, 20, 40), font=font(26))
    top = {}
    for x, y, z, c in allc.tolist():
        if x0 <= x < x1 and y0 <= y < y1 and ((x, y) not in top or z > top[(x, y)][0]):
            top[(x, y)] = (z, c)
    for (x, y), (z, c) in top.items():
        d.rectangle([40 + (x - x0) * s, 60 + (y - y0) * s, 40 + (x - x0) * s + s - 1, 60 + (y - y0) * s + s - 1], fill=palette_rgb(c))
    for g in guns:
        comp = comps[g['comp']]
        w = world_points(comp['src'], g['scale'], g['pivot'], g['at'], g['rotate'][2])[:, 0, :]
        col = (200, 30, 30) if g['comp'] != 'pierrier' else (30, 30, 200)
        for p in w[::3]:
            if x0 <= p[0] < x1 and y0 <= p[1] < y1:
                d.point((40 + (p[0] - x0) * s, 60 + (p[1] - y0) * s), fill=col)
        mx, my = g['muzzle'][0], g['muzzle'][1]
        if x0 <= mx < x1:
            d.ellipse([40 + (mx - x0) * s - 4, 60 + (my - y0) * s - 4, 40 + (mx - x0) * s + 4, 60 + (my - y0) * s + 4], outline=(0, 0, 0))
    d.text((40, H - 60), '紅點：船頭 5 門（36 磅中線、8 磅 dy ±14、6 磅在角落平台）；藍點：迴旋砲；圈：砲口。碰撞（格心＋八角）與射線讀數見 verify_guns.json。', fill=(60, 60, 60), font=font(15))
    img.save(path)


if __name__ == '__main__':
    main()

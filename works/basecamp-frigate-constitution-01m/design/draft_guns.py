# 新圖紙 18（gun deck 長砲）：plan.json 的 guns 段 ＋ 組裝件的現況（砲加進來之前）
#   ⇒ masks/guns/gun24.vox.txt（一門砲＋砲架，自己的座標）、design/guns_placement.json（每個砲門一條關聯的 at／mirror）、
#      verify_guns.json、sheet18_guns_v1.png
# 用法：python -I draft_guns.py <design 資料夾>
#   · 一門砲做一次（子作品 -gun-24），用關聯擺到每個砲門：S 舷照原樣（砲口朝 +y），P 舷 mirror=y
#   · 自己的座標：x ＝ 砲的寬（軸在 axis_x 那一格的格心，左右用整數偏移 k ⇒ 對稱）、y ＝ 砲身方向（砲口在 +y）、
#     z ＝ 高（z 0 ＝ 甲板面那一層，輪子站在甲板上）
#   · 擺法：砲架前緣先貼船殼內面（砲門下檻那一層的內面 − 1），撞到現況就往裡退一格，退到不撞為止（最多 max_back）
import sys, os, json, hashlib, math, subprocess
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160


def existing_links(work):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=links', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    for line in r.stdout.splitlines():
        if line.startswith('🔢 link_paths = '):
            return [p for p in line.split(' = ', 1)[1].split(';') if p]
    return []


def seg_r(prof, t):
    for (s0, r0), (s1, r1) in zip(prof, prof[1:]):
        if s0 <= t < s1:
            return r0 + (r1 - r0) * (t - s0) / (s1 - s0)
    return None


class Gun:
    """一門砲＋砲架（自己的座標）。"""

    def __init__(s, G):
        s.G = G
        s.cells, s.kind = {}, {}
        s.points = {}

    def put(s, k, c, kind, over=False):
        if k in s.cells and not over:
            return
        s.cells[k] = int(c)
        s.kind[k] = kind

    def build(s):
        G, col, C = s.G, s.G['colors'], s.G['carriage']
        W, L, H = G['size']
        X, Z = G['axis_x'], G['axis_z']                     # 軸所在的格（格心 ＝ 軸）
        y0 = G['breech_y']                                  # s ＝ 0（base ring 的後面）落在 y0 這一格的後緣
        prof = G['tube_profile']
        tube_len = prof[-1][0]

        def disc(y, r, kind, color):
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    if math.hypot(dx, dz) <= r + 1e-9:
                        s.put((X + dx, y, Z + dz), color, kind)
        # ── 砲身：每一格 y 取格心的 s，照剖面 r(s) 畫一個圓盤 ──
        for y in range(L):
            t = y + 0.5 - y0
            if 0 <= t < tube_len:
                r = seg_r(prof, t)
                disc(y, r, 'tube', col['tube'])
                if t > tube_len - G['bore_depth']:          # 砲口：中線那一格挖空
                    s.cells.pop((X, y, Z), None)
                    s.kind.pop((X, y, Z), None)
            for (t0, t1, r) in G['cascabel']:
                if t0 <= t < t1:
                    disc(y, r, 'cascabel', col['tube'])
        s.muzzle_y = y0 + tube_len                          # 連續座標
        ys = [y for (x, y, z), kd in s.kind.items() if kd == 'cascabel']
        for y in range(min(ys), min(ys) + 2):              # 鈕上面的環（breeching 繩穿過的地方）
            s.put((X, y, Z + 2), col['tube'], 'cascabel_loop')
        # ── 耳軸：在 trunnion_y 那一格，沿 x 穿到 cheek 的外面 ──
        ty = G['trunnion_y']
        kmax = max(C['cheek_k'])
        for k in range(-kmax, kmax + 1):
            for (dy, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if G['trunnion_plus'] else ((0, 0),):
                s.put((X + k, ty + dy, Z + dz), col['tube'], 'trunnion')
        # ── 砲架 ──
        yf = C['front_y']
        yr = yf - C['length'] + 1
        for k in C['cheek_k']:
            for sg in (-1, 1):
                x = X + sg * k
                for y in range(yr, yf + 1):
                    back = yf - y
                    top = [h for b0, h in C['cheek_steps'] if back >= b0][-1]
                    bot = C['arch']['bottom'] if C['arch']['from_back'] <= back <= C['arch']['to_back'] else C['cheek_bottom']   # 兩軸之間底下拱起
                    for z in range(bot, top + 1):
                        s.put((x, y, z), col['carriage'], 'cheek')
                for y in (ty - 1, ty, ty + 1):                # cap square（壓住耳軸的鐵條）
                    s.put((x, y, Z + 2 if G['trunnion_plus'] else Z + 1), col['iron'], 'capsquare', over=True)
        for (ya, rw) in ((yf - C['axle_front_back'], C['truck_r_front']), (yr + C['axle_rear_fwd'], C['truck_r_rear'])):
            for k in range(-max(C['truck_k']), max(C['truck_k']) + 1):    # 軸桿
                for y in (ya, ya + 1):
                    for z in C['axle_z']:
                        s.put((X + k, y, z), col['carriage'], 'axletree')
            for k in C['truck_k']:                                         # 輪子：yz 平面的圓盤，站在 z 0
                for sg in (-1, 1):
                    for y in range(L):
                        for z in range(H):
                            if math.hypot(y + 0.5 - (ya + 1), z + 0.5 - rw) <= rw:   # 輪心 ＝ 軸桿兩格（ya、ya+1）的中間
                                s.put((X + sg * k, y, z), col['truck'], 'truck', over=True)
            for sg in (-1, 1):                                             # 輪軸頭
                for y in (ya, ya + 1):
                    s.put((X + sg * (max(C['truck_k']) + 1), y, C['axle_z'][-1]), col['iron'], 'axle_cap')
        inner = min(C['cheek_k']) - 1
        for k in range(-inner, inner + 1):
            for y in range(yr, yr + C['bed_len']):                         # 床板
                s.put((X + k, y, C['bed_z']), col['carriage'], 'bed')
            for y in range(yr + 1, yr + 1 + C['quoin_len']):               # quoin
                for z in range(C['bed_z'] + 1, C['quoin_top'] + 1):
                    s.put((X + k, y, z), col['quoin'], 'quoin')
            for y in range(yf - 1, yf + 1):                                # 前面的 transom
                for z in range(C['cheek_bottom'], C['cheek_bottom'] + C['transom_h']):
                    s.put((X + k, y, z), col['carriage'], 'transom')
        for sg, nm in ((-1, 'aft'), (1, 'fwd')):                           # 環首螺栓（breeching、gun tackle）；x 是沿船長 ⇒ 名字是船尾側／船頭側，不是左右舷
            k = max(C['cheek_k']) + 1
            y, z = yf - C['eye_back'], C['eye_z']
            s.put((X + sg * k, y, z), col['iron'], 'eyebolt')
            s.points['eye-' + nm] = (X + sg * k, y, z)
        s.points['muzzle'] = (X, int(s.muzzle_y) - 1, Z)
        s.points['train'] = (X, yr, C['bed_z'])                          # 砲架尾（train tackle 綁這裡）
        s.points['cascabel'] = (X, min(y for (x, y, z) in s.cells if s.kind[(x, y, z)] == 'cascabel'), Z)
        bad = [k for k in s.cells if not (0 <= k[0] < W and 0 <= k[1] < L and 0 <= k[2] < H)]
        assert not bad, ('有格在砲的框外', bad[:5])
        s.front_y = yf
        return s


class Battery:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['guns']
        B = s.P['base']
        have = set(existing_links(ASSEMBLY))
        hide = [h for h in B['hide_links'] if h in have]     # 引擎不准藏還不存在的關聯 ⇒ 先查
        s.hidden = hide
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(hide) if hide else None)
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        m = a[a[:, 2] < 200]
        s.W = np.zeros((1024, 320, 200), np.uint8)
        s.W[m[:, 0], m[:, 1], m[:, 2]] = m[:, 3]
        s.gun = Gun(s.P['gun']).build()
        s.g = np.array([k for k in s.gun.cells], dtype=np.int32)

    def deck(s, x):
        for a, b, z in s.P['deck_z']['segments']:
            if (a is None or x >= a) and (b is None or x < b):
                return z
        raise ValueError(x)

    def hits(s, at):
        p = s.g + np.array(at)
        return int((s.W[p[:, 0], p[:, 1], p[:, 2]] > 0).sum())

    def place(s):
        G = s.P['gun']
        W, L, H = G['size']
        s.links = []
        s.rows = []
        for po in s.P['ports']:
            n, (x0, x1) = po['n'], po['x']
            xc = (x0 + x1) // 2
            zd = s.deck(xc)
            yin = po['sill_y_in']
            at0 = [xc - G['axis_x'], yin - 1 - s.gun.front_y, zd]
            # 先退得少、再挪得少：每退一格都試左右挪 0、−1、+1、−2、+2（砲管 5 格寬、砲門約 10 格寬 ⇒ 挪 2 格還在開口裡）
            found = None
            for back in range(s.P['max_back'] + 1):
                for dx in s.P['dx_try']:
                    at = [at0[0] + dx, at0[1] - back, at0[2]]
                    if not s.hits(at):
                        found = (back, dx, at)
                        break
                if found:
                    break
            if found is None:
                back, dx, at = s.P['max_back'], 0, [at0[0], at0[1] - s.P['max_back'], at0[2]]
            else:
                back, dx, at = found
            h = s.hits(at)
            row = {'n': n, 'xc': xc, 'deck': zd, 'sill_y_in': yin, 'at_S': list(at), 'back': back, 'dx': dx, 'hits_S': h}
            # P 舷：mirror=y ⇒ at.y ＝ 321 − y0 − H（同 channels）；量鏡過去的那一門撞不撞
            atP = [at[0], 321 - at[1] - L, at[2]]
            pm = s.g.copy()
            pm[:, 1] = L - 1 - pm[:, 1]
            pm = pm + np.array(atP)
            row['at_P'] = atP
            row['hits_P'] = int((s.W[pm[:, 0], pm[:, 1], pm[:, 2]] > 0).sum())
            mz = at[1] + s.gun.muzzle_y
            row['muzzle_y'] = round(mz, 1)
            row['muzzle_out'] = round(mz - (po['sill_y_out'] + 1), 1)      # 砲口伸出船殼外面幾格
            row['skip'] = h > 0 or row['hits_P'] > 0
            s.rows.append(row)
            if not row['skip']:
                s.links.append({'name': '砲-S%02d' % n, 'at': at, 'mirror': ''})
                s.links.append({'name': '砲-P%02d' % n, 'at': atP, 'mirror': 'y'})

    def verify(s):
        G = s.P['gun']
        W, L, H = G['size']
        v = {'gun_cells': len(s.gun.cells), 'by_kind': {}, 'colors': {}}
        for k, kd in s.gun.kind.items():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
            c = str(s.gun.cells[k])
            v['colors'][c] = v['colors'].get(c, 0) + 1
        # 砲本身左右對稱（x 對 axis_x）
        X = G['axis_x']
        v['gun_asym'] = sum(1 for (x, y, z), c in s.gun.cells.items() if s.gun.cells.get((2 * X - x, y, z)) != c)
        # 一門砲自己是一塊
        A = np.zeros((W, L, H), bool)
        for k in s.gun.cells:
            A[k] = True
        v['gun_components'] = int(ndimage.label(A)[1])
        # 全部擺上去：互相重疊、浮空（跟現況連在一起）
        occ = {}
        allc = []
        for lk in s.links:
            p = s.g.copy()
            if lk['mirror'] == 'y':
                p[:, 1] = L - 1 - p[:, 1]
            p = p + np.array(lk['at'])
            for q in map(tuple, p):
                occ[q] = occ.get(q, 0) + 1
            allc.append(p)
        v['guns_placed'] = len(s.links)
        v['guns_overlap_each_other'] = sum(1 for q, c in occ.items() if c > 1)
        allp = np.concatenate(allc) if allc else np.zeros((0, 3), np.int32)
        v['guns_overlap_world'] = int((s.W[allp[:, 0], allp[:, 1], allp[:, 2]] > 0).sum()) if len(allp) else 0
        # 輪子站在甲板上：每一門最低那一層正下方是現況的實心
        z0 = s.g[:, 2] == 0
        sup = []
        for lk in s.links:
            p = s.g[z0].copy()
            if lk['mirror'] == 'y':
                p[:, 1] = L - 1 - p[:, 1]
            p = p + np.array(lk['at'])
            sup.append(int((s.W[p[:, 0], p[:, 1], p[:, 2] - 1] > 0).sum()))
        v['wheel_cells_on_deck_min'] = min(sup) if sup else 0
        v['wheel_cells_bottom'] = int(z0.sum())
        v['ports'] = s.rows
        v['skipped'] = [r['n'] for r in s.rows if r['skip']]
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + len(s.gun.cells) * len(s.links)
        v['hidden_for_base'] = s.hidden
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'guns')
        os.makedirs(out, exist_ok=True)
        rows = sorted((x, y, z, c) for (x, y, z), c in s.gun.cells.items())
        p = os.path.join(out, 'gun24.vox.txt')
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# gun24 —— 24 磅長砲＋truck carriage 一門（自己的座標，砲口朝 +y、軸在 x %d／z %d）（%d 格）\n' % (s.P['gun']['axis_x'], s.P['gun']['axis_z'], len(rows))
            + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        pl = os.path.join(s.design, 'guns_placement.json')
        json.dump({'note': '每個 gun deck 砲門一條關聯（關聯進 甲板-gun；S 舷照原樣、P 舷 mirror=y）；at ＝ 子作品原點在世界的位置', 'subwork': s.P['subwork']['id'],
                   'links': s.links, 'points_local': {k: list(v) for k, v in s.gun.points.items()}},
                  open(pl, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files = {'gun24': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()},
                   'placement': {'links': len(s.links), 'sha256': hashlib.sha256(open(pl, 'rb').read()).hexdigest()}}


def render_sheet(B, path):
    f12, f18 = DD._font(13), DD._font(20)
    G = B.P['gun']
    W, L, H = G['size']
    cells = B.gun.cells
    sc = 12

    def view(axes, flip_h=False):
        a, b, depth = axes                      # 畫面橫軸、縱軸（往上）、往裡看的軸
        dims = {'x': W, 'y': L, 'z': H}
        img = np.zeros((dims[b], dims[a], 3), np.uint8)
        img[:] = DD.PAPER
        idx = {'x': 0, 'y': 1, 'z': 2}
        best = {}
        for k, c in cells.items():
            u, v_, d = k[idx[a]], k[idx[b]], k[idx[depth]]
            if (u, v_) not in best or d > best[(u, v_)][0]:
                best[(u, v_)] = (d, c)
        for (u, v_), (d, c) in best.items():
            img[dims[b] - 1 - v_, (dims[a] - 1 - u) if flip_h else u] = DP.rgb332(c)
        return Image.fromarray(img).resize((dims[a] * sc, dims[b] * sc), Image.NEAREST)
    side = view(('y', 'z', 'x'))                 # 從 +x 看（砲口在右）
    top = view(('y', 'x', 'z'))                  # 從上面看
    front = view(('x', 'z', 'y'))                # 從砲口那一頭看
    PADL = 40
    Wd = PADL + side.size[0] + 40 + front.size[0] + 60
    can = Image.new('RGB', (max(Wd, 1500), 80 + side.size[1] + top.size[1] + 520), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), B.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '一門砲（自己的座標，每格 %d px）：左上 從側面看（砲口在右）、右上 從砲口看、左下 從上面看；下：gun deck 擺放（俯視，S 舷）' % sc, font=f12, fill=DD.INK)
    can.paste(side, (PADL, 66))
    can.paste(front, (PADL + side.size[0] + 40, 66))
    can.paste(top, (PADL, 66 + side.size[1] + 20))
    # 擺放俯視：x 150–680、y 160–240，砲（S 舷）疊在現況上
    xa, xb, ya, yb = 150, 680, 160, 236
    s2 = 2
    img = np.zeros((yb - ya, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    occ = {}
    for lk in B.links:
        if lk['mirror']:
            continue
        for (x, y, z), c in cells.items():
            q = (x + lk['at'][0], y + lk['at'][1])
            if xa <= q[0] < xb and ya <= q[1] < yb:
                zz = z + lk['at'][2]
                if q not in occ or zz > occ[q][0]:
                    occ[q] = (zz, c)
    zcut = 101
    for ix, x in enumerate(range(xa, xb)):
        for iy, y in enumerate(range(yb - 1, ya - 1, -1)):
            if (x, y) in occ:
                img[iy, ix] = DP.rgb332(occ[(x, y)][1])
                continue
            col_ = B.W[x, y, :zcut]
            nz = np.nonzero(col_)[0]
            if len(nz):
                c = int(col_[nz[-1]])
                img[iy, ix] = (np.array(DP.rgb332(c)) * 0.55 + np.array(DD.PAPER) * 0.45).astype(np.uint8)
    pl = Image.fromarray(img).resize(((xb - xa) * s2, (yb - ya) * s2), Image.NEAREST)
    y = 66 + side.size[1] + 20 + top.size[1] + 30
    dr.text((PADL, y - 18), 'gun deck 俯視（z < %d，現況淡色、砲原色；x %d–%d、y %d–%d）' % (zcut, xa, xb - 1, ya, yb - 1), font=f12, fill=DD.INK)
    can.paste(pl, (PADL, y))
    y += pl.size[1] + 16
    v = B.v
    lines = ['一門 %d 格（%s）；左右不對稱 %d、元件 %d' % (v['gun_cells'], '、'.join('%s %d' % kv for kv in sorted(v['by_kind'].items())), v['gun_asym'], v['gun_components']),
             '擺上 %d 門（%d 個砲門 × 兩舷）；跳過的砲門 %s；跟現況重疊 %d、彼此重疊 %d；每門輪子底下踩到甲板的最少 %d／%d 格；組裝件預期 %d' % (
                 v['guns_placed'], v['guns_placed'] // 2, v['skipped'] or '無', v['guns_overlap_world'], v['guns_overlap_each_other'], v['wheel_cells_on_deck_min'], v['wheel_cells_bottom'], v['expect_assembly_after']),
             '每個砲門（退＝往裡退幾格、挪＝沿船長挪幾格、口外＝砲口伸出船殼外幾格）：' + '  '.join('%d:退%d挪%d口外%s' % (r['n'], r['back'], r['dx'], r['muzzle_out']) for r in v['ports'][:8]),
             '　' + '  '.join('%d:退%d挪%d口外%s' % (r['n'], r['back'], r['dx'], r['muzzle_out']) if not r['skip'] else '%d:不放' % r['n'] for r in v['ports'][8:])]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, can.size[0], y + 16))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    B = Battery(design)
    B.place()
    v = B.verify()
    B.write()
    v['files'] = B.files
    json.dump(v, open(os.path.join(design, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(B, os.path.join(design, 'sheet18_guns_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('ports',)}, ensure_ascii=False))
    for r in v['ports']:
        print(r)


if __name__ == '__main__':
    main()

# 新圖紙 09（房間子作品）：plan.json 的 rooms 段 ＋ 船殼（deckworks.world_mark）＋ 四層甲板（masks/decks/*.vox.txt）
#   ⇒ masks/rooms/<piece>.vox.txt、verify_rooms.json、sheet09_rooms_v1.png
# 用法：python -I draft_rooms.py <design 資料夾>
#   · whole（全寬艙壁）：兩舷一起產生，絕對座標（子作品尺寸 ＝ 船殼、at=0,0,0）
#   · side（舷側艙房）：只產生 y > 160 那一舷，清單是子作品自己的座標（原點 ＝ 外框最小角）；
#     關聯兩次：照原樣 at ＝ 外框最小角，另一舷 mirror=y、at.y ＝ 321 − y0 − h（160 ↔ 160 的鏡面）
#   · 牆 1 格厚，從甲板面到上一層甲板板底下，只填還空著的艙內空氣（碰到橫樑、carlings、柱子、斜肋就讓開）
import sys, os, json, glob, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_decks as DD           # noqa: E402

X0, X1, NZ, YC, Y0, SX, SY = DD.X0, DD.X1, DD.NZ, DD.YC, DD.Y0, DD.SX, DD.SY
UP = {'orlop': 'berth', 'berth': 'gun', 'gun': 'spar'}
PANEL, FRAME = 1, 2


class Rooms:
    def __init__(s, design):
        s.design = design
        s.K = DD.Decks(design)                                   # 船殼、艙內空氣、量牆、甲板高度
        s.R = s.K.plan['rooms']
        # 四層甲板：讀產物（清單），不重算
        s.DECK = np.zeros((SX, SY, NZ), np.uint8)
        s.deck_files = {}
        for i, d in enumerate(DD.DECKS):
            p = os.path.join(design, 'masks', 'decks', d + '.vox.txt')
            a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
            s.DECK[a[:, 0] - X0, a[:, 1] - Y0, a[:, 2]] = i + 1
            s.deck_files[d] = {'cells': len(a), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        s.OCC = s.DECK > 0
        s.PIECE = {k: np.zeros((SX, SY, NZ), np.uint8) for k in s.R['pieces'] if k != 'note'}
        s.log = {k: {'walls': []} for k in s.PIECE}
        s._holes = {}

    def hole(s, deck, z):
        key = (deck, z)
        if key not in s._holes:
            s._holes[key] = s.K.hole2d(deck, z)
        return s._holes[key]

    def zrange(s, deck, x, w):
        z0 = s.K.D(deck, x)
        if z0 is None:
            return None
        if 'z_top' in w:
            return z0, w['z_top']
        if 'height' in w:
            return z0, z0 + w['height'] - 1
        up = UP[deck]
        Du = s.K.D(up, x)
        return z0, Du - 2                                        # 上一層甲板板底下那一格

    def wall(s, w):
        P = s.R['pieces'][w['piece']]
        deck, kind = P['deck'], P['kind']
        cells = {}                                               # (ix, iy, z) → (u, z, z0, ztop)：u ＝ 牆面上的橫向座標
        doors = w.get('doors', [])
        dh = s.R['door']['headroom']
        if 'athwart' in w:
            xs = range(w['athwart'], w['athwart'] + w.get('width', 1))
            sides = (1, -1) if kind == 'whole' else (1,)
            for x in xs:
                zr = s.zrange(deck, x, w)
                if zr is None:
                    continue
                z0, zt = zr
                for z in range(z0, zt + 1):
                    for sgn in sides:
                        run = s.K.wall(x, z, sgn)
                        if run is None:
                            continue
                        lim = abs(run - (YC - Y0))
                        for dy in range(w['dy'][0], min(w['dy'][1], lim) + 1):
                            if sgn < 0 and dy == 0:
                                continue
                            sdy = sgn * dy
                            if any(a <= sdy <= b for a, b in doors) and z < zt + 1 - dh - (0 if 'height' in w else 0) and z <= z0 + (zt - z0) - dh:
                                continue
                            cells[(x - X0, YC - Y0 + sdy, z)] = (sdy, z, z0, zt)
        else:
            dy = w['fore_aft']
            for x in range(w['x'][0], w['x'][1] + 1):
                zr = s.zrange(deck, x, w)
                if zr is None:
                    continue
                z0, zt = zr
                for z in range(z0, zt + 1):
                    if any(a <= x <= b for a, b in doors) and z <= z0 + (zt - z0) - dh:
                        continue
                    cells[(x - X0, YC - Y0 + dy, z)] = (x, z, z0, zt)
        # 只填還空著的艙內空氣
        # 桅孔留給桅杆（照同一條桅軸、每個 z 各自算孔）—— 不然矮檻、艙壁會橫過桅孔
        keep = {k: v for k, v in cells.items() if s.K.A[k] and not s.OCC[k] and not s.hole(deck, k[2])[k[0], k[1]]}
        # 框：牆面上 4 鄰居有一格不是牆（兩端、門框、牆頂、牆腳）或每 frame_every 一根立柱 ⇒ 136，其餘 177
        U = {(v[0], v[1]): k for k, v in keep.items()}
        fe = s.R['frame_every']
        out = {}
        for k, (u, z, z0, zt) in keep.items():
            edge = any((u + a, z + b) not in U for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            post = (u % fe == 0)
            out[k] = FRAME if (edge or post) else PANEL
        return out

    def build(s):
        order = [k for k in s.PIECE if s.R['pieces'][k]['kind'] == 'whole'] + [k for k in s.PIECE if s.R['pieces'][k]['kind'] == 'side']
        for pk in order:
            for w in s.R['walls']:
                if w['piece'] != pk:
                    continue
                cells = s.wall(w)
                n = 0
                for (i, j, z), c in cells.items():
                    if s.OCC[i, j, z]:
                        continue
                    s.PIECE[pk][i, j, z] = c
                    s.OCC[i, j, z] = True
                    n += 1
                    if s.R['pieces'][pk]['kind'] == 'side':      # 另一舷的鏡像位置也預留（之後的牆不准佔）
                        jm = 2 * (YC - Y0) - j
                        s.OCC[i, jm, z] = True
                s.log[pk]['walls'].append({'name': w['name'], 'cells': n})

    def composed(s):
        """把 side 的另一舷鏡像補上，給驗收與圖紙用（作品裡是 mirror=y 關聯，不是格子）。"""
        C = np.zeros((SX, SY, NZ), np.uint8)
        for pk, M in s.PIECE.items():
            C = np.where(M > 0, M, C)
            if s.R['pieces'][pk]['kind'] == 'side':
                Mm = M[:, ::-1, :]
                C = np.where(Mm > 0, Mm, C)
        return C

    def tidy(s):
        """船殼＋甲板＋房間合起來的封閉空腔 ⇒ 補進鄰居那一件（side 那件只補 y > 160 那一舷，另一舷靠鏡像）。"""
        C = s.composed()
        SOL = (s.K.G > 0) | (s.DECK > 0) | (C > 0)
        lab, n = ndimage.label(~SOL)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        filled = {}
        for k in range(1, n + 1):
            if k in edge:
                continue
            idx = np.argwhere(lab == k)
            if len(idx) > 200:
                raise SystemExit('封閉空腔太大（%d 格 @ %s）—— 有房間沒開門？' % (len(idx), idx[0] + [X0, Y0, 0]))
            for i, j, z in idx:
                for pk, M in s.PIECE.items():
                    side = s.R['pieces'][pk]['kind'] == 'side'
                    jj = j
                    if side and j < YC - Y0:
                        jj = 2 * (YC - Y0) - j                    # 左舷的空腔 ＝ 右舷那格的鏡像
                    nb = [M[i + a, jj + b, z + c] for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
                          if 0 <= jj + b < SY]
                    nb = [v for v in nb if v]
                    if nb and not M[i, jj, z]:
                        M[i, jj, z] = FRAME if FRAME in nb else PANEL
                        filled[pk] = filled.get(pk, 0) + 1
                        break
        s.cavity_filled = filled

    def verify(s):
        C = s.composed()
        v = {}
        SOL = (s.K.G > 0) | (s.DECK > 0) | (C > 0)
        lab, n = ndimage.label(~SOL)
        edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        cav = [k for k in range(1, n + 1) if k not in edge]
        v['cavities_composed'] = {'n': len(cav), 'cells': int(sum((lab == k).sum() for k in cav))}
        v['composed_components'] = int(ndimage.label(SOL)[1])
        v['rooms_cells_composed'] = int((C > 0).sum())
        v['overlap_with_hull_or_decks'] = int(((C > 0) & ((s.K.G > 0) | (s.DECK > 0))).sum())
        v['outside_inner_air'] = int(((C > 0) & ~s.K.A).sum())
        v['mirror_mismatch_composed'] = int(((C > 0) != (C[:, ::-1, :] > 0)).sum())
        tot = 0
        for pk, M in s.PIECE.items():
            idx = np.argwhere(M > 0)
            P = s.R['pieces'][pk]
            e = {'kind': P['kind'], 'cells': len(idx), 'frame': int((M == FRAME).sum()), 'panel': int((M == PANEL).sum()),
                 'components': int(ndimage.label(M > 0)[1]), 'walls': s.log[pk]['walls']}
            if P['kind'] == 'side' and len(idx):
                lo, hi = idx.min(0), idx.max(0)
                e['box_min'] = [int(lo[0] + X0), int(lo[1] + Y0), int(lo[2])]
                e['size'] = [int(hi[0] - lo[0] + 1), int(hi[1] - lo[1] + 1), int(hi[2] - lo[2] + 1)]
                e['min_dy'] = int(lo[1] + Y0 - YC)
                y0, h = e['box_min'][1], e['size'][1]
                e['links'] = {'as_is': {'at': e['box_min'], 'mirror': ''},
                              'mirrored': {'at': [e['box_min'][0], 321 - y0 - h, e['box_min'][2]], 'mirror': 'y'}}
            tot += len(idx) * (2 if P['kind'] == 'side' else 1)
            v[pk] = e
        v['total_composed'] = tot
        # 門：每一間封起來的房間都要有開口通到外面 —— 上面的空腔檢查已經涵蓋（沒有門的房間會是一個大空腔）
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'rooms')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*')):
            os.remove(f)
        col = {PANEL: s.R['colors']['panel'], FRAME: s.R['colors']['frame']}
        s.files = {}
        for pk, M in s.PIECE.items():
            P = s.R['pieces'][pk]
            idx = np.argwhere(M > 0)
            off = np.array([X0, Y0, 0])
            if P['kind'] == 'side':
                off = off - (idx.min(0) + np.array([X0, Y0, 0])) + 0      # 子作品自己的座標
                loc = idx - idx.min(0)
                rows = ['%d,%d,%d,%d' % (a, b, c, col[M[i, j, k]]) for (a, b, c), (i, j, k) in zip(loc, idx)]
                head = '# %s —— %s（子作品 %s；y > 160 那一舷；自己的座標，原點 ＝ 作品座標 %s；%d 格）\n' % (pk, P['title'], P['id'], s.v[pk]['box_min'], len(idx))
            else:
                rows = ['%d,%d,%d,%d' % (i + X0, j + Y0, k, col[M[i, j, k]]) for i, j, k in idx]
                head = '# %s —— %s（子作品 %s；兩舷一整件；at=0,0,0；%d 格）\n' % (pk, P['title'], P['id'], len(idx))
            p = os.path.join(out, pk + '.vox.txt')
            open(p, 'w', encoding='utf-8', newline='\n').write(head + '\n'.join(rows) + '\n')
            s.files[pk] = {'cells': len(idx), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


def render_sheet(Rm, path):
    K = Rm.K
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    cols = Rm.R['colors']
    panel, frame = DD.pal(cols['panel']), DD.pal(cols['frame'])
    xa, xb = 120, 665
    pv = 2.5
    C = Rm.composed()
    side_mask = np.zeros(C.shape, bool)
    for pk, M in Rm.PIECE.items():
        if Rm.R['pieces'][pk]['kind'] == 'side':
            side_mask |= M[:, ::-1, :] > 0                       # 鏡像那一舷（關聯進來的）
    plans = []
    for d in ('gun', 'berth', 'orlop'):
        rgb = np.zeros((xb - xa, SY, 3), np.float32)
        rgb[:] = DD.PAPER
        di = DD.DECKS.index(d) + 1
        for ix in range(xb - xa):
            x = ix + xa
            Dz = K.D(d, x)
            zz = (Dz - 1) if Dz else 41
            rgb[ix][K.G[x - X0, :, zz] > 0] = DD.HULLC
            if Dz:
                pl = Rm.DECK[x - X0, :, Dz - 1] == di
                rgb[ix][pl] = (236, 226, 206)                      # 甲板板（淡）
                op = K.A[x - X0, :, Dz - 1] & ~pl
                rgb[ix][op] = (150, 152, 158)                      # 開口
                above = (Rm.DECK[x - X0, :, Dz:Dz + 4] == di).any(1)
                rgb[ix][above] = (190, 170, 140)                   # 圍板、waterway、桅座
        # 這一層的牆（取甲板面上 2 格那一層的切面 ⇒ 門洞看得出來）
        for ix in range(xb - xa):
            x = ix + xa
            Dz = K.D(d, x)
            if not Dz:
                continue
            m = (C[x - X0, :, Dz + 2] > 0)
            mm = side_mask[x - X0, :, Dz + 2]
            rgb[ix][m & ~mm] = frame
            rgb[ix][m & mm] = (150, 95, 60)                        # 鏡像那一舷畫淡一點
            low = (C[x - X0, :, Dz] > 0) & ~m
            rgb[ix][low] = (200, 150, 110)                         # 門洞（只剩牆腳）
        im = Image.fromarray(np.transpose(rgb.clip(0, 255).astype(np.uint8), (1, 0, 2))[::-1]).resize((int((xb - xa) * pv), int(SY * pv)), Image.NEAREST)
        plans.append((d, im))
    # 立面：gun deck 238 艦長室前艙壁（往船尾看）、berth wardroom staterooms 內壁（從中線往外看）
    elev = []
    x = 238
    a = np.zeros((SY, NZ, 3), np.uint8)
    a[:] = DD.PAPER
    a[K.G[x - X0] > 0] = DD.HULLC
    a[Rm.DECK[x - X0] > 0] = (200, 185, 160)
    for v, c in ((DD.pal(cols['panel']), PANEL), (DD.pal(cols['frame']), FRAME)):
        a[C[x - X0] == c] = v
    im = Image.fromarray(np.transpose(a, (1, 0, 2))[::-1][NZ - 112:NZ - 72]).resize((SY * 5, 40 * 5), Image.NEAREST)
    elev.append(('gun deck x = 238 艦長室前艙壁（往船尾看；門洞 9 格寬）', im))
    j = YC - Y0 + 20
    b = np.zeros((xb - xa, NZ, 3), np.uint8)
    b[:] = DD.PAPER
    b[K.G[xa - X0:xb - X0, j] > 0] = DD.HULLC
    b[Rm.DECK[xa - X0:xb - X0, j] > 0] = (200, 185, 160)
    for v, c in ((DD.pal(cols['panel']), PANEL), (DD.pal(cols['frame']), FRAME)):
        b[C[xa - X0:xb - X0, j] == c] = v
    im = Image.fromarray(np.transpose(b, (1, 0, 2))[::-1][NZ - 82:NZ - 55][:, 160 - xa:330 - xa]).resize((170 * 5, 27 * 5), Image.NEAREST)
    elev.append(('berth deck dy = 20 wardroom staterooms 內壁（x 160–330，從中線往外看；每間一個門洞）', im))
    PADL = 70
    W = int((xb - xa) * pv) + PADL + 40
    H = 80 + len(plans) * (int(SY * pv) + 48) + sum(e.size[1] + 40 for _, e in elev) + 40
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), Rm.R['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '平面：甲板面上 2 格那一層的切面（牆 ＝ 深棕；淡一點的 ＝ 另一舷 mirror=y 關聯進來的；淺棕 ＝ 門洞只剩牆腳）　板 %d、框 %d　1 格 ＝ 0.1 m' % (cols['panel'], cols['frame']), font=f12, fill=DD.INK)
    y = 76
    for d, im in plans:
        dr.text((PADL, y), '%s deck' % d, font=f14, fill=DD.DECKC[d])
        y += 22
        can.paste(im, (PADL, y))
        for L in Rm.R['labels']:
            if L['deck'] != d:
                continue
            px = PADL + (L['x'] - xa) * pv
            py = y + (SY - 1 - (YC - Y0 + L['dy'])) * pv
            tw = dr.textlength(L['t'], font=f12)
            dr.text((px - tw / 2, py - 8), L['t'], font=f12, fill=(30, 30, 30))
        for x in range(150, xb, 50):
            dr.text((PADL + (x - xa) * pv - 8, y + SY * pv + 2), str(x), font=f12, fill=(130, 130, 130))
        y += int(SY * pv) + 26
    for cap, im in elev:
        dr.text((PADL, y), cap, font=f14, fill=DD.INK)
        can.paste(im, (PADL, y + 22))
        y += im.size[1] + 40
    can = can.crop((0, 0, W, y + 10))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    Rm = Rooms(design)
    Rm.build()
    Rm.tidy()
    v = Rm.verify()
    Rm.write()
    v['files'] = Rm.files
    v['deck_files_read'] = Rm.deck_files
    v['cavity_filled'] = Rm.cavity_filled
    json.dump(v, open(os.path.join(design, 'verify_rooms.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(Rm, os.path.join(design, 'sheet09_rooms_v1.png'))
    short = {k: v[k] for k in ('cavities_composed', 'composed_components', 'rooms_cells_composed', 'overlap_with_hull_or_decks', 'outside_inner_air',
                               'mirror_mismatch_composed', 'total_composed', 'cavity_filled')}
    for pk in Rm.PIECE:
        short[pk] = {k: v[pk][k] for k in v[pk] if k != 'walls'}
        short[pk]['walls'] = ['%s %d' % (w['name'], w['cells']) for w in v[pk]['walls']]
    print(json.dumps(short, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

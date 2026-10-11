# 新圖紙 20（艙口梯）：plan.json 的 ladders 段 ＋ deckworks.hatches ＋ 組裝件的現況（梯子加進來之前）
#   ⇒ masks/ladders/{gun,berth,orlop}.vox.txt（世界座標）、design/rig_points_ladders.json、design/ladder_ropes.json（扶手繩）、
#      verify_ladders.json、sheet20_ladders_v1.png
# 用法：python -I draft_ladders.py <design 資料夾>
#   · 一座梯子：上端頂在上一層艙口的一邊（圍板或跨過艙口的橫樑的內面），往 dir 那一邊斜下到下一層甲板
#   · 試的順序：dir（照清單）→ band（側板高 4、3）→ cap_up（上端多出 0、1 格）；第一個「梯子每一格是空氣、
#     踏板上方 headroom 格是空氣、梯腳外 landing 格是空氣、扶手柱與扶手繩不穿東西」的就用
#   · 先放的梯子也算現況（上下兩層的梯子在同一個艙口疊在一起時，後放的會讓開）
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402
from draft_guns import existing_links           # noqa: E402

ZMAX = 200


class Ladders:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['ladders']
        s.G = s.P['geometry']
        s.decks = s.plan['interior']['decks']
        s.hatch = {h['name']: h for h in s.plan['deckworks']['hatches']['list']}
        s.coam = s.plan['deckworks']['hatches']['coaming']['height']
        B = s.P['base']
        have = set(existing_links(ASSEMBLY))
        s.hidden = [h for h in B['hide_links'] if h in have]
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(s.hidden) if s.hidden else None)
        assert len(a) == B['assembly_voxels'], ('讀到的現況格數對不上', len(a), B['assembly_voxels'])
        m = a[a[:, 2] < ZMAX]
        s.W = np.zeros((1024, 320, ZMAX), np.uint8)
        s.W[m[:, 0], m[:, 1], m[:, 2]] = m[:, 3]
        s.cells, s.kind, s.owner = {}, {}, {}
        s.anchors, s.ropes, s.rows, s.notes = [], [], [], []

    def dz(s, deck, x):
        for a, b, z in s.decks[deck]['segments']:
            if (a is None or x >= a) and (b is None or x < b):
                return z
        return None

    def free(s, k):
        return s.W[k] == 0 and k not in s.cells

    def edges(s, h, U, y0, y1):
        """艙口裡能當梯子上端的邊：上一層甲板板那一層（z ＝ 甲板面 − 1）沿 x 的實心↔空氣交界（圍板、跨過艙口的橫樑）。
        回傳 [(xe, d)]：xe ＝ 貼著那個實心的第一欄空氣，d ＝ 往哪邊斜下。梯寬 y0..y1 每一列都要一樣。"""
        x0, x1 = h['x']
        zp = s.dz(U, (x0 + x1) // 2) - 1
        out = []
        for x in range(x0 - 1, x1 + 2):
            col = [s.W[x, y, zp] > 0 for y in range(y0, y1 + 1)]
            nxt = [s.W[x + 1, y, zp] > 0 for y in range(y0, y1 + 1)]
            if all(col) and not any(nxt):
                out.append((x + 1, 1))
            if not any(col) and all(nxt):
                out.append((x, -1))
        return out, zp + 1

    def shape(s, xe, d, y0, y1, zcap, zl, band):
        """一座梯子的格子（世界座標）→ dict cell → (color, kind)；欄 t 的側板上緣 zs(t) ＝ floor(zcap − 1.5 t)。"""
        G, C = s.G, s.P['colors']
        slope = G['rise'] / G['run']
        cells = {}
        t = 0
        cols = []
        while True:
            zs = int(np.floor(zcap - slope * t))
            lo = max(zl, zs - band + 1)
            x = xe + d * t
            for y in (y0, y1):
                for z in range(lo, zs + 1):
                    cells[(x, y, z)] = (C['stringer'], 'stringer')
            cols.append((t, x, zs))
            if zs - band + 1 <= zl:
                break
            t += 1
            if t > 60:
                return None, None, None
        R = t + 1
        j = 0
        treads = []
        while True:
            zt = zcap - G['rise'] * j - 3
            if zt < zl + 2:
                break
            for tt in (G['run'] * j + 1, G['run'] * j + 2):
                if tt >= R:
                    continue
                x = xe + d * tt
                for y in range(y0 + 1, y1):
                    cells[(x, y, zt)] = (C['tread'], 'tread')
            treads.append(zt)
            j += 1
        return cells, cols, treads

    def try_one(s, L, h, d, y0, y1, band, cap_up, edges_ok):
        G = s.G
        U, deck = L['upper'], L['deck']
        cand = [e for e in edges_ok if e[1] == d]
        res = []
        for xe, _ in cand:
            zu = s.dz(U, xe)
            zcap = zu + s.coam[U] - 1 + cap_up
            # 下一層的甲板面：梯腳那一欄（先估長度再量）
            zl = None
            for guess in range(40):
                xf = xe + d * guess
                z_ = s.dz(deck, xf)
                if z_ is None:
                    break
                if zcap - 1.5 * guess - band + 1 <= z_:
                    zl = z_
                    break
            if zl is None:
                res.append((xe, '下一層在這裡沒有甲板'))
                continue
            cells, cols, treads = s.shape(xe, d, y0, y1, zcap, zl, band)
            if cells is None:
                res.append((xe, '太長'))
                continue
            xf = cols[-1][1]
            if any(s.dz(deck, x) != zl for _, x, _ in cols[-3:]):
                res.append((xe, '梯腳跨過甲板高低差'))
                continue
            bad = [k for k in cells if not s.free(k)]
            if bad:
                res.append((xe, '梯子撞到 %d 格（第一格 %s）' % (len(bad), bad[0])))
                continue
            # 梯腳要踩在甲板板上（兩根側板最下面那一格底下是實心）
            if not all(s.W[xf, y, zl - 1] > 0 for y in (y0, y1)):
                res.append((xe, '梯腳底下不是甲板'))
                continue
            head = []
            for t, x, zs in cols:
                for y in range(y0 + 1, y1):
                    for z in range(zs + 1, min(zs + 1 + G['headroom'], zu)):      # 只量兩層甲板之間（上一層甲板面以上是露天／別的東西，例：fore scuttle 上方的 bowsprit 根部）
                        if (x, y, z) in cells:
                            continue
                        if not s.free((x, y, z)):
                            head.append((x, y, z))
            if head:
                res.append((xe, '頭頂撞到 %d 格（第一格 %s）' % (len(head), head[0])))
                continue
            land = [(xf + d * k, y, z) for k in range(1, G['landing'] + 1) for y in range(y0, y1 + 1) for z in range(zl, zl + G['headroom'])]
            land = [k for k in land if not s.free(k)]
            if land:
                res.append((xe, '梯腳外撞到 %d 格（第一格 %s）' % (len(land), land[0])))
                continue
            # 扶手：兩根側板各兩根鐵柱（上 ＝ 第 1 欄、下 ＝ 倒數第 3 欄起往上找），柱頂是固定點；繩拉在兩柱頂之間不准穿東西
            # （試的順序：下柱 R−3／R−4／R−5 × 柱高 stanchion_h、−1、−2；companion 那座的繩會擦到上一層（gun deck）艙口邊的橫樑）
            R = len(cols)
            got_p = None
            for tb in (R - 3, R - 4, R - 5):
                if tb - 1 < 4:
                    break
                for hh in (G['stanchion_h'], G['stanchion_h'] - 1, G['stanchion_h'] - 2):
                    posts, tops = {}, {}
                    okp = True
                    for side, y in (('lo', y0), ('hi', y1)):
                        for which, t in (('top', 1), ('bot', tb)):
                            _, x, zs = cols[t]
                            for z in range(zs + 1, zs + 1 + hh):
                                if not s.free((x, y, z)) or (x, y, z) in cells:
                                    okp = False
                                posts[(x, y, z)] = (s.P['colors']['iron'], 'stanchion')
                            tops[(side, which)] = (x, y, zs + hh)
                    if not okp:
                        continue
                    allc = dict(cells)
                    allc.update(posts)
                    rope_bad = []
                    for side in ('lo', 'hi'):
                        a_, b_ = np.array(tops[(side, 'top')]) + 0.5, np.array(tops[(side, 'bot')]) + 0.5
                        n = int(np.linalg.norm(b_ - a_) * 3) + 2
                        for tt in np.linspace(0, 1, n):
                            q = tuple(int(np.floor(v)) for v in a_ + (b_ - a_) * tt)
                            if q in allc:
                                continue
                            if not s.free(q):
                                rope_bad.append(q)
                    if not rope_bad:
                        got_p = (tb, hh, allc, tops)
                        break
                if got_p:
                    break
            if not got_p:
                res.append((xe, '扶手柱或扶手繩放不下'))
                continue
            tb, hh, allc, tops = got_p
            return dict(xe=xe, d=d, y=[y0, y1], zcap=zcap, zl=zl, band=band, cap_up=cap_up, R=R, xf=xf,
                        treads=len(treads), cells=allc, tops=tops, post_bot=tb, post_h=hh), res
        return None, res

    def build(s):
        for L in s.P['list']:
            h = s.hatch[L['hatch']]
            y0, y1 = L['y']
            eds, zu = s.edges(h, L['upper'], y0, y1)
            got, why = None, []
            for d in L['dir']:
                for band in s.G['band']:
                    for cap_up in s.G['cap_up']:
                        got, r = s.try_one(L, h, d, y0, y1, band, cap_up, eds)
                        why += [(d, band, cap_up) + tuple(w) for w in r]
                        if got:
                            break
                    if got:
                        break
                if got:
                    break
            if not got:
                s.notes.append('%s 放不下：%s' % (L['id'], '；'.join('dir %d band %d cap %d x %d %s' % w for w in why)))
                s.rows.append({'id': L['id'], 'placed': False, 'edges': eds})
                continue
            for k, (c, kd) in got['cells'].items():
                s.cells[k] = c
                s.kind[k] = kd
                s.owner[k] = L['deck']
            sw = s.P['subworks'][L['deck']]
            for side in ('lo', 'hi'):
                for which in ('top', 'bot'):
                    nm = 'manrope-%s-%s-%s' % (L['id'], 'P' if side == 'lo' else 'S', which)
                    s.anchors.append({'name': nm, 'kind': 'stanchion', 'world': list(got['tops'][(side, which)]), 'owner': sw['id']})
                s.ropes.append(dict(name='梯-%s.manrope-%s' % (L['id'], 'P' if side == 'lo' else 'S'),
                                    **{'from': '%s/manrope-%s-%s-top' % (sw['path'], L['id'], 'P' if side == 'lo' else 'S'),
                                       'to': '%s/manrope-%s-%s-bot' % (sw['path'], L['id'], 'P' if side == 'lo' else 'S')},
                                    thickness=s.P['manrope']['thickness'], slack=s.P['manrope']['slack'], color=s.P['manrope']['color'], group='manrope'))
            row = {k: got[k] for k in ('xe', 'd', 'y', 'zcap', 'zl', 'band', 'cap_up', 'R', 'xf', 'treads', 'post_bot', 'post_h')}
            row.update(id=L['id'], placed=True, hatch=L['hatch'], upper=L['upper'], deck=L['deck'], cells=len(got['cells']),
                       rise=got['zcap'] - got['zl'] + 1, tried_before=len(why))
            s.rows.append(row)

    def verify(s):
        v = {'cells': len(s.cells), 'by_kind': {}, 'by_deck': {}}
        for k, kd in s.kind.items():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
            v['by_deck'][s.owner[k]] = v['by_deck'].get(s.owner[k], 0) + 1
        v['overlap_world'] = sum(1 for k in s.cells if s.W[k] > 0)
        xs = [k[0] for k in s.cells]
        xa, xb = min(xs) - 3, max(xs) + 4
        A = s.W[xa:xb] > 0
        for k in s.cells:
            A[k[0] - xa, k[1], k[2]] = True
        lab, _ = ndimage.label(A)
        base = set(np.unique(lab[s.W[xa:xb] > 0])) - {0}
        fl = [k for k in s.cells if lab[k[0] - xa, k[1], k[2]] not in base]
        v['floating'] = {'n': len(fl), 'first': [list(k) for k in fl[:6]]}
        v['ladders'] = s.rows
        v['placed'] = sum(1 for r in s.rows if r['placed'])
        v['anchors'] = len(s.anchors)
        v['ropes_total'] = len(s.ropes)
        v['notes'] = s.notes
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + len(s.cells)
        v['hidden_for_base'] = s.hidden
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'ladders')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for deck, sw in s.P['subworks'].items():
            if not isinstance(sw, dict):
                continue
            rows = sorted((x, y, z, c) for (x, y, z), c in s.cells.items() if s.owner[(x, y, z)] == deck)
            p = os.path.join(out, deck + '.vox.txt')
            open(p, 'w', encoding='utf-8', newline='\n').write(
                '# %s —— %s（世界座標，at=0,0,0；關聯進 %s）（%d 格）\n' % (deck, sw['title'], sw['path'], len(rows))
                + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            s.files[deck] = {'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'cells': len(rows)}
        rp = os.path.join(s.design, 'rig_points_ladders.json')
        json.dump({'note': '梯子扶手柱的柱頂（manrope-<梯>-<P|S>-<top|bot>）；P ＝ y 小那一側；世界座標；子作品 at 0,0,0', 'points': s.anchors},
                  open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        gp = os.path.join(s.design, 'ladder_ropes.json')
        json.dump({'note': '每座梯子兩條扶手繩（man ropes；掛在組裝件；端點是關聯路徑）', 'ropes': s.ropes},
                  open(gp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        for k, f in (('rig_points', rp), ('ropes', gp)):
            s.files[k] = {'sha256': hashlib.sha256(open(f, 'rb').read()).hexdigest()}


def render_sheet(F, path):
    """每座梯子一張側剖面（y ＝ 梯子中線那一片，往 −y 看）：現況淡色、梯子原色、扶手繩褐線。"""
    f12, f18 = DD._font(13), DD._font(20)
    sc = 4
    tiles = []
    for r in F.rows:
        if not r['placed']:
            continue
        xa, xb = min(r['xe'], r['xf']) - 14, max(r['xe'], r['xf']) + 15
        za, zb = r['zl'] - 6, r['zcap'] + 14
        yc = (r['y'][0] + r['y'][1]) // 2
        img = np.zeros((zb - za, xb - xa, 3), np.uint8)
        img[:] = DD.PAPER
        for ix, x in enumerate(range(xa, xb)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                best = None
                for y in (r['y'][0], yc):
                    c = F.cells.get((x, y, z))
                    if c is not None:
                        best = (c, True)
                        break
                if best is None and F.W[x, yc, z] > 0:
                    best = (int(F.W[x, yc, z]), False)
                if best:
                    rgb = np.array(DP.rgb332(best[0]))
                    img[iz, ix] = rgb if best[1] else (rgb * 0.45 + np.array(DD.PAPER) * 0.55).astype(np.uint8)
        im = Image.fromarray(img).resize(((xb - xa) * sc, (zb - za) * sc), Image.NEAREST)
        dr = ImageDraw.Draw(im)
        for side in ('lo',):
            a = next(p for p in F.anchors if p['name'].startswith('manrope-%s-P-top' % r['id']))['world']
            b = next(p for p in F.anchors if p['name'].startswith('manrope-%s-P-bot' % r['id']))['world']
            dr.line([((a[0] + 0.5 - xa) * sc, (zb - a[2] - 0.5) * sc), ((b[0] + 0.5 - xa) * sc, (zb - b[2] - 0.5) * sc)], fill=(150, 110, 60), width=3)
        tiles.append((r, im, xa, za))
    PADL = 30
    NC = 3
    Wd = max(max(im.size[0] for _, im, _, _ in tiles) * NC + PADL * (NC + 1), 1500)
    rowsH = []
    for i in range(0, len(tiles), NC):
        rowsH.append(max(im.size[1] for _, im, _, _ in tiles[i:i + NC]) + 64)
    can = Image.new('RGB', (Wd, 80 + sum(rowsH) + 60 + 20 * len(F.v['notes'])), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((PADL, 12), F.P['title'], font=f18, fill=DD.INK)
    dr.text((PADL, 40), '每座梯子一張側剖面（梯子中線那一片＋一根側板；現況淡色、梯子原色、扶手繩褐線；每格 %d px）' % sc, font=f12, fill=DD.INK)
    y = 66
    cw = (Wd - PADL) // NC
    for i in range(0, len(tiles), NC):
        x = PADL
        for r, im, xa, za in tiles[i:i + NC]:
            dr.text((x, y), '%s（%s → %s，%s 艙口）' % (r['id'], r['upper'], r['deck'], r['hatch']), font=f12, fill=DD.INK)
            dr.text((x, y + 18), 'x %d→%d、z %d→%d、%d 階、%d 格' % (r['xe'], r['xf'], r['zcap'], r['zl'], r['treads'], r['cells']), font=f12, fill=DD.INK)
            can.paste(im, (x, y + 42))
            x += cw
        y += rowsH[i // NC]
    v = F.v
    lines = ['%d 座、%d 格（%s）；跟現況重疊 %d、浮空 %d；組裝件預期 %d；扶手繩 %d 條' % (
        v['placed'], v['cells'], '、'.join('%s %d' % kv for kv in sorted(v['by_kind'].items())), v['overlap_world'], v['floating']['n'],
        v['expect_assembly_after'], v['ropes_total'])]
    lines += ['注意：' + t.replace('⇒', '→') for t in v['notes']]
    for t in lines:
        dr.text((PADL, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, can.size[0], y + 12))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    F = Ladders(design)
    F.build()
    v = F.verify()
    F.write()
    v['files'] = F.files
    json.dump(v, open(os.path.join(design, 'verify_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(F, os.path.join(design, 'sheet20_ladders_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('ladders',)}, ensure_ascii=False))
    for r in v['ladders']:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()

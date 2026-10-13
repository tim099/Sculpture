# 餘燼號 階段八b：新梯子與扶手繩（plan.json ladders_build）
#   ① 新梯子：上層砲甲板 → 上甲板（after、fore）、上甲板 → poop（poop 前緣的斷口）
#      找位置的方法照憲法號 design/draft_ladders.py（新圖紙 20）：上端頂在上一層艙口的一邊、往 dir 斜下到下一層；
#      試 dir → band → cap_up，第一個「梯子每格是空氣、踏板上方 headroom、梯腳外 landing 是空氣、扶手柱與扶手繩不穿東西」的就用。
#      edges／shape／try_one 三段照抄那支（只換資料來源：甲板面、艙口、圍板高從 ladders_build 讀，現況讀餘燼號組裝件）。
#   ② 扶手繩：新梯子照①的柱頂；階段八a 整座搬來的兩件（berth、lower）照憲法號 ladders 子作品的固定點、用同一套整座平移換算
#   ⇒ masks/ladders/{upper,spar}.vox.txt（世界座標）、ladders_placement.json（固定點＋繩）、verify_ladders.json、sheet08_ladders_v1.png
# 用法：python -I draft_ladders.py <design 資料夾>
import sys, os, json, hashlib, subprocess, re
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402

ZMAX = 200
XMAX = 1100


def existing_links(work):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=links', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    for line in r.stdout.splitlines():
        if line.startswith('🔢 link_paths = '):
            return [p for p in line.split(' = ', 1)[1].split(';') if p]
    return []


def export_hidden(work, hide):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        args = ['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out]
        if hide:
            args += ['--arg', 'hide_links=' + ','.join(hide)]
        r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-600:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def con_anchors(work):
    """憲法號梯子子作品的固定點：名字 ⇒ 格（anchors 輸出：`名` ← 作品 @x,y,z）"""
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=anchors', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r'- `([^`]+)` ← \S+ @(-?\d+),(-?\d+),(-?\d+) ', line)
        if m:
            out[m.group(1)] = tuple(int(m.group(i)) for i in (2, 3, 4))
    return out


class Ladders:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['ladders_build']
        s.G = s.P['geometry']
        s.St = s.plan['stretch']
        s.surf = s.P['surfaces']
        s.hatch = s.P['hatches']
        s.coam = s.P['coaming']
        have = set(existing_links(s.P['assembly']))
        s.hidden = [h for h in s.P['hide_links'] if h in have]
        a = export_hidden(s.P['assembly'], s.hidden)
        assert len(a) == s.P['assembly_voxels'], ('讀到的現況格數對不上', len(a), s.P['assembly_voxels'])
        m = a[(a[:, 2] < ZMAX) & (a[:, 0] < XMAX)]
        s.W = np.zeros((XMAX, 320, ZMAX), np.uint8)
        s.W[m[:, 0], m[:, 1], m[:, 2]] = m[:, 3]
        s.cells, s.kind, s.owner = {}, {}, {}
        s.anchors, s.ropes, s.rows, s.notes = [], [], [], []

    def dz(s, deck, x):
        for a, b, z in s.surf[deck]:
            if (a is None or x >= a) and (b is None or x < b):
                return z
        return None

    def free(s, k):
        return s.W[k] == 0 and k not in s.cells

    # ───── 以下三段照憲法號 draft_ladders.py ─────
    def edges(s, h, U, y0, y1):
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

    def try_one(s, L, d, y0, y1, band, cap_up, edges_ok):
        G = s.G
        U, deck = L['upper'], L['deck']
        cand = [e for e in edges_ok if e[1] == d]
        res = []
        for xe, _ in cand:
            zu = s.dz(U, xe)
            zcap = zu + s.coam[U] - 1 + cap_up
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
            if not all(s.W[xf, y, zl - 1] > 0 for y in (y0, y1)):
                res.append((xe, '梯腳底下不是甲板'))
                continue
            head = []
            for t, x, zs in cols:
                for y in range(y0 + 1, y1):
                    for z in range(zs + 1, min(zs + 1 + G['headroom'], zu)):
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
    # ───── 照抄到這裡 ─────

    def rope(s, name, a, b):
        M = s.P['manrope']
        s.ropes.append({'name': name, 'from': a, 'to': b, 'thickness': M['thickness'], 'slack': M['slack'], 'color': M['color'], 'group': M['group']})

    def build(s):
        for L in s.P['list']:
            h = s.hatch[L['hatch']]
            y0, y1 = L['y']
            eds, zu = s.edges(h, L['upper'], y0, y1)
            got, why = None, []
            for d in L['dir']:
                for band in s.G['band']:
                    for cap_up in s.G['cap_up']:
                        got, r = s.try_one(L, d, y0, y1, band, cap_up, eds)
                        why += [(d, band, cap_up) + tuple(w) for w in r]
                        if got:
                            break
                    if got:
                        break
                if got:
                    break
            if not got:
                s.notes.append('%s 放不下：%s' % (L['id'], '；'.join('dir %d band %d cap %d x %d %s' % w for w in why) or '找不到艙口邊（edges %s）' % eds))
                s.rows.append({'id': L['id'], 'placed': False, 'edges': eds})
                continue
            for k, (c, kd) in got['cells'].items():
                s.cells[k] = c
                s.kind[k] = kd
                s.owner[k] = L['deck']
            sw = s.P['subworks'][L['deck']]
            for side in ('lo', 'hi'):
                sd = 'P' if side == 'lo' else 'S'
                for which in ('top', 'bot'):
                    s.anchors.append({'name': 'manrope-%s-%s-%s' % (L['id'], sd, which), 'work': sw['id'], 'at': list(got['tops'][(side, which)]), 'note': 'stanchion（階段八b 新梯子）'})
                s.rope('梯-%s.manrope-%s' % (L['id'], sd), '%s/manrope-%s-%s-top' % (sw['path'], L['id'], sd), '%s/manrope-%s-%s-bot' % (sw['path'], L['id'], sd))
            row = {k: got[k] for k in ('xe', 'd', 'y', 'zcap', 'zl', 'band', 'cap_up', 'R', 'xf', 'treads', 'post_bot', 'post_h')}
            row.update(id=L['id'], placed=True, cells=len(got['cells']), rise=got['zcap'] - got['zl'] + 1, tried_before=len(why))
            s.rows.append(row)

    def old(s):
        """階段八a 整座搬來的兩件：固定點照憲法號換算（整座平移：那座在 x ≥ 472 ⇒ +66），繩照憲法號同名"""
        x0, L, k = s.St['x_from'], s.St['length'], s.St['copies']
        s.old_read = {}
        for nm, O in s.P['old_ladders'].items():
            if nm == 'note':
                continue
            A = con_anchors(O['from'])
            ew = DP.export_list(O['work'])
            ecells = {(int(x), int(y), int(z)) for x, y, z, c in ew}
            pairs = {}
            for an, (x, y, z) in A.items():
                dx = L * k if x >= x0 + L else 0
                at = (x + dx, y, z)
                # 柱頂那一格要是那座梯子的鐵柱（換算對不對的讀數）
                s.anchors.append({'name': an, 'work': O['work'], 'at': list(at), 'note': 'stanchion（憲法號 %s 換算，dx %d）' % (O['from'], dx), 'on_post': at in ecells})
                m = re.match(r'manrope-(.+)-([PS])-(top|bot)$', an)
                pairs.setdefault((m.group(1), m.group(2)), {})[m.group(3)] = an
            for (lid, sd), tb in sorted(pairs.items()):
                s.rope('梯-%s.manrope-%s' % (lid, sd), '%s/%s' % (O['path'], tb['top']), '%s/%s' % (O['path'], tb['bot']))
            s.old_read[nm] = {'anchors': len(A), 'ropes': len(pairs)}

    def verify(s):
        v = {'cells': len(s.cells), 'by_kind': {}, 'by_deck': {}}
        for k, kd in s.kind.items():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
            v['by_deck'][s.owner[k]] = v['by_deck'].get(s.owner[k], 0) + 1
        v['overlap_world'] = sum(1 for k in s.cells if s.W[k] > 0)
        v['mirror_mismatch'] = sum(1 for (x, y, z), c in s.cells.items() if s.cells.get((x, 320 - y, z)) != c)
        # ⚠ 結構（元件、空腔）不在這裡量：W 只有 z < 200，桅杆上半截被切掉 ⇒ 會多出一堆假的元件。套用後用引擎 stats structure=1 量整艘。
        v['assembly_expect'] = s.P['assembly_voxels'] + len(s.cells)
        v['anchors'] = len(s.anchors)
        v['old_anchor_not_on_post'] = [a['name'] + '@' + a['work'] for a in s.anchors if a.get('on_post') is False]
        v['ropes'] = len(s.ropes)
        v['old'] = s.old_read
        v['rows'] = s.rows
        v['notes'] = s.notes
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'ladders')
        os.makedirs(out, exist_ok=True)
        files = {}
        for deck in sorted(set(s.owner.values())):
            p = os.path.join(out, deck + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], c) for k, c in s.cells.items() if s.owner[k] == deck)
            open(p, 'w', encoding='utf-8', newline='\n').write('# 梯子 %s（世界座標，子作品 at 0,0,0）（%d 格）\n' % (deck, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[deck] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'file': 'masks/ladders/%s.vox.txt' % deck}
        place = {'subworks': s.P['subworks'], 'files': files, 'anchors': s.anchors, 'ropes': s.ropes, 'assembly': s.P['assembly']}
        json.dump(place, open(os.path.join(s.design, 'ladders_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        return files

    def sheet(s, path):
        # 側面（從 +y 看，只畫 y 150..170 那一條）：x 180..720、z 70..170
        x0, x1, z0, z1, sc = 180, 720, 70, 170, 3
        im = Image.new('RGB', ((x1 - x0) * sc + 40, (z1 - z0) * sc + 70), (250, 249, 244))
        d = ImageDraw.Draw(im)
        d.text((20, 10), '餘燼號 新圖紙 08 v1：梯子（中線那一條的側面；灰 ＝ 現況、彩 ＝ 新梯子）', font=DP.font(16), fill=(30, 30, 30))
        px = im.load()
        band = s.W[x0:x1, 150:171, z0:z1]
        occ = band.max(axis=1)
        for x in range(x1 - x0):
            for z in range(z1 - z0):
                if occ[x, z]:
                    for i in range(sc):
                        for j in range(sc):
                            px[20 + x * sc + i, 50 + (z1 - z0 - 1 - z) * sc + j] = (205, 205, 205)
        for (x, y, z), c in s.cells.items():
            if x0 <= x < x1 and z0 <= z < z1 and 150 <= y <= 170:
                for i in range(sc):
                    for j in range(sc):
                        px[20 + (x - x0) * sc + i, 50 + (z1 - 1 - z) * sc + j] = DP.rgb(c)
        im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    L = Ladders(design)
    L.build()
    L.old()
    v = L.verify()
    v['hidden'] = L.hidden
    v['files'] = L.write()
    L.sheet(os.path.join(design, 'sheet08_ladders_v1.png'))
    json.dump(v, open(os.path.join(design, 'verify_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k not in ('files',)}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

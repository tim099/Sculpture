# berth deck → orlop 的梯子（Tim 2026-10-14：「orlop也補一下」；ame 的配置頁把 orlop 艙房標「走不到」）—— 憲法號與餘燼號共用
#   新圖紙 20 當時三處都放不下（after hatch 底下是洞、fore scuttle 落進艙房、companion 正對中線柱子）⇒ 另開只穿 berth deck 的梯口。
#   orlop 前後兩塊平台各一座：梯口開在 berth deck 兩根橫樑之間；梯子落在 orlop 中線走道靠右舷那一側（中線有一排柱子、桅也在中線）。
#   幾何、顏色、扶手照憲法號 plan.json ladders（新圖紙 20）：rise 3／run 2、band 4→3、cap_up 0–3、headroom 8、landing 5、扶手柱高 9。
# 用法：python -I draft_orlop_ladders.py <con|emb> <組裝件 export list（梯子加進來之前）> <berth 甲板子作品 export list>
#   ⇒ <那艘的 design>/masks/ladders/orlop.vox.txt（梯子子作品，世界座標）、masks/ladders/orlop_carve.vox.txt（berth 甲板子作品開梯口，carvevox 帶顏色）、
#      rig_points_orlop_ladders.json（扶手柱頂 manrope-<梯>-<P|S>-<top|bot>）、orlop_ladder_ropes.json、verify_orlop_ladders.json
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
ZMAX = 120
SHIPS = {
    'con': {'design': os.path.join(WORKS, 'basecamp-frigate-constitution-01m', 'design'),
            'sub': 'basecamp-frigate-constitution-01m-ladders-orlop', 'title': '憲法號 berth → orlop 的梯子',
            'deck_berth': 'basecamp-frigate-constitution-01m-deck-berth', 'deck_orlop': 'basecamp-frigate-constitution-01m-deck-orlop',
            'ladders': [
                {'id': 'orlop-aft', 'open_x': [361, 370], 'xe': 361, 'd': 1, 'y': [162, 168], 'zu': 60, 'zl': 42,
                 'note': '後平台：berth 橫樑 358–359（主桅那一圈）與 372–375 之間；落在 orlop 中線走道（y 151–169，柱子 x 340／375／393、主桅 352）右舷側'},
                {'id': 'orlop-fore', 'open_x': [540, 551], 'xe': 540, 'd': 1, 'y': [162, 168], 'zu': 61, 'zl': 42,
                 'note': '前平台：berth 橫樑 535–538 與 552–555 之間（fore hatch 508–534 的前面）；落在 orlop 中線走道（柱子 x 550／566、前桅 584）右舷側'}]},
    'emb': {'design': os.path.join(WORKS, 'basecamp-ember-01m', 'design'),
            'sub': 'basecamp-ember-01m-ladders-orlop', 'title': '餘燼號 berth → orlop 的梯子',
            'deck_berth': 'basecamp-ember-01m-deck-berth', 'deck_orlop': 'basecamp-ember-01m-deck-orlop',
            'ladders': [
                {'id': 'orlop-aft', 'open_x': [361, 370], 'xe': 361, 'd': 1, 'y': [162, 168], 'zu': 60, 'zl': 42,
                 'note': '同憲法號（x < 406 沒拉長）'},
                {'id': 'orlop-fore', 'open_x': [606, 617], 'xe': 606, 'd': 1, 'y': [162, 168], 'zu': 61, 'zl': 42,
                 'note': '憲法號那座 ＋66（拉長那一段之後整段平移）'}]},
}
G = {'rise': 3, 'run': 2, 'band': [4, 3], 'cap_up': [0, 1, 2, 3], 'headroom': 8, 'landing': 5, 'stanchion_h': 9, 'coaming': 2}
C = {'stringer': 136, 'tread': 250, 'iron': 36}
MANROPE = {'thickness': 0.35, 'slack': 1.02, 'color': '#cdb88e', 'group': 'ladders/manropes'}


def read(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        if l[0] == '#' or not l.strip():
            continue
        a = l.strip().split(',')
        d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


class Orlop:
    def __init__(s, ship, asm, berth):
        s.S = SHIPS[ship]
        s.asm_sha = hashlib.sha256(open(asm, 'rb').read()).hexdigest()
        s.W = np.zeros((1024, 320, ZMAX), np.uint8)
        s.n_asm = 0
        for (x, y, z), c in read(asm).items():
            s.n_asm += 1
            if z < ZMAX:
                s.W[x, y, z] = c
        s.berth = read(berth)
        s.carve, s.cells, s.kind, s.anchors, s.ropes, s.rows = {}, {}, {}, [], [], []
        # 梯口：berth 甲板子作品在開口框裡（梯寬 ＋ 兩邊各 1 格）、甲板面以下 4 格內的格 —— 只准是甲板板（250），別的就停
        for L in s.S['ladders']:
            x0, x1 = L['open_x']
            y0, y1 = L['y'][0] - 1, L['y'][1] + 1
            for (x, y, z), c in s.berth.items():
                if x0 <= x <= x1 and y0 <= y <= y1 and L['zu'] - 4 <= z < L['zu']:
                    assert c == 250, ('梯口框裡不是甲板板', L['id'], (x, y, z), c)
                    s.carve[(x, y, z)] = c
        for k in s.carve:
            s.W[k] = 0

    def free(s, k):
        return s.W[k] == 0 and k not in s.cells

    def shape(s, xe, d, y0, y1, zcap, zl, band):
        slope = G['rise'] / G['run']
        cells, cols, t = {}, [], 0
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
        R, j, treads = t + 1, 0, []
        while True:
            zt = zcap - G['rise'] * j - 3
            if zt < zl + 2:
                break
            for tt in (G['run'] * j + 1, G['run'] * j + 2):
                if tt < R:
                    for y in range(y0 + 1, y1):
                        cells[(xe + d * tt, y, zt)] = (C['tread'], 'tread')
            treads.append(zt)
            j += 1
        return cells, cols, treads

    def try_one(s, L, band, cap_up):
        xe, d, (y0, y1), zu, zl = L['xe'], L['d'], L['y'], L['zu'], L['zl']
        zcap = zu + G['coaming'] - 1 + cap_up
        cells, cols, treads = s.shape(xe, d, y0, y1, zcap, zl, band)
        if cells is None:
            return None, '太長'
        bad = [k for k in cells if not s.free(k)]
        if bad:
            return None, '梯子撞到 %d 格（第一格 %s，色 %d）' % (len(bad), bad[0], s.W[bad[0]])
        xf = cols[-1][1]
        if not all(s.W[xf, y, zl - 1] > 0 for y in (y0, y1)):
            return None, '梯腳底下不是甲板'
        head = [(x, y, z) for t, x, zs in cols for y in range(y0 + 1, y1) for z in range(zs + 1, min(zs + 1 + G['headroom'], zu))
                if (x, y, z) not in cells and not s.free((x, y, z))]
        if head:
            return None, '頭頂撞到 %d 格（第一格 %s）' % (len(head), head[0])
        land = [(xf + d * k, y, z) for k in range(1, G['landing'] + 1) for y in range(y0, y1 + 1) for z in range(zl, zl + G['headroom'])]
        land = [k for k in land if not s.free(k)]
        if land:
            return None, '梯腳外撞到 %d 格（第一格 %s）' % (len(land), land[0])
        R = len(cols)
        for tb in (R - 3, R - 4, R - 5):
            for hh in (G['stanchion_h'], G['stanchion_h'] - 1, G['stanchion_h'] - 2):
                posts, tops, okp = {}, {}, True
                for side, y in (('P', y0), ('S', y1)):
                    for which, t in (('top', 1), ('bot', tb)):
                        _, x, zs = cols[t]
                        for z in range(zs + 1, zs + 1 + hh):
                            if not s.free((x, y, z)) or (x, y, z) in cells:
                                okp = False
                            posts[(x, y, z)] = (C['iron'], 'stanchion')
                        tops[(side, which)] = (x, y, zs + hh)
                if not okp:
                    continue
                allc = dict(cells)
                allc.update(posts)
                rope_bad = []
                for side in ('P', 'S'):
                    a_, b_ = np.array(tops[(side, 'top')]) + 0.5, np.array(tops[(side, 'bot')]) + 0.5
                    for tt in np.linspace(0, 1, int(np.linalg.norm(b_ - a_) * 3) + 2):
                        q = tuple(int(np.floor(v)) for v in a_ + (b_ - a_) * tt)
                        if q not in allc and not s.free(q):
                            rope_bad.append(q)
                if not rope_bad:
                    return dict(cells=allc, tops=tops, zcap=zcap, xf=xf, R=R, treads=len(treads), band=band, cap_up=cap_up,
                                post_bot=tb, post_h=hh), None
        return None, '扶手柱或扶手繩放不下'

    def build(s):
        for L in s.S['ladders']:
            why, got = [], None
            for band in G['band']:
                for cap_up in G['cap_up']:
                    got, w = s.try_one(L, band, cap_up)
                    if got:
                        break
                    why.append('band %d cap %d：%s' % (band, cap_up, w))
                if got:
                    break
            if not got:
                s.rows.append({'id': L['id'], 'placed': False, 'why': why})
                continue
            for k, (c, kd) in got['cells'].items():
                s.cells[k] = c
                s.kind[k] = kd
            for side in ('P', 'S'):
                for which in ('top', 'bot'):
                    s.anchors.append({'name': 'manrope-%s-%s-%s' % (L['id'], side, which), 'world': list(got['tops'][(side, which)])})
                s.ropes.append({'name': '梯-%s.manrope-%s' % (L['id'], side),
                                'from': '甲板-orlop/梯子/manrope-%s-%s-top' % (L['id'], side), 'to': '甲板-orlop/梯子/manrope-%s-%s-bot' % (L['id'], side),
                                **MANROPE})
            s.rows.append({'id': L['id'], 'placed': True, 'xe': L['xe'], 'xf': got['xf'], 'd': L['d'], 'y': L['y'], 'zcap': got['zcap'], 'zl': L['zl'],
                           'band': got['band'], 'cap_up': got['cap_up'], 'R': got['R'], 'treads': got['treads'], 'post_bot': got['post_bot'],
                           'post_h': got['post_h'], 'cells': len(got['cells']), 'tried_before': len(why), 'note': L['note']})

    def verify(s):
        v = {'assembly_cells_before': s.n_asm, 'assembly_list_sha256': s.asm_sha, 'carve': len(s.carve), 'cells': len(s.cells), 'by_kind': {}}
        for kd in s.kind.values():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
        v['overlap_world'] = sum(1 for k in s.cells if s.W[k] > 0)
        A = s.W > 0
        for k in s.cells:
            A[k] = True
        lab, _ = ndimage.label(A)
        base = set(np.unique(lab[s.W > 0])) - {0}
        v['floating'] = sum(1 for k in s.cells if lab[k] not in base)
        v['placed'] = sum(1 for r in s.rows if r['placed'])
        v['of'] = len(s.rows)
        v['anchors'] = len(s.anchors)
        v['ropes'] = len(s.ropes)
        v['expect_assembly_after'] = s.n_asm - len(s.carve) + len(s.cells)
        v['ladders'] = s.rows
        s.v = v

    def write(s):
        D = s.S['design']
        out = os.path.join(D, 'masks', 'ladders')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for name, cells, note in (('orlop', s.cells, '%s（子作品 %s；世界座標，stampvox at=0,0,0；關聯進 甲板-orlop、名 梯子）' % (s.S['title'], s.S['sub'])),
                                  ('orlop_carve', s.carve, 'berth 甲板子作品 %s 開梯口（carvevox at=0,0,0，帶顏色守門）' % s.S['deck_berth'])):
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(cells.items()))
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— draft_orlop_ladders.py 產（%d 格）\n' % (note, len(cells)) + body)
            s.files[name] = {'cells': len(cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump({'note': 'berth → orlop 梯子扶手柱的柱頂（manrope-<梯>-<P|S>-<top|bot>；P ＝ y 小那一側）；世界座標；子作品 at 0,0,0', 'points': s.anchors},
                  open(os.path.join(D, 'rig_points_orlop_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        json.dump({'note': 'berth → orlop 每座梯子兩條扶手繩（掛在組裝件；端點是關聯路徑）', 'ropes': s.ropes},
                  open(os.path.join(D, 'orlop_ladder_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    F = Orlop(sys.argv[1], sys.argv[2], sys.argv[3])
    F.build()
    F.verify()
    F.write()
    F.v['files'] = F.files
    json.dump(F.v, open(os.path.join(F.S['design'], 'verify_orlop_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: F.v[k] for k in F.v if k != 'ladders'}, ensure_ascii=False))
    for r in F.rows:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()

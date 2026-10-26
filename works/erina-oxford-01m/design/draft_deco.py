# 牛津號 步驟 6（TASK-0972）：船頭（beakhead 平台、cutwater、head rail）、獅子船首像、船尾旗桿
#   輸入：plan.json（deco）＋ 組裝件現在的格子（CLI 匯出，藏掉本階段自己的關聯）
#   輸出：masks/deco/<件>.vox.txt（世界座標、at 0,0,0）、deco_anchors.json（各件的固定點）、verify_deco.json
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=shift=figurehead:<dx>]（反向對照：船首像往 x 推幾格，看重疊與元件數報不報；⛔ 不寫檔）
#   結構參考 calli-cosecha-01m/design/draft_deco.py（讀組裝件現況、落在船上的格不放、組起來量元件數）；造型是本船的（1650 年代英國船的開放式 beakhead、鍍金獅子）。
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

HULL = 'erina-oxford-01m'
ASM = HULL + '-assembly'
OWN_LINKS = ('船首喙', '船首像', '船尾旗桿', '船尾窗玻璃')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    Y = LY.Layout(plan, L)
    YC = L.YC
    DC = plan['deco']
    C = DC['colors']
    lk = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(design))), ASM, 'links.json'), encoding='utf-8'))
    names = {l['name'] for l in lk.get('links', lk)}
    hide = ','.join(n for n in OWN_LINKS if n in names)
    A = export_list(ASM, None, links=None, hide_links=hide or None)
    occ = set(map(tuple, A[:, :3].astype(int).tolist()))
    parts = {k: {} for k in ('beakhead', 'figurehead', 'ensign_staff')}
    anchors = {k: {} for k in parts}

    def put(part, x, y, z, c):
        parts[part][(int(x), int(y), int(z))] = c

    # ── beakhead 平台：艏柱前、往前收尖；甲板面 z_deck（2 格厚）＋ 外緣金邊 ──
    B = DC['beakhead']
    zd = B['z_deck']
    x0 = int(math.floor(float(L.x_stem(zd + 0.5)))) - 1
    x1 = B['x_tip']
    for x in range(x0, x1 + 1):
        t = (x + 0.5 - x0) / (x1 + 1 - x0)
        hw = B['half'] * (1 - t ** B['pow'])
        for y in range(YC - int(hw), YC + int(hw) + 1):
            for z in (zd - 1, zd):
                edge = abs(y - YC) >= int(hw) - 0
                put('beakhead', x, y, z, C['gold'] if (edge and z == zd) else C['plank'])
    # cutwater（knee of the head）：中線 3 格寬，從水線下的艏柱斜著伸到平台尖底下
    zc0 = B['cut_z0']
    for z in range(zc0, zd - 1):
        xs = float(L.x_stem(z + 0.5))
        xf = xs + (z - zc0) / float(zd - 1 - zc0) * (x1 + 1 - xs)
        for x in range(int(math.floor(xs)) - 2, int(math.floor(xf)) + 1):
            for y in (YC - 1, YC, YC + 1):
                c = C['hull_below'] if z < plan['waterline']['z'] else C['hull']
                if x >= int(math.floor(xf)) - 1:
                    c = C['gold'] if z >= plan['waterline']['z'] else C['hull_below']
                put('beakhead', x, y, z, c)
    anchors['beakhead']['bobstay-1'] = [int(math.floor(float(L.x_stem(B['bob_z'] + 0.5)) + (B['bob_z'] - zc0) / float(zd - 1 - zc0) * (x1 + 1 - float(L.x_stem(B['bob_z'] + 0.5))))) + 1, YC, B['bob_z']]
    # head rail：兩舷各兩條，從船頭舷側往前往下彎、收在船首像後面；畫成 6 連通（每一步只動一軸 ⇒ 不會只在斜角相接、斷成小塊）
    def line6(part, pts, col):
        last = None
        for p in pts:
            c = [int(math.floor(v)) for v in p]
            if last is not None:
                while c != last:
                    for i in range(3):
                        if c[i] != last[i]:
                            last = list(last)
                            last[i] += 1 if c[i] > last[i] else -1
                            put(part, last[0], last[1], last[2], col)
                            break
            else:
                put(part, c[0], c[1], c[2], col)
            last = c
    F = DC['figurehead']
    xr_end = F['x'] - 7
    for r in B['rails']:
        for side in (1, -1):
            xa, za = r['from']
            xb, zb = xr_end, r['to_z']
            ha = float(L.hb(np.array([xa + 0.5]), np.array([za + 0.5]))[0]) + 0.5
            pts = []
            for k in range(0, 161):
                t = k / 160.0
                x = xa + (xb - xa) * t
                z = za + (zb - za) * (1 - (1 - t) ** 2)
                hw = ha * (1 - t) + 2.5 * t
                pts.append((x + 0.5, YC + side * hw + 0.5, z + 0.5))
            line6('beakhead', pts, C[r['color']])
            for xs_ in r.get('posts', []):
                t = (xs_ - xa) / float(xb - xa)
                zt = za + (zb - za) * (1 - (1 - t) ** 2)
                hw = ha * (1 - t) + 2.5 * t
                for z in range(zd + 1, int(math.floor(zt)) + 1):
                    put('beakhead', xs_, int(math.floor(YC + side * hw + 0.5)), z, C['blue'])
    # 兩舷對稱：照右舷（y ＞ YC）鏡到左舷（取整在剛好半格的地方兩舷會差一格）
    bh = parts['beakhead']
    for (x, y, z), c in list(bh.items()):
        if y < YC:
            del bh[(x, y, z)]
    for (x, y, z), c in list(bh.items()):
        if y > YC:
            bh[(x, 2 * YC - y, z)] = c
    # ── 獅子船首像（鍍金、紅冠）：站在平台尖上、朝 +x ──
    fx, fz = F['x'], zd + 1
    if probe and probe[0].startswith('shift=figurehead:'):
        fx += int(probe[0].split(':')[1])

    def ell(cx, cy, cz, rx, ry, rz, col, part='figurehead'):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for z in range(int(cz - rz) - 1, int(cz + rz) + 2):
                    if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 + ((z + 0.5 - cz) / rz) ** 2 <= 1:
                        put(part, x, y, z, col)
    ell(fx, YC + 0.5, fz + 5.5, 5.5, 3.0, 3.6, C['gold'])                        # 身體
    for dx in (-3.5, 3.0):                                                          # 四條腿
        for dy in (-1.5, 1.5):
            for z in range(fz, fz + 4):
                for xx in (int(fx + dx), int(fx + dx) + 1):
                    put('figurehead', xx, int(YC + 0.5 + dy) if dy > 0 else int(YC + dy), z, C['gold'])
    ell(fx + 5.0, YC + 0.5, fz + 9.5, 3.6, 3.6, 3.8, C['mane'])                    # 鬃毛
    ell(fx + 6.8, YC + 0.5, fz + 10.0, 2.6, 2.3, 2.6, C['gold'])                   # 臉
    for dy in (-1, 1):                                                              # 眼
        put('figurehead', int(fx + 9), YC + (1 if dy > 0 else -1), fz + 11, C['eye'])
    for k in range(9):                                                              # 尾巴：從屁股往上捲
        t = k / 8.0
        put('figurehead', int(fx - 5.5 - 1.5 * math.sin(t * 2.6)), YC, int(fz + 5 + 6 * t), C['mane'] if k == 8 else C['gold'])
    for dx in (-1.5, 0, 1.5):                                                       # 王冠：三個尖
        for z in range(fz + 13, fz + 15 + (1 if dx == 0 else 0)):
            put('figurehead', int(fx + 6.5 + dx), YC, z, C['crown'])
    for x in range(int(fx + 4.5), int(fx + 9)):
        for y in (YC - 1, YC, YC + 1):
            put('figurehead', x, y, fz + 12, C['crown'])
    # ── 船尾旗桿：船尾最後面那一欄的舷頂上，直立 ──
    S = DC['ensign_staff']
    sx = S['x']
    z0 = max(z for (x, y, z) in occ if x == sx and y == YC) + 1          # 那一欄船殼實際最上面那一格上面（⛔ 照設計的舷頂線：船尾板斜、最後那幾欄比線低 ⇒ v1 旗桿浮空）
    for z in range(z0, z0 + S['h']):
        for x in range(sx - 1, sx + 2):
            for y in range(YC - 1, YC + 2):
                if abs(x - sx) + abs(y - YC) <= 1 or z < z0 + 4:
                    put('ensign_staff', x, y, z, C['staff'] if z < z0 + S['h'] - 2 else C['gold'])
    anchors['ensign_staff']['flag-head'] = [sx - 2, YC, z0 + S['h'] - 4]
    anchors['ensign_staff']['flag-foot'] = [sx - 2, YC, z0 + S['h'] - 4 - plan['rigging']['flags']['ensign'][1]]
    # ── 讀數：落在船上的格（不放）、件與件重疊、組起來的元件數、鏡像差 ──
    R = {}
    for k, cells in parts.items():
        on = [c for c in cells if c in occ]
        for c in on:
            del cells[c]
        R[k] = {'cells': len(cells), 'on_ship_skipped': len(on), 'mirror_diff': sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * YC - y, z)) != c)}
    keys = list(parts)
    R['overlap'] = sum(len(set(parts[a]) & set(parts[b])) for i, a in enumerate(keys) for b in keys[i + 1:])
    allc = occ | set().union(*[set(p) for p in parts.values()])
    lo = np.array([min(c[i] for c in allc) for i in range(3)])
    hi = np.array([max(c[i] for c in allc) for i in range(3)])
    G = np.zeros(hi - lo + 1, bool)
    idx = np.array(list(allc)) - lo
    G[tuple(idx.T)] = True
    lab, n = ndimage.label(G)
    R['components_with_ship'] = int(n)
    R['cavities_with_ship'] = int((ndimage.binary_fill_holes(G) & ~G).sum())
    # 艏斜桅那條線（半徑 ＋1）裡的裝飾格；bobstay 線穿過的裝飾格
    p0, p1 = np.array(Y.bow['p0'], float), np.array(Y.bow_point(1.0), float)
    rb = plan['masts']['bowsprit']['r'][0] + 1
    bow_hits = 0
    for (x, y, z) in list(parts['beakhead']) + list(parts['figurehead']):
        q = np.array([x + 0.5, z + 0.5])
        t = np.clip((q - p0) @ (p1 - p0) / ((p1 - p0) @ (p1 - p0)), 0, 1)
        if np.linalg.norm(q - (p0 + t * (p1 - p0))) <= rb and abs(y - YC) <= rb:
            bow_hits += 1
    R['bowsprit_line_hits'] = bow_hits
    R['anchors'] = anchors
    if probe:
        print(json.dumps({'probe': probe[0], 'components_with_ship': R['components_with_ship'], 'figurehead': R['figurehead'], 'overlap': R['overlap']}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    for k, cells in parts.items():
        with open(os.path.join(od, k + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 牛津號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % k)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    json.dump(anchors, open(os.path.join(design, 'deco_anchors.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(R, open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

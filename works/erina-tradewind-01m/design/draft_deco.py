# 出處：erina-oxford-01m/design/draft_deco.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 步驟 6（TASK-1097）：船頭（knee of the head／cutwater、渦卷船首 scroll head、兩舷 head rail）、兩舷錨架（cathead）
#   輸入：plan.json（deco）＋ 組裝件現在的格子（CLI 匯出，藏掉本階段自己的關聯）
#   輸出：masks/deco/<件>.vox.txt（世界座標、at 0,0,0）、deco_anchors.json（各件的固定點）、verify_deco.json
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=shift=scroll:<dz>]（反向對照：渦卷往上推幾格，看艏斜桅那條線報不報；⛔ 不寫檔）
#   跟牛津號不同：沒有 beakhead 平台與船首像（〔源〕RMG：Supply 是 scroll head、沒有人像）；沒有船尾旗桿（主帆杆伸出船尾，船旗掛斜桁尖）。
#   結構照牛津號（讀組裝件現況、落在船上的格不放、組起來量元件數、6 連通畫線、照右舷鏡到左舷）。
import sys, os, json, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

HULL = 'erina-tradewind-01m'
ASM = HULL + '-assembly'
OWN_LINKS = ('船首', '錨架', '船尾窗玻璃')


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
    parts = {k: {} for k in ('head', 'catheads')}
    anchors = {k: {} for k in parts}

    def put(part, x, y, z, c):
        parts[part][(int(x), int(y), int(z))] = c

    def line6(part, pts, col):
        """點列畫成 6 連通（每一步只動一軸 ⇒ 不會只在斜角相接）。"""
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

    # ── knee of the head（cutwater）：中線 3 格寬，從水線下的艏柱往前往上彎到渦卷底下 ──
    K = DC['knee']
    z0, z1, ext = K['z0'], K['z1'], K['ext']
    wl = plan['waterline']['z']
    front = {}
    for z in range(z0, z1 + 1):
        xs = float(L.x_stem(z + 0.5))
        u = (z - z0) / float(z1 - z0)
        xf = xs + ext * u ** K['pow']
        front[z] = xf
        for x in range(int(math.floor(xs)) - 2, int(math.floor(xf)) + 1):
            for y in (YC - 1, YC, YC + 1):
                c = C['below'] if z < wl else C['wood']
                if z >= wl and x >= int(math.floor(xf)) - 1:
                    c = C['black']                                   # 前緣一條黑
                put('head', x, y, z, c)
    # 渦卷（scroll）：knee 頂端前面一個圓盤（x-z 平面、3 格寬），金底黑螺旋
    Sc = DC['scroll']
    sx, sz = front[z1] - Sc['r'] + 1.0, z1 - Sc['r'] + 1.5
    if probe and probe[0].startswith('shift=scroll:'):
        sz += int(probe[0].split(':')[1])
    for x in range(int(sx - Sc['r']) - 1, int(sx + Sc['r']) + 2):
        for z in range(int(sz - Sc['r']) - 1, int(sz + Sc['r']) + 2):
            if (x + 0.5 - sx) ** 2 + (z + 0.5 - sz) ** 2 <= Sc['r'] ** 2:
                for y in (YC - 1, YC, YC + 1):
                    put('head', x, y, z, C['gold'])
    sp = []
    for k in range(0, 121):
        t = k / 120.0
        r = 0.4 + (Sc['r'] - 0.9) * t
        a = math.pi / 2 + Sc['turns'] * 2 * math.pi * t
        sp.append((sx + r * math.cos(a), sz + r * math.sin(a)))
    for y in (YC - 1, YC + 1):                                       # 兩面刻螺旋（中間那一格留金色）
        line6('head', [(p[0], y + 0.5, p[1]) for p in sp], C['black'])
    anchors['head']['bobstay-1'] = [int(math.floor(front[K['bob_z']])) - 1, YC, K['bob_z']]
    # ── head rail：兩舷各一條，從艏樓舷側往前往下彎、收在渦卷後面（黑）──
    HR = DC['head_rail']
    for side in (1,):
        xa, za = HR['from']
        xb, zb = sx - Sc['r'] - 1, HR['to_z']
        ha = float(L.hb(np.array([xa + 0.5]), np.array([za + 0.5]))[0]) + 0.5
        pts = []
        for k in range(0, 161):
            t = k / 160.0
            x = xa + (xb - xa) * t
            z = za + (zb - za) * (1 - (1 - t) ** 2)
            hw = ha * (1 - t) + 1.5 * t
            pts.append((x + 0.5, YC + side * hw + 0.5, z + 0.5))
        line6('head', pts, C['black'])
    # ── 錨架（cathead）：艏樓舷牆頂下、從舷內斜著往前伸出舷外 ──
    CT = DC['cathead']
    cx, cz = CT['x'], CT['z']
    a = math.radians(CT['fwd_deg'])
    hb0 = float(L.hb(np.array([cx + 0.5]), np.array([cz + 0.5]))[0])
    for k in range(0, int(CT['inboard'] + hb0 + CT['out']) * 4 + 1):
        s = k / 4.0 - CT['inboard']                                  # 從舷外板往外量（負 ＝ 舷內）
        r = hb0 + s
        x = cx + max(0.0, s) * math.tan(a)
        for dz in (0, 1):
            for dx in (0, 1):
                col = C['black'] if s > CT['out'] - 2 else C['cat']
                put('catheads', x + dx, YC + r + 0.5, cz + dz, col)
    tip = hb0 + CT['out'] - 1
    anchors['catheads']['cat-S'] = [int(cx + (CT['out'] - 1) * math.tan(a)), int(YC + tip + 0.5), cz - 1]
    # 兩舷對稱：照右舷（y ＞ YC）鏡到左舷
    for part in parts:
        P = parts[part]
        for (x, y, z), c in list(P.items()):
            if y < YC:
                del P[(x, y, z)]
        for (x, y, z), c in list(P.items()):
            if y > YC:
                P[(x, 2 * YC - y, z)] = c
    cs = anchors['catheads']['cat-S']
    anchors['catheads']['cat-P'] = [cs[0], 2 * YC - cs[1], cs[2]]
    # ── 讀數：落在船上的格（不放）、件與件重疊、組起來的元件數、鏡像差、艏斜桅那條線 ──
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
    p0, p1 = np.array(Y.bow['p0'], float), np.array(Y.jib_point(1.0), float)
    rb = plan['masts']['bowsprit']['r'][0] + 1
    bow_hits = 0
    for (x, y, z) in parts['head']:
        q = np.array([x + 0.5, z + 0.5])
        t = np.clip((q - p0) @ (p1 - p0) / ((p1 - p0) @ (p1 - p0)), 0, 1)
        if np.linalg.norm(q - (p0 + t * (p1 - p0))) <= rb and abs(y - YC) <= rb:
            bow_hits += 1
    R['bowsprit_line_hits'] = bow_hits
    R['anchors'] = anchors
    if probe:
        print(json.dumps({'probe': probe[0], 'bowsprit_line_hits': bow_hits, 'components_with_ship': R['components_with_ship']}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    for f in os.listdir(od):
        if f.endswith('.vox.txt'):
            os.remove(os.path.join(od, f))
    for k, cells in parts.items():
        with open(os.path.join(od, k + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 信風號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % k)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    json.dump(anchors, open(os.path.join(design, 'deco_anchors.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(R, open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

# 出處：abigail-fluyt-01m/design/draft_fit.py「艙房」那一段（澤漢號 步驟 10：一道艙壁＋中線門洞＋kind=rooms 的框）；TASK-1147 巴貝多商人號 改成多間、每間鋪平地板、標 .door
# 巴貝多商人號 空艙房（Ship_Decks §9.2；Tim 2026-11-02「Build cabins」）
#   輸入：plan.json 的 cabins_build ＋ 組裝件現在的格子與部件（CLI 匯出；扣掉本步自己的子作品 ⇒ 重產時不會把上一輪當成船）
#   輸出：masks/cabins/cabins.vox.txt（世界座標、at 0,0,0：艙壁、門框、平地板）、cabins_placement.json（固定點 <房名>.min／.max／.door、關聯 meta）、verify_cabins.json
#   每一間：
#     · 地板：框裡每一柱原本的甲板面（第一層空氣）比 z0 低 ⇒ 往上補到 z0 − 1（舷弧 ⇒ 一路低下去）；比 z0 高 ⇒ ✗（框會吃到甲板）
#     · 框：x 照 plan、z0 照 plan；y 從艙壁（side P／S 的 y_in；C ＝ 兩舷）往船殼一路找「整條 x、z0..頂都是空氣」的那一段；頂 ＝ 框裡最低的天花板 − 1（樑底）
#     · 艙壁：橫的（walls 的 x）從船殼到船殼（C）或從 y_in 到船殼；縱的（y_in）從最後面那道到最前面那道（沒有就到框外一格）；每一柱從甲板面（含補的地板）砌到天花板
#     · 門：門洞 door 那幾格、高 door_h；門檻補到 z0 − 1；門框照 colors.frame；.door ＝ 門洞中間那一格（z0）
#   量法照遊戲：站得住 ＝ 腳下實心、頭上 head 格空（40_crew.js、rooms.py HEAD 14）；門外一步的高低差 ≤ 3 格（42_hands.js NAV_DZ）
#   用法：python -I -X utf8 draft_cabins.py <design> [--probe]（--probe ⇒ 只印讀數、⛔ 不寫檔）
import sys, os, json, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list

NX, NY, NZ = 480, 192, 384
YC = 96
NAV_HEAD = 12                   # 船員走路頭上要空幾格（42_hands.js NAV_HEAD）


def export_parts(work):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + work, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-800:])
        return json.load(open(out, encoding='utf-8'))


def write_list(path, cells):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# x,y,z,color（draft_cabins.py）\n')
        for c in sorted(cells):
            f.write('%d,%d,%d,%d\n' % c)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = '--probe' in sys.argv[2:]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    CB = plan['cabins_build']
    C, HEAD, DH = CB['colors'], CB['head'], CB['door_h']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    ASM = 'apex-two-barbados-01m-assembly'
    A = export_list(ASM, None, links=None)
    if os.path.exists(os.path.join(WORKS, CB['work'], 'work.json')):
        own = set(map(tuple, export_list(CB['work'], None)[:, :3].tolist()))
        A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own], np.int32)
    S = np.zeros((NX, NY, NZ), bool)
    S[A[:, 0], A[:, 1], A[:, 2]] = True
    boxes = [(m['path'], m['box']) for m in export_parts(ASM)['models']]

    def models_in(x0, y0, z0, x1, y1, z1):
        return sorted({n for n, b in boxes if b[0] < x1 + 1 and b[3] > x0 and b[1] < y1 + 1 and b[4] > y0 and b[2] < z1 + 1 and b[5] > z0})

    def deck_top(x, y, z0):
        """(x, y) 這一柱、z0 上下 6 格裡的甲板面（第一層空氣、腳下實心）；z0 已經是實心 ⇒ 往上找；找不到 ⇒ None"""
        for z in range(z0 + 6, z0 - 7, -1):
            if S[x, y, z - 1] and not S[x, y, z]:
                if not S[x, y, z:z0 + 1].any():
                    return z
        return None

    def ceil_of(x, y, z):
        for zz in range(z, NZ):
            if S[x, y, zz]:
                return zz
        return NZ

    cells = {}                                             # (x, y, z) ⇒ 顏色

    def put(x, y, z, col):
        if not S[x, y, z]:
            cells[(x, y, z)] = col

    V, place = {'rooms': []}, {'work': CB['work'], 'title': CB['title'], 'host': CB['host'], 'link': CB['link'], 'mask': 'masks/cabins/cabins.vox.txt',
                               'anchors': {}, 'meta': {'kind': 'rooms'}}
    for R in CB['rooms']:
        x0, x1, z0, side = R['x'][0], R['x'][1], R['z0'], R['side']
        # 框的 y：從艙壁（或中線）往船殼，整條 x、z0..z0+HEAD−1 都是空氣的那一段
        def free(y):                                       # 船殼還沒到：z0 往上 10 格都空（樑底下也算 ⇒ 不拿 HEAD；框的頂另外量）
            return not S[x0:x1 + 1, y, z0:z0 + 10].any()
        if side == 'C':
            ya = YC; yb = YC
            while free(ya - 1): ya -= 1
            while free(yb + 1): yb += 1
            yin = None
        elif side == 'S':
            ya = R['y_in'] + 1; yb = ya
            while free(yb + 1): yb += 1
            yin = R['y_in']
        else:
            yb = R['y_in'] - 1; ya = yb
            while free(ya - 1): ya -= 1
            yin = R['y_in']
        def lowc(y):                                       # 這一排最低的天花板（樑底也算）離地板幾格
            return min(ceil_of(x, y, z0) for x in range(x0, x1 + 1)) - z0
        while yb > ya and lowc(yb) < NAV_HEAD: yb -= 1      # 船殼往內收那幾排：頭上不到 NAV_HEAD ⇒ 不框（框是長方體，留著會把整間的頂壓低）
        while ya < yb and lowc(ya) < NAV_HEAD: ya += 1
        z1 = min(ceil_of(x, y, z0) for x in range(x0, x1 + 1) for y in range(ya, yb + 1)) - 1
        # 地板：比 z0 低的柱往上補
        high, filled = [], 0
        for x in range(x0, x1 + 1):
            for y in range(ya, yb + 1):
                t = deck_top(x, y, z0)
                if t is None or t > z0:
                    high.append((x, y, t)); continue
                for z in range(t, z0):
                    put(x, y, z, C['floor']); filled += 1
        # 艙壁的柱：從甲板面（比 z0 低就從 z0 往下補到甲板面）砌到天花板；門洞那幾格留空、門檻補到 z0 − 1
        wall_cols = []                                     # (x, y, door?)
        wxs = [w['x'] for w in R.get('walls', [])]
        for w in R.get('walls', []):
            wx = w['x']
            if side == 'C':
                yl, yh = ya - 1, yb + 1
                while yl > 0 and not S[wx, yl, z0:z0 + HEAD].all() and not S[wx, yl, z0 + 4]: yl -= 1
                while yh < NY - 1 and not S[wx, yh, z0:z0 + HEAD].all() and not S[wx, yh, z0 + 4]: yh += 1
            elif side == 'S':
                yl, yh = yin, yb + 1
                while yh < NY - 1 and not S[wx, yh, z0 + 4]: yh += 1
            else:
                yl, yh = ya - 1, yin
                while yl > 0 and not S[wx, yl, z0 + 4]: yl -= 1
            d = w.get('door')
            for y in range(yl, yh + 1):
                wall_cols.append((wx, y, y, d))            # 橫的艙壁：沿著 y 走
        if yin is not None:
            xa = min(wxs + [x0]) if min(wxs + [x0]) < x0 else x0 - 1
            xb = max(wxs + [x1]) if max(wxs + [x1]) > x1 else x1 + 1
            d = R.get('door')
            for x in range(xa, xb + 1):
                wall_cols.append((x, yin, x, d))           # 縱的艙壁：沿著 x 走
        nwall = 0
        for (x, y, u, d) in wall_cols:
            t = deck_top(x, y, z0)
            if t is None:
                continue
            isdoor = bool(d and d[0] <= u <= d[1])
            for z in range(t, z0):                         # 艙壁底下／門檻：補到 z0 − 1（同地板）
                put(x, y, z, C['floor'])
            for z in range(z0, ceil_of(x, y, z0)):
                if isdoor and z < z0 + DH:
                    continue
                frame = bool(d) and z <= z0 + DH and (isdoor or u in (d[0] - 1, d[1] + 1))   # 門框：門洞兩旁那一柱＋門楣
                put(x, y, z, C['frame'] if frame else C['wall'])
                nwall += 1
        # 門外的台階（steps：[[x0, x1, y0, y1, 站的高度] …]）：門外甲板比艙裡低 ⇒ 一階一階補到那一階的高度 − 1
        for (sx0, sx1, sy0, sy1, sz) in R.get('steps', []):
            for x in range(sx0, sx1 + 1):
                for y in range(sy0, sy1 + 1):
                    t = deck_top(x, y, sz)
                    for z in range(t if t is not None else sz, sz):
                        put(x, y, z, C['floor'])
        # 門口那一格（.door）：開在橫艙壁（walls 那一道有 door）⇒ 那道艙壁的門洞中間；不然開在縱艙壁（R.door）
        wd = [w for w in R.get('walls', []) if w.get('door')]
        if wd:
            dx = wd[0]['x']; dy = (wd[0]['door'][0] + wd[0]['door'][1]) // 2
        else:
            dx = (R['door'][0] + R['door'][1]) // 2; dy = yin
        # 驗：框裡全空氣（含本步的格）、地板、門口站得住、門外一步的高低差、模型
        T = S.copy()
        for (x, y, z) in cells:
            T[x, y, z] = True
        solid = int(T[x0:x1 + 1, ya:yb + 1, z0:z1 + 1].sum())
        floor_ok = int(T[x0:x1 + 1, ya:yb + 1, z0 - 1].sum())
        door_stand = bool(T[dx, dy, z0 - 1] and not T[dx, dy, z0:z0 + NAV_HEAD].any())   # 走得過去：頭上 NAV_HEAD（擺東西才要 HEAD）
        if wd:
            ox, oy = (dx + 1 if dx > x1 else dx - 1), dy     # 門外一格（橫艙壁：往框外那一側）
        else:
            ox, oy = dx, (dy - 1 if side == 'S' else dy + 1)
        ot = None
        for z in range(z0 + 3, z0 - 8, -1):
            if T[ox, oy, z - 1] and not T[ox, oy, z:z + NAV_HEAD].any():
                ot = z; break
        # 遊戲擺東西的格子：0.5 m（5 格）一格、零頭平分兩邊；整格腳下實心、頭上 HEAD 格空
        nx, ny = (x1 - x0 + 1) // 5, (yb - ya + 1) // 5
        ox0, oy0 = x0 + ((x1 - x0 + 1) - nx * 5) // 2, ya + ((yb - ya + 1) - ny * 5) // 2
        good = 0
        for i in range(nx):
            for j in range(ny):
                xs, ys = slice(ox0 + 5 * i, ox0 + 5 * i + 5), slice(oy0 + 5 * j, oy0 + 5 * j + 5)
                if T[xs, ys, z0 - 1].all() and not T[xs, ys, z0:z0 + HEAD].any():
                    good += 1
        v = {'name': R['name'], 'box': [x0, ya, z0, x1, yb, z1], 'size_m': [round((x1 - x0 + 1) / 10, 1), round((yb - ya + 1) / 10, 1), round((z1 - z0 + 1) / 10, 1)],
             'solid_in_box': solid, 'floor': [floor_ok, (x1 - x0 + 1) * (yb - ya + 1)], 'floor_high': high[:6], 'filled': filled, 'wall_cells': nwall,
             'door': [dx, dy, z0], 'door_stand': door_stand, 'outside_floor': ot, 'step': (z0 - ot) if ot is not None else None,
             'models_in': models_in(x0, ya, z0, x1, yb, z1), 'grid': [nx, ny], 'grid_ok': good}
        V['rooms'].append(v)
        place['anchors'][R['name'] + '.min'] = [x0, ya, z0]
        place['anchors'][R['name'] + '.max'] = [x1, yb, z1]
        place['anchors'][R['name'] + '.door'] = [dx, dy, z0]
    # 房間之間不重疊、本步的格不碰模型外框
    hit = sorted({n for (x, y, z) in cells for n, b in boxes if b[0] <= x + 0.5 < b[3] and b[1] <= y + 0.5 < b[4] and b[2] <= z + 0.5 < b[5]})
    V['cells'] = len(cells)
    V['cells_in_models'] = hit
    probs = []
    for v in V['rooms']:
        if v['solid_in_box']: probs.append('%s 框裡 %d 格不是空氣' % (v['name'], v['solid_in_box']))
        if v['floor'][0] < v['floor'][1]: probs.append('%s 地板 %d／%d' % (v['name'], *v['floor']))
        if v['floor_high']: probs.append('%s 甲板比 z0 高：%s' % (v['name'], v['floor_high']))
        if not v['door_stand']: probs.append('%s 門口站不住' % v['name'])
        if v['step'] is None or abs(v['step']) > 3: probs.append('%s 門外一步高低差 %s' % (v['name'], v['step']))
        if v['models_in']: probs.append('%s 框裡有模型 %s' % (v['name'], v['models_in']))
        if v['size_m'][0] < 1.5 or v['size_m'][1] < 1.5: probs.append('%s 太小 %s' % (v['name'], v['size_m']))
    if hit: probs.append('本步的格碰到模型外框：%s' % hit)
    V['problems'] = probs
    print(json.dumps(V, ensure_ascii=False, indent=1))
    if probe:
        print('（--probe ⇒ 不寫檔）')
        return
    write_list(os.path.join(design, 'masks', 'cabins', 'cabins.vox.txt'), [(x, y, z, c) for (x, y, z), c in cells.items()])
    json.dump(place, open(os.path.join(design, 'cabins_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(V, open(os.path.join(design, 'verify_cabins.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


main()

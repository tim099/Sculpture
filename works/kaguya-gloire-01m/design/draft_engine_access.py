# 光榮號 階段十 機艙的出口 —— 主艙口底下兩座鐵梯；抄自拿破崙號 kotoko-napoleon-01m/design/draft_engine_access.py（kotoko）。光榮號改：ASM、量的範圍、只有主艙口兩座（鍋爐頂梯子看讀數再決定）、起點高度（砲甲板站 z 90）
#   自己寫的。機艙（x 330–650，faux-pont 不鋪）從船底到下砲甲板底下 8 m 沒有任何東西接；主艙口（x 505–533、|dy| ≤ 12）四層都開、
#   底下直通機艙地板 ⇒ 兩座梯子掛在艙口裡（S 舷 y 207、P 舷 y 193，鏡像），從機艙地板爬到下砲甲板、往船頭出艙口。
#   梯子：機艙的鐵梯（陡）—— 每 3 格一階、每階往前 1 格（約 72°）、踏板 2 格深 7 格寬、兩側 stringer；鐵灰 73。
#   出口那一段艙口圍欄（2 格高）刻開 ⇒ 最上面一階跟甲板只差 1 格。
#   階段十四：機艙鋪了鐵地板（甲板-engine，板面 z 12）⇒ 梯子照新地板重算（梯腳那一欄最高的實心 ＝ 板）；主艙口兩座加 <梯名>.decks ＝ engine,lower。
#   輸入：作品現在的樣子（組裝件 export format=list links=all）；plan.json 的 decks_build.hatches（主艙口）
#   輸出：masks/engine_access/ladders.vox.txt（梯子子作品，世界座標、at 0,0,0）、masks/engine_access/coaming_carve.vox.txt（甲板-lower 要刻的圍欄格，帶顏色守門）、
#         engine_access_points.json（梯子固定點）、verify_engine_access.json
#   用法：python -I -X utf8 draft_engine_access.py <design> [--grid <已匯出的 list>] [--probe drop=<梯名>]（反向對照：少一座梯子，連通讀數要照實變）
import sys, os, json, subprocess, tempfile, hashlib
import numpy as np
from collections import deque

ASM = 'kaguya-gloire-01m-assembly'
NX, NY, NZ = 1200, 400, 260
YC = 200
IRON = 73
FP_UP, FP_DOWN, FP_HEAD = 6, 8, 7          # 第一人稱：跨得上 0.6 m、踩得下 0.8 m、頭上 0.7 m（Blockside 81_fps.js）
ROOM = (370, 680, 92)                       # 量連通的範圍：機艙（x 400–650）前後各多 30 格（faux-pont 底下的貨艙）、砲甲板（stand 90）以下


def export_grid(path=None):
    if path is None:
        d = tempfile.mkdtemp()
        path = os.path.join(d, 'asm.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + ASM, '--arg', 'out=' + path,
                            '--arg', 'links=all', '--arg', 'hide_links=甲板-lower/梯子-機艙'], capture_output=True, text=True, encoding='utf-8', errors='replace')   # 藏本件：落格之後重跑讀到的還是同一份
        if r.returncode != 0 and '梯子-機艙' in (r.stdout + r.stderr):   # 還沒落格：那條關聯不存在
            r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + ASM, '--arg', 'out=' + path,
                                '--arg', 'links=all'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(path):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-800:])
    A = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((NX, NY, NZ), np.uint8)
    A = A[A[:, 2] < NZ]
    G[A[:, 0], A[:, 1], A[:, 2]] = A[:, 3]
    return G


def ladder(G, yc, x_top, s, top):
    """一座梯子：往 s（+1 船頭／−1 船尾）爬，最上面一階在 x_top、緊貼它前面那一欄（x_top + s）的頂面底下 1 格（站上去跟頂面只差 1 格）。
    top ＝ 'deck'（那一欄 z 60 以上第一格實心 ＝ 甲板板；上面的圍欄另外刻）｜'boiler'（那一欄 z 62 以下最高的實心 ＝ 鍋爐頂）。
    最下面一階在地板上 3 格；地板 ＝ 梯腳那一欄 z 60 以下最高的實心。"""
    S = G > 0
    col = S[x_top + s, yc]
    zdeck = int(np.nonzero(col[60:100])[0][0]) + 60 if top == 'deck' else int(np.nonzero(col[:62])[0][-1])
    n = None
    for _ in range(3):                                    # 梯腳那一欄看階數 ⇒ 地板高度 ⇒ 階數（船底是彎的，兩次就收斂）
        xf = x_top - s * ((n or 27))
        zf = int(np.nonzero(S[xf, yc, :60])[0][-1])
        n2 = (zdeck - 1 - zf) // 3
        if n2 == n:
            break
        n = n2
    cells = {}
    treads = []
    for k in range(1, n + 1):
        zt = zf + 3 * k
        xa = x_top - s * (n - k)                          # 踏板 2 格深：xa、xa − s；最上面一階 ＝ x_top、x_top − s
        treads.append((xa, zt))
        for xx in (xa, xa - s):
            for yy in range(yc - 3, yc + 4):
                cells[(xx, yy, zt)] = IRON
    x0 = treads[0][0]
    for kk in range(0, n + 1):                            # stringer：沿斜線 4 格高，接到地板與頂面底下
        xx = x0 + s * kk - s
        zc = zf + 3 * kk
        for z in range(max(zf + 1, zc - 3), min(zdeck - 1, zc + 1) + 1):
            for yy in (yc - 4, yc + 4):
                cells[(xx, yy, z)] = IRON
    over = [k for k in cells if S[k]]
    for k in over:
        del cells[k]                                      # 已有的格優先（讀數照實報幾格）
    xh = x_top + 4 * s
    zh = zdeck + 1 if top == 'deck' else int(np.nonzero(S[xh, yc, :62])[0][-1]) + 1
    pts = {'foot': [x0 - 2 * s, yc, zf + 1], 'lo': [treads[0][0] - s, yc, treads[0][1] + 1], 'hi': [treads[-1][0] - s, yc, treads[-1][1] + 1],
           'head': [xh, yc, zh]}
    return cells, pts, {'steps': n, 'floor_z': zf, 'top_z': zdeck, 'x': sorted([x0 - s, x_top]), 'dir': s, 'top': top, 'dropped_overlap': len(over)}


def stand_map(S, x0, x1, ztop):
    sub = S[x0:x1]
    st = np.zeros(sub.shape[:2] + (ztop + 1,), bool)
    for z in range(1, ztop + 1):
        ok = sub[:, :, z - 1] & ~sub[:, :, z]
        for h in range(1, FP_HEAD):
            ok &= ~sub[:, :, z + h]
        st[:, :, z] = ok
    return st


def reach(st, x0, starts, ladders_pts, back=False):
    """從起點照第一人稱走 ＋ 爬梯子（foot ↔ head）能到的站位。走：四鄰那一柱、上 ≤ 6／下 ≤ 8 之內**離腳最近**的那個高度
    （同 81_fps.js fpStand：⛔ 不是窗裡任何一個 —— 站在斜殼外面時，旁邊那柱最近的是殼頂，不會掉進殼底下）；跳不算。
    back ⇒ 反過來：哪些站位**走得到起點**（同一張有向圖反著走）—— 「掉得進去」跟「上得來」是兩件事（下 0.8 m、上 0.6 m）。"""
    cols = {}
    xs, ys, zs = np.nonzero(st)
    for x, y, z in zip((xs + x0).tolist(), ys.tolist(), zs.tolist()):
        cols.setdefault((x, y), []).append(z)
    nxt = {}
    for (x, y), zl in cols.items():
        for z in zl:
            out = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c = [z2 for z2 in cols.get((x + dx, y + dy), ()) if -FP_DOWN <= z2 - z <= FP_UP]
                if c:
                    out.append((x + dx, y + dy, min(c, key=lambda z2: (abs(z2 - z), -z2))))
            nxt[(x, y, z)] = out
    for P in ladders_pts:
        a, b = tuple(P['foot']), tuple(P['head'])
        if a in nxt and b in nxt:
            nxt[a].append(b)
            nxt[b].append(a)
    if back:
        rev = {}
        for p, qs in nxt.items():
            for q in qs:
                rev.setdefault(q, []).append(p)
        nxt = rev
    seen = {tuple(p) for p in starts if p[2] in cols.get((p[0], p[1]), ())}
    q = deque(seen)
    while q:
        p = q.popleft()
        for t in nxt.get(p, ()):
            if t not in seen:
                seen.add(t)
                q.append(t)
    return seen


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    args = sys.argv[2:]
    gpath = args[args.index('--grid') + 1] if '--grid' in args else None
    probe = [a.split('=', 1)[1] for a in args if a.startswith('drop=')]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    hatch = [h for h in plan['decks_build']['hatches'] if h['name'] == '主艙口'][0]
    G = export_grid(gpath)
    S0 = G > 0
    # 梯名 ⇒ (yc, 最上面一階的 x, 方向, 頂面)。主艙口：前緣 x1 那一欄、往船頭出艙口（光榮號：主艙口 x 505–533 在主桅與鍋爐之間，底下直通機艙地板）。
    names = {'engine-S': (YC + 7, hatch['x1'], 1, 'deck'), 'engine-P': (YC - 7, hatch['x1'], 1, 'deck')}
    if probe:
        names = {k: v for k, v in names.items() if k not in probe}
    cells, pts, info = {}, {}, {}
    for nm, (yc, xt, sd, top) in names.items():
        c, p, i = ladder(G, yc, xt, sd, top)
        cells.update(c)
        pts[nm] = {'points': p, **i}
        if top == 'deck':
            pts[nm]['decks'] = 'engine,lower'                         # §9.3 直接指定：機艙地板（甲板-engine，階段十四）↔ 下砲甲板
    # 圍欄：出口那一欄（艙口前緣外一格 x1+1）、踏板與 stringer 寬（|y − yc| ≤ 4）、甲板面上 2 格
    carve = {}
    for nm, (yc, xt, sd, top) in names.items():
        if top != 'deck':
            continue
        x = hatch['x1'] + 1
        zd = pts[nm]['top_z']
        for yy in range(yc - 4, yc + 5):
            for z in (zd + 1, zd + 2):
                if G[x, yy, z]:
                    carve[(x, yy, z)] = int(G[x, yy, z])
    R = {'ladders': pts, 'cells': len(cells), 'coaming_carve': len(carve)}
    R['overlap_existing'] = int(sum(1 for k in cells if S0[k]))
    R['mirror_diff'] = int(sum(1 for (x, y, z), c in cells.items() if cells.get((x, 400 - y, z)) != c)) if not probe else None
    # 套上之後的格子
    S = S0.copy()
    for k in cells:
        S[k] = True
    for k in carve:
        S[k] = False
    bad = []
    for nm, v in pts.items():
        for pk, (x, y, z) in v['points'].items():
            if S[x, y, z] or not S[x, y, z - 1] and pk in ('foot', 'head'):
                bad.append('%s.%s 那一格不是空的、或腳下不是實心' % (nm, pk))
            if any(S[x, y, z + h] for h in range(1, FP_HEAD)):
                bad.append('%s.%s 頭上 %d 格內有實心：%s' % (nm, pk, FP_HEAD, [z + h for h in range(1, FP_HEAD) if S[x, y, z + h]]))
    R['point_problems'] = bad
    # 連通（第一人稱）：機艙地板上每一個站得住的格，能不能走＋爬回下砲甲板
    x0, x1, zt = ROOM
    st = stand_map(S, x0, x1, zt)
    st_before = stand_map(S0, x0, x1, zt)
    lp = [v['points'] for v in pts.values()]
    deck_starts = [v['points']['head'] for v in pts.values() if v['top'] == 'deck'] or [[537, YC + 7, 90]]
    up = reach(st, x0, deck_starts, lp, back=True)                     # 從機艙走得回甲板的
    down = reach(st, x0, deck_starts, lp)                              # 從甲板走得到的（含掉下去）
    engine_floor = set(zip(*[a.tolist() for a in np.nonzero(st[:, :, :60])]))
    engine_floor = {(x + x0, y, z) for x, y, z in engine_floor}
    R['reach'] = {'engine_floor_stand_cells': len(engine_floor), 'back_to_deck': len(engine_floor & up),
                  'not_back': len(engine_floor - up), 'reachable_from_deck': len(engine_floor & down),
                  'reachable_but_not_back': len((engine_floor & down) - up)}
    left = np.array(sorted(engine_floor - up)) if engine_floor - up else np.zeros((0, 3), int)
    if len(left):
        R['reach']['not_reached_box'] = {'x': [int(left[:, 0].min()), int(left[:, 0].max())], 'y': [int(left[:, 1].min()), int(left[:, 1].max())],
                                          'z': [int(left[:, 2].min()), int(left[:, 2].max())]}
    eb = {(x + x0, y, z) for x, y, z in zip(*[a.tolist() for a in np.nonzero(st_before[:, :, :60])])}
    R['reach']['before'] = {'reachable_from_deck': len(eb & reach(st_before, x0, [[537, YC + 7, 90]], [])),
                            'back_to_deck': len(eb & reach(st_before, x0, [[537, YC + 7, 90]], [], back=True))}
    if probe:
        print(json.dumps({'probe': probe, 'reach': R['reach'], 'ladders': sorted(pts)}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'engine_access')
    os.makedirs(od, exist_ok=True)

    def dump(path, d, head, color=True):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for k in sorted(d):
                f.write(('%d,%d,%d,%d\n' % (k + (d[k],))) if color else '%d,%d,%d\n' % k)
        return hashlib.sha256(open(path, 'rb').read()).hexdigest()
    R['sha256'] = {
        'ladders': dump(os.path.join(od, 'ladders.vox.txt'), cells, '# 光榮號 機艙梯子（主艙口底下兩座；世界座標，at 0,0,0）\n'),
        'coaming_carve': dump(os.path.join(od, 'coaming_carve.vox.txt'), carve, '# 光榮號 甲板-lower 主艙口前緣圍欄刻開（梯子出口；x,y,z,原色 ＝ 守門）\n')
        if carve or not os.path.exists(os.path.join(od, 'coaming_carve.vox.txt')) else hashlib.sha256(open(os.path.join(od, 'coaming_carve.vox.txt'), 'rb').read()).hexdigest()}
    if not carve:
        R['coaming_carve_note'] = '圍欄已經刻過（甲板-lower 標記「機艙梯子出口」）⇒ 沿用階段十三那一份清單'
    with open(os.path.join(design, 'engine_access_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'verify_engine_access.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

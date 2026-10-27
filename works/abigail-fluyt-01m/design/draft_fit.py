# 澤漢號 步驟 10（TASK-0966）：出處 ame-labelle-01m/design/draft_fit.py（拉貝爾號步驟 16）；本船：空間、中線、甲板 floor 改讀 plan／decks_meta.tsv，windlass 可以 skip。原檔頭：拉貝爾號 步驟 16 補做（TASK-0966；Tim 2026-10-26「測試ok 加上還沒做的部分吧」）：艙蓋 ×3（模型 kind=door）、廚房（爐灶挪位、kind=galley）、
#   絞盤（關聯）、貨艙前段艙房（艙壁子作品＋kind=rooms 的框）、下桅繩梯（橫繩組 climb 的落腳點）
#   輸入：plan.json（fit_build）＋ 組裝件現在的格子與部件（CLI 匯出；扣掉本步自己的關聯與模型 ⇒ 重產時不會把上一輪當成船）
#   輸出：masks/fit/hatch-{aft,main,fore}.vox.txt（艙蓋子作品自己的座標）、masks/fit/{windlass,hold_room}.vox.txt（世界座標、at 0,0,0）、
#         fit_placement.json、verify_fit.json
#   量法照遊戲：門的開口 ＝ 門外框正下方那一層（floor(z0) − 1）原本空的格（25_doors.js doorsShip）；廚師的面 ＝ 外框外 2 格的四個面中點、
#   3 格內有走路格（腳下實心、頭上 12 格空、不在別的模型外框裡；45_galley.js galleyInit）；繩梯落腳點腳下實心、上面 7 格空（Ship_Rigging §6）
#   用法：python -I -X utf8 draft_fit.py <design> [--probe=galley_x=<x>｜--probe=room_y0=<y>]（反向對照，⛔ 不寫檔）
import sys, os, json, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list

NX, NY, NZ = 480, 192, 384      # 本船的空間（拉貝爾號 352×160×256）


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
        f.write('# x,y,z,color（draft_fit.py）\n')
        for c in sorted(cells):
            f.write('%d,%d,%d,%d\n' % c)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = dict(a.split('=', 1)[1].split('=', 1) for a in sys.argv[2:] if a.startswith('--probe='))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    FB = plan['fit_build']
    HT, GL, WL, RM, RL = FB['hatches'], FB['galley'], FB['windlass'], FB['room'], FB['ratlines']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(FB['assembly'], None, links=None)
    own = set()
    for w in [RM['work']] + ([] if WL.get('skip') else [WL['work']]):
        if os.path.exists(os.path.join(WORKS, w, 'work.json')):
            own |= set(map(tuple, export_list(w, None)[:, :3].tolist()))
    for h in HT['list']:                                   # 走得過去的蓋子是關聯（一層、剛好佔設計的框）
        if h.get('walk'):
            own |= {(x, y, h['z']) for x in range(h['x0'], h['x1'] + 1) for y in range(h['y0'], h['y1'] + 1)}
    A = np.array([r for r in A.tolist() if tuple(r[:3]) not in own], np.int32)
    S = np.zeros((NX, NY, NZ), bool)
    S[A[:, 0], A[:, 1], A[:, 2]] = True
    own_models = {h['name'] for h in HT['list']} | {GL['name']}
    boxes = [(m['path'], m['box']) for m in export_parts(FB['assembly'])['models'] if m['path'].split('/')[-1] not in own_models]

    def in_box(x, y, z, pad=0.0):
        return [n for n, b in boxes if b[0] - pad <= x + 0.5 < b[3] + pad and b[1] - pad <= y + 0.5 < b[4] + pad and b[2] <= z + 0.5 < b[5]]

    def box_hits(b):           # 跟外框相交的別的模型
        return [n for n, o in boxes if b[0] < o[3] and o[0] < b[3] and b[1] < o[4] and o[1] < b[4] and b[2] < o[5] and o[2] < b[5]]

    def solid_in(b):           # 外框裡（格心在框內）有幾格實心
        n = 0
        for x in range(int(np.floor(b[0])), int(np.ceil(b[3]))):
            for y in range(int(np.floor(b[1])), int(np.ceil(b[4]))):
                for z in range(int(np.floor(b[2])), int(np.ceil(b[5]))):
                    if b[0] <= x + 0.5 < b[3] and b[1] <= y + 0.5 < b[4] and b[2] <= z + 0.5 < b[5] and S[x, y, z]:
                        n += 1
        return n

    def stand(x, y, z, head):
        return bool(S[x, y, z - 1] and not S[x, y, z:z + head].any())

    V = {}
    place = {'note': 'draft_fit.py（步驟 16 補做）產生；build_fit.py 照它落格', 'hatches': [], 'galley': None, 'windlass': None, 'room': None, 'ratlines': []}

    # ── 艙蓋：一層板（邊框橡木、裡面甲板色）＋兩根橫檔＋一個鐵環；鉸鏈沿 +x 在 y=0 那一邊 ──
    C = HT['colors']
    YC = plan['space']['yc']
    floor_main = [tuple(map(float, p.split(':'))) for p in next(json.loads(l.split('	')[2])['floor'] for l in open(os.path.join(design, 'decks_meta.tsv'), encoding='utf-8') if l.split('	')[1] == '甲板-main').split(',')]   # 甲板-main 的 floor meta（本船讀 decks_meta.tsv；拉貝爾號寫死）
    for h in HT['list']:
        X, Y, z0 = h['x1'] - h['x0'] + 1, h['y1'] - h['y0'] + 1, h['z']
        walk = bool(h.get('walk'))
        cells = set()
        for x in range(X):
            for y in range(Y):
                cells.add((x, y, 0, C['frame'] if x in (0, X - 1) or y in (0, Y - 1) else C['plank']))
        if not walk:                                       # 門：橫檔＋鐵環；走得過去的蓋子只有一層（頂要在地板 +3 格內）
            for x in (1, X - 2):
                for y in range(1, Y - 1):
                    cells.add((x, y, 1, C['frame']))
            cells.add((X // 2, Y - 2, 1, C['iron']))
        key = h['work'].rsplit('-', 1)[1]
        write_list(os.path.join(design, 'masks', 'fit', 'hatch-%s.vox.txt' % key), cells)
        zs = 1 if walk else 2
        b = [h['x0'], h['y0'], z0, h['x1'] + 1, h['y1'] + 1, z0 + zs]
        hit_solid = sum(1 for (x, y, z, c) in cells if S[h['x0'] + x, h['y0'] + y, z0 + z])
        if walk:
            # 遊戲的走路點（x0 奇數、y 偶數，每 2 格）：蓋子頂上站得住（上面 12 格空）、在那一欄地板 −2～+3 格裡
            pts = [(x, y) for x in range(h['x0'], h['x1'] + 1) if x % 2 == 1 for y in range(h['y0'], h['y1'] + 1) if y % 2 == 0]
            fl = lambda x: float(np.interp(x, [p[0] for p in floor_main], [p[1] for p in floor_main]))
            ok_n = sum(1 for (x, y) in pts if not S[x, y, z0 + 1:z0 + 13].any() and fl(x) - 2 <= z0 + 1 <= fl(x) + 3)
            V[h['name']] = {'cells': len(cells), 'box': b, 'hit_solid': hit_solid, 'hit_models': box_hits(b), 'walk_points': len(pts), 'walk_ok': ok_n,
                            'rim_top': int(max(z for z in range(20, 70) if S[h['x0'] - 1, YC, z]))}
            place['hatches'].append({'name': h['name'], 'work': h['work'], 'title': h['title'], 'host': HT['host'], 'size': [X, Y, 1], 'at': [h['x0'], h['y0'], z0],
                                     'mask': 'masks/fit/hatch-%s.vox.txt' % key, 'link': True})
            continue
        zt = z0 - 1
        opening = [(x, y) for x in range(h['x0'], h['x1'] + 1) for y in range(h['y0'], h['y1'] + 1) if not S[x, y, zt]]
        through = sum(1 for (x, y) in opening if not S[x, y, zt - 3:zt].any())     # 開口底下 3 層也空 ＝ 真的通到艙裡
        V[h['name']] = {'cells': len(cells), 'box': b, 'hit_solid': hit_solid, 'hit_models': box_hits(b), 'opening': len(opening), 'opening_through': through,
                        'rim_z': zt, 'rim_solid': int(sum(S[x, y, zt] for x in range(h['x0'], h['x1'] + 1) for y in range(h['y0'], h['y1'] + 1)))}
        place['hatches'].append({'name': h['name'], 'work': h['work'], 'title': h['title'], 'host': HT['host'], 'size': [X, Y, 2], 'at': [h['x0'], h['y0'], z0],
                                 'mask': 'masks/fit/hatch-%s.vox.txt' % key, 'anchors': {'hinge-a': [0, 0, 0], 'hinge-b': [X - 1, 0, 0]},
                                 'meta': {'kind': 'door', 'open': 'up', 'open_deg': h['open_deg']}})

    # ── 廚房：爐灶挪位，z 照腳下量（同 draft_gear：外框底下最高的實心 ＋ 1） ──
    gx, gy = float(probe.get('galley_x', GL['at'][0])), float(probe.get('galley_y', GL['at'][1]))   # 反向對照：v1 的位置 x 203、y 88.5
    s = GL['scale']
    W = [44 * s, 32 * s, 44 * s]                       # 元件 44 × 32 × 44 格（kaguya-gloire-01m-galley 匯出量）
    x0, y0 = gx - GL['pivot'][0] * s, gy - GL['pivot'][1] * s
    zfoot = 0
    for x in range(int(np.floor(x0)), int(np.ceil(x0 + W[0]))):
        for y in range(int(np.floor(y0)), int(np.ceil(y0 + W[1]))):
            zfoot = max(zfoot, max(z for z in range(0, GL['below_z']) if S[x, y, z]))      # 船首樓甲板底下（本船 below_z 57：船首樓的樑 z 57–58）最高的實心 ＝ 主甲板頂
    gz = zfoot + 1
    gb = [x0, y0, gz, x0 + W[0], y0 + W[1], gz + W[2]]
    cx, cy = gx, gy
    faces = []
    for nm, (fx, fy) in (('−x', (gb[0] - 2, cy)), ('+x', (gb[3] + 2, cy)), ('−y', (cx, gb[1] - 2)), ('+y', (cx, gb[4] + 2))):
        best = None
        for x in range(int(fx) - 3, int(fx) + 4):
            for y in range(int(fy) - 3, int(fy) + 4):
                for z in range(gz - 3, gz + 4):
                    if 0 <= x < NX and 0 <= y < NY and stand(x, y, z, 12) and not in_box(x, y, z) and not (gb[0] <= x + 0.5 < gb[3] and gb[1] <= y + 0.5 < gb[4]):
                        d = ((x + 0.5 - fx) ** 2 + (y + 0.5 - fy) ** 2) ** 0.5
                        if d <= 3 and (best is None or d < best[0]):
                            best = (round(d, 2), [x, y, z])
        faces.append({'face': nm, 'at': [round(fx, 2), round(fy, 2)], 'walk': best[1] if best else None, 'd': best[0] if best else None})
    V['廚房'] = {'box': [round(v, 2) for v in gb], 'hit_solid': solid_in(gb), 'hit_models': box_hits(gb), 'faces': faces, 'faces_ok': sum(1 for f in faces if f['walk'])}
    place['galley'] = {'name': GL['name'], 'host': GL['host'], 'work': GL['work'], 'at': [gx, GL['at'][1], gz], 'pivot': GL['pivot'], 'scale': s, 'rotate': GL['rotate'], 'meta': GL['meta']}

    # ── 絞盤：兩根立柱（離船殼內壁 post_in 格）＋橫的絞筒＋撬棍孔 ──
    if WL.get('skip'):                                # 本船：船首樓下太短、橫跨船寬的 windlass 會切斷主甲板 ⇒ 不做（直立絞盤是 gear_build 的模型）
        V['絞盤'] = {'skip': WL['src']}
    else:
        C = WL['colors']
        x = WL['x']
        zdeck = max(z for z in range(10, 56) if S[x, YC, z] and not S[x, YC, z + 1]) + 1         # 主甲板頂上第一層空氣
        ztop = min(z for z in range(zdeck, 80) if S[x, YC, z]) - 1                                 # 船首樓甲板底下那一格
        lo, hi = 0, NY
        for z in range(zdeck, ztop + 1):
            yl = max(y for y in range(0, YC) if S[x, y, z] or S[x + 1, y, z])
            yh = min(y for y in range(YC + 1, NY) if S[x, y, z] or S[x + 1, y, z])
            lo, hi = max(lo, yl), min(hi, yh)
        pw, pin = WL['post_w'], WL['post_in']
        pyl = list(range(lo + 1 + pin, lo + 1 + pin + pw))
        pyh = list(range(hi - pin - pw, hi - pin))
        wcells = {}
        for yy in pyl + pyh:
            for xx in range(x, x + pw):
                for z in range(zdeck, ztop + 1):
                    wcells[(xx, yy, z)] = C['oak']
        zc, r = WL['barrel_zc'], WL['barrel_r']
        for yy in range(pyl[-1] + 1, pyh[0]):
            for xx in range(x - 3, x + pw + 3):
                for z in range(int(zc) - 3, int(zc) + 4):
                    d = ((xx + 0.5 - (x + pw / 2)) ** 2 + (z + 0.5 - zc) ** 2) ** 0.5
                    if d <= r:
                        top = z + 0.5 > zc + r - 1 or xx + 0.5 < x + pw / 2 - r + 1
                        wcells[(xx, yy, z)] = C['dark'] if ((yy - YC) % 3 == 0 and top) else C['barrel']    # 照離中線算 ⇒ 兩舷對稱（v1 yy % 3 ⇒ 鏡像色差 20 對）
        wl = [(a, b, c, col) for (a, b, c), col in wcells.items()]
        write_list(os.path.join(design, 'masks', 'fit', 'windlass.vox.txt'), wl)
        V['絞盤'] = {'cells': len(wl), 'deck_z': zdeck, 'top_z': ztop, 'inner_y': [lo, hi], 'posts_y': [pyl, pyh], 'barrel_y': [pyl[-1] + 1, pyh[0] - 1],
                     'hit_solid': sum(1 for (a, b, c, _) in wl if S[a, b, c]), 'hit_models': sorted({n for (a, b, c, _) in wl for n in in_box(a, b, c)}),
                     'posts_touch': [bool(S[x, pyl[0], zdeck - 1] and S[x, pyl[0], ztop + 1]), bool(S[x, pyh[0], zdeck - 1] and S[x, pyh[0], ztop + 1])]}
        place['windlass'] = {'work': WL['work'], 'title': WL['title'], 'link': WL['link'], 'mask': 'masks/fit/windlass.vox.txt'}

    # ── 艙房：x = wall_x 一道艙壁（貨艙地板到主甲板底下，兩舷到船殼內壁），中線門洞；框 kind=rooms ──
    C = RM['colors']
    wx, dy0, dy1 = RM['wall_x'], RM['door_y'][0], RM['door_y'][1]
    rcells = []
    for z in range(RM['z_lo'], 80):
        if S[wx, YC, z]:
            break
        yl = max(y for y in range(0, YC) if S[wx, y, z])
        yh = min(y for y in range(YC + 1, NY) if S[wx, y, z])
        for y in range(yl + 1, yh):
            if dy0 <= y <= dy1 and z <= RM['door_top']:
                continue
            frame = (y in (dy0 - 1, dy1 + 1) and z <= RM['door_top'] + 1) or (dy0 - 1 <= y <= dy1 + 1 and z == RM['door_top'] + 1)
            rcells.append((wx, y, z, C['frame'] if frame else C['plank']))
    write_list(os.path.join(design, 'masks', 'fit', 'hold_room.vox.txt'), rcells)
    for c in rcells:
        S[c[0], c[1], c[2]] = True
    bx = RM['box']
    zl = bx['z_lo']
    zh = min(min([z for z in range(zl, 80) if S[xx, yy, z]] or [99]) for xx in range(bx['x'][0], bx['x'][1] + 1) for yy in range(bx['y'][0], bx['y'][1] + 1)) - 1   # 前艙口底下那幾欄沒有頂 ⇒ 不算
    by0 = int(probe.get('room_y0', bx['y'][0]))        # 反向對照：框往船殼那一側多拉幾格（頂照設計的框量好的）
    box = [bx['x'][0], by0, zl, bx['x'][1], bx['y'][1], zh]
    nonair = int(S[box[0]:box[3] + 1, box[1]:box[4] + 1, box[2]:box[5] + 1].sum())
    nofloor = int((~S[box[0]:box[3] + 1, box[1]:box[4] + 1, zl - 1]).sum())
    door = RM['door']
    V['艙房'] = {'wall_cells': len(rcells), 'wall_hit_models': sorted({n for (a, b, c, _) in rcells for n in in_box(a, b, c)}), 'box': box,
                 'size_m': [round((box[3] - box[0] + 1) / 10, 1), round((box[4] - box[1] + 1) / 10, 1), round((box[5] - box[2] + 1) / 10, 1)],
                 'nonair': nonair, 'nofloor': nofloor, 'models_in': sorted({n for xx in range(box[0], box[3] + 1) for yy in range(box[1], box[4] + 1) for n in in_box(xx, yy, zl)}),
                 'door_stand': stand(door[0], door[1], door[2], 14), 'out_stand': [stand(xx, YC, zl, 7) for xx in range(wx - 8, wx)].count(True)}
    place['room'] = {'work': RM['work'], 'title': RM['title'], 'host': RM['host'], 'link': RM['link'], 'mask': 'masks/fit/hold_room.vox.txt',
                     'anchors': {RM['name'] + '.min': box[:3], RM['name'] + '.max': box[3:], RM['name'] + '.door': door}, 'meta': {'kind': 'rooms'}}

    # ── 下桅繩梯：落腳點腳下實心、上面 7 格空、不在模型外框裡 ──
    V['繩梯'] = []
    for r in RL['list']:
        f, h = r['foot'], r['head']
        V['繩梯'].append({'name': r['name'], 'foot_ok': stand(*f, 7) and not in_box(*f), 'head_ok': stand(*h, 7) and not in_box(*h)})
        place['ratlines'].append(r)

    print(json.dumps(V, ensure_ascii=False, indent=1))
    if probe:
        print('（probe ⇒ 不寫檔）')
        return
    json.dump(place, open(os.path.join(design, 'fit_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(V, open(os.path.join(design, 'verify_fit.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


main()

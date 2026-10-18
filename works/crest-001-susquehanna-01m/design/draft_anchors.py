# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_anchors.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段九（TASK-0614）錨：沿用共用錨元件（憲法號 -anchor，0.1 m bower，造船規格 §9 anchor），兩舷各一隻掛在船頭側面；船殼登記 hawse-S／P。
#   擺法（自己寫的）：S 舷算、P 舷鏡像（mirror=y、at.y ＝ 401 − at.y、rotate 取負）。
#   候選：錨的中心 x（每 3 格）、ring 高度（每 2 格）、繞 z 轉的角度（錨爪沿船殼切線攤開）；每個候選從船殼外面往裡推，推到「模型每一格的格心＋八角都不在現況實心裡」的最裡面那一步；
#   錨環 ring 離船的實心 ≤ ring_reach 格（遊戲拿 ring 旁 8 格內的實心當掛點，太遠 ⇒ 開局就掉）；⛔ 不擋砲門（錨的格落在任一個砲門 x 範圍 ±2、z 範圍 ±2 裡 ⇒ 不要）。排序：貼船殼的格數（往船裡一格就是實心）多 ＞ 離船殼最遠的那格近 ＞ x 靠 plan 的 x。
#   hawse：船頭外表面（plan 的 x、z；那一排 S 舷最外面那一格），P 舷鏡像。
#   現況 ＝ 組裝件 links=all ＋ 模型外框（錨自己的不算）。輸出：verify_anchors.json。用法：python -I -X utf8 draft_anchors.py <design>
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio

NX, NY, NZ = 1300, 400, 260   # 蘇士奎哈納號改：框 1300
YC = 200
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + mio.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    works = os.path.dirname(os.path.dirname(D))
    plan = HL.load_plan(D)
    AN = plan['anchors']
    A = mio.export_list(mio.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    solid = occ.copy()                                                    # 貼船殼只看格子
    nbox = 0
    for m in parts():
        if (m.get('meta') or {}).get('kind') == 'anchor':
            continue
        b = m['box']
        if b[2] >= NZ:
            continue
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
        nbox += 1
    noport = np.zeros((NX, NZ), bool)
    for p in LY.ports(plan):
        noport[p['x0'] - 2:p['x1'] + 3, p['z0'] - 2:p['z1'] + 3] = True
    C = mio.export_list(AN['work'], None)
    an = {a['name']: a['at'] for a in json.load(open(os.path.join(works, AN['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
    piv = np.array(AN['pivot'], float)
    s = AN['scale']
    samp = (C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
    cen = C[:, :3].astype(float) + 0.5
    ring_rel = (np.array(an['ring'], float) + 0.5 - piv) * s

    def place(P, at, th):
        return rotz((P - piv) * s, th) + np.asarray(at, float)

    best = None
    tried = 0
    why = {"no_room": 0, "port": 0, "ring_far": 0}   # 蘇士奎哈納號加的：每個候選被哪一關淘汰
    for x in np.arange(AN['x'][0], AN['x'][1] + 0.01, 3.0):
        for zr in range(AN['ring_z'][0], AN['ring_z'][1] + 1, 2):
            for th in AN['angles']:
                tried += 1
                rr = rotz(ring_rel[None], th)[0]
                at0 = np.array([x - rr[0], 0.0, zr + 0.5 - rr[2]])
                ok_at = None
                for y in np.arange(AN['y_out'], YC, -0.5):                 # 從船外往裡推，推到碰到為止；取最後一個不碰的
                    at = at0.copy(); at[1] = y - rr[1]
                    W = place(samp, at, th)
                    i = np.floor(W).astype(int)
                    if (i[:, 2] < 0).any() or occ[i[:, 0], i[:, 1], i[:, 2]].any():
                        break
                    ok_at = at
                if ok_at is None:
                    why["no_room"] += 1
                    continue
                c = np.floor(place(cen, ok_at, th)).astype(int)
                if noport[c[:, 0], c[:, 2]].any():
                    why["port"] += 1
                    continue
                rw = np.floor(place((np.array(an['ring'], float) + 0.5)[None], ok_at, th)[0]).astype(int)
                R_ = AN['ring_reach']
                win = solid[rw[0] - R_:rw[0] + R_ + 1, rw[1] - R_:rw[1] + R_ + 1, rw[2] - R_:rw[2] + R_ + 1]
                gi = np.argwhere(win) - R_
                if not len(gi) or float(np.sqrt((gi ** 2).sum(1)).min()) > R_:
                    why["ring_far"] += 1
                    continue                                                  # 遊戲（10_ship.js）拿錨環 ring 旁 8 格內的實心當支點 ⇒ 這裡要求 ≤ ring_reach 格
                touch = int(solid[c[:, 0], c[:, 1] - 1, c[:, 2]].sum())
                # 離船殼最遠的那格：每格往船裡走幾格碰到實心（上限 20）
                far = 0
                for (cx, cy, cz) in c[::7]:
                    k = 1
                    while k < 20 and not solid[cx, cy - k, cz]:
                        k += 1
                    far = max(far, k)
                key = (-touch, far, abs(x - AN['x_pref']), abs(th - AN['angles'][0]), zr)
                if best is None or key < best[0]:
                    best = (key, [round(float(v), 3) for v in ok_at], float(th), touch, far, int(zr), float(x))
    assert best, ('錨擺不下', tried, why)
    _, at, th, touch, far, zr, xr = best
    at_p = [at[0], round(2 * YC + 1 - at[1], 3), at[2]]
    rows = [{'model': AN['name'] + '-S', 'at': at, 'rotate': [0, 0, th], 'mirror': 'none'},
            {'model': AN['name'] + '-P', 'at': at_p, 'rotate': [0, 0, -th], 'mirror': 'y'}]
    pts = {}
    for r in rows:
        for nm in ('ring', 'crown', 'fluke-a', 'fluke-b'):
            q = (np.array(an[nm], float)[None] + 0.5 - piv) * s
            if r['mirror'] == 'y':
                q[:, 1] = -q[:, 1]
            pts.setdefault(r['model'], {})[nm] = [round(float(v), 3) for v in (rotz(q, r['rotate'][2]) + np.array(r['at']))[0]]
    # 鏡像那一隻也真的量
    cP = samp - piv
    cP = cP * s
    cP[:, 1] = -cP[:, 1]
    i = np.floor(rotz(cP, -th) + np.array(at_p)).astype(int)
    hitP = int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())
    # hawse：船頭外表面（S 舷最外面那一格）
    hx, hz = AN['hawse']['x'], AN['hawse']['z']
    ys = np.nonzero(solid[hx, YC:, hz])[0]
    hy = int(YC + ys.max())
    hawse = {'hawse-S': [hx, hy, hz], 'hawse-P': [hx, 2 * YC - hy, hz]}
    for k, v in hawse.items():
        assert solid[v[0], v[1], v[2]], (k, '不是船殼的格')
    out = {'note': 'draft_anchors.py —— 現況 ＝ 組裝件 links=all（%d 格）＋ 模型外框 %d（錨自己的不算）；候選 %d' % (len(A), nbox, tried),
           'work': AN['work'], 'scale': s, 'pivot': AN['pivot'], 'meta': AN['meta'], 'rows': rows, 'points': pts,
           'pick': {'x': xr, 'ring_z': zr, 'angle': th, 'touch_cells': touch, 'far': far}, 'mirror_hits': hitP, 'hawse': hawse}
    with open(os.path.join(D, 'verify_anchors.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()

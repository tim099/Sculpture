# 階段十五：舵輪與羅經櫃 —— 舵輪兩件子作品（會轉的／不會轉的，0.02 m）＋羅經櫃引用夜隼號的 -binnacle，三個都當外部模型擺上後甲板（甲板-後）
# 設計 plan.json helm（出處 provenance helm）；現況 ＝ 引擎匯出的組裝件格子（<exports>/assembly.list.txt）＋ 組裝件 obj 的繩（<exports>/assembly.obj）。
# 從夜隼號 draft_helm.py（階段十五）改：沒有隼的疤（那是夜隼號的故事）；舵已經是外部模型（階段六）⇒ 這裡不碰舵；
#   多一個「斷了的把手」（broken_handle：第幾根輪幅的把手不做，鬼船的作者決定）；羅經櫃直接引用夜隼號那件（同是 0.02 m、scale 0.2）。
# 子作品座標（同憲法號 -wheel）：x 沿船長（輪軸，船頭 +x）、y 橫向、z 上，z 0 ＝ 甲板面上第一層；輪軸中心線 y CY、z axle_z（格心）。
# 擺法：x 在 x_search 裡每 step 試，y 中線；要求 模型的取樣點都不在實心格、底面每個取樣點正下方是實心（四角著地）、
#   模型外框（外擴 rope_clear）裡沒有任何一條繩的管子頂點（obj）；舵輪離 x_target 最近；羅經櫃在舵輪之前、跟舵輪外框隔 gap_min 以上。
# 輸出：masks/helm/{wheel,stand}.vox.txt、verify_helm.json
# 用法：python -I -X utf8 -B draft_helm.py <design 資料夾> <exports 資料夾（assembly.list.txt、assembly.obj）>
import sys, os, json, math, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
NX, NY, NZ = plan['frame']['NX'], plan['frame']['NY'], plan['frame']['NZ_work']
HP = plan['helm']
SX, SY, SZ = HP['size']
CY, AZ = HP['CY'], HP['axle_z']
COL = HP['colors']


class Part:
    def __init__(s, size):
        s.cells = {}; s.size = size

    def put(s, k, c, over=False):
        if not all(0 <= k[i] < s.size[i] for i in range(3)):
            raise ValueError(('框外', k))
        if k in s.cells and not over:
            return
        s.cells[k] = c


def rad(y, z):
    return math.hypot(y + 0.5 - CY, z + 0.5 - AZ)


def build_wheel():
    P = Part(HP['size'])
    rim, boss = HP['rim'], HP['boss']
    for x in range(boss['x'][0], boss['x'][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rad(y, z) <= boss['r']:
                    P.put((x, y, z), COL['boss'])
    for x in range(rim['x'][0], rim['x'][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rim['r_in'] <= rad(y, z) <= rim['r_out']:
                    P.put((x, y, z), COL['wheel'])
    xm = [(rim['x'][0] + rim['x'][1]) // 2, (rim['x'][0] + rim['x'][1]) // 2 + 1]
    broken = 0
    for k in range(HP['spokes']):
        th = math.pi / 2 + 2 * math.pi * k / HP['spokes']
        uy, uz = math.cos(th), math.sin(th)
        for y in range(SY):
            for z in range(SZ):
                dy, dz = y + 0.5 - CY, z + 0.5 - AZ             # 斷了一個把手 ⇒ 左右本來就不對稱，用帶號的 dy（夜隼號用 |dy| 是為了對稱）
                t = dy * uy + dz * uz
                d = abs(-dy * uz + dz * uy)
                if boss['r'] - 1 <= t <= rim['r_in'] + 0.5 and d <= HP['spoke_half']:
                    for x in xm:
                        P.put((x, y, z), COL['wheel'])
                elif rim['r_out'] - 0.5 <= t <= HP['handle_r'] and d <= HP['handle_half']:
                    if k == HP['broken_handle'] and t > rim['r_out'] + 1.5:   # 斷口：把手只剩貼著輪緣的一截
                        broken += 1
                        continue
                    for x in range(rim['x'][0], rim['x'][1] + 1):
                        if abs(x + 0.5 - (rim['x'][0] + rim['x'][1] + 1) / 2.0) <= HP['handle_half']:
                            P.put((x, y, z), COL['wheel'])
    for x in range(boss['x'][1] + 1, HP['stanchion']['x'][1][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rad(y, z) <= HP['axle_r']:
                    P.put((x, y, z), COL['iron'])
    dr = HP['drum']
    for x in range(dr['x'][0], dr['x'][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rad(y, z) <= dr['r']:
                    P.put((x, y, z), COL['iron'] if x in dr['x'] else COL['wheel'], over=True)
    AY, AZi = int(math.floor(CY)), int(math.floor(AZ))
    x0 = boss['x'][0]
    pts = {'axle': (x0, AY, AZi), 'hub-aft': (x0, AY, AZi),
           'drum-rope-a': ((dr['x'][0] + dr['x'][1]) // 2, AY, AZi + int(dr['r'])), 'drum-rope-b': ((dr['x'][0] + dr['x'][1]) // 2, AY, AZi - int(dr['r']))}
    return P, pts, broken


def build_stand():
    P = Part(HP['size'])
    st, b = HP['stanchion'], HP['base']
    for x in range(b['x'][0], b['x'][1] + 1):
        for y in range(SY):
            if abs(y + 0.5 - CY) <= b['half_y']:
                for z in range(b['z'][0], b['z'][1] + 1):
                    P.put((x, y, z), COL['base'])
    for xa, xb in st['x']:
        for x in range(xa, xb + 1):
            for y in range(SY):
                if abs(y + 0.5 - CY) > st['half_y']:
                    continue
                for z in range(b['z'][1] + 1, st['top'] + 1):
                    if rad(y, z) <= HP['axle_r']:
                        continue
                    P.put((x, y, z), COL['iron'] if z >= st['top'] - 1 else COL['stand'])
    pts = {'base': ((b['x'][0] + b['x'][1]) // 2, int(math.floor(CY)), 0)}
    return P, pts


def components(cells):
    S = set(cells); seen = set(); n = 0
    for c in S:
        if c in seen:
            continue
        n += 1; st = [c]; seen.add(c)
        while st:
            x, y, z = st.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
    return n


def write(P, name, title):
    path = os.path.join(D, 'masks', 'helm', name + '.vox.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = '# 風暴角號' + title + '（draft_helm.py，0.02 m）x,y,z,color —— at 0,0,0\n' + ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(P.cells.items()))
    open(path, 'w', encoding='utf-8', newline='\n').write(txt)
    return 'masks/helm/' + name + '.vox.txt', hashlib.sha256(txt.encode('utf-8')).hexdigest()


def main():
    PW, wpts, nbroken = build_wheel()
    PS, spts = build_stand()
    fw, hw = write(PW, 'wheel', '舵輪（會轉的：輪、輪幅、輪轂、輪軸、鼓輪；斷了一個把手）')
    fs, hs = write(PS, 'stand', '舵輪座（底座、兩根支柱）')
    print('wheel', len(PW.cells), 'stand', len(PS.cells), 'broken handle cells skipped', nbroken, 'comp', components(PW.cells), components(PS.cells))

    a = np.loadtxt(os.path.join(EX, 'assembly.list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
    occ = np.zeros((NX, NY, NZ), bool); occ[a[:, 0], a[:, 1], a[:, 2]] = True
    # 繩的管子頂點（obj：y 朝上 ⇒ (x, 作品 z, 作品 y) 換回）
    vs, isrope, cur = [], [], False
    for line in open(os.path.join(EX, 'assembly.obj'), encoding='utf-8'):
        if line.startswith('o '):
            cur = line[2:].startswith('rope_')
        elif line.startswith('v '):
            vs.append([float(t) for t in line.split()[1:4]])
            isrope.append(cur)
    vs = np.array(vs)[:, [0, 2, 1]]; RV = vs[np.array(isrope)]
    print('rope vertices', len(RV))

    S = HP['scale']
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
    samp = lambda cells: (np.array(sorted(cells), float)[:, None, :] + offs[None]).reshape(-1, 3)
    botf = lambda cells: np.array([[x + ox, y + oy, 0.0] for (x, y, z) in cells if z == 0 for ox in (0.25, 0.75) for oy in (0.25, 0.75)])

    def tryplace(cells, pivot, scale, xs_, step, y, extra_ok):
        sm, bt = samp(cells), botf(cells)
        out = []
        x = xs_[0]
        while x <= xs_[1] + 1e-9:
            xw = range(int(math.floor(x - 6)), int(math.ceil(x + 6)) + 1)
            # 甲板面候選：那一段後甲板的頂（引擎匯出的格，中線兩旁 ±3）
            tops = set()
            for xx in xw:
                for yy in range(int(y) - 3, int(y) + 4):
                    zs = np.nonzero(occ[xx, yy, 95:115])[0]
                    if len(zs):
                        tops.add(int(zs.max()) + 95)
            for t in sorted(tops):
                at = np.array([x, y, t + 1 + pivot[2] * scale])
                W_ = (sm - pivot) * scale + at
                i = np.floor(W_).astype(int)
                if occ[i[:, 0], i[:, 1], i[:, 2]].any():
                    continue
                b = np.floor((bt - pivot) * scale + at).astype(int)
                if occ[b[:, 0], b[:, 1], b[:, 2] - 1].sum() != len(b):
                    continue
                lo, hi = W_.min(0) - HP['rope_clear'], W_.max(0) + HP['rope_clear']
                nr = int(((RV >= lo) & (RV <= hi)).all(1).sum())
                if nr or not extra_ok(lo, hi):
                    continue
                out.append((x, at, t, [lo.round(2).tolist(), hi.round(2).tolist()]))
            x += step
        return out

    pl = HP['place']
    pivot_w = np.array([SX / 2.0, CY, AZ])
    allc = dict(PW.cells); allc.update(PS.cells)
    cw = tryplace(allc.keys(), pivot_w, S, pl['x_search'], pl['step'], pl['y'], lambda lo, hi: True)
    if not cw:
        raise SystemExit('後甲板上找不到四角著地、不撞、不碰繩的舵輪位置')
    xw_, at_w, t_w, box_w = min(cw, key=lambda c: abs(c[0] - pl['x_target']))
    print('wheel at', at_w.round(3).tolist(), 'deck_top', t_w, 'candidates', len(cw), 'x', min(c[0] for c in cw), '–', max(c[0] for c in cw))

    B = HP['binnacle']
    # 羅經櫃的格：讀夜隼號那件的 mask（它的產生程式輸出；子作品的格是照它貼的 —— 驗收時另外拿引擎匯出的子作品對）
    nf = os.path.join(D, '..', '..', 'summit-night-falcon-01m', 'design', 'masks', 'binnacle', 'binnacle.vox.txt')
    bcells = [tuple(map(int, l.split(',')[:3])) for l in open(nf, encoding='utf-8') if l.strip() and not l.startswith('#')]
    cb = tryplace(bcells, np.array(B['pivot'], float), B['scale'], B['x_search'], B['step'], pl['y'],
                  lambda lo, hi: lo[0] - box_w[1][0] >= B['gap_min'])
    if not cb:
        raise SystemExit('舵輪之前找不到羅經櫃的位置')
    xb_, at_b, t_b, box_b = min(cb, key=lambda c: abs(c[0] - B['x_target']))
    print('binnacle at', at_b.round(3).tolist(), 'deck_top', t_b, 'candidates', len(cb), 'gap to wheel box', round(box_b[0][0] - box_w[1][0], 2))

    out = {'note': 'draft_helm.py（階段十五）—— 現況 ＝ 引擎匯出 %s（%d 格）＋ 組裝件 obj 的繩（%d 個頂點）' % (os.path.relpath(EX, os.path.dirname(D)).replace('\\', '/'), len(a), len(RV)),
           'host_work': HP['host_work'], 'host_link': HP['host_link'],
           'wheel': {'work': HP['wheel_work'], 'title': HP['wheel_title'], 'file': fw, 'sha256': hw, 'cells': len(PW.cells), 'broken_handle_skipped': nbroken,
                     'anchors': {k: list(v) for k, v in wpts.items()}},
           'stand': {'work': HP['stand_work'], 'title': HP['stand_title'], 'file': fs, 'sha256': hs, 'cells': len(PS.cells), 'anchors': {k: list(v) for k, v in spts.items()}},
           'size': HP['size'], 'mpv': HP['mpv'],
           'models': [{'name': '舵輪', 'work': HP['wheel_work'], 'at': at_w.round(4).tolist(), 'pivot': pivot_w.tolist(), 'scale': S, 'meta': {'kind': 'wheel', 'turn_axis': 'x', 'pivot_anchor': 'axle'}, 'box': box_w},
                      {'name': '舵輪座', 'work': HP['stand_work'], 'at': at_w.round(4).tolist(), 'pivot': pivot_w.tolist(), 'scale': S, 'meta': {'kind': 'wheel_stand'}, 'box': box_w},
                      {'name': '羅經櫃', 'work': B['source_work'], 'at': at_b.round(4).tolist(), 'pivot': B['pivot'], 'scale': B['scale'], 'meta': {'kind': 'binnacle'}, 'box': box_b}],
           'deck_top': {'wheel': t_w, 'binnacle': t_b},
           'candidates': {'wheel': [c[0] for c in cw], 'binnacle': [c[0] for c in cb]}}
    with open(os.path.join(D, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()

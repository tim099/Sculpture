# 光榮號 砲門蓋板（TASK-0719；kaguya 自己寫的 —— 沒有可以抄的：莫尼特號艙蓋 meadow-monitor-01m-hatch 是一刀 stampvox、沒有產生程式）
#   Tim 2026-10-19：「另外我想加一個遊戲內功能 炮門(同時也在動畫內展示) 是否可以用光榮號展示 炮門可以開關(關閉時炮往內縮)」
#                   「然後炮門屬於裝飾物 因此相關機制在低畫質不啟用」
#   設計（kaguya 拍板 2026-10-19；造船規格 §9.12）：
#   · 通用部件（§2.2）：一件子作品 kaguya-gloire-01m-portlid（0.1 m，12 × 11 × 2 ＝ 開口 10 × 9 每邊大 1 格，照 §9.7；厚 2 ＝ 鐵甲帶的厚度、1 格開著從側面看像紙），
#     掛 34 次（砲甲板兩舷各 17）。艏樓那 2 門（gun-35／36）砲管從舷牆頂上過（砲口 z 150.25、舷牆頂 z 147）⇒ 不做蓋板。
#   · 畫「開著」（水平往外伸；x 沿船長、y 0 ＝ 鉸鏈那一邊、往 +y ＝ 往外、z 0 ＝ 下面那一層）；關上 ＝ 繞鉸鏈反轉 close_deg。
#     ⇐ 畫成關著（door 的慣例）的話 3–17 號每片都跟推出去的砲重疊 648–1,368 個取樣點（sculpt §4.3）；開著 0 ⇒ 低畫質（不載蓋板）、觀測頁都跟現在一樣。
#   · 顏色（外部模型不吃 material，§9.5 ⇒ 只是顏色）：z 1（開著朝上、關上朝外）黑 36 ＝ 鐵甲帶的色；z 0（關上貼船殼）橡木 141；兩條鉸鏈板 73 橫過外層。
#     史料沒寫光榮號的蓋板（references/gloire_research_2026-10-15.md:130）⇒ 設計決定：同時代 Warrior、RMG 1862 模型是鐵蓋、上緣外側鉸鏈 ⇒ 鐵外層。
#   · 固定點 hinge-a 0,0,0 → hinge-b 11,0,0（a→b ＝ +x；照 door 的右手定則：正轉 ＝ 再往上掀、反轉 ＝ 往下關）。
#   · 擺法：pivot 6,0,0（鉸鏈那條邊的正中間）、at ＝（開口 x0 ＋ 5, 鉸鏈 y, 開口 z1 ＋ 1）、scale 1。
#     S 舷 rotate 0,0,rz；P 舷 rotate 0,0,180 − rz、at.y ＝ 401 − 鉸鏈 y —— ⛔ 不用 mirror=y：鏡像不改 a→b 的方向 ⇒ P 舷會往船裡開、往上關。
#     鉸鏈 y ＝ 蓋板最上面那一排（開口 z1 ＋ 1）外表面最外那一格（第一格空氣）；
#     rz ＝ 外表面沿 x 的斜度（平面擬合；|rz| ≤ 2° 取 0 ⇒ 1–13 號共用一份網格）；close_deg ＝ 90 ＋ 外表面沿 z 的斜度（平面擬合；tumblehome ＜ 90、外張 ＞ 90）。
#   · meta：kind=portlid、lid_of=<砲的物件 id>（照 deck-lower 的 models.json 讀 —— ⛔ 不照位置猜，§12.1）、close_deg、house。
#     house ＝ 收砲時沿砲軸往船裡拉幾格（只是畫面）＝ max(ceil(至少縮), 4)：至少縮 ＝ 砲口退到外表面往裡 1 格要拉幾格（scratchpad gun_runin.py 的量法）；
#     最少 4 讓 1–3 號開火時也有後座；⛔ 不超過 6：砲班站位（Blockside 40_crew.js:71）有一個人站在砲外框後面 6 格，拉 8（sculpt 建議）砲尾就畫進他身上。
#   輸出：masks/portlids/lid.txt（子作品自己的座標，stampvox at 0,0,0）、portlids_placement.json（34 個擺法與量法讀數）。
#     碰撞讀數另外由 tools/check_portlids.py 在組裝件現況上量（開／關兩種姿勢跟船、跟縮回後的砲）。重跑逐位元組相同。
#   用法：python -I -X utf8 draft_portlids.py <design>
import sys, os, json, math, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout as LY

HULL = 'kaguya-gloire-01m'
SUB = HULL + '-portlid'
HOST = HULL + '-deck-lower'
GUN_WORK = 'basecamp-ember-01m-gun-long32'
SIZE = (12, 11, 2)                       # 開口 10 × 9 每邊大 1 格；厚 2
COL = {'outer': 36, 'inner': 141, 'strap': 73}
STRAPS_X = (2, 9)                        # 兩條鉸鏈板（左右對稱：11 − 2 ＝ 9）
STRAP_Y = 9                              # 鉸鏈板從鉸鏈往外 9 格（y 0–8；最外 2 格不包，看得出是鉸鏈板不是框）
PIVOT = [6, 0, 0]
ANCHORS = {'hinge-a': [0, 0, 0], 'hinge-b': [SIZE[0] - 1, 0, 0]}
RZ_FLAT = 2.0                            # |rz| ≤ 2° 取 0（共用一份網格；sculpt §3.2）
HOUSE_MIN, HOUSE_MAX = 4, 6
NX, NY, NZ = 1200, 400, 260
YC = 200


def load(p):
    A = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    A = A.reshape(-1, 4) if A.size else np.zeros((0, 4), np.int32)
    return A[A[:, 2] < NZ]


def lid_cells():
    """蓋板（開著）：{(x, y, z): 色}。z 0 橡木、z 1 黑；z 1 上兩條鉸鏈板。"""
    c = {}
    for x in range(SIZE[0]):
        for y in range(SIZE[1]):
            c[(x, y, 0)] = COL['inner']
            c[(x, y, 1)] = COL['strap'] if (x in STRAPS_X and y < STRAP_Y) else COL['outer']
    return c


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def r1(v, k=1):
    v = round(float(v), k)
    return int(v) if v == int(v) else v


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    works = os.path.dirname(os.path.dirname(design))
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))

    # ── 蓋板子作品的格子 ──
    cells = lid_cells()
    od = os.path.join(design, 'masks', 'portlids')
    os.makedirs(od, exist_ok=True)
    fn = os.path.join(od, 'lid.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 光榮號 砲門蓋板（draft_portlids.py；TASK-0719）x,y,z,color —— 子作品 %s 自己的座標（畫開著：水平往外伸），stampvox at 0,0,0\n' % SUB)
        for (x, y, z) in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    lid_sha = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    by_col = {}
    for v in cells.values():
        by_col[str(v)] = by_col.get(str(v), 0) + 1

    # ── 船殼外表面（masks/build ＝ 船殼＋鐵甲帶的最終狀態，砲門已刻穿；build_hull.py）──
    hull = np.zeros((NX, NY, NZ), bool)
    bd = os.path.join(design, 'masks', 'build')
    for f in sorted(os.listdir(bd)):
        if f.endswith('.vox.txt'):
            A = load(os.path.join(bd, f))
            hull[A[:, 0], A[:, 1], A[:, 2]] = True

    def face(x, z, side):
        """那一欄外表面外面第一格空氣（格號）：S ＝ 最外那格 ＋1、P ＝ 最外那格 −1。"""
        col = np.nonzero(hull[x, :, z])[0]
        col = col[col > YC] if side > 0 else col[col < YC]
        if len(col) == 0:
            return None
        return int(col.max() + 1) if side > 0 else int(col.min() - 1)

    # ── 砲（deck-lower 的 models.json：S 舷第 n 號 ＝ gun-(2n−1)、P 舷 ＝ gun-2n；照 meta 讀，不照位置猜）──
    gm = {}
    for m in json.load(open(os.path.join(works, HOST, 'models.json'), encoding='utf-8'))['models']:
        mt = m.get('meta') or {}
        if mt.get('kind') == 'gun' and mt.get('deck') == 'lower':
            gm[(mt['side'], int(mt['port']))] = m
    an = {a['name']: a['at'] for a in json.load(open(os.path.join(works, GUN_WORK, 'anchors.json'), encoding='utf-8'))['anchors']}

    def gun_point(m, nm):
        q = (np.array([an[nm]], float) + 0.5 - np.array(m['pivot'], float)) * np.array(m['scale'], float)
        if m['mirror'] == 'y':
            q[:, 1] = -q[:, 1]
        return (rotz(q, m['rotate'][2]) + np.array(m['at'], float))[0]

    def need_pull(m, side):
        """砲口退到外表面往裡 1 格要沿砲軸拉幾格（scratchpad gun_runin.py 的量法：砲口那一欄往下找船殼、取那一排的外表面）。"""
        mz, br = gun_point(m, 'muzzle'), gun_point(m, 'breech')
        ax = (mz - br) / np.linalg.norm(mz - br)
        xi, zi = int(math.floor(mz[0])), int(math.floor(mz[2]))
        col = np.zeros(0, int)
        for zz in range(zi, zi - 12, -1):
            for dx in (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7):
                c = np.nonzero(hull[xi + dx, :, zz])[0]
                c = c[c > YC] if side > 0 else c[c < YC]
                if len(c):
                    col = c
                    break
            if len(col):
                break
        outer = (col.max() + 1) if side > 0 else col.min()           # 外表面（格的角落座標）
        need = (mz[1] - (outer - 1)) * side / abs(ax[1]) if side > 0 else (mz[1] - (outer + 1)) * side / abs(ax[1])
        return mz, ax, int(outer), float(need)

    rows, sym = [], []
    for p in LY.ports(plan):
        if p['deck'] != 'lower':
            continue
        n = p['i']
        x0, x1, z0, z1 = p['x0'] - 1, p['x1'] + 1, p['z0'] - 1, p['z1'] + 1      # 蓋板關上蓋住的範圍（含端點）
        fit = {}
        for side, nm in ((1, 'S'), (-1, 'P')):
            fc = {}
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    v = face(x, z, side)
                    if v is not None:
                        fc[(x, z)] = v if side > 0 else 400 - v                # 都換成 S 舷的寫法（往外 ＝ +y）
            # 開口裡刻穿了（整層牆厚）⇒ 只剩開口外那一圈（蓋板比開口每邊大的那 1 格：2 × 12 ＋ 2 × 9 ＝ 42 欄）有外表面 —— 擬合就照這一圈（同 lid_fit.py）
            assert len(fc) == 2 * (x1 - x0 + 1) + 2 * (z1 - z0 - 1), (nm, n, '蓋板那一圈有一欄沒有船殼、或開口裡還有格', len(fc))
            top = [fc[(x, z1)] for x in range(x0, x1 + 1)]
            pts = np.array([[x, z, y] for (x, z), y in sorted(fc.items())], float)
            xc, zc = pts[:, 0].mean(), pts[:, 1].mean()
            Am = np.c_[np.ones(len(pts)), pts[:, 0] - xc, pts[:, 1] - zc]
            coef, *_ = np.linalg.lstsq(Am, pts[:, 2], rcond=None)
            fit[nm] = {'hinge_y': int(max(top)), 'top_ends': [int(top[0]), int(top[-1])], 'face_y': [int(pts[:, 2].min()), int(pts[:, 2].max())],
                       'rx': round(math.degrees(math.atan(coef[2])), 1), 'rz': round(math.degrees(math.atan(coef[1])), 1),
                       'resid': round(float(np.abs(Am @ coef - pts[:, 2]).max()), 2)}
        if fit['S'] != fit['P']:
            sym.append(n)                                                       # 兩舷外表面不對稱 ⇒ 下面照各舷自己的值，讀數列出來
        for side, nm in ((1, 'S'), (-1, 'P')):
            F = fit[nm]
            rz = 0 if abs(F['rz']) <= RZ_FLAT else r1(F['rz'])
            close = r1(90 + F['rx'])
            g = gm[(nm, n)]
            gid = g['meta']['id']
            assert gid == 'gun-%d' % (2 * n - 1 if side > 0 else 2 * n), (nm, n, gid)
            mz, ax, outer, need = need_pull(g, side)
            need_c = max(0.0, round(need, 2))
            house = max(int(math.ceil(need_c)), HOUSE_MIN)
            assert house <= HOUSE_MAX, (nm, n, '收砲要拉超過 6 格 ⇒ 砲尾會畫進砲班的人', need)
            hy = F['hinge_y'] if side > 0 else 400 - F['hinge_y']            # 鉸鏈那一排的格號（P 舷照實的格號）
            at = [p['x0'] + 5, hy if side > 0 else hy + 1, p['z1'] + 1]        # P 舷轉 180°：模型 y 0 那一排落在 [at.y − 1, at.y)
            rot = rz if side > 0 else r1(180 - rz)
            meta = {'kind': 'portlid', 'lid_of': gid, 'close_deg': close, 'house': house}
            rows.append({'model': '砲門蓋-%s%02d' % (nm, n), 'gun_model': g['name'], 'host_work': HOST, 'source_work': SUB, 'side': nm, 'port': n,
                         'at': at, 'pivot': PIVOT, 'rotate': [0, 0, rot], 'scale': 1, 'mirror': 'none', 'meta': meta,
                         'open_x': [p['x0'], p['x1']], 'open_z': [p['z0'], p['z1']], 'lid_x': [x0, x1], 'lid_z': [z0, z1],
                         'face': dict(F, rz_used=rz, close_deg=close), 'hinge_cell_y': hy,
                         'gun': {'id': gid, 'muzzle': [round(float(v), 2) for v in mz], 'axis': [round(float(v), 3) for v in ax], 'outer_face_y': outer,
                                 'need_pull': need_c, 'house': house}})
    rows.sort(key=lambda r: (r['port'], r['side'] != 'S'))
    meshes = sorted({(r['side'], r['rotate'][2]) for r in rows})
    out = {'note': 'draft_portlids.py（TASK-0719）—— 光榮號砲甲板砲門蓋板：一件子作品 %s 掛 %d 次（兩舷各 17；艏樓 gun-35／36 不做）。'
                   '外表面照 masks/build（船殼＋鐵甲帶最終狀態）；砲照 %s models.json。碰撞讀數在 verify_portlids.json（tools/check_portlids.py）' % (SUB, len(rows), HOST),
           'lid': {'work': SUB, 'title': '砲門蓋板（上緣鉸鏈，通用部件，0.1 m）', 'parent_work': HULL, 'tags': 'sub', 'meters_per_voxel': 0.1,
                   'size': list(SIZE), 'file': 'masks/portlids/lid.txt', 'cells': len(cells), 'sha256': lid_sha, 'colors': dict(sorted(by_col.items())),
                   'anchors': ANCHORS, 'pivot': PIVOT, 'straps_x': list(STRAPS_X), 'strap_y': [0, STRAP_Y - 1]},
           'rules': {'rz_flat_deg': RZ_FLAT, 'house_min': HOUSE_MIN, 'house_max': HOUSE_MAX,
                     'S': 'rotate 0,0,rz；at ＝ (x0 + 5, 鉸鏈 y, z1 + 1)', 'P': 'rotate 0,0,180 − rz；at.y ＝ 401 − 鉸鏈 y（⛔ mirror=y）'},
           'rows': rows, 'count': len(rows), 'meshes': [{'side': s, 'rz': r, 'n': sum(1 for x in rows if x['side'] == s and x['rotate'][2] == r)} for s, r in meshes],
           'asymmetric_ports': sym}
    with open(os.path.join(design, 'portlids_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('蓋板 %d 格 %s sha256 %s…；擺法 %d 片（網格 %d 份）；兩舷外表面不對稱的砲門 %s' % (len(cells), out['lid']['colors'], lid_sha[:12], len(rows), len(meshes), sym))
    for r in rows:
        if r['side'] == 'S':
            print('  %s %s at %s rot %s close %s house %s（至少縮 %s）' % (r['model'], r['meta']['lid_of'], r['at'], r['rotate'][2], r['meta']['close_deg'], r['meta']['house'], r['gun']['need_pull']))


if __name__ == '__main__':
    main()

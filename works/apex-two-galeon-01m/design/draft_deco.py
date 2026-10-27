# 直接出處：gura-pinas-01m/design/draft_deco.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/draft_deco.py（收穫號）的框架 —— 部件換成荷蘭 pinas 的（TASK-0969 步驟 6）
# 康塞普西翁號 步驟 6：船首喙（espolón＋cutwater＋head rail）、船首像（鍍金獅子）、船尾走廊＋兩舷側廊、船尾拱形板（無原罪聖母＋CONCEPCION 名帶）、三盞船尾燈
#   ⚠ 康塞普西翁號改：部件 galjoen → espolon、FONT 補 C／O／N／P、圖案多一個膚色 S、圖的範圍、船尾面的 x 門檻（210 → 220）
#   輸入：plan.json（espolon、figurehead、stern_deco）＋ 組裝件現在的格子（CLI 匯出 ⇒ 船殼＋甲板＋梯子＋玻璃，佔用與貼面都照它算）
#   輸出：masks/deco/<部件>.vox.txt（世界座標、at 0,0,0）、verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=shift=<部件>:<dy>]（反向對照：某一件整件往 y 推幾格，⛔ 不寫檔）
#   · galjoen、獅子、船尾走廊、側廊兩舷一起產（照 |dy| 算 ⇒ 對稱）；hackebort 的鯊魚與字不對稱（照實報鏡像差）。
#   · 側廊的窗是畫上去的（87，後面是側廊的實心）—— 只有鏡板的窗是真的玻璃（-stern-glass，material=glass）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

BLACK, GOLD, GLASS, WOOD, TRIM, DECK, BLUE = 36, 248, 87, 141, 136, 209, 6
PARTS = ('espolon', 'figurehead', 'stern-deco', 'hackebort')
EXCLUDE = PARTS + ('ornament',)          # 步驟 16 的裝飾（draft_ornament.py）是疊在本步驟上面的 ⇒ 重產本步驟時也扣掉（才會逐位元組相同）

FONT = {  # 3×5，列由上往下
    'B': ['XX.', 'X.X', 'XX.', 'X.X', 'XX.'], 'L': ['X..', 'X..', 'X..', 'X..', 'XXX'], 'A': ['.X.', 'X.X', 'XXX', 'X.X', 'X.X'],
    'U': ['X.X', 'X.X', 'X.X', 'X.X', 'XXX'], 'W': ['X.X', 'X.X', 'XXX', 'XXX', 'X.X'], 'E': ['XXX', 'X..', 'XX.', 'X..', 'XXX'],
    'H': ['X.X', 'X.X', 'XXX', 'X.X', 'X.X'], 'I': ['XXX', '.X.', '.X.', '.X.', 'XXX'], ' ': ['.', '.', '.', '.', '.'],
    'C': ['XXX', 'X..', 'X..', 'X..', 'XXX'], 'O': ['XXX', 'X.X', 'X.X', 'X.X', 'XXX'], 'N': ['X.X', 'XXX', 'XXX', 'X.X', 'X.X'], 'P': ['XX.', 'X.X', 'XX.', 'X..', 'X..'],
}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    occ_arg = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--occ=')), None)
    if occ_arg:       # 步驟 17：設計還沒落格時拿本機清單當「船」（--occ=<清單;清單…>：船殼帳＋甲板＋梯子…）；⛔ 正式產清單一律從組裝件讀
        A = np.concatenate([np.loadtxt(p_, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :4] for p_ in occ_arg.split(';')])
    else:
        A = export_list('apex-two-galeon-01m-assembly', None, links=None)
    # 船 ＝ 組裝件扣掉本步驟自己的件（已經落過一次的話；收穫號 v1 沒扣 ⇒ 重產時把舊裝飾當成船）
    own = set()
    for nm in (() if occ_arg else EXCLUDE):
        if os.path.exists(os.path.join(WORKS, 'apex-two-galeon-01m-' + nm, 'work.json')):
            own |= set(map(tuple, export_list('apex-two-galeon-01m-' + nm, None)[:, :3].tolist()))
    if own:
        A = A[np.array([tuple(r) not in own for r in A[:, :3].tolist()], bool)]
    # 側廊 v2 自己改過的格放回去再量（重跑逐位元組相同）：船殼刻掉的窗洞照原色補回、側廊的玻璃拿掉
    gc_path = os.path.join(design, 'masks', 'deco', 'gallery_carve.vox.txt')
    gg_path = os.path.join(design, 'masks', 'glass', 'gallery_glass.vox.txt')
    sg_path = os.path.join(design, 'masks', 'glass', 'stern_glass.vox.txt')
    for gp in (gg_path, sg_path):       # 康塞普西翁號：鏡板窗的玻璃也扣掉（玻璃子作品落了之後重跑，圖紙才會逐位元組相同）
        if os.path.exists(gp):
            gg = set(map(tuple, np.loadtxt(gp, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist()))
            A = A[np.array([tuple(r) not in gg for r in A[:, :3].tolist()], bool)]
    Hl = np.loadtxt(occ_arg.split(';')[0], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :4] if occ_arg else export_list('apex-two-galeon-01m', None)
    if os.path.exists(gc_path) and not occ_arg:
        G0 = np.loadtxt(gc_path, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
        have = set(map(tuple, A[:, :3].tolist()))
        add = np.array([r for r in G0.tolist() if tuple(r[:3]) not in have], dtype=A.dtype).reshape(-1, A.shape[1])
        A = np.concatenate([A, add[:, :A.shape[1]]]) if len(add) else A
        hs = set(map(tuple, Hl[:, :3].tolist()))
        addh = np.array([r for r in G0.tolist() if tuple(r[:3]) not in hs], dtype=Hl.dtype).reshape(-1, Hl.shape[1])
        Hl = np.concatenate([Hl, addh[:, :Hl.shape[1]]]) if len(addh) else Hl
    hull_col = {tuple(r[:3]): int(r[3]) for r in Hl.tolist()}
    hull_cells = set(hull_col)
    GLASS_REAL = int(open(os.path.join(design, 'masks', 'glass', 'stern_glass.vox.txt'), encoding='utf-8').read().splitlines()[1].split(',')[3])   # 跟鏡板的玻璃同一色
    occ = set(map(tuple, A[:, :3].tolist()))
    aft, outer, fwd = {}, {}, {}
    for x, y, z in A[:, :3].tolist():
        if x < 220:
            if x < aft.get((y, z), 10 ** 6):
                aft[(y, z)] = x
        dy = abs(y - YC)
        if dy > outer.get((x, z), -1):
            outer[(x, z)] = dy
        if x >= 400 and y == YC and x > fwd.get(z, -1):
            fwd[z] = x
    parts = {}

    def put(part, x, y, z, c):
        parts.setdefault(part, {})[(int(x), int(y), int(z))] = c

    def both(part, x, dy, z, c):
        put(part, x, YC + dy, z, c)
        put(part, x, YC - dy, z, c)

    # ── espolón（船首喙）：甲板＋head rail＋cutwater ──
    E = plan['espolon']
    F = plan['figurehead']
    xs0 = int(math.floor(float(L.x_stem(80)) + 0.5)) - 1           # 艏柱前緣那一格（z 73.6 以上直立）
    tip = xs0 + E['len_beyond_stem']
    zt, th = E['deck_top_z'], E['thick']
    wpar = lambda x: E['half_at_tip'] + (E['half_at_stem'] - E['half_at_tip']) * (1 - (x - xs0) / float(E['len_beyond_stem'])) ** E['taper_pow']
    x_d0 = E.get('deck_from_x', xs0 + 1)                               # 步驟 17：從 beakhead 艙壁前面起鋪 ⇒ 跟船殼的平台連成一整片（船殼佔的格照樣跳過）

    def wdeck(x):
        if x <= xs0:                                                     # 艙壁到艏柱：從艙壁的半寬收到喙根的半寬
            return E['half_at_stem'] + (E.get('half_at_deck_from', E['half_at_stem']) - E['half_at_stem']) * (xs0 - x) / float(max(1, xs0 - x_d0))
        return wpar(x)
    zsk = E.get('skirt_from_z')
    for x in range(x_d0, tip + 1):
        w = int(math.floor(wdeck(x) + 0.5))
        for dy in range(0, w + 1):
            for z in range(zt - th + 1, zt + 1):
                both('espolon', x, dy, z, DECK if z == zt else TRIM)
        if zsk is not None:                                              # 側板：甲板邊往下包到 skirt_from_z（Tim「讓船頭變成一整個平台」—— 側面看是一整塊；底下不封 ⇒ 沒有封閉空腔），最前面那一欄整片封
            wn = int(math.floor(wdeck(x + 1) + 0.5)) if x < tip else 0
            for z in range(zsk, zt - th + 1):
                for dy in range(min(wn, w), w + 1):
                    both('espolon', x, dy, z, GOLD if z in (zsk, zt - th) else TRIM)
        for z in range(zt + 1, zt + 1 + E['rail_h']):
            cap = z == zt + E['rail_h']
            if x > F['x'] - 6:
                continue                                              # head rail 停在獅子後面（收穫號 v1 跟船首像重疊）
            if cap or (x - xs0) % E['stanchion_every'] == 0:
                both('espolon', x, w, z, GOLD if cap else WOOD)
            if cap:                                                   # 寬度往前收的地方補台階 ⇒ 頂條面相接（收穫號 v1 只在斜角相接）
                w2 = int(math.floor(wpar(x + 1) + 0.5))
                for dy in range(w2, w):
                    both('espolon', x, dy, z, GOLD)
    z_cw0 = E['cutwater_from_z']
    cw_top = E.get('cutwater_to_z', zt - th + 1)                         # 步驟 17：knee 頂到平台底（skirt_from_z）、前緣在 cutwater_tip_x 接上 ⇒ 平台前段懸空伸出去（Tim 圈的那條線）
    cw_tip = E.get('cutwater_tip_x', tip)
    for z in range(z_cw0, cw_top):
        u = (z - z_cw0) / float(cw_top - z_cw0)
        xa = fwd.get(z, xs0) + 1
        xf = int(math.floor(xa + (cw_tip - xa) * u ** E['cutwater_pow'] + 0.5))
        for x in range(max(xa, xf - E['cutwater_band']), max(xa, xf) + 1):
            for dy in range(0, E['cutwater_half'] + 1):
                if dy == E['cutwater_half'] and z >= E.get('trail_from_z', 999) and xf - x in E.get('trail_off', ()):
                    c = GOLD                                           # 步驟 17：knee 兩側的金線（trailboard），沿前緣往裡 trail_off 格
                elif z < plan['hull_build']['bottom_top_z']:
                    c = plan['hull_build']['bottom_color']            # 步驟 17：水線以下跟船底同色（knee 填成一整片之後露出來）
                else:
                    c = GOLD if xf - x == 2 and dy == E['cutwater_half'] else TRIM
                both('espolon', x, dy, z, c)
    # ── 船首像：紅獅子（W p.85：長 9 呎、厚 19 duim、前端翹起 2'7"）——趴在喙尖上、往前往上翹 ──
    xr, ln, ht, rs = F['x'], F['len'], F['half_t'], F['raise']
    xf_ = xr + ln
    zc = lambda x: zt + 4 + rs * (x - xr) / float(ln)               # 身體中線的高度
    body, mane, crown, eye = F['body'], F['mane'], F['crown'], F['eye']
    for x in range(xr + 2, xf_ - 4):                                   # 身體（橢圓截面：半厚 ht、半高 3.2）
        for z in range(int(zc(x) - 4), int(zc(x) + 5)):
            for dy in range(0, int(ht) + 1):
                if (dy / ht) ** 2 + ((z + 0.5 - zc(x)) / 3.2) ** 2 <= 1.0:
                    both('figurehead', x, dy, z, body)
    hx, hz = xf_ - 3, zc(xf_) + 3                                       # 頭
    mx, mz = xf_ - 6, zc(xf_) + 2                                       # 鬃
    for x in range(xf_ - 11, xf_ + 1):
        for z in range(int(mz - 5), int(hz + 5)):
            for dy in range(0, 4):
                in_head = ((x + 0.5 - hx) / 3.2) ** 2 + (dy / ht) ** 2 + ((z + 0.5 - hz) / 3.2) ** 2 <= 1.0
                in_mane = ((x + 0.5 - mx) / 3.6) ** 2 + (dy / 3.0) ** 2 + ((z + 0.5 - mz) / 4.6) ** 2 <= 1.0
                if in_head:
                    both('figurehead', x, dy, z, body)
                elif in_mane:
                    both('figurehead', x, dy, z, mane)
    ztop = int(hz + 3.2)                                                # 金冠：頭頂一圈、上面一排尖
    for x in range(int(hx) - 2, int(hx) + 3):
        for dy in range(0, 3):
            both('figurehead', x, dy, ztop, crown)
            if (x + dy) % 2 == 0:
                both('figurehead', x, dy, ztop + 1, crown)
    both('figurehead', int(hx) + 2, 1, int(hz) + 1, eye)               # 眼睛
    for x0_, x1_ in ((xr + 3, xr + 6), (xf_ - 9, xf_ - 6)):           # 後腳、前腳：從喙的甲板面往上接到身體
        for x in range(x0_, x1_ + 1):
            for dy in (1, 2):
                for z in range(zt + 1, int(zc(x)) + 1):
                    both('figurehead', x, dy, z, body)
    for k, z in enumerate(range(int(zc(xr)), int(zc(xr)) + 7)):        # 尾巴：從屁股往後上翹，尾端一撮金
        put('figurehead', xr + 2 - k // 3, YC, z, mane if k >= 5 else body)
        if k and k % 3 == 0:                                            # 往後挪一格的那一階補一格 ⇒ 面相接（v1 只在斜角相接 ⇒ 尾端 1 格浮空）
            put('figurehead', xr + 3 - k // 3, YC, z, mane if k >= 5 else body)
    # ── 步驟 17：兩層 stern walk（San Felipe／OcCre 模型：開放的走廊從船尾繞過兩角、沿兩舷往前到 x_end；欄杆、金扶手、底下一排金托架）──
    #   取代步驟 6 的船尾走廊＋兩舷側廊（側廊的窗改成船殼上的窗：plan.stern.side_windows，在 draft_ports.py）
    S = plan['stern_deco']
    from scipy import ndimage
    occ_np = A[:, :3]
    gal_glass, gal_carve, gal_block = {}, {}, []
    walk_info = []
    for T in S['walks']:
        f, dep, rh = T['floor_z'], T['dep'], T['rail_h']
        xl, xh = T['x_from'], T['x_end']
        yl, yh = YC - 80, YC + 80
        ox = xl - dep
        X_ = np.arange(xh - xl + 1 + 2 * dep)[:, None] + ox
        Y_ = np.arange(yh - yl + 1)[None, :] + yl

        def env(zq):                                                     # 那一層的船殼外形：照線形（窗、門刻出來的凹口不算外面；v1 照格子 ⇒ 托架落進窗洞裡浮空）
            hb_ = L.hb(np.broadcast_to(X_ + 0.5, (X_.shape[0], Y_.shape[1])), np.full((X_.shape[0], Y_.shape[1]), zq + 0.5))
            return (np.abs(Y_ - YC) <= hb_) & (zq <= L.top_z(X_ + 0.5) + 0.5)
        E = env(f)
        dist, (ix, iy) = ndimage.distance_transform_edt(~E, return_indices=True)
        W_ = (~E) & (dist <= dep) & (X_ <= xh)
        ring = W_ & (dist > dep - 1.5)                                   # 外緣 1.5 格 ⇒ 斜的地方兩格相接（6 連通；v1 dep − 1 只有斜角相接 ⇒ 扶手斷成單格）
        Ez = {}                                                          # 地板以下每一層的船（填滿內部）：托架往裡接到那一層的船殼
        for k in range(1, T['bracket_len'] + 2):
            Ez[f - k] = env(f - k)
        ring |= W_ & (X_ == xh)                                          # 走廊的前端封一片欄杆
        hx, hy = ix + ox, np.abs(iy + yl - YC)
        per = hy + (hx - int(np.floor(float(L.x_aft(f + 0.5)))))         # 沿走廊的位置（船尾面 ≈ |dy|、兩舷 ≈ 往前的 x）⇒ 托架每 every 一組
        brk = (np.mod(per + T.get('bracket_off', 0), T['bracket_every']) < 2) & W_      # bracket_off：整組錯開（步驟 17：上層走廊正中間那組會撞到下層的門頂）
        pe = T.get('post_every')
        if pe:                                                           # 步驟 19（Tim「船尾的陽台是否可以改成欄杆(目前一整片會遮住窗戶視野)」）：欄杆柱只在最外那一層、沿走廊每 pe 格一根；v1 外緣 2 層各隔一格一根 ⇒ 前後錯開、看過去一整片
            ay = np.abs(Y_ - YC)
            face = ((hx - X_) > (ay - hy)) | (X_ == xh)                  # 船尾面（在最近那格船殼的後面）與前端那一片照 |dy| 排、兩舷（在外側）照 x 排 ⇒ 間距均勻（per 在斜的舷邊上會三根擠一起、再空十幾格）
            post = ring & ((dist > dep - 1) | (X_ == xh)) & (np.mod(np.where(face, ay, X_), pe) == 0)
            op_ = os.path.join(design, 'masks', 'deco', 'ornament.vox.txt')     # 鏡板的金壁柱（步驟 16 ornament，疊在本步驟上面）站在欄杆這一圈裡 ⇒ 那一格柱子讓開（壁柱本身就是一根金柱；不讓 ⇒ link_overlap 10）
            orn = set(map(tuple, np.loadtxt(op_, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist())) if os.path.exists(op_) else set()
        else:
            post, orn = ring & (np.mod(X_ + Y_, 2) == 0), set()
        n0 = 0
        for xi, yi in np.argwhere(W_):
            x, y = int(X_[xi, 0]), int(Y_[0, yi])
            dy = y - YC
            if dy < 0:
                continue                                                 # 只算右舷 ⇒ both() 鏡到左舷
            both('stern-deco', x, dy, f, GOLD if ring[xi, yi] else WOOD)
            if not Ez[f - 1][xi, yi]:
                both('stern-deco', x, dy, f - 1, GOLD if ring[xi, yi] else WOOD)    # 地板 2 格厚：外緣下面那一條金（腰線）；v1 只有外緣 ⇒ 船殼往外鼓的那段被圍成封閉空腔
            if ring[xi, yi]:
                for z in range(f + 1, f + rh + 1):
                    if z == f + rh:
                        both('stern-deco', x, dy, z, GOLD)               # 扶手
                    elif z == f + 1:
                        both('stern-deco', x, dy, z, TRIM)               # 底欄
                    elif post[xi, yi] and (x, y, z) not in orn and (x, 2 * YC - y, z) not in orn:
                        both('stern-deco', x, dy, z, BLUE)               # 欄杆柱
            if brk[xi, yi]:                                              # 托架：從地板底下往下收成 0（外面那一格金）；裡面接到那一層的船殼
                for k in range(1, T['bracket_len'] + 1):
                    reach = dep * (1 - k / float(T['bracket_len'] + 1)) ** 1.2
                    if dist[xi, yi] <= reach and not Ez[f - 1 - k][xi, yi]:
                        both('stern-deco', x, dy, f - 1 - k, GOLD if dist[xi, yi] > reach - 1.2 else WOOD)
            n0 += 1
        walk_info.append({'floor_z': f, 'footprint_S': n0})
    # ── hackebort：鏡板頂上那塊板（順著鏡板往後倒、頂上拱形）；奶油底、藍帶金字、藍鯊紋章 ──
    H = S['hackebort']
    z0, z1, half, af, htop = H['z0'], H['z1'], H['half'], H['arch_from'], H['half_top']
    rake = math.tan(math.radians(plan['lines']['sternpost_rake_deg']['v']))
    zb = z0 - 1                                                         # 坐在船殼頂那一層上
    halfz = lambda z: half if z < af else htop + (half - htop) * math.sqrt(max(0.0, 1 - ((z - af + 0.5) / float(z1 - af + 1)) ** 2))
    base = {}
    for dy in range(-half, half + 1):                                   # 每一欄的船尾位置照船殼頂那一層；船殼頂比板窄的那幾欄照最近的一欄
        b = aft.get((YC + dy, zb))
        if b is None:
            for k in range(1, 6):
                b = aft.get((YC + (dy - k if dy > 0 else dy + k), zb))
                if b is not None:
                    break
        base[dy] = b
    face = {}
    for z in range(z0, z1 + 1):
        hw = halfz(z)
        for dy in range(-half, half + 1):
            if abs(dy) > hw + 1e-9 or base[dy] is None:
                continue
            xf0 = base[dy] - int((z - zb) * rake + 0.5)
            edge = abs(dy) + 1 > hw or z in (z0, z1) or abs(dy) + 1 > halfz(z + 1)
            for t in range(H['thick']):
                put('hackebort', xf0 + t, YC + dy, z, H['border'] if edge else H['field'])
            face[(dy, z)] = xf0
    R_ = H['ribbon']
    for (dy, z), xf0 in face.items():                                   # 名帶（只換最外那一層）
        if R_['z0'] < z < R_['z1'] and abs(dy) < half - 1:
            put('hackebort', xf0, YC + dy, z, R_['color'])
    text = R_['text']
    wtxt = sum(len(FONT[ch][0]) for ch in text) + (len(text) - 1)
    ycur = -(wtxt // 2)
    for ch in text:                                                     # 從船尾看左手 ＝ −y ⇒ 第一個字在 y 最小那邊
        g = FONT[ch]
        for c in range(len(g[0])):
            for r in range(5):
                if g[r][c] == 'X':
                    z = R_['z1'] - 1 - r
                    put('hackebort', face[(ycur + c, z)], YC + ycur + c, z, R_['text_color'])
        ycur += len(g[0]) + 1
    SH = H['shark']                                                     # 藍鯊：頭朝左（−y）
    wsh = len(SH['rows'][0])
    for r, row in enumerate(SH['rows']):
        z = SH['z_top'] - r
        for c, ch in enumerate(row):
            if ch in SH:
                dy = c - wsh // 2
                put('hackebort', face[(dy, z)], YC + dy, z, SH[ch])
    # 步驟 17 v2：喙的側板貼著船殼的那幾格會跟船殼圍出 1 格的縫（封閉空腔）⇒ 喙的範圍外擴 3 格的框裡，船＋所有部件填滿內部、多出來的空格補進喙（木色）
    if plan['espolon'].get('skirt_from_z') is not None and parts.get('espolon'):     # （E 在 stern walk 那一段被拿去當外形了 ⇒ 直接讀 plan）
        from scipy import ndimage
        ek = np.array(list(parts['espolon'].keys()))
        lo_, hi_ = ek.min(axis=0) - 3, ek.max(axis=0) + 4
        G = np.zeros(tuple(hi_ - lo_), bool)
        for src in (occ, *[set(c) for c in parts.values()]):
            for (x, y, z) in src:
                if lo_[0] <= x < hi_[0] and lo_[1] <= y < hi_[1] and lo_[2] <= z < hi_[2]:
                    G[x - lo_[0], y - lo_[1], z - lo_[2]] = True
        holes = ndimage.binary_fill_holes(G) & ~G
        for xi, yi, zi in np.argwhere(holes):
            put('espolon', xi + lo_[0], yi + lo_[1], zi + lo_[2], TRIM)
        espolon_filled = int(holes.sum())
    else:
        espolon_filled = 0
    # 裝飾不蓋船的格：落在佔用格上的照實數出來、不放
    skipped = {}
    for nm in list(parts):
        bad = [k for k in parts[nm] if k in occ]
        skipped[nm] = len(bad)
        for k in bad:
            del parts[nm][k]
    if probe:
        nm, dv = probe[0].split('=')[1].split(':')
        parts[nm] = {(x, y + int(dv), z): c for (x, y, z), c in parts[nm].items()}

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_on_ship': skipped, 'espolon_cavity_filled': espolon_filled}
    allk = {}
    for nm, cells in parts.items():
        ks = set(cells)
        ov = len(ks & occ)
        touch = sum(1 for (x, y, z) in ks if any(n in occ for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1))))
        mir = sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * YC - y, z)) != c)
        cross = sum(1 for k in ks if k in allk)
        for k in ks:
            allk[k] = nm
        bb = np.array(list(ks))
        R['parts'][nm] = {'cells': len(ks), 'overlap_ship': ov, 'overlap_other_parts': cross, 'cells_touching_ship': touch, 'mirror_diff': mir,
                          'bbox': [bb.min(axis=0).tolist(), bb.max(axis=0).tolist()],
                          'colors': {int(c): int(n) for c, n in zip(*np.unique(np.array(list(cells.values())), return_counts=True))}}
    B = LY.bowsprit(plan)                                               # 艏斜桅那一條線（半徑 3）有沒有被喙、獅子擋到
    a = math.radians(B['angle'])
    hit = 0
    for (x, y, z) in allk:
        t = (x + 0.5 - B['x0']) * math.cos(a) + (z + 0.5 - B['z0']) * math.sin(a)
        if 0 <= t <= B['len']:
            px, pz = B['x0'] + t * math.cos(a), B['z0'] + t * math.sin(a)
            if (x + 0.5 - px) ** 2 + (y - YC) ** 2 + (z + 0.5 - pz) ** 2 <= 3.0 ** 2:
                hit += 1
    R['bowsprit_clearance_hits'] = hit
    LA = S['lanterns']
    R['lanterns'] = []
    for dy in LA['dy']:
        xl = face[(dy, z1)]
        R['lanterns'].append({'dy': dy, 'at': [xl + 1.0, YC + dy + 0.5, z1 + 1], 'on_solid': (xl, YC + dy, z1) in allk,
                              'air_above': (xl, YC + dy, z1 + 1) not in occ and (xl, YC + dy, z1 + 1) not in allk})
    if probe:
        print(json.dumps({'probe': probe[0], 'parts': {k: {kk: v[kk] for kk in ('overlap_ship', 'mirror_diff', 'cells_touching_ship')} for k, v in R['parts'].items()}}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    R['lists'] = {}
    for nm, cells in parts.items():
        p = os.path.join(od, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 康塞普西翁號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % nm)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
        R['lists'][nm] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    # 側廊 v2：玻璃與船殼要刻的窗洞
    os.makedirs(os.path.dirname(gg_path), exist_ok=True)
    for path, cells, head in ((gg_path, gal_glass, '# 康塞普西翁號 側廊窗玻璃（draft_deco.py 側廊 v2；1 格厚、後面一路空到艙裡；併進 -stern-glass 子作品）'),
                              (gc_path, gal_carve, '# 康塞普西翁號 側廊窗洞：船殼的牆要刻的格（carvevox；第 4 欄 ＝ 刻之前的顏色，守門；tools/hull_expected.py 的一步）')):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + '\n')
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k + (cells[k],)))
        R['lists'][os.path.basename(path)] = [len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    allparts = set(allk)
    left = {k for k in occ if k not in gal_carve}
    deep = {}
    for (x, y, z) in gal_carve:
        k = (x, z, 1 if y > YC else -1)
        deep[k] = min(deep.get(k, 10 ** 6), abs(y - YC))
    shafts = {(x, z, 1 if y > YC else -1) for (x, y, z) in gal_glass}
    reach = sum(1 for (x, z, sg) in shafts if (x, z, sg) in deep and (x, YC + sg * (deep[(x, z, sg)] - 1), z) not in left)
    R['gallery_v2'] = {'glass': len(gal_glass), 'hull_carve': len(gal_carve), 'blocked': [list(b) for b in gal_block[:6]], 'blocked_n': len(gal_block),
                       'glass_on_ship': sum(1 for k in gal_glass if k in occ and k not in gal_carve), 'glass_on_parts': sum(1 for k in gal_glass if k in allparts),
                       'shafts': len(shafts), 'shafts_reach_cabin': reach, 'glass_mirror_diff': sum(1 for (x, y, z) in gal_glass if (x, 2 * YC - y, z) not in gal_glass),
                       'carve_mirror_diff': sum(1 for (x, y, z) in gal_carve if (x, 2 * YC - y, z) not in gal_carve)}
    # 圖：船頭側面、船尾正面
    sc = 6
    im = Image.new('RGB', (1560, 760), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '康塞普西翁號 新圖紙 05：espolón、鍍金獅子、船尾走廊、側廊、船尾拱形板（無原罪聖母＋CONCEPCION）　v1', fill=(0, 0, 0), font=font(18))
    deco = [(k, c) for nm, cells in parts.items() for k, c in cells.items()]
    hullcells = [((x, y, z), c) for x, y, z, c in A.tolist() if x >= 560 or x <= 220]
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x < 560 or y < YC:
            continue
        if y > best.get((x, z), (-1, 0))[0]:
            best[(x, z)] = (y, c)
    for (x, z), (y, c) in best.items():
        if 560 <= x <= 690 and 40 <= z <= 175:
            X, Y = 20 + (x - 560) * sc / 1.5, 50 + (175 - z) * sc / 1.5
            d.rectangle([X, Y, X + sc / 1.5 - 1, Y + sc / 1.5 - 1], fill=palette_rgb(int(c)))
    d.text((20, 50 + 138 * sc / 1.5), '船頭（右舷側面）', fill=(0, 0, 0), font=font(14))
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x > 220:
            continue
        if x < best.get((y, z), (10 ** 6, 0))[0]:
            best[(y, z)] = (x, c)
    ox, oy, s2 = 840, 50, 5
    for (y, z), (x, c) in best.items():
        if 70 <= z <= 200 and 90 <= y <= 230:
            X, Y = ox + (y - 90) * s2, oy + (200 - z) * s2
            d.rectangle([X, Y, X + s2 - 1, Y + s2 - 1], fill=palette_rgb(int(c)))
    d.text((ox, oy + 132 * s2), '船尾正面（從船尾看，左手 ＝ −y）', fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

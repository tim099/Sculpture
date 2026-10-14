# 新圖紙 13 欄杆 v1（階段十二，TASK-0538）：plan.json rails ＋ 組裝件 export list（草稿開著：梯子、梯口都算現況）＋ masks/decks ＋ decks.json
#   ⇒ masks/rails/rails.vox.txt（子作品 -rails、船殼座標、關聯 at 0,0,0）、verify_rails.json、sheet13_rails_v1.png
# 用法：python -I draft_rails.py <design 資料夾> <組裝件 export list>
#   · 欄杆 ＝ 立柱（每 post_every 欄一根，走的那一格起 height−1 格）＋ 扶手（走的那一格 ＋ height − 1 那一層，連續）。
#   · 內側的邊：後甲板前緣（X qd_edge）、兩舷走道的內緣、前甲板後緣（X fc_edge）、船尾樓前緣（X poop_edge）—— 站在那一層甲板板上；梯子到的地方（梯寬 ±1）留開口。
#   · 外側：走道那一層與船尾樓，舷頂比「走的那一格 ＋ height − 1」低的地方，立柱與扶手站在舷頂那一格上、補到同一個高度。
#   · 扶手是一條連續的線：相鄰兩格差不只一個軸時補中間那一格（面接面，6 連通）。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

NX, NY, NZ = 1024, 320, 260
YC = 160


class Rails:
    def __init__(s, design, asm_list):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['rails']
        w = DP.read_list(asm_list)
        assert len(w) == s.P['assembly_cells'], ('組裝件格數對不上', len(w), s.P['assembly_cells'])
        s.asm_sha = hashlib.sha256(open(asm_list, 'rb').read()).hexdigest()
        s.W = np.zeros((NX, NY, NZ), bool)
        for (x, y, z) in w:
            s.W[x, y, z] = True
        s.spar = DP.read_list(os.path.join(design, 'masks', 'decks', 'spar.vox.txt'))
        s.poop = DP.read_list(os.path.join(design, 'masks', 'decks', 'poop.vox.txt'))
        dk = json.load(open(os.path.join(design, 'decks.json'), encoding='utf-8'))
        s.X0 = dk['X0']
        s.walk_spar = dk['decks']['spar']
        s.poop_walk = s.plan['deckworks']['decks']['poop']['walk_Z']
        s.ladders = s.plan['ladders']['list']
        s.lw = s.plan['ladders']['geometry']['width'] // 2
        s.cells = {}
        s.rows = {}

    def walk(s, x):
        P = s.plan['deckworks']['decks']['poop']['X']
        if P[0] <= x <= P[1]:
            return s.poop_walk
        return int(s.walk_spar[x - s.X0])

    def free(s, c):
        return 0 <= c[2] < NZ and not s.W[c] and c not in s.cells

    def ladder_gap(s, x, y, which):
        """這一格是不是梯子到的地方（梯寬 ±1；which ＝ 梯名的前綴）"""
        for L in s.ladders:
            if L['name'].startswith(which) and abs(y - L['yc']) <= s.lw + 1:
                return True
        return False

    def line(s, pts, name):
        """pts：依序的 (x, y, z, post?) —— 扶手格（z）連成一條；post 的那幾欄往下補立柱到地板。回傳放了幾格。"""
        H = s.P['height']
        C = s.P['color']
        n0 = len(s.cells)
        prev = None
        for (x, y, z, post) in pts:
            cur = (x, y, z)
            if prev is not None:
                # 補中間的格（一次動一個軸），讓扶手面接面
                a = list(prev)
                for ax in (2, 1, 0):
                    while a[ax] != cur[ax]:
                        a[ax] += 1 if cur[ax] > a[ax] else -1
                        t = tuple(a)
                        if t != cur and s.free(t):
                            s.cells[t] = C
            if s.free(cur):
                s.cells[cur] = C
            if post:
                for zz in range(z - 1, z - H, -1):
                    c = (x, y, zz)
                    if not s.free(c):
                        break
                    s.cells[c] = C
            prev = cur
        s.rows[name] = s.rows.get(name, 0) + len(s.cells) - n0

    def inner_edges(s):
        H, E = s.P['height'], s.P['post_every']
        R = s.P
        # 走道內緣（每一欄、每一舷）：走道那一層板在 X 的最小 dy
        inner = {}
        for (x, y, z) in s.spar:
            if R['qd_edge'] < x < R['fc_edge'] and z == s.walk(x) - 1:
                side = 1 if y > YC else -1
                dy = abs(y - YC)
                k = (x, side)
                if dy > 0 and (k not in inner or dy < inner[k]):
                    inner[k] = dy
        s.inner = inner
        for side in (1, -1):
            # 一條：前甲板後緣（從中線往這一舷）→ 走道內緣（往船尾）→ 後甲板前緣（往中線）
            pts = []
            # 後甲板前緣：X qd_edge，dy 0 → 走道內緣
            dq = inner[(R['qd_edge'] + 1, side)]
            for dy in range(0, dq + 1):
                y = YC + side * dy
                gap = s.ladder_gap(R['qd_edge'] + 1, y, 'qd')
                pts.append((R['qd_edge'], y, s.walk(R['qd_edge']) + H - 1, not gap and dy % E == 0, gap))
            for x in range(R['qd_edge'] + 1, R['fc_edge']):
                dy = inner[(x, side)]
                pts.append((x, YC + side * dy, s.walk(x) + H - 1, (x - R['qd_edge']) % E == 0, False))
            df = inner[(R['fc_edge'] - 1, side)]
            for dy in range(df, -1, -1):
                y = YC + side * dy
                gap = s.ladder_gap(R['fc_edge'] - 1, y, 'fc')
                pts.append((R['fc_edge'], y, s.walk(R['fc_edge']) + H - 1, not gap and dy % E == 0, gap))
            # 梯子到的地方斷開
            seg = []
            for p in pts:
                if p[4]:
                    if seg:
                        s.line([q[:4] for q in seg], 'inner')
                    seg = []
                else:
                    seg.append(p)
            if seg:
                s.line([q[:4] for q in seg], 'inner')
            # 船尾樓前緣：X poop_edge，中線 → 這一舷船尾樓板的邊
            xp = R['poop_edge']
            dys = sorted(abs(y - YC) for (x, y, z) in s.poop if x == xp and z == s.poop_walk - 1 and (y - YC) * side >= 0)
            seg = []
            for dy in range(0, dys[-1] + 1):
                y = YC + side * dy
                gap = s.ladder_gap(xp + 1, y, 'poop')
                if gap:
                    if seg:
                        s.line(seg, 'poop_front')
                    seg = []
                    continue
                seg.append((xp, y, s.poop_walk + H - 1, dy % E == 0))
            if seg:
                s.line(seg, 'poop_front')

    def outer(s):
        """舷頂比扶手低的地方：站在舷頂那一格上補到扶手高度（走道那一層＋船尾樓）。"""
        H, E = s.P['height'], s.P['post_every']
        xs = sorted({x for (x, y, z) in s.spar} | {x for (x, y, z) in s.poop})
        for side in (1, -1):
            pts = []
            for x in xs:
                half = (s.W[x, YC + 1:, :] if side > 0 else s.W[x, :YC, :][::-1]).copy()
                # 只看舷牆：每一層 z 離那一層最外那一格 ≤ 6 格的實心 —— v1 量整個半舷的最高格，前甲板艙口圍欄比舷頂高，欄杆爬到圍欄上（X 494–518）；
                # v2 用「整欄最寬那一格 − 6」⇒ 船尾的牆往內收（tumblehome），上半截不算牆，欄杆掛在船尾樓裡面
                #     還要離整欄最寬那一格 ≤ 20 格（艙口圍欄高過舷頂時，那一層最外的實心就是圍欄自己）
                dmax = int(np.where(half.any(1))[0].max())
                half[:max(0, dmax - 20)] = False
                for zi in np.where(half.any(0))[0]:
                    ys_ = np.where(half[:, zi])[0]
                    half[:max(0, int(ys_.max()) - 6), zi] = False
                zz = np.where(half.any(0))[0]
                if not len(zz):
                    continue
                T = int(zz.max())
                ys = np.where(half[:, T])[0]
                dy = int(ys.max()) - 1 if len(ys) > 1 else int(ys.max())    # 舷頂那一列靠外、讓開最外那一格
                y = YC + side * (dy + 1)
                rt = s.walk(x) + H - 1
                if T + 1 > rt:
                    if pts:
                        s.line(pts, 'outer')
                    pts = []
                    continue
                pts.append((x, y, rt, x % E == 0))
            if pts:
                s.line(pts, 'outer')

    def verify(s):
        v = {'cells': len(s.cells), 'by_part': s.rows, 'overlap_world': sum(1 for c in s.cells if s.W[c])}
        xs = [c[0] for c in s.cells]
        xa, xb = min(xs) - 3, max(xs) + 4
        A = s.W[xa:xb].copy()
        for c in s.cells:
            A[c[0] - xa, c[1], c[2]] = True
        lab, _ = ndimage.label(A)
        base = set(np.unique(lab[s.W[xa:xb]])) - {0}
        fl = [c for c in s.cells if lab[c[0] - xa, c[1], c[2]] not in base]
        v['floating'] = len(fl)
        v['floating_first'] = [list(c) for c in fl[:6]]
        v['mirror_missing'] = sum(1 for (x, y, z) in s.cells if (x, 320 - y, z) not in s.cells)
        # 梯子到的地方：扶手那一層、梯子中線那一格是空的
        v['ladder_openings_blocked'] = [L['name'] for L in s.ladders if not L['name'].startswith('scuttle')
                                        and any((x, L['yc'], z) in s.cells for x in range(L['xe'] - 2, L['xe'] + 3) for z in range(120, 180))]
        v['expect_assembly_after'] = s.P['assembly_cells'] + len(s.cells)
        s.v = v

    def write(s):
        out = os.path.join(s.design, 'masks', 'rails')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'rails.vox.txt')
        body = ''.join('%d,%d,%d,%d\n' % (c[0], c[1], c[2], v) for c, v in sorted(s.cells.items()))
        open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 欄杆（子作品 -rails；船殼座標；新圖紙 13 v1，draft_rails.py 產；%d 格，stampvox at=0,0,0）\n' % len(s.cells) + body)
        s.files = {'rails': {'cells': len(s.cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}


def render_sheet(F, path):
    """平面（從上往下看，扶手黑、甲板淡）＋右舷外側立面。"""
    sc = 2
    X0, X1 = 40, 700
    top = np.full((NY, X1 - X0, 3), 250, np.uint8)
    occ = F.W[X0:X1].any(2)
    top[occ.T] = (225, 218, 205)
    for (x, y, z) in F.spar:
        top[y, x - X0] = (250, 225, 170)
    for (x, y, z) in F.poop:
        top[y, x - X0] = (240, 210, 160)
    for (x, y, z) in F.cells:
        top[y, x - X0] = (30, 30, 30)
    im1 = Image.fromarray(top[::-1][60:260]).resize(((X1 - X0) * sc, 200 * sc), Image.NEAREST)
    ImageDraw.Draw(im1).text((6, 4), 'sheet 13 v1  rails (plan view, bow right, starboard up): black = rail/posts', fill=(0, 0, 0))
    el = np.full((NZ, X1 - X0, 3), 250, np.uint8)
    el[(F.W[X0:X1, YC:, :].any(1)).T] = (190, 185, 175)
    for (x, y, z) in F.cells:
        if y >= YC:
            el[z, x - X0] = (30, 30, 30)
    im2 = Image.fromarray(el[::-1][40:200]).resize(((X1 - X0) * sc, 160 * sc), Image.NEAREST)
    ImageDraw.Draw(im2).text((6, 4), 'starboard elevation (rails black)', fill=(0, 0, 0))
    can = Image.new('RGB', (im1.size[0], im1.size[1] + im2.size[1] + 10), (255, 255, 255))
    can.paste(im1, (0, 0))
    can.paste(im2, (0, im1.size[1] + 10))
    can.save(path)


def main():
    design, asm = sys.argv[1], sys.argv[2]
    F = Rails(design, asm)
    F.inner_edges()
    F.outer()
    F.verify()
    F.write()
    F.v['files'] = F.files
    F.v['assembly_list_sha256'] = F.asm_sha
    json.dump(F.v, open(os.path.join(design, 'verify_rails.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(F, os.path.join(design, 'sheet13_rails_v1.png'))
    print(json.dumps(F.v, ensure_ascii=False))


if __name__ == '__main__':
    main()

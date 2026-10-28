# 抄來的（燕子號 TASK-0968）：出處 gura-flyingfish-01m/design/draft_deco.py（飛魚號；作品 id、船名、單號已換）
# 燕子號 步驟 6（TASK-0968）：裝飾 —— 船首像（燕子）、窄平艉板的金色燕子（船殼換色）、船尾窗玻璃後面刻穿
#   本船自己寫的（拉貝爾號那支是 knee of head、Fontanges 船首像、假艉廊、百合花，換掉）；船頭外緣、船尾面從作品匯出量（⛔ 不拿設計陣列當作品）。
#   輸入：plan.json（deco、masts 的 bowsprit）＋ 船殼作品（CLI 匯出）
#   輸出：masks/deco/figurehead.vox.txt（世界座標，at 0,0,0）、masks/deco/emblem_paint.vox.txt（船殼 stampvox overwrite=1）、
#         masks/glass/carve_behind.vox.txt（玻璃後面那幾格，carvevox 顏色守門）、verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--mark=裝飾:begin] [--probe=emblem_dy=<偏幾格>]（反向對照：金魚整條往右舷偏；⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list


def swallow(F):
    """燕子號：局部座標 (u 往船頭, v 船寬, w 往上) ⇒ 顏色；u 0 ＝ 尾巴根。身體沿 u 漸粗漸細、頭微微往上；
    藏青的背、白腹、喉嚨一圈紅褐；翅膀從肩往後掠、往外漸低（滑翔）；尾巴左右分叉成兩根長尾羽。"""
    C = F['colors']
    out = {}
    n = F['len']
    rad = [0.8, 1.1, 1.4, 1.6, 1.6, 1.4, 1.2, 0.9]
    wc = lambda u: 0.15 * u
    for u in range(n):
        r = rad[min(u, len(rad) - 1)]
        R = int(math.ceil(r))
        for v in range(-R, R + 1):
            for w in range(-R - 1, R + 2):
                dw = w - wc(u)
                if v * v + dw * dw <= r * r + 0.25:
                    out[(u, v, w)] = C['back'] if dw > 0.3 else (C['throat'] if u >= n - 3 else C['belly'])
    out[(n, 0, int(round(wc(n))))] = C['eye']                     # 嘴：頭前面一格（深色）
    ue = n - 2                                                    # 眼睛：頭後面一格、兩側
    out[(ue, 1, int(round(wc(ue) + 0.6)))] = C['eye']
    out[(ue, -1, int(round(wc(ue) + 0.6)))] = C['eye']
    for v in range(2, 8):                                         # 翅膀：前緣 5.5 − 0.6(v−2)、後緣 3 − 0.8(v−2)，每往外一格低 0.25
        a, b = 3 - 0.8 * (v - 2), 5.5 - 0.6 * (v - 2)
        for u in range(int(math.ceil(a)), int(math.floor(b)) + 1):
            w = int(round(wc(u) + 0.6 - 0.25 * (v - 2)))
            for s in (1, -1):
                out[(u, s * v, w)] = C['back']
    for k in (1, 2, 3, 4):                                        # 尾巴：u −1..−4 往兩舷分叉（燕尾）
        for s in (1, -1):
            out[(-k, s * ((k + 1) // 2), 0)] = C['back']
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    D = plan['deco']
    mark = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--mark=')), '裝飾:begin')   # 量「落格之前」的船殼 ⇒ 落格之後重跑照樣逐位元組相同
    W = export_list('gura-swallow-01m', mark)
    occ = {(x, y, z): c for x, y, z, c in W.tolist()}

    # ── 船首像：尾巴根貼在艏柱前緣（中線那一欄、那個 z 最前面的格）＋ gap ──
    F = D['figurehead']
    bow = {}
    for (x, y, z) in occ:
        if y == YC and x > 180:
            bow[z] = max(bow.get(z, -1), x)
    bz = F['z']
    bx = bow[bz] + 1 + F['gap']
    fig = {}
    embedded = 0
    for (u, v, w), c in swallow(F).items():
        p = (bx + u, YC + v, bz + w)
        if p in occ:              # 尾巴尖插進艏柱的那幾格不放（v1 3 格撞船殼）
            embedded += 1
            continue
        fig[p] = c
    # 艏斜桅會不會撞到：沿桅軸、半徑 2.5 格內的格
    B = LY.bowsprit(plan)
    ax = np.array([B['x1'] - B['x0'], 0.0, B['z1'] - B['z0']])
    ax /= np.linalg.norm(ax)

    def near_sprit(p):
        d = np.array([p[0] + 0.5 - B['x0'], p[1] + 0.5 - (YC + 0.5), p[2] + 0.5 - B['z0']])
        t = float(d @ ax)
        return t > 0 and float(np.linalg.norm(d - t * ax)) <= 2.5
    fig_hit_sprit = sum(1 for p in fig if near_sprit(p))
    fig_hit_hull = sum(1 for p in fig if p in occ)
    fig_mirror = sum(1 for (x, y, z), c in fig.items() if fig.get((x, 2 * YC - y, z)) != c)

    # ── 方艉金魚：每個 (y, z) 最後面那一格（x < stern_x_max），只塗原本是 frieze 的格 ──
    E = D['emblem']
    sx = plan['paint']['stern_x_max']
    aft = {}
    for (x, y, z) in occ:
        if x < sx and x < aft.get((y, z), 999):
            aft[(y, z)] = x
    shift = int(probe[0].split('=')[1]) if probe else 0
    paint, skipped = {}, []
    for j, row in enumerate(E['rows']):
        z = E['z0'] + j
        half = (len(row) - 1) // 2
        for i, ch in enumerate(row):
            if ch != 'G':
                continue
            y = YC + (i - half) + shift
            x = aft.get((y, z))
            if x is None or occ[(x, y, z)] != plan['paint']['frieze']:
                skipped.append((y, z))
                continue
            paint[(x, y, z)] = E['color']
    em_mirror = sum(1 for (x, y, z) in paint if (x, 2 * YC - y, z) not in paint)

    # ── 船尾窗玻璃：玻璃格往船頭（+x）那幾格牆刻穿到艙裡的空氣（最多 4 格） ──
    G = D['glass']
    glass = [p for p, c in occ.items() if c == G['color']]
    behind = {}
    open_after = 0
    for (x, y, z) in glass:
        k = 1
        while k <= 4 and (x + k, y, z) in occ and occ[(x + k, y, z)] != G['color']:
            behind[(x + k, y, z)] = occ[(x + k, y, z)]
            k += 1
        if (x + k, y, z) not in occ:
            open_after += 1
    R = {'figurehead': {'cells': len(fig), 'embedded_tail': embedded, 'at_x': bx, 'stem_front_x': bow[bz], 'x': [min(p[0] for p in fig), max(p[0] for p in fig)],
                        'z': [min(p[2] for p in fig), max(p[2] for p in fig)], 'hit_hull': fig_hit_hull, 'hit_bowsprit': fig_hit_sprit, 'mirror_diff': fig_mirror,
                        'colors': {str(c): sum(1 for v in fig.values() if v == c) for c in sorted(set(fig.values()))}},
         'emblem': {'cells': len(paint), 'skipped': skipped, 'mirror_diff': em_mirror},
         'glass': {'cells': len(glass), 'carve_behind': len(behind), 'open_behind': open_after}}
    if probe:
        print(json.dumps({'probe': probe[0], 'emblem': R['emblem']}, ensure_ascii=False))
        return

    def dump(path, cells, head):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
        return [len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    R['lists'] = {
        'figurehead': dump(os.path.join(design, 'masks', 'deco', 'figurehead.vox.txt'), fig, '# 燕子號 船首像（燕子；世界座標，at 0,0,0）\n'),
        'emblem': dump(os.path.join(design, 'masks', 'deco', 'emblem_paint.vox.txt'), paint, '# 燕子號 艉板金燕（船殼 stampvox overwrite=1）\n'),
        'carve_behind': dump(os.path.join(design, 'masks', 'glass', 'carve_behind.vox.txt'), behind, '# 燕子號 船尾窗玻璃後面的牆（carvevox，第 4 欄 ＝ 現在的顏色）\n')}

    # ── 圖：船頭側面（船首像）、船尾正面（金魚＋窗） ──
    sc = 10
    im = Image.new('RGB', (1100, 520), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((10, 6), '燕子號 新圖紙 05：船首像（燕子）、艉板金燕、船尾窗玻璃　v1', fill=(0, 0, 0), font=font(18))
    ox, oz = 20, 480
    x_lo, z_lo = 195, 28
    side = {}
    for (x, y, z), c in occ.items():
        if x >= x_lo and z >= z_lo and y >= YC and y >= side.get((x, z), (-1, 0))[0]:
            side[(x, z)] = (y, c)
    for (x, z), (y, c) in side.items():
        d.rectangle([ox + (x - x_lo) * sc, oz - (z - z_lo + 1) * sc, ox + (x - x_lo + 1) * sc, oz - (z - z_lo) * sc], fill=palette_rgb(int(c)))
    fs = {}
    for (x, y, z), c in fig.items():
        if y >= fs.get((x, z), (-1, 0))[0]:
            fs[(x, z)] = (y, c)
    for (x, z), (y, c) in fs.items():
        d.rectangle([ox + (x - x_lo) * sc, oz - (z - z_lo + 1) * sc, ox + (x - x_lo + 1) * sc, oz - (z - z_lo) * sc], fill=palette_rgb(int(c)), outline=(0, 0, 0))
    t0, t1 = 0.0, 30.0
    pts = [(ox + (B['x0'] + t * ax[0] - x_lo) * sc, oz - (B['z0'] + t * ax[2] - z_lo) * sc) for t in (t0, t1)]
    d.line(pts, fill=(110, 70, 30), width=int(2.5 * sc))
    sc2, ox2, oz2 = 12, 600, 480
    for (y, z), x in aft.items():
        c = paint.get((x, y, z), occ[(x, y, z)])
        if z >= 20:
            d.rectangle([ox2 + (y - YC + 16) * sc2, oz2 - (z - 20 + 1) * sc2, ox2 + (y - YC + 17) * sc2, oz2 - (z - 20) * sc2], fill=palette_rgb(int(c)))
    d.text((10, 495), '船首像 %d 格（撞船殼 %d、撞艏斜桅 %d、鏡像差 %d）；金魚 %d 格（鏡像差 %d、跳過 %d）；玻璃 %d 格、後面刻 %d 格、刻完後面是空的 %d' % (
        len(fig), fig_hit_hull, fig_hit_sprit, fig_mirror, len(paint), em_mirror, len(skipped), len(glass), len(behind), open_after), fill=(0, 0, 0), font=font(13))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

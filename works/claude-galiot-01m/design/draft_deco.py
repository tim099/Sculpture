# 蠍子號 新圖紙 04（TASK-0023 步驟 6）：裝飾 ⇒ masks/deco/{spur,poop,awning}.vox.txt、masks/step6/hull_paint.vox.txt（船殼換色，overwrite）、
#   verify_deco.json、sheet04_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py [--probe=emblem_x=3]   （probe ⇒ 紋章挪幾格，只印換色清單差幾格；⛔ 不寫檔）
#   出處：做法照海鷗號 claude-felucca-01m/design/draft_deco.py（船殼換色只動露在外面的那一層、兩舷鏡過去；裝飾子作品）；
#         船名用星座圖照星辰號 claude-baghlah-01m（八角星代表 al-Najm）的想法。件的格子照 layout.py（spur、poop、awning）。
#   · 船名：al-ʿAqrab（العقرب）是天蠍座的阿拉伯名 ⇒ 兩舷船尾的黑舷側點天蠍座的星（金 244，心宿二 Antares 紅 196）；頭朝船頭。
#   · 換色只動船殼「那一格往外一格是空的」那一層、原本是黑 36 的格；不加格、不刻格 ⇒ 重量、命中、走路都不變。
#   · 篷（awning）做成外部模型 deco=1（Ship_Fittings §9.9：純看的、上面不掛東西）；spur、艉台與燈桿是格子（燈要掛在燈桿上）。
import sys, os, json, copy, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import layout as LY

sys.stdout.reconfigure(encoding='utf-8')
GOLD, RED, BLACK = 244, 196, 36
# 天蠍座（右邊 ＝ 船頭 +x，上 ＝ +z）：頭三顆（β δ π）一直排 → σ → 心宿二 α（紅）→ τ ε μ 往下彎 → ζ η 底 → θ ι κ 往上勾 → λ υ 尾針（設計決定：照星圖的樣子排在 12 × 8 的格裡）
STARS = [(11, 7, 'b'), (11, 6, 'd'), (11, 5, 'p'), (9, 5, 's'), (8, 4, 'A'), (7, 3, 't'), (6, 2, 'e'), (5, 1, 'm'),
         (4, 0, 'z'), (3, 0, 'h'), (2, 1, 'th'), (1, 2, 'i'), (1, 3, 'k'), (2, 4, 'l')]


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def paint(K, plan, shift=0):
    """右舷算好、左舷鏡過去：{(x, y, z): 新色}；每一點找那一排 (x, z) 最外面的船殼格（往外一格空）。"""
    YC = K.YC
    em = V(plan['deco'])['emblem']
    H = K.hull
    out, skipped = {}, []
    for sx, sz, name in STARS:
        x, z = em['x'] + sx + shift, em['z'] + sz
        ys = np.where(H[x, YC:, z] > 0)[0]
        if not len(ys):
            skipped.append([name, x, z, 'no hull'])
            continue
        y = YC + int(ys.max())
        if H[x, y + 1, z] or H[x, y, z] != BLACK:
            skipped.append([name, x, z, 'not outer black (%d)' % H[x, y, z]])
            continue
        c = RED if name == 'A' else GOLD
        out[(x, y, z)] = c
        out[(x, 2 * YC - y, z)] = c
    return out, skipped


def readings(plan, K, pieces, P, skipped):
    YC = K.YC
    H = K.hull
    R = {'cells': {k: int((pieces[k] > 0).sum()) for k in ('spur', 'poop', 'awning')}}
    others = (H > 0) | (pieces['deck'] > 0) | (pieces['rambade'] > 0)
    R['overlap'] = {k: int(((pieces[k] > 0) & others).sum()) for k in ('spur', 'poop', 'awning')}
    R['overlap']['poop_awning'] = int(((pieces['poop'] > 0) & (pieces['awning'] > 0)).sum())
    R['components'] = {k: int(ndimage.label(pieces[k] > 0)[1]) for k in ('spur', 'poop', 'awning')}
    R['mirror_diff'] = {k: int((pieces[k] != pieces[k][:, ::-1, :]).sum()) for k in ('spur', 'poop', 'awning')}
    U = others | (pieces['spur'] > 0) | (pieces['poop'] > 0)
    lab, n = ndimage.label(U)
    R['cells_hull_deck_bow_spur_poop'] = {'cells': int(U.sum()), 'components': int(n), 'cavity_cells': int((ndimage.binary_fill_holes(U) & ~U).sum())}
    # 篷要靠在船上（模型，不連也不會掉，但看起來要貼著）：篷的格旁邊 6 鄰有船的格
    aw = pieces['awning'] > 0
    touch = int((aw & ndimage.binary_dilation(U, structure=ndimage.generate_binary_structure(3, 1))).sum())
    R['awning_cells_touching_ship'] = touch
    G = H.copy()
    for (x, y, z), c in P.items():
        G[x, y, z] = c
    R['paint'] = {'cells': len(P), 'colors': {str(c): sum(1 for v in P.values() if v == c) for c in sorted(set(P.values()))},
                  'skipped': skipped, 'hull_mirror_diff_after': int((G != G[:, ::-1, :]).sum()),
                  'all_outer': all(not H[x, y + (1 if y > YC else -1), z] for (x, y, z) in P), 'all_were_black': all(H[k] == BLACK for k in P)}
    sp = np.where((pieces['spur'] > 0).any(axis=(1, 2)))[0]
    R['spur_x'] = [int(sp.min()), int(sp.max())]
    la = V(plan['layout']['stern'])['lantern']
    R['lantern'] = {'pole_top_z': int(np.where(pieces['poop'][la['x'], YC, :] == K.C['iron'])[0].max()), 'lamp_at': [la['x'], YC, la['top_z']],
                    'lamp_air': not bool(U[la['x'], YC, la['top_z']] or aw[la['x'], YC, la['top_z']])}
    return R


def sheet(plan, K, pieces, P, R, path):
    YC = K.YC
    s = 3
    img = Image.new("RGB", (K.SX * s + 120, 620), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((40, 12), '%s - new sheet 04: decoration (spur, poop and lantern pole, awning = deco model, Scorpius emblem = ship name)   0.1 m/cell' % plan['title_en'], fill=(20, 20, 40), font=f)
    comp = K.hull.copy()
    for (x, y, z), c in P.items():
        comp[x, y, z] = c
    for k in ('deck', 'rambade', 'spur', 'poop', 'awning'):
        comp[pieces[k] > 0] = pieces[k][pieces[k] > 0]
    ox, oy = 60, 60 + 70 * s
    d.text((40, 36), '1. starboard elevation (outermost colour seen from +y; bow to the right)', fill=(20, 20, 40), font=f)
    S = comp > 0
    for x in range(K.SX):
        for z in range(70):
            ys = np.where(S[x, YC:, z])[0]
            if len(ys):
                d.rectangle([ox + x * s, oy - (z + 1) * s, ox + x * s + s - 1, oy - z * s - 1], fill=rgb(int(comp[x, YC + ys.max(), z])))
    em = V(plan['deco'])['emblem']
    k = 14
    ox2, oy2 = 60, oy + 40 + 13 * k      # 特寫 13 列：底在這裡，往上畫（v1 少算 3 列、蓋到標題）
    d.text((40, oy + 16), '2. emblem close-up (starboard, x %d-%d, z %d-%d; one square = one cell)' % (em['x'] - 2, em['x'] + 14, em['z'] - 2, em['z'] + 10), fill=(20, 20, 40), font=f)
    for x in range(em['x'] - 2, em['x'] + 15):
        for z in range(em['z'] - 2, em['z'] + 11):
            ys = np.where(S[x, YC:, z])[0]
            if len(ys):
                c = rgb(int(comp[x, YC + ys.max(), z]))
                d.rectangle([ox2 + (x - em['x'] + 2) * k, oy2 - (z - em['z'] + 3) * k, ox2 + (x - em['x'] + 3) * k - 2, oy2 - (z - em['z'] + 2) * k - 2], fill=c)
    rows = ['spur %d cells (x %d-%d), poop %d, awning %d (deco model); overlaps with hull/deck/bow: %s' % (R['cells']['spur'], R['spur_x'][0], R['spur_x'][1], R['cells']['poop'], R['cells']['awning'], R['overlap']),
            'components %s, mirror diff %s; hull+deck+bow+spur+poop %s' % (R['components'], R['mirror_diff'], R['cells_hull_deck_bow_spur_poop']),
            'emblem: %d cells repainted %s, all outer %s, all were black %s, skipped %d; hull mirror diff after %d' % (R['paint']['cells'], R['paint']['colors'], R['paint']['all_outer'], R['paint']['all_were_black'], len(R['paint']['skipped']), R['paint']['hull_mirror_diff_after']),
            'lantern pole top z %d, lamp at %s in air %s' % (R['lantern']['pole_top_z'], R['lantern']['lamp_at'], R['lantern']['lamp_air'])]
    for i, r in enumerate(rows):
        d.text((300, oy + 40 + i * 18), r, fill=(30, 30, 30), font=f)
    img.save(path)


def main():
    plan = HL.load_plan(HERE)
    shift = 0
    for a in sys.argv[1:]:
        if a.startswith('--probe=emblem_x='):
            shift = int(a.split('=')[-1])
    K = LY.Ctx(plan)
    pieces, _, _ = LY.assemble(K)
    P, skipped = paint(K, plan, shift)
    if shift:
        P0, _ = paint(K, plan, 0)
        print(json.dumps({'probe_emblem_x': shift, 'paint_cells': len(P), 'differs_from_design': len(set(P.items()) ^ set(P0.items()))}, ensure_ascii=False))
        return
    R = readings(plan, K, pieces, P, skipped)
    R['lists'] = []
    for key, sub, title in (('spur', 'deco', 'spur（sperone）'), ('poop', 'deco', '艉台與燈桿'), ('awning', 'deco', '船尾篷（外部模型 deco=1）')):
        os.makedirs(os.path.join(HERE, 'masks', sub), exist_ok=True)
        fn = os.path.join(HERE, 'masks', sub, key + '.vox.txt')
        a = pieces[key]
        with open(fn, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('# 蠍子號 %s（draft_deco.py）x,y,z,color —— at 0,0,0（子作品用船殼的框）\n' % title)
            fh.write(''.join('%d,%d,%d,%d\n' % (x, y, z, a[x, y, z]) for x, y, z in np.argwhere(a > 0)))
        R['lists'].append({'file': 'masks/%s/%s.vox.txt' % (sub, key), 'cells': int((a > 0).sum()), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()})
    os.makedirs(os.path.join(HERE, 'masks', 'step6'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'step6', 'hull_paint.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('# 蠍子號 船殼換色（draft_deco.py；天蠍座紋章）x,y,z,color —— at 0,0,0，stampvox overwrite=1\n')
        fh.write(''.join('%d,%d,%d,%d\n' % (x, y, z, c) for (x, y, z), c in sorted(P.items())))
    R['lists'].append({'file': 'masks/step6/hull_paint.vox.txt', 'cells': len(P), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()})
    with open(os.path.join(HERE, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    sheet(plan, K, pieces, P, R, os.path.join(HERE, 'sheet04_deco_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

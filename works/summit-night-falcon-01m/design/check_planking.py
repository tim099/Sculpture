# 階段三讀數（作品落格之後）：讀作品 export list（⛔ 不讀設計陣列）。
# 用法：python -I -X utf8 -B check_planking.py <design 資料夾> <作品 export format=list 的檔>
#   · 漏水：船艙 ＝ 圖紙曲面（Hull.hb）圍出來的體積裡、作品沒有格、不是插板槽的格；從船外角落 6 連通灌水（z < 主甲板最低點），走到船艙幾格。
#   · 探針（從圖紙取）：x 95／135／175／215／245 × z 8／15／25 ⇒ 右舷最外那一格的外緣（y+1）離圖紙船殼外面多少；
#     中線那一欄沿艏柱前緣／艉板面（z 5／20／35／50）。
#   · 反向對照：作品整份偏 3 格（y 一次、x 一次）⇒ 每根探針多報 3。
#   · 漏水的尺先餵已知答案：x 177、z 8 右舷 ① 只拿掉最外一格 ② 把 z 8 那一排外板（往船內連著的）都拿掉 ⇒ 各報幾格；剖面圖 overlays/stage3_leak_probe.png。
#     （船舭在那裡幾乎是平的：z 8 這一層有三格外板橫著並排，最外那格上面是 z 9 那一排 —— 只拿一格，水進得了洞、進不了船艙。）
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, font

NX, NY, NZ = 384, 161, 74
PX = [95, 135, 175, 215, 245]; PZ = [8, 15, 25]; EZ = [5, 20, 35, 50]


def occ_of(pts, dx=0, dy=0):
    o = np.zeros((NX + 8, NY + 8, NZ), bool)
    o[pts[:, 0] + dx, pts[:, 1] + dy, pts[:, 2]] = True
    return o[:NX, :NY]


def probes(H, o):
    side = []
    for x in PX:
        for z in PZ:
            ys = np.nonzero(o[x, YC:, z])[0]
            hb = float(H.hb(x + 0.5, z + 0.5))
            side.append({'x': x, 'z': z, 'gap': round(hb - (YC + ys.max() + 1 - (YC + 0.5)), 3) if len(ys) else None})
    ends = []
    for z in EZ:
        xs = np.nonzero(o[:, YC, z])[0]
        ends.append({'z': z, 'bow_gap': round(float(H.stem_face(z + 0.5)) - (xs.max() + 1), 3),
                     'stern_gap': round(xs.min() - float(H.aft_limit(z + 0.5)), 3)})
    return side, ends


def leak_of(H, T, o):
    zl = int(np.floor(H.sh['z_low']))
    x = np.arange(NX) + 0.5; z = np.arange(zl) + 0.5
    hb = H.hb(*np.meshgrid(x, z, indexing='ij'))
    dyv = np.abs(np.arange(NY) - YC)[None, :, None]
    vol = (~np.isnan(hb))[:, None, :] & (dyv <= np.nan_to_num(hb, nan=-1)[:, None, :])
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(zl)[None, None, :]
    slot = (X >= T['x'][0]) & (X <= T['x'][1]) & (Y == YC) & (Z <= T['top_z'])
    empty = ~o[:, :, :zl]
    lab, _ = ndimage.label(empty)
    hold = vol & empty & ~slot
    return int(hold.sum()), int((hold & (lab == lab[0, 0, 0])).sum()), zl


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan); T = plan['planking']['trunk']
    pts = np.loadtxt(lst, delimiter=',', dtype=int, comments='#')
    o = occ_of(pts)
    # 漏水
    hold_n, leak, zl = leak_of(H, T, o)
    # 已知答案：x 177（兩根肋骨之間）、z 8、右舷
    hx, hz = 177, 8
    ys = np.nonzero(o[hx, :, hz])[0]; ys = ys[ys > YC]
    o1 = o.copy(); o1[hx, ys.max(), hz] = False
    run = [ys.max()]
    while o[hx, run[-1] - 1, hz]: run.append(run[-1] - 1)
    o2 = o.copy(); o2[hx, run, hz] = False
    k1 = leak_of(H, T, o1); k2 = leak_of(H, T, o2)
    known = {'at': [hx, hz], 'one_cell': {'removed': [int(ys.max())], 'reached': k1[1]},
             'through': {'removed': [int(v) for v in run], 'reached': k2[1], 'hold_cells': k2[0]}}
    # 剖面圖（x 177，y 90..112、z 0..20）
    S = 22; W, Hh = 2 * 23 * S + 60, 21 * S + 110
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    for pi, (oo, rem, cap) in enumerate(((o1, [ys.max()], '① 拿掉最外一格 → 報 ' + str(k1[1])), (o2, run, '② z 8 那一排都拿掉 → 報 ' + str(k2[1])))):
        ox = 20 + pi * (23 * S + 20)
        g.text((ox, 10), cap, fill=(30, 30, 30), font=font(20))
        for yy in range(90, 113):
            for zz in range(0, 21):
                X0, Y0 = ox + (yy - 90) * S, 60 + (20 - zz) * S
                col = (60, 60, 40) if o[hx, yy, zz] else (250, 248, 242)
                if zz == hz and yy in rem: col = (210, 50, 50)
                g.rectangle([X0, Y0, X0 + S - 2, Y0 + S - 2], fill=col)
    g.text((20, Hh - 36), "x 177 剖面（兩根肋骨之間）：深色 ＝ 作品的格；紅 ＝ 拿掉的格；右下是船外", fill=(90, 90, 90), font=font(16))
    im.save(os.path.join(d, '..', 'overlays', 'stage3_leak_probe.png'), optimize=False)
    s0, e0 = probes(H, o)
    sy, _ = probes(H, occ_of(pts, dy=3))
    _, ex = probes(H, occ_of(pts, dx=3))
    rev_side = [round(a['gap'] - b['gap'], 3) for a, b in zip(s0, sy)]
    rev_ends = [round(a['bow_gap'] - b['bow_gap'], 3) for a, b in zip(e0, ex)] + [round(b['stern_gap'] - a['stern_gap'], 3) for a, b in zip(e0, ex)]
    R = {'leak': {'hold_cells': hold_n, 'reached_from_outside': leak, 'z_below': zl, 'known_answer': known},
         'probes_side': s0, 'probes_ends': e0,
         'reverse_offset3': {'side_y': rev_side, 'ends_x': rev_ends,
                             'all_report_3': all(abs(v - 3) < 1e-9 for v in rev_side) and all(abs(v - 3) < 1e-9 for v in rev_ends)},
         'note': 'gap ＝ 圖紙船殼外面 − 作品最外那一格的外緣；外板就在曲面那一層 ⇒ 照設計約 −0.5..+0.5（格心判斷的量化）'}
    with open(os.path.join(d, 'verify_planking_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()

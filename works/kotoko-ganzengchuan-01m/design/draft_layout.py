# 福建趕繒船 新圖紙 02（TASK-1314 步驟 3）：配置總圖 sheet02_layout_v1.png ＋ verify_layout.json
#   出處：kaguya-shachuan-01m/design/draft_layout.py（改寫為雙桅竹篾硬篷趕繒船：4 層甲板、8 道水密隔艙、12 門火砲、輔佐長櫓、雙桅硬篷）
#   用法：python -I -X utf8 draft_layout.py <design 資料夾>
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def main():
    design = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else HERE
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    SX, SY, SZ = plan['space']['assembly']
    sc = 3
    padL, padT = 60, 70
    W = SX * sc + padL * 2 + 120
    side_h = 260 * sc
    plan_h = SY * sc
    H = padT + side_h + 70 + plan_h + 110
    im = Image.new('RGB', (W, H), (250, 246, 236))
    d = ImageDraw.Draw(im)
    f20, f14, f12 = font(20), font(14), font(12)
    d.text((padL, 14), '福建趕繒船（1666 亞洲船③）配置總圖 v1：雙桅硬篷、8 道隔艙、12 門火砲、輔佐長櫓', fill=(25, 20, 15), font=f20)

    # ① 側面全船配置（含雙桅竹篾硬篷）
    oy = padT
    zmax_s = 255
    xs_hull = np.arange(60, 325)
    pts_top = [(padL + x * sc, oy + (zmax_s - float(L.top_z(x + 0.5))) * sc) for x in xs_hull]
    pts_bot = [(padL + x * sc, oy + (zmax_s - float(L.zb(x + 0.5))) * sc) for x in reversed(xs_hull)]
    d.polygon(pts_top + pts_bot, outline=(120, 70, 20), fill=(235, 222, 196))

    wl = int(plan['waterline']['z'])
    yw = oy + (zmax_s - wl) * sc
    d.line([padL + 35 * sc, yw, padL + 345 * sc, yw], fill=(30, 100, 200), width=2)
    d.text((padL + 348 * sc, yw - 8), f'DWL z={wl} (2.4m)', fill=(30, 100, 200), font=f12)

    dk = plan['decks']
    for k, col in (('hold', (160, 70, 30)), ('main', (180, 0, 0)), ('fore', (180, 0, 0)), ('poop', (180, 0, 0))):
        info = dk[k]
        zy = oy + (zmax_s - info['floor']) * sc
        d.line([padL + info['x0'] * sc, zy, padL + info['x1'] * sc, zy], fill=col, width=2)

    for bx in plan['bulkheads']['x']:
        d.line([padL + bx * sc, oy + (zmax_s - float(L.zb(bx + 0.5))) * sc,
                padL + bx * sc, oy + (zmax_s - dk['main']['floor']) * sc], fill=(90, 90, 90), width=2)

    # 砲位
    for gx in plan['ports']['gun']['x']:
        d.rectangle([padL + (gx - 4) * sc, oy + (zmax_s - 45) * sc, padL + (gx + 4) * sc, oy + (zmax_s - 39) * sc], fill=(200, 30, 30))
    for sw in plan['ports']['swivels']:
        sz = dk[sw['deck']]['floor'] + 10
        d.ellipse([padL + (sw['x'] - 2) * sc, oy + (zmax_s - sz - 2) * sc, padL + (sw['x'] + 2) * sc, oy + (zmax_s - sz + 2) * sc], fill=(220, 120, 0))

    # 輔佐長櫓（後腰兩舷）
    for ox_oar in plan['oars']['ports_x']:
        d.line([padL + ox_oar * sc, oy + (zmax_s - 40) * sc, padL + (ox_oar - 26) * sc, oy + (zmax_s - 18) * sc], fill=(30, 130, 90), width=3)

    # 雙桅與竹篾硬篷
    ms = plan['masts']
    mast_info = {}
    for mk in ('fore', 'main'):
        m = ms[mk]
        ang = math.radians(m['rake_deg'])
        x0_m, z0_m = m['x'], m['heel_z']
        x1_m, z1_m = x0_m + m['len'] * math.sin(ang), z0_m + m['len'] * math.cos(ang)
        d.line([padL + x0_m * sc, oy + (zmax_s - z0_m) * sc, padL + x1_m * sc, oy + (zmax_s - z1_m) * sc], fill=(110, 65, 25), width=4)

        gf = ms['yards'][f'{mk}_gaff']
        bm = ms['yards'][f'{mk}_boom']
        zg, zb_y = gf['z'], bm['z']
        xg_c = x0_m + (zg - z0_m) * math.tan(ang)
        xb_c = x0_m + (zb_y - z0_m) * math.tan(ang)
        ga = math.radians(gf['angle_deg'])
        p0 = (xg_c + gf['fore_len'] * math.cos(ga), zg + gf['fore_len'] * math.sin(ga))
        p1 = (xg_c - gf['aft_len'] * math.cos(ga), zg - gf['aft_len'] * math.sin(ga))
        p2 = (xb_c - bm['aft_len'], zb_y)
        p3 = (xb_c + bm['fore_len'], zb_y)
        poly = [(padL + px * sc, oy + (zmax_s - pz) * sc) for px, pz in (p0, p1, p2, p3)]
        d.polygon(poly, outline=(120, 90, 50), fill=(242, 232, 206))
        d.line([poly[0], poly[1]], fill=(90, 55, 20), width=3)
        d.line([poly[2], poly[3]], fill=(90, 55, 20), width=3)
        nb = ms['battens'][mk]
        for bi in range(1, nb):
            t = bi / nb
            bx0 = p3[0] + t * (p0[0] - p3[0])
            bz0 = p3[1] + t * (p0[1] - p3[1])
            bx1 = p2[0] + t * (p1[0] - p2[0])
            bz1 = p2[1] + t * (p1[1] - p2[1])
            d.line([padL + bx0 * sc, oy + (zmax_s - bz0) * sc, padL + bx1 * sc, oy + (zmax_s - bz1) * sc], fill=(150, 115, 70), width=1)
        area = 0.5 * (gf['len'] * 0.1 + bm['len'] * 0.1) * ((zg - zb_y) * 0.1)
        mast_info[mk] = {'top_x': round(x1_m, 1), 'top_z': round(z1_m, 1), 'sail_area_m2': round(area, 1), 'battens': nb}

    # ② 平面配置
    oy2 = oy + side_h + 48
    d.text((padL, oy2 - 24), '② 平面配置（8 道隔艙、兩舷 8×4l＋艏艉 4×pierrier 砲位、2 支輔佐長櫓、雙桅）', fill=(0, 0, 0), font=f14)
    yc_y = oy2 + (SY // 2) * sc
    d.line([padL, yc_y, padL + SX * sc, yc_y], fill=(160, 160, 160))
    pts_p = [(padL + x * sc, yc_y + float(L.Bs(x + 0.5, L.top_z(x + 0.5))) * sc) for x in range(60, 325)]
    pts_s = [(padL + x * sc, yc_y - float(L.Bs(x + 0.5, L.top_z(x + 0.5))) * sc) for x in reversed(range(60, 325))]
    d.polygon(pts_p + pts_s, outline=(120, 70, 20), fill=(238, 226, 200))
    for bx in plan['bulkheads']['x']:
        hb = float(L.Bs(bx + 0.5, dk['main']['floor']))
        d.line([padL + bx * sc, yc_y - hb * sc, padL + bx * sc, yc_y + hb * sc], fill=(80, 80, 80), width=2)
    for gx in plan['ports']['gun']['x']:
        for sgn in (-1, 1):
            yg = yc_y + sgn * 25 * sc
            d.rectangle([padL + (gx - 4) * sc, yg - 2 * sc, padL + (gx + 4) * sc, yg + 2 * sc], fill=(200, 30, 30))
    for sw in plan['ports']['swivels']:
        hb = float(L.Bs(sw['x'] + 0.5, dk[sw['deck']]['floor'])) - 2
        for sgn in (-1, 1):
            yg = yc_y + sgn * hb * sc
            d.ellipse([padL + (sw['x'] - 2) * sc, yg - 2 * sc, padL + (sw['x'] + 2) * sc, yg + 2 * sc], fill=(220, 120, 0))
    for ox_oar in plan['oars']['ports_x']:
        hb = float(L.Bs(ox_oar + 0.5, dk['main']['floor']))
        for sgn in (-1, 1):
            d.line([padL + ox_oar * sc, yc_y + sgn * (hb - 4) * sc, padL + (ox_oar - 12) * sc, yc_y + sgn * (hb + 24) * sc], fill=(30, 130, 90), width=3)
    for mk in ('fore', 'main'):
        m = ms[mk]
        r = m['r'][0] * sc
        d.ellipse([padL + m['x'] * sc - r, yc_y - r, padL + m['x'] * sc + r, yc_y + r], fill=(90, 50, 15))

    tot_area = round(sum(v['sail_area_m2'] for v in mast_info.values()), 1)
    d.text((padL, H - 45), f"雙桅硬篷總帆面積約 {tot_area} m²（頭 {mast_info['fore']['sail_area_m2']} / 大 {mast_info['main']['sail_area_m2']}）| 12 門砲（8×long4 + 4×pierrier）| 輔佐長櫓", fill=(40, 30, 20), font=f14)
    out_png = os.path.join(design, 'sheet02_layout_v1.png')
    im.save(out_png)
    out_json = {
        'masts': mast_info,
        'total_sail_area_m2': tot_area,
        'bulkheads_count': len(plan['bulkheads']['x']),
        'guns': {'long4': 8, 'pierrier': 4, 'total_guns': 12},
        'oars': {'side_sweeps': 2, 'ports_x': plan['oars']['ports_x']},
        'sheet02_sha256': hashlib.sha256(open(out_png, 'rb').read()).hexdigest(),
    }
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    print(json.dumps(out_json, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

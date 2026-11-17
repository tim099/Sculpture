# 沙船 新圖紙 02（TASK-1313 步驟 3）：配置總圖 sheet02_layout_v1.png ＋ verify_layout.json
#   展示：三層甲板（底艙／主甲板／尾樓）、8 道水密隔艙、兩舷披水板位置、6 門砲位（long4 + pierrier）、三桅硬篷（頭／大／尾）
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
    side_h = 220 * sc
    plan_h = SY * sc
    H = padT + side_h + 60 + plan_h + 120
    im = Image.new('RGB', (W, H), (250, 246, 236))
    d = ImageDraw.Draw(im)
    f20, f14, f12 = font(20), font(14), font(12)
    d.text((padL, 14), '沙船（1666 中式沿海沙船）配置總圖 v1：甲板、水密隔艙、披水板、輕砲、三桅硬篷', fill=(25, 20, 15), font=f20)

    # ① 側面全船配置（含三桅硬篷）
    oy = padT
    zmax_s = 215
    # 船殼輪廓
    xs_hull = np.arange(36, 248)
    pts_top = [(padL + x * sc, oy + (zmax_s - float(L.top_z(x + 0.5))) * sc) for x in xs_hull]
    pts_bot = [(padL + x * sc, oy + (zmax_s - float(L.zb(x + 0.5))) * sc) for x in reversed(xs_hull) if x >= L.xa - 12 and x <= L.xf + 2]
    d.polygon(pts_top + pts_bot, outline=(120, 70, 20), fill=(235, 222, 196))

    # 水線
    wl = plan['waterline']['z']
    yw = oy + (zmax_s - wl) * sc
    d.line([padL + 20 * sc, yw, padL + 265 * sc, yw], fill=(30, 100, 200), width=2)
    d.text((padL + 268 * sc, yw - 8), f'DWL z={wl}', fill=(30, 100, 200), font=f12)

    # 甲板線
    dk = plan['decks']
    # 底艙
    d.line([padL + dk['hold']['x0'] * sc, oy + (zmax_s - dk['hold']['z']) * sc,
            padL + dk['hold']['x1'] * sc, oy + (zmax_s - dk['hold']['z']) * sc], fill=(160, 50, 20), width=2)
    # 主甲板（含前段微翹）
    mx0, mx1 = dk['main']['x_aft'], dk['main']['x_fwd']
    rx0, rf = dk['main']['rise_x0'], dk['main']['rise_fwd']
    mz0 = dk['main']['z_low']
    d.line([padL + mx0 * sc, oy + (zmax_s - mz0) * sc, padL + rx0 * sc, oy + (zmax_s - mz0) * sc,
            padL + mx1 * sc, oy + (zmax_s - (mz0 + rf)) * sc], fill=(180, 0, 0), width=2)
    # 尾樓
    d.line([padL + dk['poop']['x0'] * sc, oy + (zmax_s - dk['poop']['z']) * sc,
            padL + dk['poop']['x1'] * sc, oy + (zmax_s - dk['poop']['z']) * sc], fill=(180, 0, 0), width=2)

    # 水密隔艙
    for bx in plan['bulkheads']['x']:
        zt_b = float(L.top_z(bx + 0.5))
        zm_b = mz0 if bx <= rx0 else mz0 + rf * (bx - rx0) / max(1, mx1 - rx0)
        d.line([padL + bx * sc, oy + (zmax_s - float(L.zb(bx + 0.5))) * sc,
                padL + bx * sc, oy + (zmax_s - zm_b) * sc], fill=(90, 90, 90), width=2)

    # 披水板
    lb = plan['leeboards']
    d.rectangle([padL + lb['x0'] * sc, oy + (zmax_s - lb['z_top']) * sc,
                 padL + lb['x1'] * sc, oy + (zmax_s - lb['z_bot']) * sc], outline=(100, 50, 0), fill=(185, 130, 70))

    # 砲位
    for gx in plan['ports']['gun']['x']:
        d.rectangle([padL + (gx - 3) * sc, oy + (zmax_s - 31) * sc, padL + (gx + 3) * sc, oy + (zmax_s - 27) * sc], fill=(200, 30, 30))
    for sw in plan['ports']['swivels']:
        sz = 48 if sw['deck'] == 'poop' else 36
        d.ellipse([padL + (sw['x'] - 2) * sc, oy + (zmax_s - sz - 2) * sc, padL + (sw['x'] + 2) * sc, oy + (zmax_s - sz + 2) * sc], fill=(220, 120, 0))

    # 三桅與硬篷
    ms = plan['masts']
    mast_info = {}
    for mk in ('fore', 'main', 'mizzen'):
        m = ms[mk]
        ang = math.radians(m['rake_deg'])
        x0_m, z0_m = m['x'], m['heel_z']
        x1_m, z1_m = x0_m + m['len'] * math.sin(ang), z0_m + m['len'] * math.cos(ang)
        d.line([padL + x0_m * sc, oy + (zmax_s - z0_m) * sc, padL + x1_m * sc, oy + (zmax_s - z1_m) * sc], fill=(110, 65, 25), width=4)
        # 帆面預覽（gaff + boom）
        gf = ms['yards'][f'{mk}_gaff']
        bm = ms['yards'][f'{mk}_boom']
        # 簡化梯形硬篷輪廓
        zg, zb_y = gf['z'], bm['z']
        xg_c = x0_m + (zg - z0_m) * math.tan(ang)
        xb_c = x0_m + (zb_y - z0_m) * math.tan(ang)
        ga = math.radians(gf['angle_deg'])
        p0 = (xg_c + gf['len'] * 0.25 * math.cos(ga), zg + gf['len'] * 0.25 * math.sin(ga))
        p1 = (xg_c - gf['len'] * 0.75 * math.cos(ga), zg - gf['len'] * 0.75 * math.sin(ga))
        p2 = (xb_c - bm['len'] * 0.75, zb_y)
        p3 = (xb_c + bm['len'] * 0.25, zb_y)
        poly = [(padL + px * sc, oy + (zmax_s - pz) * sc) for px, pz in (p0, p1, p2, p3)]
        d.polygon(poly, outline=(120, 90, 50), fill=(242, 232, 206))
        d.line([poly[0], poly[1]], fill=(90, 55, 20), width=3)
        d.line([poly[2], poly[3]], fill=(90, 55, 20), width=3)
        area = 0.5 * (gf['len'] * 0.1 + bm['len'] * 0.1) * ((zg - zb_y) * 0.1)
        mast_info[mk] = {'top_z': round(z1_m, 1), 'sail_area_m2': round(area, 1)}

    # ② 平面配置（全船寬，x 軸對齊上方）
    oy2 = oy + side_h + 45
    d.text((padL, oy2 - 18), '② 平面配置（水密隔艙 8 道、兩舷披水板、4 磅砲 2 門＋迴旋砲 4 門、三桅）', fill=(0, 0, 0), font=f14)
    yc_y = oy2 + (SY // 2) * sc
    d.line([padL, yc_y, padL + SX * sc, yc_y], fill=(160, 160, 160))
    pts_p = [(padL + x * sc, yc_y + float(L.Bs(x + 0.5)) * sc) for x in range(36, 247)]
    pts_s = [(padL + x * sc, yc_y - float(L.Bs(x + 0.5)) * sc) for x in reversed(range(36, 247))]
    d.polygon(pts_p + pts_s, outline=(120, 70, 20), fill=(238, 226, 200))
    for bx in plan['bulkheads']['x']:
        hb = float(L.Bs(bx + 0.5))
        d.line([padL + bx * sc, yc_y - hb * sc, padL + bx * sc, yc_y + hb * sc], fill=(80, 80, 80), width=2)
    # 披水板兩舷外
    for sgn in (-1, 1):
        y_lb = yc_y + sgn * 30 * sc
        d.rectangle([padL + lb['x0'] * sc, y_lb - 2 * sc, padL + lb['x1'] * sc, y_lb + 2 * sc], fill=(160, 100, 40))
    # 砲位兩舷
    for gx in plan['ports']['gun']['x']:
        for sgn in (-1, 1):
            yg = yc_y + sgn * 22 * sc
            d.rectangle([padL + (gx - 3) * sc, yg - 2 * sc, padL + (gx + 3) * sc, yg + 2 * sc], fill=(200, 30, 30))
    for sw in plan['ports']['swivels']:
        hb = float(L.Bs(sw['x'] + 0.5)) - 1
        for sgn in (-1, 1):
            yg = yc_y + sgn * hb * sc
            d.ellipse([padL + (sw['x'] - 2) * sc, yg - 2 * sc, padL + (sw['x'] + 2) * sc, yg + 2 * sc], fill=(220, 120, 0))
    for mk in ('fore', 'main', 'mizzen'):
        m = ms[mk]
        r = m['r'][0] * sc
        d.ellipse([padL + m['x'] * sc - r, yc_y - r, padL + m['x'] * sc + r, yc_y + r], fill=(90, 50, 15))

    tot_area = round(sum(v['sail_area_m2'] for v in mast_info.values()), 1)
    d.text((padL, H - 40), f"三桅硬篷總帆面積約 {tot_area} m²（頭 {mast_info['fore']['sail_area_m2']} / 大 {mast_info['main']['sail_area_m2']} / 尾 {mast_info['mizzen']['sail_area_m2']}）| 6 門砲（2×long4 + 4×pierrier = 1,600 kg）", fill=(40, 30, 20), font=f14)
    out_png = os.path.join(design, 'sheet02_layout_v1.png')
    im.save(out_png)
    out_json = {
        'masts': mast_info,
        'total_sail_area_m2': tot_area,
        'bulkheads_count': len(plan['bulkheads']['x']) + 1,
        'guns': {'long4': 2, 'pierrier': 4, 'total_guns': 6, 'total_mass_kg': 1600},
        'sheet02_sha256': hashlib.sha256(open(out_png, 'rb').read()).hexdigest()
    }
    with open(os.path.join(design, 'verify_layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)
    print(json.dumps(out_json, ensure_ascii=False))


if __name__ == '__main__':
    main()

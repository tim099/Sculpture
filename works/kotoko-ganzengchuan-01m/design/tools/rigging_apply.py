# 福建趕繒船 步驟 8 索具、雙桅扇形竹篾硬帆、旗與貼圖、meta 與 ropecheck（TASK-1314）：
#   出處：kaguya-shachuan-01m/design/tools/rigging_apply.py（改寫為雙桅趕繒船，含 roach=0.05,0.16 ＋ battens=7/9 ＋ 明鄭軍旗）
import json
import math
import os
import re
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')

PERSONA = 'kotoko'
HULL = 'kotoko-ganzengchuan-01m'
ASM = HULL + '-assembly'


def cli(*args, ok=(0,)):
    cmd = ['senate', 'cmd', 'sculpture']
    for kv in args:
        cmd += ['--arg', kv]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit(f'✗ exit {r.returncode}：{" ".join(args)}')
    return out


def make_sail_tex(path, n_battens):
    h = (n_battens + 1) * 12
    im = Image.new('RGB', (128, h), '#dbc498')
    d = ImageDraw.Draw(im)
    for x in range(0, 128, 16):
        d.rectangle((x, 0, min(127, x + 7), h - 1), fill='#e2cca2')
        d.rectangle((min(127, x + 8), 0, min(127, x + 15), h - 1), fill='#d4bc8f')
    for x in range(0, 128, 16):
        d.line((x, 0, x, h - 1), fill='#c2a778', width=1)
    for y in range(h):
        ip = y % 12
        if ip <= 2 or ip >= 10:
            d.line((0, y, 127, y), fill='#bfa372')
    for m in range(1, n_battens + 1):
        y = m * 12
        d.line((0, y - 1, 127, y - 1), fill='#735b3b', width=1)
        d.line((0, y, 127, y), fill='#5e492e', width=1)
    d.rectangle((0, 0, 127, h - 1), outline='#644e32', width=2)
    im.save(path)


def main():
    design = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..'))
    works_root = os.path.dirname(os.path.dirname(design))
    sys.path.insert(0, os.path.join(design, 'tools'))
    from wio import export_list

    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    mp = json.load(open(os.path.join(design, 'masts_placement.json'), encoding='utf-8'))
    YC = int(plan['space']['yc'])

    # ── 1. 生成雙帆條紋布紋貼圖 ＋ 明鄭水師朱紅金邊軍旗／長旒貼圖 ──
    tex_dir = os.path.join(design, 'textures')
    os.makedirs(tex_dir, exist_ok=True)
    fore_tex = os.path.join(tex_dir, 'fore-junk-battens.png')
    main_tex = os.path.join(tex_dir, 'main-junk-battens.png')
    make_sail_tex(fore_tex, int(plan['masts']['battens']['fore']))
    make_sail_tex(main_tex, int(plan['masts']['battens']['main']))

    ens_png = os.path.join(tex_dir, 'ensign.png')
    im_e = Image.new('RGBA', (32, 20), (195, 32, 24, 255))
    de = ImageDraw.Draw(im_e)
    de.rectangle([0, 0, 31, 19], outline=(240, 196, 40, 255), width=2)
    de.polygon([(16, 4), (22, 10), (16, 16), (10, 10)], fill=(240, 196, 40, 255))
    de.ellipse([13, 7, 19, 13], fill=(255, 245, 210, 255))
    im_e.save(ens_png)

    pen_png = os.path.join(tex_dir, 'pennant.png')
    im_p = Image.new('RGBA', (40, 6), (200, 32, 24, 255))
    dp = ImageDraw.Draw(im_p)
    dp.line([0, 0, 39, 0], fill=(240, 196, 40, 255))
    dp.line([0, 5, 39, 5], fill=(240, 196, 40, 255))
    im_p.save(pen_png)

    # ── 2. 船尾旗桿子作品（停立於 x=62, y=96, z=68..98，貼齊 z=67 實船殼且避開 x<=60 陽台與翔龍牌飾）──
    w_staff = f'{HULL}-ensign-staff'
    if not os.path.exists(os.path.join(works_root, w_staff, 'work.json')):
        cli('op=work', 'sub=create', f'persona={PERSONA}', f'id={w_staff}', 'title=福建趕繒船 船尾旗桿（0.1 m）',
            f'parent_work={HULL}', 'size=3,3,32')
        cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={w_staff}', 'tags=sub', 'meters_per_voxel=0.1')
        p_staff = os.path.join(design, 'masks', 'masts', 'ensign_staff.vox.txt')
        with open(p_staff, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 福建趕繒船 步驟 8：船尾旗桿（局部 0..30 => 世界 z=68..98）x,y,z,color\n')
            for z in range(30):
                f.write(f'1,1,{z},104\n')
            f.write('1,1,30,212\n')
        p_staff_norm = p_staff.replace('\\', '/')
        cli('op=stampvox', f'persona={PERSONA}', f'work={w_staff}', f'voxels={p_staff_norm}',
            'at=0,0,0', 'expect_pixels=31')
    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w_staff}', 'name=flag-head', 'at=1,1,29', 'overwrite=1', 'note=步驟 8：國旗上角')
    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w_staff}', 'name=flag-foot', 'at=1,1,13', 'overwrite=1', 'note=步驟 8：國旗下角')
    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}', 'name=船尾旗桿', f'source_work={w_staff}',
        'at=61,95,68', 'note=步驟 8：船尾旗桿（與翔龍牌飾 0 重疊）')

    # ── 3. 量測實船殼外舷頂＆登記所有索具固定點 ──
    hull_pts = export_list(HULL, links='none')
    hull_occ = {(int(r[0]), int(r[1]), int(r[2])) for r in hull_pts}

    def hull_rail(x, sgn):
        ztop = max(z for (xx, y, z) in hull_occ if xx == x)
        ys = [y for (xx, y, zz) in hull_occ if xx == x and zz == ztop and ((y >= YC) if sgn > 0 else (y <= YC))]
        return (max(ys) if sgn > 0 else min(ys)), ztop

    hull_anchors = {'stay-bow': [321, YC, 57]}
    shroud_xs = {'fore': [265, 270, 275], 'main': [175, 181, 188]}
    for mk, xs in shroud_xs.items():
        for i, sx in enumerate(xs, 1):
            for s_lbl, sgn in (('S', 1), ('P', -1)):
                yv, zv = hull_rail(sx, sgn)
                hull_anchors[f'shroud-{mk}-{s_lbl}{i}'] = [sx, yv, zv]

    for mk, bx_s in (('fore', 218), ('main', 98)):
        for s_lbl, sgn in (('S', 1), ('P', -1)):
            yv, zv = hull_rail(bx_s, sgn)
            hull_anchors[f'belay-{mk}-{s_lbl}'] = [bx_s, yv - sgn, zv]

    for ak, pt in sorted(hull_anchors.items()):
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={HULL}', f'name={ak}',
            'at=%d,%d,%d' % tuple(pt), 'overwrite=1', 'note=步驟 8：船殼索具固定點')

    # 甲板前／中舵腳固定點（落在實心鋪板上）
    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={HULL}-deck-main', 'name=tack-main',
        f'at=204,{YC},34', 'overwrite=1', 'note=步驟 8：大帆 tack 固定點')
    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={HULL}-deck-fore', 'name=tack-fore',
        f'at=304,{YC},43', 'overwrite=1', 'note=步驟 8：頭帆 tack 固定點')

    # 頭桅下方 main-stay 撞擊固定點（z=50，位於 fore-lower 桁 z=60 下方不干涉轉帆）
    sp_f = plan['masts']['fore']
    x_ms = int(round(sp_f['x'] + (50 - sp_f['heel_z']) * math.tan(math.radians(sp_f['rake_deg']))))
    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={HULL}-mast-fore', 'name=mainstay-hit',
        f'at={x_ms},{YC},50', 'overwrite=1', 'note=步驟 8：大桅前支索固定點')

    # ── 4. 靜索（shrouds 12 ＋ stays 2）與橫繩組（ratlines，climb=0）──
    def add_rope(name, r_from, r_to, slack=1.0, thick=0.5, color='#2b2620', group='standing/shrouds', meta=None):
        cli('op=work', 'sub=rope', f'persona={PERSONA}', f'work={ASM}', f'name={name}',
            f'from={r_from}', f'to={r_to}', f'slack={slack}', f'thickness={thick}',
            f'color={color}', f'group={group}', 'overwrite=1', 'note=步驟 8')
        if meta:
            cli('op=work', 'sub=meta', f'persona={PERSONA}', 'part=rope', f'work={ASM}', f'name={name}',
                'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))

    for mk, th in (('fore', 0.6), ('main', 0.75)):
        for i in range(1, len(shroud_xs[mk]) + 1):
            for s_lbl in ('S', 'P'):
                add_rope(f'{mk}-shroud-{s_lbl}{i}', f'桅-{mk}/hounds', f'船殼/shroud-{mk}-{s_lbl}{i}',
                         slack=1.0, thick=th, color='#2b2620', group='standing/shrouds')

    add_rope('fore-stay', '桅-fore/hounds', '船殼/stay-bow', slack=1.0006, thick=0.85, color='#2b2620', group='standing/stays')
    # 大桅頂連向頭桅頂之高空聯桅支索（triatic stay：z=223->174，高於 fore-junk 峰頂 z=176 逾 2.1 m 不貫穿帆面）
    add_rope('main-stay', '桅-main/hounds', '桅-fore/top', slack=1.0006, thick=0.95, color='#2b2620', group='standing/stays')

    for mk in ('fore', 'main'):
        n_sh = len(shroud_xs[mk])
        for s_lbl in ('S', 'P'):
            cli('op=work', 'sub=ratlines', f'persona={PERSONA}', f'work={ASM}',
                f'name={mk}-lower-{s_lbl}',
                f'rope_a={mk}-shroud-{s_lbl}{n_sh}',
                f'rope_b={mk}-shroud-{s_lbl}1',
                'step=4', 'start=7', 'stop=16', 'min_span=5', 'thickness=0.3',
                'color=#2b2620', 'group=ratlines/lower', 'climb=0', 'overwrite=1')

    # ── 5. 雙桅扇形竹篾硬篷（fore-junk N=7 set=2, main-junk N=9 set=1）＋ 帆自己的繩 ──
    SAILS = [
        ('fore', 'fore-junk', 7, 32, 2, fore_tex, '甲板-fore/tack-fore'),
        ('main', 'main-junk', 9, 40, 1, main_tex, '甲板-main/tack-main'),
    ]
    for mk, sname, nb, res, sset, tex_p, tack_to in SAILS:
        yu = f'桅-{mk}/yard-{mk}-upper'
        yl = f'桅-{mk}/yard-{mk}-lower'
        corners = f'model:{yu}/fore|model:{yu}/aft|model:{yl}/aft|model:{yl}/fore'
        cli('op=work', 'sub=sail', f'persona={PERSONA}', f'work={ASM}', f'name={sname}',
            f'corners={corners}', 'corner_names=throat|peak|clew|tack', 'bind=0,2',
            f'res={res}', 'color=#ffffff', 'fullness=1.05',
            'texture=' + tex_p.replace('\\', '/'), 'overwrite=1', 'note=步驟 8：中式竹篾扇形硬篷')
        meta_s = {'kind': 'sail', 'mast': mk, 'sail': 'gaff', 'set': sset, 'battens': nb, 'roach': '0.05,0.16'}
        cli('op=work', 'sub=meta', f'persona={PERSONA}', 'part=sail', f'work={ASM}', f'name={sname}',
            'meta=' + json.dumps(meta_s, ensure_ascii=False, separators=(',', ':')))

        for s_lbl in ('S', 'P'):
            add_rope(f'{sname}-sheet-{s_lbl}', f'sail:{sname}/clew', f'船殼/belay-{mk}-{s_lbl}',
                     slack=1.04, thick=0.45, color='#a08458', group='running/sheets',
                     meta={'kind': 'sheet', 'sail': sname})
        add_rope(f'{sname}-tack', f'sail:{sname}/tack', tack_to,
                 slack=1.0, thick=0.45, color='#a08458', group='running/tacks',
                 meta={'kind': 'tack', 'sail': sname})
        add_rope(f'{sname}-halyard', f'桅-{mk}/cap', f'model:{yu}/sling',
                 slack=1.02, thick=0.45, color='#a08458', group='running/halyards',
                 meta={'kind': 'halyard', 'sail': sname})

    # ── 6. 旗（ensign + pennant，皆附貼圖 UV 與 nation=ming）──
    cli('op=work', 'sub=sail', f'persona={PERSONA}', f'work={ASM}', 'name=ensign',
        f'corners=船尾旗桿/flag-head|38.0,{YC}.5,97.0|38.0,{YC}.5,81.0|船尾旗桿/flag-foot',
        'free=1,2', 'bind=3', 'fullness=1.04', 'texture=' + ens_png.replace('\\', '/'),
        'overwrite=1', 'note=步驟 8：明鄭船尾戰旗')
    cli('op=work', 'sub=meta', f'persona={PERSONA}', 'part=sail', f'work={ASM}', 'name=ensign',
        'meta=' + json.dumps({'kind': 'flag', 'flag': 'ensign', 'nation': 'ming'}, ensure_ascii=False, separators=(',', ':')))

    mhx, mhy, mhz = mp['masts']['main']['anchors']['top']
    cli('op=work', 'sub=sail', f'persona={PERSONA}', f'work={ASM}', 'name=pennant',
        f'corners={mhx}.5,{mhy}.5,{mhz}.0|{mhx-38}.5,{mhy}.5,{mhz-1}.0|{mhx}.5,{mhy}.5,{mhz-5}.5',
        'free=1', 'bind=2', 'fullness=1.04', 'texture=' + pen_png.replace('\\', '/'),
        'overwrite=1', 'note=步驟 8：大桅長旒')
    cli('op=work', 'sub=meta', f'persona={PERSONA}', 'part=sail', f'work={ASM}', 'name=pennant',
        'meta=' + json.dumps({'kind': 'flag', 'flag': 'pennant', 'mast': 'main', 'nation': 'ming'}, ensure_ascii=False, separators=(',', ':')))

    # ── 7. 預設風向與檢查 ──
    cli('op=work', 'sub=wind', f'persona={PERSONA}', f'work={ASM}', 'wind=-4.5,-1.5,0', 'sail_seconds=3')
    rc = cli('op=work', 'sub=ropecheck', f'persona={PERSONA}', f'work={ASM}')
    print(rc)
    print('=== sails ===')
    print(cli('op=work', 'sub=sails', f'work={ASM}'))
    print('=== stats (links=all) ===')
    print(cli('op=stats', f'work={ASM}', 'links=all', 'structure=1'))


if __name__ == '__main__':
    main()

# 出處：kaguya-guineaman-01m/design/draft_rigging.py ＋ tools/rigging_apply.py
# 沙船 步驟 8（TASK-1313）：靜索、橫繩組（ratlines）、三面中式硬篷帆（gaff+boom）、帆索（sheet/tack/halyard）、旗與貼圖、meta 與 ropecheck
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.abspath(design))
HULL = 'kaguya-shachuan-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
YP = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
YC = plan['space']['yc']


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


# ── 1. 生成明鄭／東寧朱紅金邊軍旗貼圖（ensign.png, pennant.png）──
tex_dir = os.path.join(design, 'textures')
os.makedirs(tex_dir, exist_ok=True)
ens_png = os.path.join(tex_dir, 'ensign.png')
im_e = Image.new('RGBA', (32, 20), (195, 32, 24, 255))
de = ImageDraw.Draw(im_e)
de.rectangle([0, 0, 31, 19], outline=(240, 196, 40, 255), width=2)
# 中央簡潔菱形金紋（代表「鄭」／明字旗徽意象）
de.polygon([(16, 4), (22, 10), (16, 16), (10, 10)], fill=(240, 196, 40, 255))
im_e.save(ens_png)

pen_png = os.path.join(tex_dir, 'pennant.png')
im_p = Image.new('RGBA', (40, 6), (200, 32, 24, 255))
dp = ImageDraw.Draw(im_p)
dp.line([0, 0, 39, 0], fill=(240, 196, 40, 255))
dp.line([0, 5, 39, 5], fill=(240, 196, 40, 255))
im_p.save(pen_png)

# ── 2. 船尾旗桿子作品（掛國旗用，不標 deco=1）──
sw = f'{HULL}-ensign-staff'
if not os.path.exists(os.path.join(WORKS, sw, 'work.json')):
    cli('op=work', 'sub=create', 'persona=kaguya', 'work=' + sw, 'title=沙船 船尾旗桿（0.1 m）', 'parent_work=' + HULL, 'size=4,4,40', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=kaguya', 'work=' + sw, 'meters_per_voxel=0.1')
    staff_txt = os.path.join(design, 'masks', 'masts', 'ensign_staff.vox.txt')
    with open(staff_txt, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 船尾旗桿\n')
        for z in range(0, 36):
            f.write(f'1,1,{z},136\n')
        f.write('1,1,36,248\n')
    cli('op=stampvox', 'persona=kaguya', 'work=' + sw, 'voxels=' + staff_txt.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=37', 'share=0')
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + sw, 'name=flag-head', 'at=1,1,35', 'note=國旗上角')
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + sw, 'name=flag-foot', 'at=1,1,15', 'note=國旗下角')
cli('op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=船尾旗桿', 'source_work=' + sw, 'at=37,95,49', 'note=步驟 8：船尾旗桿', ok=(0, 2))

# ── 3. 船殼與桅的固定點 ──
# 量船殼上各處實際舷頂格，確定固定點踩在實心邊上
import numpy as np
from draft_decks import load_carved_hull
import lines as HL
from draft_lines import build as hull_build
L, _, S, x0, ylo = hull_build(plan, None)
H_col = load_carved_hull(design, x0, ylo, S.shape)

def hull_rail_y(x, side_sign):
    xi = x - x0
    z_top = int(round(L.top_z(x + 0.5))) - 1
    for zz in range(z_top, z_top - 4, -1):
        ys = np.nonzero(H_col[xi, :, zz] > 0)[0]
        if len(ys):
            y_val = int(ys.max() + ylo) if side_sign > 0 else int(ys.min() + ylo)
            return y_val, zz
    raise ValueError(f'no rail at x={x}')

hull_anchors = {}
# shrouds 固定點（頭桅 3、大桅 3、尾桅 2）
shroud_xs = {
    'fore': [214, 219, 224],
    'main': [144, 150, 156],
    'mizzen': [51, 57],
}
for mk, xs in shroud_xs.items():
    for i, x in enumerate(xs, 1):
        for s_lbl, sgn in (('S', 1), ('P', -1)):
            yv, zv = hull_rail_y(x, sgn)
            hull_anchors[f'shroud-{mk}-{s_lbl}{i}'] = [x, yv, zv]

# stays 固定點
yb_s, zb_s = hull_rail_y(243, 1)
hull_anchors['stay-bow'] = [243, YC, zb_s]

# sheets / tacks 固定點
for mk, bx_s, bx_t in (('fore', 184, 236), ('main', 88, 174), ('mizzen', 40, 74)):
    for s_lbl, sgn in (('S', 1), ('P', -1)):
        ys_v, zs_v = hull_rail_y(bx_s, sgn)
        hull_anchors[f'belay-{mk}-{s_lbl}'] = [bx_s, ys_v - sgn, zs_v]
    hull_anchors[f'tack-{mk}'] = [bx_t, YC, 28 if mk == 'fore' else (23 if mk == 'main' else 41)]

for ak, (ax, ay, az) in sorted(hull_anchors.items()):
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + HULL, 'name=' + ak, 'at=%d,%d,%d' % (ax, ay, az), 'overwrite=1', 'note=步驟 8：索具固定點')

# 桅領口固定點（略低於桅頂，給 shrouds / stay / halyard 用）
for mk, dz_col in (('fore', 10), ('main', 14), ('mizzen', 8)):
    mv = YP['masts'][mk]
    ang = math.radians(mv['rake_deg'])
    zc = mv['z_end'] - dz_col
    xc = int(round(mv['x0'] + (zc - mv['z_start']) * math.tan(ang)))
    cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + f'{HULL}-mast-{mk}', 'name=collar', 'at=%d,%d,%d' % (xc, YC, zc), 'overwrite=1', 'note=步驟 8：桅領固定點')
    if mk == 'fore':
        z_stay = 40
        x_stay = int(round(mv['x0'] + (z_stay - mv['z_start']) * math.tan(ang)))
        cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + f'{HULL}-mast-{mk}', 'name=mainstay-hit', 'at=%d,%d,%d' % (x_stay, YC, z_stay), 'overwrite=1', 'note=大桅支索綁點')
    if mk == 'main':
        z_mstay = 64
        x_mstay = int(round(mv['x0'] + (z_mstay - mv['z_start']) * math.tan(ang)))
        cli('op=work', 'sub=anchor', 'persona=kaguya', 'work=' + f'{HULL}-mast-{mk}', 'name=mizzenstay-hit', 'at=%d,%d,%d' % (x_mstay, YC, z_mstay), 'overwrite=1', 'note=尾桅支索綁點')

# ── 4. 靜索（shrouds + stays）與橫繩組（ratlines）──
def add_rope(name, r_from, r_to, slack=1.0, thick=0.5, color='#2b2620', group='standing/shrouds', meta=None):
    args = ['op=work', 'sub=rope', 'persona=kaguya', 'work=' + ASM, 'name=' + name,
            'from=' + r_from, 'to=' + r_to, f'slack={slack}', f'thickness={thick}',
            'color=' + color, 'group=' + group, 'overwrite=1', 'note=步驟 8']
    cli(*args)
    if meta:
        cli('op=work', 'sub=meta', 'persona=kaguya', 'part=rope', 'work=' + ASM, 'name=' + name, 'meta=' + json.dumps(meta, ensure_ascii=False))

for mk, th_sh in (('fore', 0.6), ('main', 0.7), ('mizzen', 0.5)):
    for i in range(1, len(shroud_xs[mk]) + 1):
        for s_lbl in ('S', 'P'):
            add_rope(f'{mk}-shroud-{s_lbl}{i}', f'桅-{mk}/collar', f'船殼/shroud-{mk}-{s_lbl}{i}',
                     slack=1.0, thick=th_sh, color='#2b2620', group='standing/shrouds')

add_rope('fore-stay', '桅-fore/collar', '船殼/stay-bow', slack=1.0005, thick=0.8, color='#2b2620', group='standing/stays')
add_rope('main-stay', '桅-main/collar', '桅-fore/mainstay-hit', slack=1.0005, thick=0.9, color='#2b2620', group='standing/stays')
add_rope('mizzen-stay', '桅-mizzen/collar', '桅-main/mizzenstay-hit', slack=1.0005, thick=0.7, color='#2b2620', group='standing/stays')

# 橫繩組 ratlines（rope_a 用最前 x 最大、rope_b 用最後 x 最小；climb=0 沙船無歐式桅樓）
for mk in ('fore', 'main'):
    n_sh = len(shroud_xs[mk])
    for s_lbl in ('S', 'P'):
        cli('op=work', 'sub=ratlines', 'persona=kaguya', 'work=' + ASM,
            'name=' + f'{mk}-lower-{s_lbl}',
            'rope_a=' + f'{mk}-shroud-{s_lbl}{n_sh}',
            'rope_b=' + f'{mk}-shroud-{s_lbl}1',
            'step=4', 'start=7', 'stop=16', 'min_span=5', 'thickness=0.3', 'color=#2b2620',
            'group=ratlines/lower', 'climb=0', 'overwrite=1')

# ── 5. 三面中式硬篷帆（fore-junk, main-junk, mizzen-junk）與帆自己的繩 ──
SAIL_SET = {'fore': 1, 'main': 2, 'mizzen': 3}
for mk in ('fore', 'main', 'mizzen'):
    sname = f'{mk}-junk'
    yg = f'桅-{mk}/yard-{mk}-gaff'
    yb = f'桅-{mk}/yard-{mk}-boom'
    corners = f'model:{yg}/fore|model:{yg}/aft|model:{yb}/aft|model:{yb}/fore'
    cli('op=work', 'sub=sail', 'persona=kaguya', 'work=' + ASM, 'name=' + sname,
        'corners=' + corners, 'corner_names=throat|peak|clew|tack', 'bind=0,2',
        'color=#e8dcc2', 'fullness=1.05', 'overwrite=1', 'note=步驟 8：中式竹篾硬篷')
    cli('op=work', 'sub=meta', 'persona=kaguya', 'part=sail', 'work=' + ASM, 'name=' + sname,
        'meta=' + json.dumps({'kind': 'sail', 'mast': mk, 'sail': 'gaff', 'set': SAIL_SET[mk]}, ensure_ascii=False))

    # 帆自己的繩（kind=sheet/tack/halyard, sail=<sname>）
    for s_lbl in ('S', 'P'):
        add_rope(f'{sname}-sheet-{s_lbl}', f'sail:{sname}/clew', f'船殼/belay-{mk}-{s_lbl}',
                 slack=1.04, thick=0.4, color='#a08458', group='running/sheets',
                 meta={'kind': 'sheet', 'sail': sname})
    add_rope(f'{sname}-tack', f'sail:{sname}/tack', f'船殼/tack-{mk}',
             slack=1.0, thick=0.45, color='#a08458', group='running/tacks',
             meta={'kind': 'tack', 'sail': sname})
    add_rope(f'{sname}-halyard', f'桅-{mk}/head', f'model:{yg}/sling',
             slack=1.02, thick=0.4, color='#a08458', group='running/halyards',
             meta={'kind': 'halyard', 'sail': sname})

# ── 6. 旗（ensign + pennant，附 PNG 貼圖與 nation）──
cli('op=work', 'sub=sail', 'persona=kaguya', 'work=' + ASM, 'name=ensign',
    'corners=船尾旗桿/flag-head|12.0,96.5,84.0|12.0,96.5,64.0|船尾旗桿/flag-foot',
    'free=1,2', 'bind=3', 'fullness=1.04', 'texture=' + ens_png.replace('\\', '/'), 'note=步驟 8：明鄭船尾戰旗')
cli('op=work', 'sub=meta', 'persona=kaguya', 'part=sail', 'work=' + ASM, 'name=ensign',
    'meta=' + json.dumps({'kind': 'flag', 'flag': 'ensign', 'nation': 'ming'}, ensure_ascii=False))

mhx, mhy, mhz = YP['masts']['main']['anchors']['head']
cli('op=work', 'sub=sail', 'persona=kaguya', 'work=' + ASM, 'name=pennant',
    f'corners={mhx}.5,{mhy}.5,{mhz}.0|{mhx-36}.5,{mhy}.5,{mhz-1}.0|{mhx}.5,{mhy}.5,{mhz-5}.0',
    'free=1', 'bind=2', 'fullness=1.04', 'texture=' + pen_png.replace('\\', '/'), 'note=步驟 8：大桅長旗')
cli('op=work', 'sub=meta', 'persona=kaguya', 'part=sail', 'work=' + ASM, 'name=pennant',
    'meta=' + json.dumps({'kind': 'flag', 'flag': 'pennant', 'mast': 'main', 'nation': 'ming'}, ensure_ascii=False))

# ── 7. 預設風向與 ropecheck ──
cli('op=work', 'sub=wind', 'persona=kaguya', 'work=' + ASM, 'wind=-4.5,-1.5,0', 'sail_seconds=3')
print(cli('op=work', 'sub=ropecheck', 'persona=kaguya', 'work=' + ASM))

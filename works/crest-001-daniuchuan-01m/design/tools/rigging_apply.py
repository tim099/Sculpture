# 步驟 8：硬骨帆貼圖與明鄭戰旗、旗桿、靜索、橫繩梯、3 面竹篾硬帆（set=1/2/3, roach=0.16,0.05）與動索
import json, math, os, re, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
TEX = os.path.join(DESIGN, 'textures')
sys.path.insert(0, HERE)
from wio import cli, PERSONA, HULL, ASM

sys.stdout.reconfigure(encoding='utf-8')


def make_textures():
    os.makedirs(TEX, exist_ok=True)
    # 1) 三面硬骨竹篾帆貼圖（每邊 <= 128；竹蓆底色＋竹縫細線＋明鄭朱邊滾條）
    for mk, n_bat in (('fore', 7), ('main', 9), ('mizzen', 6)):
        h = (n_bat + 1) * 12  # 84 / 96 / 120 <= 128
        im = Image.new('RGBA', (128, h), (206, 178, 132, 255))
        d = ImageDraw.Draw(im)
        for y in range(0, h, 4):
            d.line((0, y, 127, y), fill=(194, 166, 120, 255))
        for x in range(3, 128, 8):
            d.line((x, 0, x, h - 1), fill=(192, 162, 114, 255))
        for m in range(1, n_bat + 1):
            d.line((0, m * 12, 127, m * 12), fill=(138, 108, 68, 255), width=2)
        d.rectangle((0, 0, 127, h - 1), outline=(146, 36, 28, 255), width=3)
        im.save(os.path.join(TEX, f'{mk}-junk-battens.png'))

    # 2) 明鄭戰艦主帥大旗（ensign：朱底金鋸齒邊＋金色八角團紋＋「明」徽記）
    ew, eh = 96, 64
    ens = Image.new('RGBA', (ew, eh), (186, 26, 22, 255))
    ed = ImageDraw.Draw(ens)
    # 金色鋸齒邊
    ed.rectangle((0, 0, ew - 1, eh - 1), outline=(228, 184, 40, 255), width=3)
    for y in range(4, eh - 4, 8):
        ed.polygon([(ew - 1, y), (ew - 10, y + 4), (ew - 1, y + 8)], fill=(0, 0, 0, 0))
    for x in range(6, ew - 8, 10):
        ed.line((x, 3, x + 4, 7), fill=(228, 184, 40, 255), width=2)
        ed.line((x, eh - 4, x + 4, eh - 8), fill=(228, 184, 40, 255), width=2)
    # 中央金日金圈與「明」像素印記
    cx, cy = 44, eh // 2
    ed.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), outline=(232, 190, 48, 255), width=3, fill=(140, 18, 18, 255))
    # 左「日」右「月」簡潔 pixel glyph
    ed.rectangle((cx - 10, cy - 7, cx - 3, cy + 7), outline=(240, 204, 64, 255), width=2)
    ed.line((cx - 9, cy, cx - 4, cy), fill=(240, 204, 64, 255), width=2)
    ed.line((cx + 2, cy - 8, cx + 2, cy + 8), fill=(240, 204, 64, 255), width=2)
    ed.line((cx + 2, cy - 8, cx + 9, cy - 8), fill=(240, 204, 64, 255), width=2)
    ed.line((cx + 9, cy - 8, cx + 9, cy + 8), fill=(240, 204, 64, 255), width=2)
    ed.line((cx + 2, cy - 1, cx + 8, cy - 1), fill=(240, 204, 64, 255), width=2)
    ed.line((cx + 2, cy + 4, cx + 8, cy + 4), fill=(240, 204, 64, 255), width=2)
    ens.save(os.path.join(TEX, 'ensign.png'))

    # 3) 明鄭檣頂燕尾長幡（pennant：128×28 漸縮雙燕尾紅金幡）
    pw, ph = 128, 28
    pen = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pen)
    pd.polygon([(0, 0), (127, 8), (104, 14), (127, 20), (0, 27)], fill=(192, 28, 24, 255))
    pd.line([(0, 1), (126, 9), (103, 14), (126, 19), (0, 26)], fill=(230, 188, 46, 255), width=2)
    pd.ellipse((10, 6, 24, 21), fill=(230, 188, 46, 255))
    pen.save(os.path.join(TEX, 'pennant.png'))


def build_ensign_staff():
    # 後方斜伸低矮艉旗桿（x=31..53, y=128, z=107..114，全段低於尾帆下桁 z=116.5 且在尾帆後面，轉帆零碰撞）
    w = f'{HULL}-ensign-staff'
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', f'persona={PERSONA}', f'work={w}', 'title=明鄭一號大鳥船 艉斜旗桿（0.1 m）',
            f'parent_work={HULL}', 'size=512,256,512', 'tags=sub')
        cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={w}', 'meters_per_voxel=0.1')
        pts = []
        for i in range(23):
            t = i / 22.0
            x = int(round(53 - 22 * t))
            z = int(round(107 + 7 * t))
            col = 212 if i >= 21 else (192 if i % 6 == 0 else 104)
            pts.append((x, 128, z, col))
        vox_p = os.path.join(DESIGN, 'masks', 'masts', 'ensign-staff.vox.txt')
        with open(vox_p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 艉斜旗桿\n')
            for x, y, z, c in sorted(set(pts)):
                f.write(f'{x},{y},{z},{c}\n')
        cli('op=stampvox', f'persona={PERSONA}', f'work={w}',
            'voxels=' + os.path.abspath(vox_p).replace('\\', '/'), 'at=0,0,0',
            f'expect_pixels={len(set(pts))}', 'draft=0', 'share=0')
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}', 'name=base', 'at=53,128,107')
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}', 'name=peak', 'at=31,128,114')
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}', 'name=hoist-lo', 'at=39,128,111')
    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}',
        'name=旗桿', f'source_work={w}', 'at=0,0,0', 'note=步驟 8：艉斜旗桿', ok=(0, 2))


def main():
    make_textures()
    build_ensign_staff()

    sys.path.insert(0, DESIGN)
    import lines as HL
    spec = json.load(open(os.path.join(DESIGN, 'masts_placement.json'), encoding='utf-8'))
    plan = json.load(open(os.path.join(DESIGN, 'plan.json'), encoding='utf-8'))
    L = HL.Lines(plan)
    YC = int(plan['space']['yc'])

    def outer_rail_pt(xw, z_off=-2):
        zt = int(round(float(L.top_z(xw + 0.5)))) + z_off
        hb = float(L.hb(xw + 0.5, zt + 0.5))
        yo = int(math.floor(hb)) + 1
        return zt, YC + yo, YC - yo

    hull_anchors = {}
    for i, xw in enumerate((376, 368, 360, 352), 1):
        z, ys, yp = outer_rail_pt(xw, -1)
        hull_anchors[f'ch-fore-S{i}'] = (xw, ys, z)
        hull_anchors[f'ch-fore-P{i}'] = (xw, yp, z)
    for i, xw in enumerate((244, 236, 228, 220, 212), 1):
        z, ys, yp = outer_rail_pt(xw, -1)
        hull_anchors[f'ch-main-S{i}'] = (xw, ys, z)
        hull_anchors[f'ch-main-P{i}'] = (xw, yp, z)
    for i, xw in enumerate((100, 95, 90), 1):
        z, ys, yp = outer_rail_pt(xw, -1)
        hull_anchors[f'ch-miz-S{i}'] = (xw, ys, z)
        hull_anchors[f'ch-miz-P{i}'] = (xw, yp, z)
    zb, ybs, ybp = outer_rail_pt(132, -1)
    hull_anchors['bkst-main-S'] = (132, ybs, zb)
    hull_anchors['bkst-main-P'] = (132, ybp, zb)

    hull_anchors.update({
        # 上戰棚內側繩梯落腳點（舷牆內側至少 2 格於甲板上）
        'climb-fore-S': (364, 165, 70), 'climb-fore-P': (364, 91, 70),
        'climb-main-S': (228, 168, 70), 'climb-main-P': (228, 88, 70),
        # sheet 與 brace 甲板繫纜栓（沿舷內側甲板）
        'bitt-fore-aft-S': (306, 162, 70), 'bitt-fore-aft-P': (306, 94, 70),
        'bitt-fore-fwd-S': (406, 152, 70), 'bitt-fore-fwd-P': (406, 104, 70),
        'bitt-main-aft-S': (146, 166, 70), 'bitt-main-aft-P': (146, 90, 70),
        'bitt-main-fwd-S': (280, 168, 70), 'bitt-main-fwd-P': (280, 88, 70),
        'bitt-miz-aft-S':  (62, 148, 92),  'bitt-miz-aft-P':  (62, 108, 92),
        'bitt-miz-fwd-S':  (118, 160, 92), 'bitt-miz-fwd-P':  (118, 96, 92),
    })
    for an_k, (x, y, z) in hull_anchors.items():
        cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={ASM}', f'name={an_k}', f'at={x},{y},{z}', 'note=步驟 8：索具固定點')

    def add_rope(name, frm, to, slack=1.0, thick=0.5, color='#2b2620', group=None, meta=None):
        args = ['op=work', 'sub=rope', f'persona={PERSONA}', f'work={ASM}',
                f'name={name}', f'from={frm}', f'to={to}',
                f'slack={slack}', f'thickness={thick}', f'color={color}']
        if group:
            args.append(f'group={group}')
        cli(*args, ok=(0, 2))
        if meta:
            cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={ASM}',
                'part=rope', f'name={name}',
                'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))

    # ── 1. 靜索（shrouds＋triatic stay＋主桅/尾桅不穿帆支索）──
    for mk, prefix, cnt, mast_link, hound_anc, side_meta_k in (
        ('fore', 'ch-fore', 4, '前桅', '前桅/hound', 'fore'),
        ('main', 'ch-main', 5, '主桅', '主桅/hound', 'main'),
        ('mizzen', 'ch-miz', 3, '尾桅', '尾桅/hound', 'mizzen'),
    ):
        for sd in ('S', 'P'):
            for i in range(1, cnt + 1):
                add_rope(f'{mk}-shroud-{sd}{i}', f'{prefix}-{sd}{i}', hound_anc,
                         slack=1.0, thick=0.65, color='#2b2620', group=f'standing/{mk}',
                         meta={'kind': 'shroud'})

    # 橫繩梯組（ratlines：fore 與 main 加 climb=1；mizzen 不加 climb）
    for mk, cnt, grp, has_climb in (
        ('fore', 4, 'ratlines/fore', True),
        ('main', 5, 'ratlines/main', True),
        ('mizzen', 3, 'ratlines/mizzen', False),
    ):
        for sd in ('S', 'P'):
            rname = f'{mk}-lower-{sd}'
            args = ['op=work', 'sub=ratlines', f'persona={PERSONA}', f'work={ASM}',
                    f'name={rname}', f'rope_a={mk}-shroud-{sd}1', f'rope_b={mk}-shroud-{sd}{cnt}',
                    'step=4', 'start=7', 'stop=14', 'min_span=5', 'thickness=0.3', 'color=#2b2620',
                    f'group={grp}']
            if has_climb:
                args += ['climb=1', f'foot=climb-{mk}-{sd}']
            cli(*args, ok=(0, 2))

    # 桅頂縱向牽索（triatic stays 嚴格高於各帆頂緣，不穿任何帆面）
    add_rope('stay-fore-main', '前桅/cap', '主桅/cap', slack=1.0006, thick=0.75, color='#2b2620', group='standing/stays', meta={'kind': 'stay'})
    add_rope('stay-fore-bow-S', '前桅/cap', '438,146,89', slack=1.0006, thick=0.65, color='#2b2620', group='standing/stays', meta={'kind': 'stay'})
    add_rope('stay-fore-bow-P', '前桅/cap', '438,110,89', slack=1.0006, thick=0.65, color='#2b2620', group='standing/stays', meta={'kind': 'stay'})
    add_rope('stay-main-aft-S', '主桅/cap', 'bkst-main-S', slack=1.0, thick=0.65, color='#2b2620', group='standing/stays', meta={'kind': 'backstay'})
    add_rope('stay-main-aft-P', '主桅/cap', 'bkst-main-P', slack=1.0, thick=0.65, color='#2b2620', group='standing/stays', meta={'kind': 'backstay'})
    add_rope('stay-miz-aft-S', '尾桅/cap', '58,154,96', slack=1.0, thick=0.5, color='#2b2620', group='standing/stays', meta={'kind': 'backstay'})
    add_rope('stay-miz-aft-P', '尾桅/cap', '58,102,96', slack=1.0, thick=0.5, color='#2b2620', group='standing/stays', meta={'kind': 'backstay'})

    # ── 2. 三面竹篾硬帆（bind=0,2 綁定上下桁 earing；meta 含 set=1/2/3, battens=N, roach=0.16,0.05）──
    for mk, sp in spec['placements'].items():
        lk = sp['mast_name']
        sname = sp['sail']
        n_bat = int(sp['battens'])
        s_set = int(sp['set'])
        up_p = f'model:{lk}/yard-upper/'
        lo_p = f'model:{lk}/yard-lower/'
        tex_p = os.path.abspath(os.path.join(TEX, f'{mk}-junk-battens.png')).replace('\\', '/')
        cli('op=work', 'sub=sail', f'persona={PERSONA}', f'work={ASM}',
            f'name={sname}',
            f'corners={up_p}earing-aft|{up_p}earing-fore|{lo_p}earing-fore|{lo_p}earing-aft',
            'corner_names=peak|throat|tack|clew',
            'bind=0,2',
            'color=#ffffff',
            'fullness=1.025',
            f'res={max(24, (n_bat + 1) * 4)}',
            f'texture={tex_p}',
            'overwrite=1',
            'note=步驟 8：明鄭竹篾硬帆（Ship_Battens）')
        cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={ASM}',
            'part=sail', f'name={sname}',
            'meta=' + json.dumps({
                'kind': 'sail', 'mast': mk, 'sail': 'course',
                'set': s_set, 'battens': n_bat, 'roach': '0.16,0.05'
            }, ensure_ascii=False, separators=(',', ':')))

        # 每面帆自己的動索（halyard, lifts, sheets, tacks — 標 sail=<sname>）
        add_rope(f'{sname}-halyard', f'{lk}/hound', f'{up_p}sling', slack=1.02, thick=0.45, color='#a08458',
                 group=f'running/{mk}', meta={'kind': 'halyard', 'sail': sname})
        add_rope(f'{sname}-lift-aft', f'{lk}/top', f'{up_p}arm-P', slack=1.03, thick=0.35, color='#a08458',
                 group=f'running/{mk}', meta={'kind': 'lift', 'sail': sname})
        add_rope(f'{sname}-lift-fore', f'{lk}/top', f'{up_p}arm-S', slack=1.03, thick=0.35, color='#a08458',
                 group=f'running/{mk}', meta={'kind': 'lift', 'sail': sname})
        tag_short = 'miz' if mk == 'mizzen' else mk
        for sd in ('S', 'P'):
            add_rope(f'{sname}-sheet-{sd}', f'sail:{sname}/clew', f'bitt-{tag_short}-aft-{sd}', slack=1.06, thick=0.4, color='#a08458',
                     group=f'running/{mk}', meta={'kind': 'sheet', 'sail': sname})
            add_rope(f'{sname}-tack-{sd}', f'sail:{sname}/tack', f'bitt-{tag_short}-fwd-{sd}', slack=1.06, thick=0.4, color='#a08458',
                     group=f'running/{mk}', meta={'kind': 'tack', 'sail': sname})

    # ── 3. 明鄭戰旗（ensign + 2× masthead pennants）──
    # 艉大旗（bind=3 ⇒ 角0->角3 貼在旗桿 peak..hoist-lo，向後下垂 24×16 格）
    cli('op=work', 'sub=sail', f'persona={PERSONA}', f'work={ASM}',
        'name=ensign',
        'corners=旗桿/peak|10,128,118|10,128,104|旗桿/hoist-lo',
        'bind=3', 'free=1,2', 'color=#ffffff', 'fullness=1.06', 'res=16',
        'texture=' + os.path.abspath(os.path.join(TEX, 'ensign.png')).replace('\\', '/'),
        'overwrite=1', 'note=步驟 8：明鄭國姓戰旗 (flag=ensign)')
    cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={ASM}',
        'part=sail', 'name=ensign',
        'meta={"kind":"flag","flag":"ensign","nation":"mingzheng"}')

    for f_name, lk_name, x_top, z_top, x_fly in (
        ('pennant-main', '主桅', 235, 320, 212),
        ('pennant-fore', '前桅', 395, 249, 376),
    ):
        cli('op=work', 'sub=sail', f'persona={PERSONA}', f'work={ASM}',
            f'name={f_name}',
            f'corners={lk_name}/cap|{x_fly},128,{z_top}|{x_fly},128,{z_top - 6}|{lk_name}/top',
            'bind=3', 'free=1,2', 'color=#ffffff', 'fullness=1.05', 'res=12',
            'texture=' + os.path.abspath(os.path.join(TEX, 'pennant.png')).replace('\\', '/'),
            'overwrite=1', f'note=步驟 8：{lk_name}長幡')
        cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={ASM}',
            'part=sail', f'name={f_name}',
            'meta={"kind":"flag","flag":"pennant"}')

    # 設定預設風場（左後舷側風使硬帆與戰旗飽滿展開）
    cli('op=work', 'sub=wind', f'persona={PERSONA}', f'work={ASM}', 'wind=4.5,-1.5,0', 'sail_seconds=3')

    print(cli('op=work', 'sub=sails', f'work={ASM}'))
    print(cli('op=work', 'sub=ropecheck', f'persona={PERSONA}', f'work={ASM}'))


if __name__ == '__main__':
    main()

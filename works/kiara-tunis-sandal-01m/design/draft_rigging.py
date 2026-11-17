# 步驟 8 索具、拉丁帆與鄂圖曼突尼斯旗幟（kiara-tunis-sandal-01m-assembly）：
#   - 登記船殼、甲板、主桅固定點
#   - 建立 9 條繩索：standing/shrouds (×4)、running/halyards (×2)、running/tacks (×1)、running/sheets (×2)
#   - 建立主拉丁帆 `lateen` (bind=0, set=1, #f2ead8)＋桅頂長旗 `pennant`＋桁尖突尼斯國旗 `ensign` (nation=ottoman, 附 PNG 貼圖)
#   - 檢核帆面靜態包絡線與船殼／甲板／坐板零穿插，並產出帆裝三段張帆表
#   用法：python -I -X utf8 draft_rigging.py [--apply] [--probe=clew_z=-15]
import sys, os, json, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_ASM = 'kiara-tunis-sandal-01m-assembly'
WORK_HULL = 'kiara-tunis-sandal-01m'
WORK_DECK = 'kiara-tunis-sandal-01m-deck-main'
WORK_MAST = 'kiara-tunis-sandal-01m-mast'
WORK_FLAGSTAFF = 'kiara-tunis-sandal-01m-flagstaff'


def load_vox(path):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros((136, 101, 110), bool)
    if len(a):
        G[a[:, 0], a[:, 1], a[:, 2]] = True
    return G


def check_sail_clearance(occ, p0, p1, p2):
    hits = 0
    min_clear_z = 999.0
    for i in range(25):
        u = i / 24.0
        for j in range(25 - i):
            v = j / 24.0
            w = 1.0 - u - v
            p = w * p0 + u * p1 + v * p2
            ix, iy, iz = int(round(p[0])), int(round(p[1])), int(round(p[2]))
            if 0 <= ix < 136 and 0 <= iy < 101 and 0 <= iz < 110:
                if occ[ix, iy, iz]:
                    hits += 1
                zs = np.where(occ[ix, iy, :30])[0]
                if len(zs):
                    min_clear_z = min(min_clear_z, float(p[2]) - float(zs.max()))
    return hits, round(min_clear_z, 2)


def run_cli(args):
    cmd = ['senate', 'cmd', 'sculpture'] + args
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise SystemExit(f'CLI fail {" ".join(args)}:\n{r.stdout}\n{r.stderr}')
    return r.stdout


def main():
    apply_mode = '--apply' in sys.argv[1:]
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)

    H = load_vox(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'))
    occ = H | D

    # 三角帆 `lateen` 靜態三頂點（對應步驟 7 帆桁實測值）
    p_tack = np.array([108.03, 48.5, 21.11])
    p_head = np.array([44.19, 48.5, 64.16])
    p_clew = np.array([36.0, 50.5, 19.5 + probe.get('clew_z', 0.0)])

    sail_hits, min_z_clear = check_sail_clearance(occ, p_tack, p_head, p_clew)

    # 計算帆三角面積 (m²) 與三段張帆表
    area_v2 = float(0.5 * np.linalg.norm(np.cross(p_head - p_tack, p_clew - p_tack)))
    area_m2 = round(area_v2 * 0.01, 2)
    stages = {
        '0_全收': [],
        '1_收帆': ['lateen'],
        '2_戰鬥帆': ['lateen'],
        '3_滿帆': ['lateen'],
        '常駐旗幟': ['pennant (flag=pennant, nation=ottoman)', 'ensign (flag=ensign, nation=ottoman)'],
    }

    R = {
        'sail_area_m2': area_m2,
        'sail_static_occ_hits': sail_hits,
        'sail_min_clearance_above_hull_deck_cells': min_z_clear,
        'stages': stages,
    }
    if probe:
        print(json.dumps({'probe': probe, **R}, ensure_ascii=False))
        return

    with open(os.path.join(HERE, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    print('STATIC_CHECK:', json.dumps(R, ensure_ascii=False))

    if not apply_mode:
        return

    # 0. 產生與落格船尾右舷旗桿 kiara-tunis-sandal-01m-flagstaff (19, 54, z=11..24)
    os.makedirs(os.path.join(HERE, 'masks', 'rig'), exist_ok=True)
    fs_vox = os.path.join(HERE, 'masks', 'rig', 'flagstaff.vox.txt')
    with open(fs_vox, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 突尼斯湖轉運艇 Sandal 船尾右舷旗桿（draft_rigging.py）x,y,z,color\n')
        for z in range(11, 25):
            c = 68 if z == 11 else (208 if z == 24 else 136)
            f.write(f'19,54,{z},{c}\n')
    # 清空舊格後以 stamp_lists 落格（確保幂等）
    flag_mask = np.loadtxt(fs_vox, delimiter=',', comments='#', dtype=int)
    assert all(not occ[r[0], r[1], r[2]] for r in flag_mask), '旗桿與船殼/甲板重疊!'
    chk = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', f'work={WORK_FLAGSTAFF}'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    if 'total_voxels = 0' in chk.stdout:
        subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'),
                        WORK_FLAGSTAFF, '0', fs_vox], check=True)
    run_cli(['--arg', 'op=work', '--arg', 'sub=link', '--arg', 'persona=kiara',
             '--arg', f'work={WORK_ASM}', '--arg', 'name=旗桿',
             '--arg', f'source_work={WORK_FLAGSTAFF}', '--arg', 'at=0,0,0', '--arg', 'overwrite=1'])

    # 1. 登記各部件固定點
    anchors = [
        (WORK_HULL, 'shroud-P1', '76,39,8',  '步驟 8 左舷前靜索綁點'),
        (WORK_HULL, 'shroud-P2', '72,38,8',  '步驟 8 左舷後靜索綁點'),
        (WORK_HULL, 'shroud-S1', '76,61,8',  '步驟 8 右舷前靜索綁點'),
        (WORK_HULL, 'shroud-S2', '72,62,8',  '步驟 8 右舷後靜索綁點'),
        (WORK_HULL, 'belay-sheet-P', '30,42,9', '步驟 8 左舷主帆腳索栓'),
        (WORK_HULL, 'belay-sheet-S', '30,58,9', '步驟 8 右舷主帆腳索栓'),
        (WORK_DECK, 'tack-main', '104,50,4', '步驟 8 艏甲板帆前角索眼'),
        (WORK_MAST, 'hound', '81,50,51', '步驟 8 主桅靜索掛耳'),
        (WORK_MAST, 'calcet-halyard', '80,50,53', '步驟 8 拉丁桅首滑輪塊'),
        (WORK_MAST, 'mast-foot-belay', '81,50,6', '步驟 8 桅腳升降索繫點'),
        (WORK_MAST, 'truck', '81,50,56', '步驟 8 桅頂旗鈕'),
        (WORK_FLAGSTAFF, 'top', '19,54,23', '步驟 8 國旗上升索綁點'),
        (WORK_FLAGSTAFF, 'bot', '19,54,15', '步驟 8 國旗下升索綁點'),
    ]
    for w, name, at, note in anchors:
        run_cli(['--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=kiara',
                 '--arg', f'work={w}', '--arg', f'name={name}', '--arg', f'at={at}',
                 '--arg', f'note={note}', '--arg', 'overwrite=1'])
    print('Anchors registered:', len(anchors))

    # 2. 建立帆與旗（先清同名舊帆以保冪等：lateen / pennant / ensign）
    for old_s in ('lateen', 'pennant', 'ensign'):
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=unsail',
                        '--arg', 'persona=kiara', '--arg', f'work={WORK_ASM}', '--arg', f'name={old_s}'],
                       capture_output=True)
    tex_ens = os.path.join(HERE, 'textures', 'ensign.png').replace('\\', '/')
    tex_pen = os.path.join(HERE, 'textures', 'pennant.png').replace('\\', '/')
    sails = [
        ('lateen', 'model:桅-main/yard/fore|model:桅-main/yard/peak|36.0,50.5,19.5',
         'tack|head|clew', '2', '0', '20', '1.05', '#f2ead8', None,
         {'kind': 'sail', 'mast': 'main', 'sail': 'gaff', 'set': 1}),
        ('pennant', '81.5,50.5,56.5|66.5,50.5,56.0|81.5,50.5,53.5',
         'head|fly|foot', '1', '2', '12', '1.04', '#b60000', tex_pen,
         {'kind': 'flag', 'flag': 'pennant', 'mast': 'main', 'nation': 'ottoman'}),
        ('ensign', '旗桿/top|7.5,54.5,23.5|7.5,54.5,15.5|旗桿/bot',
         'head|fly-top|fly-foot|foot', '1,2', '3', '10', '1.04', '#b60000', tex_ens,
         {'kind': 'flag', 'flag': 'ensign', 'nation': 'ottoman'}),
    ]
    for name, corners, cnames, free, bind, res, full, color, tex, meta in sails:
        args = ['--arg', 'op=work', '--arg', 'sub=sail', '--arg', 'persona=kiara',
                '--arg', f'work={WORK_ASM}', '--arg', f'name={name}',
                '--arg', f'corners={corners}', '--arg', f'corner_names={cnames}',
                '--arg', f'free={free}', '--arg', f'bind={bind}',
                '--arg', f'res={res}', '--arg', f'fullness={full}', '--arg', f'color={color}']
        if tex:
            args += ['--arg', f'texture={tex}']
        run_cli(args)
        run_cli(['--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'persona=kiara',
                 '--arg', f'work={WORK_ASM}', '--arg', 'part=sail', '--arg', f'name={name}',
                 '--arg', 'meta=' + json.dumps(meta, ensure_ascii=False)])
    print('Sails & flags created:', len(sails))

    # 3. 建立 9 條繩索並寫 meta
    ropes = [
        ('shroud-P1', '桅-main/hound', '船殼/shroud-P1', '1.0', '0.4', '#2b2620', 'standing/shrouds', {'kind': 'shroud'}),
        ('shroud-P2', '桅-main/hound', '船殼/shroud-P2', '1.0', '0.4', '#2b2620', 'standing/shrouds', {'kind': 'shroud'}),
        ('shroud-S1', '桅-main/hound', '船殼/shroud-S1', '1.0', '0.4', '#2b2620', 'standing/shrouds', {'kind': 'shroud'}),
        ('shroud-S2', '桅-main/hound', '船殼/shroud-S2', '1.0', '0.4', '#2b2620', 'standing/shrouds', {'kind': 'shroud'}),
        ('main.halyard', '桅-main/calcet-halyard', 'model:桅-main/yard/sling', '1.0', '0.4', '#a08458', 'running/halyards', {'kind': 'halyard'}),
        ('main.halyard-fall', '桅-main/calcet-halyard', '桅-main/mast-foot-belay', '1.02', '0.35', '#a08458', 'running/halyards', {'kind': 'halyard'}),
        ('lateen.tack', 'sail:lateen/tack', '甲板-main/tack-main', '1.02', '0.35', '#a08458', 'running/tacks', {'kind': 'tack', 'sail': 'lateen'}),
        ('lateen.sheet-P', 'sail:lateen/clew', '船殼/belay-sheet-P', '1.03', '0.35', '#a08458', 'running/sheets', {'kind': 'sheet', 'sail': 'lateen'}),
        ('lateen.sheet-S', 'sail:lateen/clew', '船殼/belay-sheet-S', '1.03', '0.35', '#a08458', 'running/sheets', {'kind': 'sheet', 'sail': 'lateen'}),
    ]
    for rname, rfrom, rto, slack, thick, color, grp, meta in ropes:
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=unrope',
                        '--arg', 'persona=kiara', '--arg', f'work={WORK_ASM}', '--arg', f'name={rname}'],
                       capture_output=True)
        run_cli(['--arg', 'op=work', '--arg', 'sub=rope', '--arg', 'persona=kiara',
                 '--arg', f'work={WORK_ASM}', '--arg', f'name={rname}',
                 '--arg', f'from={rfrom}', '--arg', f'to={rto}',
                 '--arg', f'slack={slack}', '--arg', f'thickness={thick}',
                 '--arg', f'color={color}', '--arg', f'group={grp}'])
        run_cli(['--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'persona=kiara',
                 '--arg', f'work={WORK_ASM}', '--arg', 'part=rope', '--arg', f'name={rname}',
                 '--arg', 'meta=' + json.dumps(meta, ensure_ascii=False)])
    print('Ropes created:', len(ropes))


if __name__ == '__main__':
    main()

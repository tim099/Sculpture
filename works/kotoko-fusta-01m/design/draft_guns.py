# 越嶺號 階段四（TASK-0761）：武器 ⇒ masks/guns/bombardella.vox.txt（新通用部件）、guns_placement.json、verify_guns.json
#   用法：python -I -X utf8 draft_guns.py [--probe=move=<模型名>:dx,dy,dz]   （probe ⇒ 那一件挪幾格，只印碰撞；⛔ 不寫檔）
#   · 船首中線：bombardella（鍛鐵箍砲＋後膛藥室，固定在一根挖槽的木床上、沒有砲車；R §4.2）—— 遊戲砲種表沒有 ⇒ 新通用部件、新砲種代碼（造船規格 §2.2）。
#   · 船首胸牆兩角：迴旋砲 pierrier（沿用皇家號 apex-one-reale-01m-gun-pierrier；Barbaro「bombardele」、zarabotane 一類的小砲）。
#   · 船首平台兩舷：弓手（沿用蓬特號 apex-one-punt-01m-gun-bow 的弓，換皮大砲；Kritovoulos §206 從甲板放箭）。
#   · 量：每件模型格心＋八角不落在船的實心（船殼、階段二、桅、帆桁模型）；砲口往砲軸方向 40 格（迴旋砲、弓 20 格）的射線不碰自己的船。
#   · 座標與擺法照皇家號 draft_guns.py（模型 rotate 繞 z、scale 0.5、pivot 是元件座標）。
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_lines as DL
import draft_upper as DU

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 360, 161, 230
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load_list(f):
    return np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def export(work):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode:
            raise SystemExit(r.stdout[-600:])
        return load_list(out)


# ── 新通用部件：bombardella（0.05 m；§4.1：x 中線 6、砲口朝 +y、z 0 ＝ 站的那一面）──
def bombardella():
    C_BED, C_IRON, C_HOOP = 104, 73, 36
    cells = {}
    ax, az = 6.5, 8.5
    for y in range(2, 42):                                       # 木床：挖槽的原木（2 m），前端收窄
        w = 4 if y < 36 else 3
        for x in range(6 - w, 7 + w):
            for z in range(0, 5):
                cells[(x, y, z)] = C_BED
    for y in range(5, 44):
        for x in range(2, 11):
            for z in range(3, 13):
                r = math.hypot(x + 0.5 - ax, z + 0.5 - az)
                if 16 <= y <= 43:                               # 砲管 1.4 m：外半徑 2.3、每 4 格一道箍 2.8；前 6 格挖出內膛
                    rr = 2.8 if (y - 16) % 4 == 0 or y == 43 else 2.3
                    if r <= rr and not (y >= 38 and r <= 0.75):
                        cells[(x, y, z)] = C_HOOP if rr > 2.5 else C_IRON
                elif 8 <= y <= 15:                              # 後膛藥室 mascolo
                    if r <= 2.4:
                        cells[(x, y, z)] = C_IRON
                elif 5 <= y <= 7:                               # 楔子 zeppa 頂住藥室
                    if abs(x + 0.5 - ax) <= 1.5 and 5 <= z <= 10:
                        cells[(x, y, z)] = C_BED
    for y in (10, 11, 12, 13):                                   # 藥室上的提把
        cells[(6, y, 12)] = C_HOOP
    for y in (10, 13):
        cells[(6, y, 11)] = C_HOOP
    for y in (19, 31, 40):                                       # 鐵箍把砲管綁在木床上
        for x in range(2, 11):
            for z in range(0, 12):
                edge = x in (2, 10) or z == 11
                if edge and (x, y, z) not in cells:
                    cells[(x, y, z)] = C_HOOP
    anchors = {'muzzle': (6, 43, 8), 'breech': (6, 16, 8), 'cascabel': (6, 8, 8)}
    assert anchors['muzzle'] not in cells and anchors['breech'] in cells
    return cells, anchors, (13, 46, 14)


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def place(Q, m):
    q = (np.asarray(Q, float) - np.array(m['pivot'], float)) * m['scale']
    if m.get('mirror') == 'y':
        q[:, 1] = -q[:, 1]
    return rotz(q, m['rotate'][2]) + np.array(m['at'], float)


def world():
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan)
    occ = np.zeros((SX, SY, SZ), bool)
    hc = DL.hull_cells(L, plan)
    occ[DL.X0:DL.X0 + hc.shape[0], :, :hc.shape[2]] |= hc > 0
    for f in [os.path.join(HERE, 'masks', 'upper', p + '.vox.txt') for p in DU.PARTS] + [os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt')]:
        a = load_list(f)
        occ[a[:, 0], a[:, 1], a[:, 2]] = True
    holes = load_list(os.path.join(HERE, 'masks', 'masts', 'deck_holes.vox.txt'))
    mast = load_list(os.path.join(HERE, 'masks', 'masts', 'mast.vox.txt'))
    occ[holes[:, 0], holes[:, 1], holes[:, 2]] = False
    occ[mast[:, 0], mast[:, 1], mast[:, 2]] = True
    yj = json.load(open(os.path.join(HERE, 'yards.json'), encoding='utf-8'))['main']
    ya = load_list(os.path.join(HERE, 'masks', 'yards', 'yard.vox.txt'))
    occ[ya[:, 0] + yj['offset'][0], ya[:, 1] + yj['offset'][1], ya[:, 2] + yj['offset'][2]] = True
    return plan, L, occ


def hits(occ, P):
    i = np.floor(P).astype(int)
    ok = (i[:, 0] >= 0) & (i[:, 0] < SX) & (i[:, 1] >= 0) & (i[:, 1] < SY) & (i[:, 2] >= 0) & (i[:, 2] < SZ)
    i = i[ok]
    return int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()) + int((~ok).sum())


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=', 1)
            probe[k] = v
    plan, L, occ = world()
    YC = L.YC
    tz = np.floor(L.sheer(np.arange(SX) + 0.5)).astype(int)
    bp = V(plan['layout']['bow_platform'])
    bomb, bomb_anc, bomb_size = bombardella()
    comps = {'bombardella': (np.array(list(bomb.keys())), bomb_anc),
             'pierrier': (export('apex-one-reale-01m-gun-pierrier'), {'muzzle': (5, 36, 9), 'breech': (5, 5, 9), 'pivot': (5, 18, 0)}),
             'bow': (export('apex-one-punt-01m-gun-bow'), {'muzzle': (5, 21, 26), 'breech': (5, 4, 26), 'pivot': (5, 20, 0)})}
    src = {'bombardella': 'kotoko-fusta-01m-gun-bombardella', 'pierrier': 'apex-one-reale-01m-gun-pierrier', 'bow': 'apex-one-punt-01m-gun-bow'}

    def hw_at(x, z):
        ys = np.where(occ[x, :, z])[0]
        return int(np.abs(ys - YC).max()) if len(ys) else -1
    floor_z = bp['top'] + 1                                        # 船首平台上站的那一層
    wall_top = bp['top'] + bp['wall_h']
    rows = []
    # 船首中線 bombardella：朝前（rotate −90），木床後端 pivot (6.5, 0, 0)；砲口伸出胸牆的中線砲口
    rows.append({'name': 'bow-gun', 'comp': 'bombardella',      # ⛔ 模型名不能跟砲種代碼同名：遊戲的 metaRebase 會把 gun=bombardella 改寫成路徑「甲板-bow/bombardella」（匯入檢查 v1 ✗）
                 'at': [296.0, YC + 0.5, floor_z], 'pivot': [6.5, 0, 0], 'rotate': [0, 0, -90], 'scale': 0.5, 'mirror': '',
                 'meta': {'kind': 'gun', 'gun': 'bombardella'}, 'ray': 40})
    # 迴旋砲：站在兩舷胸牆頂（x 305），朝舷外；轉 ±80°
    for side, sg in (('S', 1), ('P', -1)):
        x = 305
        hw = hw_at(x, wall_top)
        rows.append({'name': 'pierrier-' + side, 'comp': 'pierrier', 'at': [x + 0.5, YC + sg * hw + 0.5, wall_top + 1], 'pivot': [5.5, 18.5, 0],
                     'rotate': [0, 0, 0 if sg > 0 else 180], 'scale': 0.5, 'mirror': '',
                     'meta': {'kind': 'gun', 'gun': 'pierrier', 'mount': 'turret', 'arc': '-80,80', 'rate': 45}, 'ray': 20})
    # 弓手：船首平台兩舷（x 299、dy ±5），朝舷外；pivot 停 0、±45°
    for side, sg in (('S', 1), ('P', -1)):
        rows.append({'name': 'bow-' + side, 'comp': 'bow', 'at': [299.5, YC + sg * 5 + 0.5, floor_z], 'pivot': [5.5, 20.5, 0],
                     'rotate': [0, 0, 0 if sg > 0 else 180], 'scale': 0.5, 'mirror': '',
                     'meta': {'kind': 'gun', 'gun': 'bow', 'weapon': 'bow', 'ammo': 'bolt', 'mount': 'pivot', 'ports': '0,45,-45'}, 'ray': 20})
    if 'move' in probe:                                          # --probe=move=<模型名>:dx,dy,dz
        nm, dv = probe['move'].split(':')
        for r in rows:
            if r['name'] == nm:
                r['at'] = [a + float(b) for a, b in zip(r['at'], dv.split(','))]
    out = []
    for r in rows:
        Q, anc = comps[r['comp']]
        S = (Q[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
        Pw = place(S, r)
        mz = place(np.array([anc['muzzle']], float) + 0.5, r)[0]
        br = place(np.array([anc['breech']], float) + 0.5, r)[0]
        axv = (mz - br) / np.linalg.norm(mz - br)
        ray = np.array([mz + axv * (k * 0.5) for k in range(2, 2 * r['ray'])])
        foot = place(np.array([[anc['pivot'][0] + 0.5, anc['pivot'][1] + 0.5, -0.5]]), r)[0] if 'pivot' in anc else None
        rec = {'name': r['name'], 'hits': hits(occ, Pw), 'ray_hits': hits(occ, ray), 'muzzle': [round(float(v), 2) for v in mz],
               'axis': [round(float(v), 3) for v in axv]}
        if foot is not None:
            rec['foot_solid'] = bool(occ[tuple(np.floor(foot).astype(int))])
        out.append(rec)
    if probe:
        print(json.dumps({'probe': probe, 'rows': [{k: o[k] for k in ('name', 'hits', 'ray_hits')} for o in out]}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'guns'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'guns', 'bombardella.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# bombardella（15 世紀鍛鐵箍砲＋後膛藥室、固定在木床上；通用部件 0.05 m）x,y,z,color —— 元件自己的座標（x 中線 6、砲口 +y、z 0 ＝ 站的那一面）\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c) for k, c in sorted(bomb.items())))
    pl = {'note': 'draft_guns.py（造船規格 §2.2、§4）—— 模型都掛在 甲板-bow（kotoko-fusta-01m-bow）', 'host_work': 'kotoko-fusta-01m-bow',
          'components': {'bombardella': {'work': src['bombardella'], 'size': list(bomb_size), 'cells': len(bomb), 'anchors': {k: list(v) for k, v in bomb_anc.items()},
                                         'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest(), 'meters_per_voxel': 0.05}},
          'rows': [dict({k: v for k, v in r.items() if k not in ('ray',)}, source_work=src[r['comp']]) for r in rows]}
    with open(os.path.join(HERE, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pl, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': out, 'bombardella_cells': len(bomb)}, f, ensure_ascii=False, indent=1)
    print(json.dumps({'bombardella_cells': len(bomb), 'rows': out}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

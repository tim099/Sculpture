# 岩堡港 房屋放上地塊（TASK-0580 第四階段）：plan.json site.lots ＋ verify_houses.json ⇒ 每塊地一條關聯（配色、mirror、at）。
# 用法：python -I -X utf8 -B place_houses.py <design 資料夾> plan|link
#   plan：算位置、落 placements.json，並用房屋清單（masks/houses）＋地形／碼頭清單（masks/terrain）自己量：
#         房屋彼此、房屋跟地形碼頭 重疊幾格；房屋最底層（z 0）底下那一格是不是地形（不浮空）、房屋的格有沒有在地面以下（不埋）。
#   link：照 placements.json 下 work sub=link（已有同名 ⇒ 先 unlink 再放，讓重跑等於重放）。
#   · 屋身在地塊裡置中（x）；臨街那一側（y 小）貼地塊前緣；z ＝ 地塊的地面（site_height 的第一層空氣）。
#   · mirror=x：同一型左右翻，讓並排的同型看起來不一樣；酒館翻過來 ⇒ 吊招牌伸到 Grande Rue 上空（設計決定）。
import sys, os, json, subprocess
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
S = plan['site']
VH = json.load(open(os.path.join(D, 'verify_houses.json'), encoding='utf-8'))
VT = json.load(open(os.path.join(D, 'verify_terrain.json'), encoding='utf-8'))
H = np.load(os.path.join(D, 'site_height.npy')).astype(np.int32)
PARENT = 'summit-rocher-01m'
ROWS = {1: S['terraces'][0], 2: S['terraces'][-1]}
# 每塊地用哪一件（設計決定：同型相鄰不重複、翻面錯開）
PICK = {'Q1': ('C1', ''), 'Q2': ('A1', ''), 'Q3': ('B1', 'x'), 'Q4': ('A2', ''), 'Q5': ('A3', 'x'), 'Q6': ('A1', 'x'), 'Q7': ('D1', ''),
        'B1': ('A3', ''), 'B2': ('D2', ''), 'B3': ('A2', 'x'), 'B4': ('A1', ''), 'B5': ('D1', 'x'), 'B6': ('A3', 'x'), 'B7': ('A2', ''), 'B8': ('A1', 'x'), 'B9': ('C2', '')}


def rd(p):
    out = []
    for l in open(p, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            out.append(tuple(map(int, l.split(',')[:4])))
    return np.array(out, np.int32)


def placements():
    P = []
    for L in S['lots']:
        var, mir = PICK[L['id']]
        R = VH[var]; m = R['meta']; bx = R['bbox'][0]
        body0 = L['x0'] + (L['x1'] - L['x0'] - m['W']) // 2               # 屋身在地塊裡置中
        xoff = m['X0'] if not mir else bx - m['X0'] - m['W']               # 翻面後屋身在框裡從哪起
        t = ROWS[L['row']]
        z = int(H[(L['x0'] + L['x1']) // 2, t['y0'] + 1])
        P.append({'lot': L['id'], 'var': var, 'mirror': mir, 'at': [body0 - xoff, t['y0'], z], 'bbox': R['bbox'], 'name': '房屋-' + L['id']})
    return P


def key(a):
    return (a[:, 0].astype(np.int64) * 2048 + a[:, 1]) * 1024 + a[:, 2]


if step == 'plan':
    P = placements()
    hv = {}
    for p in P:
        a = rd(os.path.join(D, 'masks', 'houses', p['var'] + '.vox.txt'))
        if p['mirror'] == 'x':
            a[:, 0] = p['bbox'][0] - 1 - a[:, 0]
        a[:, :3] += np.array(p['at'], np.int32)
        hv[p['lot']] = a
    terr = rd(os.path.join(D, 'masks', 'terrain', 'terrain.vox.txt'))
    quay = rd(os.path.join(D, 'masks', 'terrain', 'quay.vox.txt')); quay[:, :3] += np.array(VT['quay']['origin'], np.int32)
    ground = set(key(terr).tolist()) | set(key(quay).tolist())
    over_ground, over_pair, float_, buried = {}, 0, {}, {}
    allk = {}
    for lot, a in hv.items():
        k = key(a)
        over_ground[lot] = int(np.isin(k, list(ground)).sum()) if len(ground) else 0
        for kk in k.tolist():
            if kk in allk:
                over_pair += 1
            allk[kk] = lot
        p = next(q for q in P if q['lot'] == lot)
        bot = a[a[:, 2] == p['at'][2]]                                     # 房屋最底層
        under = bot.copy(); under[:, 2] -= 1
        float_[lot] = int((~np.isin(key(under), list(ground))).sum())
        buried[lot] = int((a[:, 2] < H[a[:, 0], a[:, 1]]).sum())
    out = {'placements': P, 'overlap_with_ground': over_ground, 'overlap_between_houses': over_pair,
           'bottom_cells_not_on_ground': float_, 'cells_below_ground': buried, 'house_voxels': int(sum(len(a) for a in hv.values()))}
    with open(os.path.join(D, 'placements.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=1); fo.write('\n')
    for p in P:
        print(p['lot'], p['var'], p['mirror'] or '-', p['at'], '重疊地形', over_ground[p['lot']], '底層懸空', float_[p['lot']], '地面以下', buried[p['lot']])
    print('房屋彼此重疊', over_pair, '房屋總格數', out['house_voxels'])
elif step == 'link':
    P = json.load(open(os.path.join(D, 'placements.json'), encoding='utf-8'))['placements']
    for p in P:
        base = ['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'persona=summit', '--arg', 'work=' + PARENT, '--arg', 'name=' + p['name']]
        subprocess.run(base + ['--arg', 'sub=unlink'], capture_output=True)
        r = subprocess.run(base + ['--arg', 'sub=link', '--arg', 'source_work=%s-house-%s' % (PARENT, p['var'].lower()), '--arg', 'at=' + ','.join(map(str, p['at']))]
                           + (['--arg', 'mirror=' + p['mirror']] if p['mirror'] else []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(p['name'], 'rc', r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1] if r.returncode else '')
        if r.returncode:
            raise SystemExit((r.stdout + r.stderr)[-1500:])
else:
    raise SystemExit('步驟？ plan|link')

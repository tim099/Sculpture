# 岩堡港 街景落格與擺放（TASK-0580 第六階段）：照 street.json＋masks/street/ 下 CLI。
# 用法：python -I -X utf8 -B apply_street.py <design 資料夾> <步驟>
#   create   建小件子作品（0.05 m、parent＝組裝件、tags sub,prop）
#   stamp    小件落格（匯出現況跟清單比，多的刻掉、少的／色不同的補）
#   check    只讀引擎匯出：缺／多／色差；元件與封閉空腔
#   anchors  登記固定點（wick、mount、base）
#   verify   拿組裝件匯出的格子量擺放：地面高度（補 at.z）、撞到幾格、底下沒撐住幾格 ⇒ placements_resolved.json；⛔ 撞到或沒撐住 ⇒ exit 1
#   place    照 placements_resolved.json 在組裝件擺外部模型（同名已在 ⇒ 改變換）；meta 照小件
import sys, os, json, re, subprocess, math
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
ST = json.load(open(os.path.join(D, 'street.json'), encoding='utf-8'))
PARENT = 'summit-rocher-01m'
TMP = os.path.join(os.path.dirname(D), 'exports', 'street')
os.makedirs(TMP, exist_ok=True)
SC = ST['scale']
ok = bad = 0


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:6])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


def wid(p):
    return PARENT + '-' + p


def export(work, name):
    path = os.path.join(TMP, name + '.list.txt').replace('\\', '/')
    rc, _ = cli(['op=export', 'format=list', 'work=' + work, 'out=' + path])
    return path if rc == 0 else None


def world_cells(pl, pr):                                                  # 小件每一格（佔 [i, i+1)）取四個近角的點換到世界、取所在的世界格（連續座標：世界格 j 佔 [j, j+1)）
    P = ST['props'][pr]
    piv = P['pivot']
    th = math.radians(pl['rot'])
    co, si = math.cos(th), math.sin(th)
    out = set()
    for (x, y, z) in rd(os.path.join(D, 'masks', 'street', pr + '.vox.txt')):
        for ox in (0.05, 0.95):                                           # 一個小件格 ＝ 世界的半格；取近角的點，免得斜擺時漏掉
            for oy in (0.05, 0.95):
                u, v, w = (x + ox - piv[0]) * SC, (y + oy - piv[1]) * SC, (z + 0.5 - piv[2]) * SC
                X, Y, Z = pl['at'][0] + co * u - si * v, pl['at'][1] + si * u + co * v, pl['at'][2] + w
                out.add((int(math.floor(X)), int(math.floor(Y)), int(math.floor(Z))))
    return out


if step in ('create', 'stamp', 'check', 'anchors'):
    for p, P in ST['props'].items():
        mask = os.path.join(D, 'masks', 'street', p + '.vox.txt')
        if step == 'create':
            rc, _ = cli(['op=work', 'sub=show', 'work=' + wid(p)], quiet_fail=True)
            if rc:
                cli(['op=work', 'sub=create', 'persona=summit', 'id=' + wid(p), 'title=' + P['title'], 'size=' + ','.join(str(v) for v in P['bbox']), 'parent_work=' + PARENT])
            cli(['op=work', 'sub=update', 'persona=summit', 'work=' + wid(p), 'meters_per_voxel=' + str(ST['meters_per_voxel']), 'tags=sub,prop'])
            print('create', wid(p))
        elif step == 'stamp':
            path = export(wid(p), wid(p))
            cur, want = rd(path), rd(mask)
            carve = sorted((k, c) for k, c in cur.items() if k not in want)
            add = sorted((k, c) for k, c in want.items() if cur.get(k) != c)
            for nm, cells, args in (('carve', carve, ['op=carvevox']), ('stamp', add, ['op=stampvox', 'overwrite=1'])):
                if not cells:
                    continue
                fp = os.path.join(TMP, '%s.%s.vox.txt' % (wid(p), nm))
                with open(fp, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(''.join('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c) for k, c in cells))
                rc, out = cli(args + ['persona=summit', 'work=' + wid(p), 'voxels=' + fp.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'draft=0', 'share=0'])
                if rc:
                    raise SystemExit('停：%s %s 失敗' % (p, nm))
            print(p, '現況 %d → 清單 %d｜刻 %d、補／換色 %d' % (len(cur), len(want), len(carve), len(add)))
        elif step == 'check':
            cur, want = rd(export(wid(p), wid(p))), rd(mask)
            miss = sum(1 for k in want if k not in cur)
            extra = sum(1 for k in cur if k not in want)
            diff = sum(1 for k, c in want.items() if k in cur and cur[k] != c)
            rc, out = cli(['op=stats', 'work=' + wid(p), 'structure=1'])
            nums = dict(re.findall(r'🔢 (\w+) = (\S+)', out))
            print(p, '作品 %d 格｜缺 %d 多 %d 色差 %d｜元件 %s 空腔 %s' % (len(cur), miss, extra, diff, nums.get('components'), nums.get('cavities')))
        elif step == 'anchors':
            for an, at in P['anchors'].items():
                cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + wid(p), 'name=' + an, 'at=' + ','.join(str(v) for v in at), 'overwrite=1',
                     'note=' + {'wick': '火焰中心（遊戲在這裡放點光源）', 'mount': '背板的掛點（貼在柱子正面）', 'base': '底面中心'}[an]])
            print('anchors', p, list(P['anchors']))

elif step == 'verify':
    path = export(PARENT, PARENT)
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int64)
    key = lambda x, y, z: (x * 960 + y) * 600 + z
    occ = np.unique(key(a[:, 0], a[:, 1], a[:, 2]))
    has = lambda cells: np.isin(np.array([key(*c) for c in cells], dtype=np.int64), occ)
    top = {}
    for x, y, z in a[:, :3]:
        k = (int(x), int(y))
        if z + 1 > top.get(k, -1):
            top[k] = int(z) + 1
    res, fails, placed = [], 0, {}
    HT = {p: P['bbox'][2] * SC for p, P in ST['props'].items()}
    for pl in ST['placements']:
        pl = dict(pl)
        pr = pl['prop']
        if pl['at'][2] is None:                                           # 地面：底面中心那一欄的地面頂 ＝ 第一層空氣 g
            x0, y0 = int(math.floor(pl['at'][0])), int(math.floor(pl['at'][1]))
            g = top[(x0, y0)]
            pl['at'] = [pl['at'][0], pl['at'][1], g + pl.get('stack', 0) * HT[pr]]
        cells = world_cells(pl, pr)
        hit = int(has(cells).sum())
        if pr == 'lantern':
            unsup = 0                                                     # 燈籠掛在柱上：背板貼柱，撞到的格數應為 0
        elif pl.get('stack'):
            # 疊在別的小件上（模型、不是格子）⇒ 底下看 placed
            zmin = min(c[2] for c in cells)
            base = [(x, y, z - 1) for (x, y, z) in cells if z == zmin]
            unsup = sum(1 for c in base if c not in placed)
            unsup = 0 if unsup <= len(base) // 2 else unsup               # 疊在兩件中間：底面一半以上有撐就算穩（桶疊在兩個桶的溝上本來就懸一半）
        else:
            zmin = min(c[2] for c in cells)
            base = [(x, y, z - 1) for (x, y, z) in cells if z == zmin]
            unsup = int((~has(base)).sum())
        clash = sum(1 for c in cells if c in placed)
        for c in cells:
            placed[c] = pl['name']
        pl.update({'cells': len(cells), 'hit_voxels': hit, 'unsupported': unsup, 'clash_props': clash})
        bad_ = hit or clash or (unsup and unsup > 0)
        fails += 1 if bad_ else 0
        print(('✗ ' if bad_ else '· ') + '%s %s at %s rot %s｜佔 %d 格、撞格子 %d、撞別的小件 %d、底下沒撐 %s' % (pl['name'], pr, pl['at'], pl['rot'], len(cells), hit, clash, unsup))
        res.append(pl)
    with open(os.path.join(D, 'placements_resolved.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(res, fo, ensure_ascii=False, indent=1); fo.write('\n')
    print('verify：%d 個擺放、%d 個有問題' % (len(res), fails))
    if fails:
        raise SystemExit(1)

elif step == 'place':
    mj = os.path.join(os.path.dirname(D), 'models.json')
    have = {m['name']: m.get('work') for m in (json.load(open(mj, encoding='utf-8'))['models'] if os.path.exists(mj) else [])}
    for pl in json.load(open(os.path.join(D, 'placements_resolved.json'), encoding='utf-8')):
        P = ST['props'][pl['prop']]
        args = ['op=work', 'sub=model', 'persona=summit', 'work=' + PARENT, 'name=' + pl['name'],
                'pivot=' + ','.join(str(v) for v in P['pivot']), 'at=' + ','.join(str(round(v, 3)) for v in pl['at']), 'rotate=0,0,%s' % pl['rot']]
        if pl['name'] not in have:
            args.append('source_work=' + wid(pl['prop']))                 # 新的才給來源；已在 ⇒ 只改變換（給來源會被當成換來源擋下）
        elif have[pl['name']] != wid(pl['prop']):
            raise SystemExit('停：%s 現在的來源是 %s，不是 %s' % (pl['name'], have[pl['name']], wid(pl['prop'])))
        if P['meta']:
            args.append('meta=' + json.dumps(P['meta'], ensure_ascii=False))
        rc, out = cli(args)
        print(pl['name'], 'rc', rc)
else:
    raise SystemExit('步驟？ create|stamp|check|anchors|verify|place')
print(step, 'ok', ok, 'bad', bad)

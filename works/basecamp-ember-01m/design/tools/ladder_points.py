# 梯子給遊戲的固定點（ame 2026-10-13 tavern 23321：預備水手爬梯子補砲班；Tim：梯子位置在模型裡用 meta 標）
#   每座梯子 4 個固定點，登記在梯子子作品裡，名字 `<梯名>.<點>`；梯子所在的關聯 meta kind=ladders。
#     foot：下層甲板上、最低一階往下梯方向、站著等著爬的那一格
#     lo  ：最低那一階      hi：最高那一階
#     head：上層甲板上、最高一階往上梯方向、跨過艙口圍欄站穩的那一格
#   四個點都取「腳踩的那一格」＝ 地板（或踏板）上面第一格空氣（固定點收整數格、讀的人取格心 x.5,y.5,z.5）。
#   梯名與方向從扶手繩固定點 `manrope-<梯名>-<P|S>-<top|bot>` 讀：兩條扶手的 y 夾住踏板、top→bot 的 x 是下梯方向。
#   踏板 ＝ 梯子子作品在兩條扶手之間的格，依 z 分階；一階有兩格寬時取靠梯子中段的那一格。
#   foot／head：沿梯子的軸往外一欄一欄走，取那一欄（梯中線 y）最高的實心當地板；
#   第一段「連續 3 欄地板一樣高、上面 headroom 格都是空氣」的第一欄 ⇒ 那一格（艙口圍欄湊不成平地 ⇒ 跨過去）。
# 用法：python -I ladder_points.py <組裝件> <甲板子作品>:<關聯名>:<梯子子作品> [...] [--apply]
#   --draft：讀「作品＋草稿」（2026-10-14 berth → orlop 梯子：格子還在草稿等預覽、點先登記；套用後格子不變 ⇒ 點照樣成立）
#   不帶 --apply 只算、寫 verify（零寫入作品）；帶了才登記固定點、補 meta。⇒ <設計資料夾>/verify_ladder_points_<組裝件>.json
import sys, os, json, re, subprocess, time, collections
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
HEADROOM = 3       # 站的那一格往上至少幾格空氣（不是人高；人高另外讀出來寫進 verify）
SCAN = 25          # 往外最多走幾欄
FLAT = 3           # 幾欄一樣高才算站得穩的平地


def cli(args, retry=True):
    for k in range(4):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []),
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode and retry and '無法移除要被取代的檔案' in (r.stdout + r.stderr) and k < 3:
            time.sleep(0.5)
            continue
        return r


def export(work):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = cli(['op=export', 'format=list', 'work=' + work, 'out=' + out] + (['draft=1'] if '--draft' in sys.argv else []))
        if r.returncode and '沒有開著的草稿' in (r.stdout + r.stderr):      # --draft：這件沒有草稿 ⇒ 讀作品本身
            r = cli(['op=export', 'format=list', 'work=' + work, 'out=' + out])
        if r.returncode or not os.path.exists(out):
            raise SystemExit('匯出失敗 %s：%s' % (work, (r.stdout + r.stderr)[-400:]))
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def anchors(work):
    r = cli(['op=work', 'sub=anchors', 'work=' + work])
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r'- `([^`]+)` ← (\S+) @(-?\d+),(-?\d+),(-?\d+)', line)
        if m and m.group(2) == work:
            out[m.group(1)] = tuple(int(m.group(i)) for i in (3, 4, 5))
    return out


def link_lines(work):
    return cli(['op=work', 'sub=links', 'work=' + work]).stdout.splitlines()


def main():
    av = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply = '--apply' in sys.argv
    asm, specs = av[0], [s.split(':') for s in av[1:]]
    # 座標系：甲板關聯與梯子關聯都要 @0,0,0 turn 0、沒有鏡像 ⇒ 梯子子作品的格 ＝ 組裝件的格（不是的話這支不換算，停）
    L = link_lines(asm)
    for deck, link, lw in specs:
        hit = [l for l in L if ('/%s` → %s' % (link, lw)) in l]
        assert hit and '@0,0,0 turn 0' in hit[0], ('梯子關聯不在原點，這支不換算', deck, link, hit[:1])
        dl = [l for l in L if ('` → %s' % deck) in l]
        assert dl and '@0,0,0 turn 0' in dl[0], ('甲板關聯不在原點', deck, dl[:1])
    a = export(asm)
    S = {(int(x), int(y), int(z)) for x, y, z, c in a}

    def solid(x, y, z):
        return (x, y, z) in S

    def floor_top(x, y, zlo, zhi):
        zs = [z for z in range(zlo, zhi + 1) if solid(x, y, z)]
        return max(zs) if zs else None

    def air_above(x, y, z, n):
        return all(not solid(x, y, z + k) for k in range(n))

    def headroom(x, y, z):
        k = 0
        while k < 40 and not solid(x, y, z + k):
            k += 1
        return k

    def outward(x0, step, y, zlo, zhi):
        """沿 x 往外走：每欄 (x, 地板頂)；回第一段「連續 FLAT 欄地板一樣高、上面站得住」的第一欄
        （艙口圍欄一兩格寬、比甲板高 ⇒ 湊不成一段平地，被跨過去；v1 取 4..20 欄最常見的高度，fore-berth 被梯腳外 10 欄起一塊 z 66 的東西帶走）"""
        cols = []
        for i in range(1, SCAN + FLAT + 1):
            x = x0 + step * i
            cols.append((x, floor_top(x, y, zlo, zhi)))
        for i in range(SCAN):
            run = cols[i:i + FLAT]
            t = run[0][1]
            if t is not None and all(c[1] == t for c in run) and all(air_above(c[0], y, t + 1, HEADROOM) for c in run):
                return (run[0][0], y, t + 1), t, cols
        raise AssertionError(('站不住', x0, step, y, cols))

    report, todo = [], []
    for deck, link, lw in specs:
        an = anchors(lw)
        lad = collections.defaultdict(dict)
        for n, p in an.items():
            m = re.match(r'manrope-(.+)-([PS])-(top|bot)$', n)
            if m:
                lad[m.group(1)][(m.group(2), m.group(3))] = p
        cells = export(lw)
        for name, pts in sorted(lad.items()):
            assert len(pts) == 4, ('扶手固定點不齊', lw, name, pts)
            ys = sorted({p[1] for p in pts.values()})
            assert len(ys) == 2, ('兩條扶手的 y 不是兩個', name, ys)
            y0, y1 = ys
            yc = (y0 + y1) // 2
            xt = pts[('P', 'top')][0]
            xb = pts[('P', 'bot')][0]
            up = 1 if xt > xb else -1                      # 往上梯的 x 方向
            xlo, xhi = min(xt, xb) - 4, max(xt, xb) + 4
            m = cells[(cells[:, 1] > y0) & (cells[:, 1] < y1) & (cells[:, 0] >= xlo) & (cells[:, 0] <= xhi)]
            assert len(m), ('兩條扶手之間沒有踏板', name)
            byz = collections.defaultdict(set)
            for x, y, z, c in m:
                if y == yc:
                    byz[int(z)].add(int(x))
            zs = sorted(byz)
            mid = (xt + xb) / 2.0

            def tread(z):
                return (min(byz[z], key=lambda x: (abs(x - mid), x)), yc, z + 1)

            lo, hi = tread(zs[0]), tread(zs[-1])
            for p in (lo, hi):
                assert not solid(*p), ('踏板上面那格不是空氣', name, p)
            foot, fplane, fcols = outward(lo[0], -up, yc, lo[2] - 15, lo[2])
            head, hplane, hcols = outward(hi[0], up, yc, hi[2] - 10, hi[2] + 2)
            steps = [z2 - z1 for z1, z2 in zip(zs, zs[1:])]
            rec = {'link': '%s/%s' % (deck, link), 'ladder_work': lw, 'ladder': name, 'up_dir_x': up, 'y_center': yc,
                   'treads': len(zs), 'tread_rise': sorted(set(steps)),
                   'foot': foot, 'lo': lo, 'hi': hi, 'head': head,
                   'foot_floor_top': fplane, 'head_floor_top': hplane,
                   'headroom_cells': {'foot': headroom(*foot), 'head': headroom(*head)},
                   'coaming_cells_skipped': sum(1 for x, t in hcols[:hcols.index(next(c for c in hcols if c[0] == head[0]))] if t is not None and t > hplane)}
            report.append(rec)
            for k in ('foot', 'lo', 'hi', 'head'):
                todo.append((lw, '%s.%s' % (name, k), rec[k]))
            print('%-14s %-16s 上梯 x%+d　foot %s　lo %s　hi %s　head %s　踏板 %d 階（每階 %s）　頭頂 foot %d／head %d' % (
                link, name, up, foot, lo, hi, head, len(zs), rec['tread_rise'], rec['headroom_cells']['foot'], rec['headroom_cells']['head']))

    D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(D, 'verify_ladder_points_%s.json' % asm)
    json.dump({'assembly': asm, 'assembly_voxels': int(len(a)), 'headroom_min': HEADROOM, 'ladders': report},
              open(out, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('梯子 %d 座、固定點 %d 個 ⇒ %s' % (len(report), len(todo), out))
    if not apply:
        print('（沒帶 --apply ⇒ 零寫入）')
        return
    ok = bad = 0
    for lw, n, p in todo:
        r = cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + lw, 'name=' + n, 'at=%d,%d,%d' % p, 'overwrite=1',
                 'note=梯子給遊戲的點（ladder_points.py；ame tavern 23321）'])
        if r.returncode:
            bad += 1
            print('✗', lw, n, (r.stdout + r.stderr)[-300:])
        else:
            ok += 1
    for deck, link, lw in specs:
        r = cli(['op=work', 'sub=link', 'persona=basecamp', 'work=' + deck, 'name=' + link, 'meta={"kind":"ladders"}'])
        if r.returncode:
            bad += 1
            print('✗ meta', deck, link, (r.stdout + r.stderr)[-300:])
        else:
            ok += 1
    print('ok %d / bad %d' % (ok, bad))


main()

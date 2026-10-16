# 拿破崙號 階段十三落格（自己寫的）：機艙梯子子作品、固定點、甲板-lower 的關聯（meta kind=ladders）、主艙口前緣圍欄刻開
#   用法：python -I -X utf8 tools/apply_engine_access.py <design>
#   · 每一步讀回 exit 0 才往下；子作品已有格 ⇒ 格數對上就不重貼；圍欄已經刻過（標記 end 在）⇒ 不重刻
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'kotoko-napoleon-01m'
W = HULL + '-ladders-engine'
DECK = HULL + '-deck-lower'
MARK = '機艙梯子出口'
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
        print(out[-1200:])
        raise SystemExit(1)
    ok += 1
    return r.stdout


def count(path):
    return sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))


lad = os.path.join(D, 'masks', 'engine_access', 'ladders.vox.txt').replace(os.sep, '/')
carve = os.path.join(D, 'masks', 'engine_access', 'coaming_carve.vox.txt').replace(os.sep, '/')
pts = json.load(open(os.path.join(D, 'engine_access_points.json'), encoding='utf-8'))
n = count(lad)
if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
    cli(['op=work', 'sub=create', 'persona=kotoko', 'id=' + W, 'title=拿破崙號 機艙梯子（主艙口兩座、鍋爐頂四座）', 'size=1200,400,800', 'parent_work=' + HULL, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=kotoko', 'work=' + W, 'meters_per_voxel=0.1'])
have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
if have == 0:
    out = cli(['op=stampvox', 'persona=kotoko', 'work=' + W, 'voxels=' + lad, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0'])
    got = int(re.search(r'🔢 placed = (\d+)', out).group(1))
    if got != n:
        raise SystemExit('✗ placed %d ≠ %d' % (got, n))
elif have != n:
    raise SystemExit('✗ %s 已有 %d 格 ≠ %d（清單換過 ⇒ 先跑 tools/delta_apply.py）' % (W, have, n))
for nm, v in sorted(pts.items()):
    for pk in ('foot', 'lo', 'hi', 'head'):
        cli(['op=work', 'sub=anchor', 'persona=kotoko', 'work=' + W, 'name=%s.%s' % (nm, pk), 'at=%d,%d,%d' % tuple(v['points'][pk]), 'overwrite=1',
             'note=梯子點（draft_engine_access.py：腳踩的那一格）'])
cli(['op=work', 'sub=link', 'persona=kotoko', 'work=' + DECK, 'name=梯子-機艙', 'source_work=' + W, 'at=0,0,0', 'overwrite=1',
     'meta=' + json.dumps(dict({'kind': 'ladders'}, **{nm + '.decks': v['decks'] for nm, v in pts.items() if v.get('decks')}), ensure_ascii=False, sort_keys=True),
     'note=階段十三：機艙的出口（主艙口兩座到下砲甲板、鍋爐頂四座）；階段十四：照機艙地板重算、主艙口兩座 .decks'])
marks = cli(['op=work', 'sub=marks', 'work=' + DECK])
if (MARK + ':end') not in marks and not re.search(re.escape(MARK) + r'.{0,40}end', marks):
    m = count(carve)
    cli(['op=work', 'sub=mark', 'persona=kotoko', 'work=' + DECK, 'name=' + MARK, 'phase=begin', 'note=階段十三：主艙口前緣圍欄刻開（機艙梯子出口）'])
    out = cli(['op=carvevox', 'persona=kotoko', 'work=' + DECK, 'voxels=' + carve, 'at=0,0,0', 'expect_pixels=%d' % m])
    cli(['op=work', 'sub=mark', 'persona=kotoko', 'work=' + DECK, 'name=' + MARK, 'phase=end', 'note=刻 %d 格（顏色守門）' % m])
    print(out.strip().splitlines()[-6:])
else:
    print('· 圍欄已刻過（標記在）')
print('✓', W, n, '格', '固定點', 4 * len(pts), 'ok', ok, 'IOException 重試', retried)

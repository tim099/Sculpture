# 拿破崙號 機艙落格：照 engine_placement.json —— 每件一個子作品（0.1 m、parent 船殼、tags sub；已在且格數對 ⇒ 不重落）→ stampvox（讀回 placed）
#   → 固定點（core、cyl-*、gear；boiler-*、uptake；aft、fwd）→ 組裝件關聯（at ＝ 外框最小角、meta kind=engine／boiler／shaft）
#   結構照 tools/apply_stage9.py（抄三叉戟號）。用法：python -I -X utf8 tools/apply_engine.py <design>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL, ASM = 'kotoko-napoleon-01m', 'kotoko-napoleon-01m-assembly'
PL = json.load(open(os.path.join(D, 'engine_placement.json'), encoding='utf-8'))
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


xyz = lambda v: ','.join('%g' % c for c in v)
for k in ('shaft', 'engine', 'boilers_aft', 'boilers_fore'):
    P = PL[k]
    W = P['work']
    vox = os.path.join(D, 'masks', 'engine', k + '.vox.txt').replace(os.sep, '/')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
        cli(['op=work', 'sub=create', 'persona=kotoko', 'id=' + W, 'title=' + P['title'], 'size=' + xyz(P['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=kotoko', 'work=' + W, 'meters_per_voxel=0.1'])
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
    if have == 0:
        out = cli(['op=stampvox', 'persona=kotoko', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % P['cells'], 'share=0'])
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != P['cells']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, P['cells']))
    elif have != P['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, P['cells']))
    for name, v in sorted(P['anchors'].items()):
        cli(['op=work', 'sub=anchor', 'persona=kotoko', 'work=' + W, 'name=' + name, 'at=' + xyz(v), 'overwrite=1',
             'note=機艙（draft_engine.py）：遊戲照這一點旁邊的格子剩多少判斷這一件壞了沒有'])
    cli(['op=work', 'sub=link', 'persona=kotoko', 'work=' + ASM, 'name=' + P['link'], 'source_work=' + W, 'at=' + xyz(P['at']), 'overwrite=1',
         'note=機艙：%s' % P['title'], 'meta=' + json.dumps(P['meta'], ensure_ascii=False, sort_keys=True)])
    print('✓', k, W, P['cells'], '格', '關聯', P['link'], P['at'], P['meta'])
print('ok', ok, 'IOException 重試', retried)

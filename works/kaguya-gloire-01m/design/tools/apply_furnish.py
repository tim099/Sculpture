# 光榮號 階段十一落格（內部陳設；裝飾 meta deco=1）—— 抄自拿破崙號 kotoko-napoleon-01m/design/tools/apply_furnish.py（kotoko）
#   光榮號改：只有爐灶是自己的子作品（0.05 m、parent 船殼、tags sub）；繫纜柱、繫索栓圍欄、砲彈架直接引用拿破崙號的子作品（source_work 照 placement）。
#   用法：python -I -X utf8 tools/apply_furnish.py <design>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'kaguya-gloire-01m'
TITLE = {'galley': '光榮號 陳設・廚房爐灶（上甲板艏樓底下；0.05 m，外部模型的來源，裝飾 deco；形狀照拿破崙號、煙管照光榮號量）'}
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


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


PL = json.load(open(os.path.join(D, 'furnish_placement.json'), encoding='utf-8'))
for k, P in sorted(PL['pieces'].items()):
    W = P['source_work']
    if not W.startswith(HULL):
        have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
        assert have == P['cells'], (W, have, P['cells'])
        print('· 引用', W, have, '格')
        continue
    vox = os.path.join(D, 'masks', 'furnish', k + '.vox.txt').replace('\\', '/')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
        cli(['op=work', 'sub=create', 'persona=kaguya', 'id=' + W, 'title=' + TITLE[k], 'size=' + xyz(P['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=kaguya', 'work=' + W, 'meters_per_voxel=0.05'])
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
    if have == 0:
        out = cli(['op=stampvox', 'persona=kaguya', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % P['cells'], 'share=0'])
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != P['cells']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, P['cells']))
    elif have != P['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, P['cells']))
    print('✓ 子作品', W, P['cells'], '格', P['size'])
for r in PL['rows']:
    cli(['op=work', 'sub=model', 'persona=kaguya', 'work=' + r['deck_work'], 'name=' + r['model'], 'source_work=' + r['source_work'],
         'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=0,0,0', 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
         'meta=' + json.dumps(r['meta'], sort_keys=True), 'note=光榮號 陳設 %s（階段十一 draft_furnish.py；裝飾 deco=1：遊戲畫質「裝飾」關著就不載入、不算重量）' % r['piece']])
    print('✓ 模型', r['path'], r['source_work'], r['at'], r['mirror'])
print('furnish ok', ok, 'IOException 重試', retried)

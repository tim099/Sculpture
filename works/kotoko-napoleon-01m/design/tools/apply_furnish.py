# 拿破崙號 階段十五落格（陳設第一批；TASK-0682 裝飾 meta）—— 照 furnish_placement.json 下 CLI（cli／run 抄 apply_stage9.py）
#   每種一件子作品（0.05 m、parent 船殼、tags sub；已在且格數對 ⇒ 不重落）→ 甲板子作品掛外部模型（meta deco=1，造船規格 §9.9）。
#   用法：python -I -X utf8 tools/apply_furnish.py <design>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL = 'kotoko-napoleon-01m'
TITLE = {'galley': '拿破崙號 陳設・廚房爐灶（上砲甲板；0.05 m，外部模型的來源，裝飾 deco）',
         'bitts': '拿破崙號 陳設・錨鏈繫纜柱（上砲甲板船頭；0.05 m，裝飾 deco）',
         'fiferail': '拿破崙號 陳設・桅腳繫索栓圍欄（上甲板主桅、前桅；0.05 m，裝飾 deco）',
         'shotrack': '拿破崙號 陳設・砲彈架（主艙口兩舷；0.05 m，裝飾 deco）'}
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
    W = HULL + '-' + k
    vox = os.path.join(D, 'masks', 'furnish', k + '.vox.txt').replace('\\', '/')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
        cli(['op=work', 'sub=create', 'persona=kotoko', 'id=' + W, 'title=' + TITLE[k], 'size=' + xyz(P['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=kotoko', 'work=' + W, 'meters_per_voxel=0.05'])
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
    if have == 0:
        out = cli(['op=stampvox', 'persona=kotoko', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % P['cells'], 'share=0'])
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != P['cells']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, P['cells']))
    elif have != P['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, P['cells']))
    print('✓ 子作品', W, P['cells'], '格', P['size'])
for r in PL['rows']:
    cli(['op=work', 'sub=model', 'persona=kotoko', 'work=' + r['deck_work'], 'name=' + r['model'], 'source_work=' + HULL + '-' + r['piece'],
         'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=0,0,0', 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
         'meta=' + json.dumps(r['meta'], sort_keys=True), 'note=拿破崙號 陳設 %s（階段十五 draft_furnish.py；裝飾 deco=1：遊戲畫質「裝飾」關著就不載入、不算重量）' % r['piece']])
    print('✓ 模型', r['path'], r['at'], r['mirror'])
print('furnish ok', ok, 'IOException 重試', retried)

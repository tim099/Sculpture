# 海鷗號 步驟 9 落格（TASK-0024）：船首砲柱貼進甲板-main（stampvox，讀回 placed）、四門迴旋砲＋座的模型掛在甲板-main（guns_placement.json）。
#   出處：照杉心號的做法（砲柱落在甲板-main、迴旋砲與座兩個模型、座的 meta mount_of）；呼叫方式照本船 tools/build_masts.py。
#   用法：python -I -X utf8 tools/build_guns.py [--skip=post,models]   · 只認 exit 0。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
P = 'persona=Claude-Ojousama'
NOTE = '步驟 9（TASK-0024；design/draft_guns.py）'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
GP = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


if 'post' not in skip:
    f = os.path.join(HERE, 'masks', 'guns', 'post.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', P, 'work=' + GP['hosts']['deck'], 'voxels=' + f, 'at=0,0,0', 'expect_pixels=%d' % n)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        sys.exit('✗ placed != %d' % n)

if 'models' not in skip:
    for g in GP['models']:
        cli('op=work', 'sub=model', P, 'work=' + GP['hosts'][g['host']], 'name=' + g['name'], 'source_work=' + g['work'],
            'at=%g,%g,%g' % tuple(g['at']), 'pivot=%g,%g,%g' % tuple(g['pivot']), 'scale=%g' % g['scale'], 'rotate=%g,%g,%g' % tuple(g['rotate']),
            'meta=' + json.dumps(g['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE)

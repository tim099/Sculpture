# 海鷗號 步驟 13 落格（TASK-0024）：槳栓子作品（整船的框，stampvox 讀回）＋組裝件關聯「槳栓」、14 支槳的模型掛在槳栓子作品裡（皇家號的槳掛在舷外槳架子作品裡，同一個做法）。
#   出處：照杉心號 basecamp-piragua-01m/design/tools/build_oars.py；呼叫方式照本船 tools/build_masts.py。
#   用法：python -I -X utf8 tools/build_oars.py   · 只認 exit 0；已經存在的子作品不重建、不重貼。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKS = os.path.dirname(os.path.dirname(HERE))
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
P = 'persona=Claude-Ojousama'
HULL = 'claude-felucca-01m'
ASM = HULL + '-assembly'
NOTE = '步驟 13（TASK-0024；design/draft_oars.py）'
OP = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


W = OP['tholes_work']
if not os.path.exists(os.path.join(WORKS, W, 'work.json')):
    cli('op=work', 'sub=create', P, 'id=' + W, 'title=海鷗號 槳栓（每舷 7 根）', 'parent_work=' + HULL, 'size=170,161,50')
    cli('op=work', 'sub=update', P, 'work=' + W, 'meters_per_voxel=0.1', 'tags=sub')
    f = os.path.join(HERE, 'masks', 'oars', 'tholes.vox.txt')
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', P, 'work=' + W, 'voxels=' + f, 'at=0,0,0', 'expect_pixels=%d' % n)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        sys.exit('✗ placed != %d' % n)
    cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=槳栓', 'source_work=' + W, 'at=0,0,0', 'note=' + NOTE)
for m in OP['models']:
    args = ['op=work', 'sub=model', P, 'work=' + OP['host'], 'name=' + m['name'], 'source_work=' + OP['component'], 'at=%g,%g,%g' % tuple(m['at']),
            'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'], 'rotate=%g,%g,%g' % tuple(m['rotate']),
            'meta=' + json.dumps(m['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE]
    if m['mirror']:
        args.append('mirror=' + m['mirror'])
    cli(*args)

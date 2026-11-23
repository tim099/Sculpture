# 海鷗號 步驟 10 落格（TASK-0024）：彈藥庫子作品的固定點（blast／door）、組裝件關聯「彈藥庫」＋meta、火藥桶模型（放在彈藥庫子作品裡）、沙箱灶模型（放在甲板-main）。
#   出處：照杉心號 basecamp-piragua-01m/design/tools/build_magazine.py 的順序；呼叫方式照本船 tools/build_guns.py。藥箱的格子另外一刀 stampvox（已落、讀回 144）。
#   用法：python -I -X utf8 tools/build_magazine.py   · 只認 exit 0。
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
P = 'persona=Claude-Ojousama'
ASM = 'claude-felucca-01m-assembly'
NOTE = '步驟 10（TASK-0024；design/draft_magazine.py）'
MP = json.load(open(os.path.join(HERE, 'magazine_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


for name, at in MP['anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + MP['hosts']['magazine'], 'name=' + name, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE)
cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + MP['link']['name'], 'source_work=' + MP['hosts']['magazine'], 'at=0,0,0',
    'meta=' + json.dumps(MP['link']['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE + '：艉部藥箱')
for m in MP['models']:
    cli('op=work', 'sub=model', P, 'work=' + MP['hosts'][m['host']], 'name=' + m['name'], 'source_work=' + m['work'],
        'at=%g,%g,%g' % tuple(m['at']), 'pivot=%g,%g,%g' % tuple(m['pivot']), 'scale=%g' % m['scale'], 'rotate=%g,%g,%g' % tuple(m['rotate']),
        'meta=' + json.dumps(m['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE)

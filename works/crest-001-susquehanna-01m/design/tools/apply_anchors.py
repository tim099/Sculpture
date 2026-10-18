# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/apply_anchors.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 錨落格（kaguya 寫的；拿破崙號是手下 CLI）：照 verify_anchors.json —— 兩隻錨（外部模型、掛在組裝件、meta kind=anchor）＋ 船殼的 hawse-S／P 固定點
#   用法：python -I -X utf8 tools/apply_anchors.py <design>
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_anchors.json'), encoding='utf-8'))
HULL = 'crest-001-susquehanna-01m'


def cli(*a):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print((r.stdout + r.stderr)[-1200:])
        raise SystemExit('✗ ' + ' '.join(a[:4]))


xyz = lambda v: ','.join('%g' % c for c in v)
for r in V['rows']:
    cli('op=work', 'sub=model', 'persona=crest-001', 'work=' + HULL + '-assembly', 'name=' + r['model'], 'source_work=' + V['work'], 'at=' + xyz(r['at']),
        'pivot=' + xyz(V['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % V['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
        'meta=' + json.dumps(V['meta']), 'note=蘇士奎哈納號 錨（draft_anchors.py；共用錨元件，掛在 cathead 底下）')
    print('✓', r['model'])
for nm, p in sorted(V['hawse'].items()):
    cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=' + HULL, 'name=' + nm, 'at=' + xyz(p), 'note=錨鏈孔（船頭外表面、砲門頂那一層）')
    print('✓', nm, p)

# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/deck_meta.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 甲板 meta（造船規格 §9.3）：每層甲板子作品匯出 .vxk ⇒ Blockside/src/decks.py 量 floor／thick ⇒ design/decks_meta.tsv（換成本船的 deck 代號、level、中文名）⇒ work sub=meta
#   用法：python -I -X utf8 tools/deck_meta.py <design> [--apply]
import os, sys, json, subprocess, tempfile

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
HULL = 'crest-001-susquehanna-01m'
ROOT = 'D:/Unity/Valhalla'
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
ROWS = {r['key']: r for r in plan['decks']['rows']}
CODE = {'engine': 'engine', 'orlop': 'orlop', 'berth': 'berth', 'gun': 'gun'}   # 蘇士奎哈納號改（機艙鐵地板 level −1，階段九）
LEVEL = {'engine': -1, 'orlop': 0, 'berth': 1, 'gun': 2}
tmp = tempfile.mkdtemp(prefix='susq_decks_')
args = []
for k in LEVEL:
    out = os.path.join(tmp, k + '.vxk').replace('\\', '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=vxk', '--arg', 'work=%s-deck-%s' % (HULL, k), '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    assert r.returncode == 0 and os.path.exists(out), r.stdout[-800:]
    args += ['--vxk', '甲板-%s=%s' % (k, out)]
raw = os.path.join(tmp, 'raw.tsv')
r = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'Blockside/src/decks.py')] + args + ['--tsv', raw], capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout[-1500:], r.stderr[-800:])
lines = []
for l in open(raw, encoding='utf-8'):
    part, name, meta = l.rstrip('\n').split('\t')
    k = name.split('-', 1)[1]
    m = json.loads(meta)
    if k == 'engine':   # 機艙地板是收緊框的子作品（關聯 at ≠ 0）⇒ decks.py 量到的是子作品座標；直接寫世界座標（plan.machinery.floor）
        fl = plan['machinery']['floor']
        m.update({'floor': '%d:%d,%d:%d' % (fl['x'][0], fl['z'] + 1, fl['x'][1], fl['z'] + 1), 'thick': 1})
    m.update({'kind': 'deck', 'deck': CODE[k], 'level': LEVEL[k], 'name': ROWS[k]['name'] if k in ROWS else '機艙'})
    lines.append('%s\t%s\t%s' % (part, name, json.dumps(m, ensure_ascii=False, separators=(',', ':'))))
tsv = os.path.join(design, 'decks_meta.tsv')
open(tsv, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print(open(tsv, encoding='utf-8').read())
if '--apply' in sys.argv:
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=meta', '--arg', 'work=%s-assembly' % HULL, '--arg', 'persona=crest-001',
                        '--arg', 'file=' + tsv.replace('\\', '/')], capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('apply exit', r.returncode, r.stdout[-600:])

# 組裝件的關聯（at 0,0,0）＋ meta；各子作品的固定點；砲塔元件的關聯與固定點；預覽 preset。
# 用法：python -I -X utf8 apply_links.py <out 資料夾> [--dry]
import sys, json, subprocess, shutil
out = sys.argv[1]; DRY = '--dry' in sys.argv
M = json.load(open(out + '/monitor_meta.json', encoding='utf-8'))
TM = json.load(open(out + '/turret_meta.json', encoding='utf-8'))
A = M['anchors']
S = shutil.which('senate')
W = 'meadow-monitor-01m'; ASM = W + '-assembly'; PER = 'meadow'


def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    if DRY: print('· ' + ' '.join('%s=%s' % kv for kv in a)); return True
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    ok = p.returncode == 0
    print(('✓ ' if ok else '✗ ') + ' '.join(v for k, v in a if k in ('sub', 'work', 'name')) + ('' if ok else '\n' + (p.stdout + p.stderr)[-700:]))
    if not ok: sys.exit(1)
    return ok


def link(work, nm, src, meta=None, mirror=''):
    a = [('op', 'work'), ('sub', 'link'), ('work', work), ('persona', PER), ('name', nm), ('source_work', src), ('at', '0,0,0')]
    if mirror: a.append(('mirror', mirror))
    if meta: a.append(('meta', json.dumps(meta, ensure_ascii=False)))
    run(*a)


def anchor(work, nm, at):
    run(('op', 'work'), ('sub', 'anchor'), ('work', work), ('persona', PER), ('name', nm), ('at', '%d,%d,%d' % tuple(at)))


D = M['decks']
IRON = {'material': 'iron'}
LINKS = [
    ('船殼', W, {'kind': 'ship', 'waterline_z': M['plan']['z_waterline'], 'material': 'iron'}, ''),
    ('浮筏-木背板', W + '-raft-wood', None, ''),
    ('浮筏-鐵甲', W + '-raft-iron', {'material': 'iron', 'render': 'smooth'}, ''),
    ('甲板-berth', W + '-deck-berth', D['berth'], ''),
    ('甲板-main', W + '-deck-main', D['main'], ''),
    ('駕駛塔', W + '-pilothouse', IRON, ''),
    ('煙囪', W + '-funnel', {'kind': 'funnel', 'material': 'iron'}, ''),
    ('煙囪-鏡像', W + '-funnel', {'kind': 'funnel', 'material': 'iron'}, 'y'),
    ('鍋爐', W + '-boilers', {'kind': 'boiler', 'boilers': 1, 'funnel': '煙囪'}, ''),
    ('鍋爐-鏡像', W + '-boilers', {'kind': 'boiler', 'boilers': 1, 'funnel': '煙囪-鏡像'}, 'y'),
    ('機艙-主機', W + '-engine', M['engine_meta'], ''),
    ('螺旋槳軸', W + '-shaft', {'kind': 'shaft', 'material': 'iron'}, ''),
    ('鼓風機進氣管', W + '-deck-fittings', IRON, ''),
    ('彈藥庫', W + '-magazine', {'kind': 'magazine', 'pos': 'mid'}, ''),
    ('艙房', W + '-cabins', None, ''),
    ('梯子', W + '-ladders', {'kind': 'ladders'}, ''),
]
for nm, src, meta, mir in LINKS:
    link(ASM, nm, src, meta, mir)
# ── 固定點 ──
for L in A['ladders']:
    for k in ('foot', 'lo', 'hi', 'head'):
        anchor(W + '-ladders', L['name'] + '.' + k, L[k])
for nm, mm in A['mags'].items():
    for k in ('blast', 'door'):
        anchor(W + '-' + nm, k, mm[k])
anchor(W + '-funnel', 'smoke', A['funnel']['smoke'])
for k, v in A['boilers'].items(): anchor(W + '-boilers', k, v)
for k, v in A['engine'].items(): anchor(W + '-engine', k, v)
for k, v in A['shaft'].items(): anchor(W + '-shaft', k, v)
for k, v in A['screw'].items(): anchor(W + '-screw', k, v)
for k, v in A['hull'].items(): anchor(W, k, v)
# ── 砲塔元件：-turret ＝ 關聯 shell＋gun＋gun(mirror x)；固定點 ──
TA = TM['anchors']
for k, v in TA['gun'].items(): anchor(W + '-turret-gun', k, v)
for k, v in TA['shell'].items(): anchor(W + '-turret-shell', k, v)
link(W + '-turret', '圓筒', W + '-turret-shell')
link(W + '-turret', '砲-a', W + '-turret-gun')
link(W + '-turret', '砲-b', W + '-turret-gun', None, 'x')
for k, v in TA['turret'].items(): anchor(W + '-turret', k, v)
# ── 預覽 preset ──
def preset(nm, note, **kw):
    a = [('op', 'work'), ('sub', 'preset'), ('work', ASM), ('persona', PER), ('name', nm), ('note', note)] + list(kw.items())
    run(*a)
preset('藏浮筏與甲板', '看下船殼裡面：機艙、鍋爐、彈藥庫、艙房、梯子', hide_links='浮筏-鐵甲,浮筏-木背板,甲板-main')
preset('只看動力', '主機、鍋爐、煙囪、軸、螺旋槳', links='機艙-主機,鍋爐,鍋爐-鏡像,煙囪,煙囪-鏡像,螺旋槳軸', hide_links='self')
preset('只看甲板上', '甲板、砲塔、駕駛塔、煙囪、進氣管', links='甲板-main,駕駛塔,煙囪,煙囪-鏡像,鼓風機進氣管', hide_links='self')

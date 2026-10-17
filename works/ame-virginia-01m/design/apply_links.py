# 組裝件的關聯（at 0,0,0）＋ meta；梯子、彈藥庫、船殼（錨鏈孔）的固定點。用法：python -I -X utf8 apply_links.py <out 資料夾>
import sys, json, subprocess, shutil
out = sys.argv[1]
M = json.load(open(out + '/virginia_meta.json', encoding='utf-8'))
S = shutil.which('senate')
W = 'ame-virginia-01m'
def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    ok = p.returncode == 0
    print(('✓ ' if ok else '✗ ') + ' '.join(v for k, v in a if k in ('sub', 'name', 'work')) + ('' if ok else '\n' + (p.stdout + p.stderr)[-600:]))
    return ok
LINKS = [
    ('船殼', W, {'kind': 'ship', 'waterline_z': 65}),
    ('包銅皮', W + '-sheathing', {'material': 'copper_sheath'}),
    ('甲板-hold', W + '-deck-hold', {'kind': 'deck', 'deck': 'hold', 'level': 0, 'name': '艙底甲板', 'floor': '190:23,720:23', 'thick': 3}),
    ('甲板-berth', W + '-deck-berth', {'kind': 'deck', 'deck': 'berth', 'level': 1, 'name': '住艙甲板', 'floor': '110:47,800:47', 'thick': 3}),
    ('甲板-main', W + '-deck-main', {'kind': 'deck', 'deck': 'main', 'level': 2, 'name': '主甲板（砲甲板）', 'floor': '48:69,850:69', 'thick': 6}),
    ('砲廓-木背板', W + '-casemate-wood', {}),
    ('砲廓-鐵甲', W + '-casemate-iron', {'material': 'iron', 'render': 'smooth'}),
    ('颶風甲板', W + '-hurricane', {'kind': 'deck', 'deck': 'hurricane', 'level': 3, 'name': '颶風甲板（砲廓頂）', 'floor': '283:101,689:101', 'thick': 4}),
    ('駕駛塔', W + '-pilothouse', {'material': 'iron', 'render': 'smooth'}),
    ('煙囪', W + '-funnel', {'material': 'iron', 'render': 'smooth'}),
    ('撞角', W + '-ram', {'material': 'iron', 'render': 'smooth'}),
    ('機艙', W + '-engine', {'material': 'iron'}),
    ('梯子', W + '-ladders', {'kind': 'ladders'}),
    ('螺旋槳軸', W + '-shaft', {'kind': 'shaft', 'material': 'iron'}),   # 傳動件（TASK-0653）：固定點 aft（轂那頭）、fwd（主機那頭）
    ('鍋爐', W + '-boiler', {'kind': 'boiler', 'boilers': len(M['boilers']), 'funnel': '煙囪'}),   # 四座鍋爐＋煙道（2026-10-16；造船規格 §9.6）；⛔ 不標 iron：煙道牆 2 格厚（真的鐵板約 1 公分）⇒ 標了多 150 噸
    ('彈藥庫-前', W + '-magazine-fore', {'kind': 'magazine', 'pos': 'fore', 'powder_lb': M['mags']['magazine-fore']['kegs'] * 100}),
    ('彈藥庫-後', W + '-magazine-aft', {'kind': 'magazine', 'pos': 'aft', 'powder_lb': M['mags']['magazine-aft']['kegs'] * 100}),
]
for nm, src, meta in LINKS:
    a = [('op', 'work'), ('sub', 'link'), ('work', W + '-assembly'), ('persona', 'ame'), ('name', nm), ('source_work', src), ('at', '0,0,0')]
    if meta: a.append(('meta', json.dumps(meta, ensure_ascii=False)))
    run(*a)
for L in M['ladders']:
    for k in ('foot', 'lo', 'hi', 'head'):
        run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-ladders'), ('persona', 'ame'), ('name', L['name'] + '.' + k), ('at', '%d,%d,%d' % tuple(L[k])))
for nm in ('magazine-fore', 'magazine-aft'):
    for k in ('blast', 'door'):
        run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-' + nm), ('persona', 'ame'), ('name', k), ('at', '%d,%d,%d' % tuple(M['mags'][nm][k])))
for i, p in enumerate(M['boilers']):                               # 鍋爐：每座中心 boiler-1…n、煙道底 uptake
    run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-boiler'), ('persona', 'ame'), ('name', 'boiler-%d' % (i + 1)), ('at', '%d,%d,%d' % tuple(p)))
run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-boiler'), ('persona', 'ame'), ('name', 'uptake'), ('at', '%d,%d,%d' % tuple(M['uptake'])))
for k, p in (('aft', (77, 90, 28)), ('fwd', (254, 90, 28))):          # 軸的兩頭（gen_virginia.py shaft：x 77–254、z 28；fwd 貼著主機前牆）
    run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-shaft'), ('persona', 'ame'), ('name', k), ('at', '%d,%d,%d' % p))
# ⚠ 2026-10-16：舵（summit）與螺旋槳（kotoko）已拆成模型 ⇒ 重跑 gen_virginia.py 之後 ⛔ 不要整份同步船殼與機艙（會把舵、螺旋槳的格補回去）；只同步改到的部件。

# 彈藥庫的火藥桶（Tim 2026-10-15：維吉尼亞號打一下就沒火藥 ⇒ 兩間彈藥庫原本沒有桶 ⇒ 遊戲不擺取用點、送藥手沒地方拿）。
#   桶沿用憲法號 -powder-barrel（scale 0.2、pivot 11,11,0 ⇒ 4.4×4.4×5.4 格），meta kind=powder／powder_lb=100，掛在彈藥庫子作品裡（遊戲照「關聯名/」認是哪一間的）。
#   放在艙底甲板（地板 z 22 ⇒ 桶腳 z 23），一格 5 格排；門那一頭留 8 格走道。
#   前 x 641–689：8 欄 × 8 排 ＝ 64，門口那一欄中間 4 個不放 ⇒ 60。後 x 201–244：螺旋槳軸（y 89–91、z 27–29）從中線穿過 ⇒ 中間兩排讓開，5 欄 × 8 排 ＝ 40。
#   用法：python -I -X utf8 apply_powder.py [--dry]
import sys, json, subprocess, shutil
S = shutil.which('senate'); W = 'ame-virginia-01m'; DRY = '--dry' in sys.argv
BARREL, PIV, SC = 'basecamp-frigate-constitution-01m-powder-barrel', '11,11,0', '0.2,0.2,0.2'
def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    if DRY: return True
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0: print('✗ ' + ' '.join(v for k, v in a if k in ('sub', 'name', 'work')) + '\n' + (p.stdout + p.stderr)[-700:])
    return p.returncode == 0
YC = 90.5
PLAN = {
    'magazine-fore': {'xs': [651.5 + 5 * i for i in range(8)], 'ys': [YC + d for d in (-17.5, -12.5, -7.5, -2.5, 2.5, 7.5, 12.5, 17.5)],
                      'skip': lambda i, j: i == 0 and j in (2, 3, 4, 5)},
    'magazine-aft': {'xs': [203.5 + 5 * i for i in range(5)], 'ys': [71.5, 76.5, 81.5, 86.5, 94.5, 99.5, 104.5, 109.5], 'skip': lambda i, j: False},
}
tot = {}
for nm, P in PLAN.items():
    n = 0
    for i, x in enumerate(P['xs']):
        for j, y in enumerate(P['ys']):
            if P['skip'](i, j): continue
            n += 1
            ok = run(('op', 'work'), ('sub', 'model'), ('work', W + '-' + nm), ('persona', 'ame'), ('name', '桶-%03d' % n), ('source_work', BARREL),
                     ('at', '%.1f,%.1f,23' % (x, y)), ('pivot', PIV), ('rotate', '0,0,0'), ('scale', SC), ('overwrite', '1'),
                     ('meta', json.dumps({'kind': 'powder', 'powder_lb': 100})))
            if not ok: sys.exit(1)
    tot[nm] = n
print('桶', tot)
# 關聯 meta：pos（前／後；TASK-0539）＋ powder_lb 照桶數
for ln, nm, pos in (('彈藥庫-前', 'magazine-fore', 'fore'), ('彈藥庫-後', 'magazine-aft', 'aft')):
    run(('op', 'work'), ('sub', 'meta'), ('work', W + '-assembly'), ('persona', 'ame'), ('part', 'link'), ('name', ln),
        ('meta', json.dumps({'pos': pos, 'powder_lb': tot[nm] * 100})))
print('✓ 關聯 meta pos／powder_lb')

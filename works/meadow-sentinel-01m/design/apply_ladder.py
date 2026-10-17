# 哨兵號主砲塔的繩梯（Tim 2026-10-17：「是否可以用繩梯來上下跑塔上方那一塊」「繩梯直接綁在頂部開口」）：
#   砲塔頂（-turret-roof，鐵軌格柵）有前後兩個 7×7 的艙口（作品座標 x 11–17／47–53、y 29–35）。前面那個在兩門 XI 吋砲中間（兩門砲之間只有 3 格縫），
#   後面那個在砲尾後面、彈藥箱前面 ⇒ 綁在後艙口靠砲尾那一邊的格條（x 46）上，兩根直繩垂到吊籃（z 1），橫繩組串起來、標 climb ⇒ 遊戲裡第一人稱爬得上下。
#   繩在 -turret 這一層裡 ⇒ 匯出時 frame ＝「砲塔」⇒ 遊戲照砲塔現在的角度擺（Blockside 27_turret.js ropeRideOf：兩端都在同一座 ⇒ 整座跟著轉）。
#   落腳點：foot ＝ 吊籃上、繩梯旁那一格（48,32,1）；head ＝ 頂上格條 x 46 上面那一格（46,32,29）—— 都在砲塔座標裡、站得住（腳下實心、上面 7 格空）。
# 用法：python -I -X utf8 apply_ladder.py
import sys, shutil, subprocess
S = shutil.which('senate'); PER = 'meadow'; TUR = 'meadow-sentinel-01m-turret'
X, YA, YB, ZT, ZB = 47.0, 30.5, 34.5, 28.5, 1.0                         # 直繩：x 47.0 ＝ 格條 46 的內緣；兩根相距 0.4 m；從頂的格條（z 28）垂到吊籃面（z 1）


def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0: print((p.stdout + p.stderr)[-1500:]); sys.exit(1)
    return p.stdout


for nm, y in (('繩梯-a', YA), ('繩梯-b', YB)):
    run(('op', 'work'), ('sub', 'rope'), ('persona', PER), ('work', TUR), ('name', nm), ('from', '%g,%g,%g' % (X, y, ZT)), ('to', '%g,%g,%g' % (X, y, ZB)),
        ('slack', 1), ('color', '#2b2620'), ('thickness', 0.4), ('group', 'ladders/hatch'), ('note', '後艙口的繩梯：直繩（垂到吊籃）'))
    print('  繩 %s' % nm)
run(('op', 'work'), ('sub', 'ratlines'), ('persona', PER), ('work', TUR), ('name', '繩梯-後艙口'), ('rope_a', '繩梯-a'), ('rope_b', '繩梯-b'),
    ('step', 3), ('start', 2), ('stop', 2), ('thickness', 0.3), ('color', '#2b2620'), ('group', 'ladders/hatch'),
    ('climb', 1), ('foot', '48,32,1'), ('head', '46,32,29'), ('note', '後艙口的繩梯：吊籃 ⇄ 砲塔頂'))
print('  橫繩組 繩梯-後艙口（climb）')
print('done')

# 外部模型：砲（餘燼號 32 磅長砲元件放大）、舵輪（憲法號元件）、錨（憲法號 bower）；船殼的錨鏈孔、煙囪的排煙點。
import sys, json, subprocess, shutil
S = shutil.which('senate'); W = 'ame-virginia-01m'
def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(('✓ ' if p.returncode == 0 else '✗ ') + ' '.join(v for k, v in a if k in ('sub', 'name', 'work')) + ('' if p.returncode == 0 else '\n' + (p.stdout + p.stderr)[-700:]))
GUN = 'basecamp-ember-01m-gun-long32'
def gun(nm, at, rot, sc, code, mirror=''):
    a = [('op', 'work'), ('sub', 'model'), ('work', W + '-deck-main'), ('persona', 'ame'), ('name', nm), ('source_work', GUN),
         ('at', '%.1f,%.1f,%d' % at), ('pivot', '15.5,43.5,0'), ('rotate', '0,0,%d' % rot), ('scale', str(sc)),
         ('meta', json.dumps({'kind': 'gun', 'gun': code}))]
    if mirror: a.append(('mirror', mirror))
    run(*a)
S_PORTS = [330, 420, 510, 600]; P_PORTS = [375, 465, 555, 645]
for i, px in enumerate(S_PORTS):
    fwd = px == max(S_PORTS); gun('砲-S%d' % (i + 1), (px + 0.5, 126.5, 69), 0, 0.55, '64b' if fwd else '9d')
for i, px in enumerate(P_PORTS):
    fwd = px == max(P_PORTS); gun('砲-P%d' % (i + 1), (px + 0.5, 54.5, 69), 0, 0.55, '64b' if fwd else '9d', 'y')
gun('砲-船頭', (700.5, 90.5, 69), -90, 0.6, '7b')
gun('砲-船尾', (270.5, 90.5, 69), 90, 0.6, '7b')
# 船頭、船尾的 7 吋砲是迴旋砲（TASK-0626）：3 個砲門（中線、±45°）都從砲廓圓頭的圓心（x 670／302）放射 ⇒ 繞那一點轉；pivot ＝ 從砲尾沿砲軸量幾格（負 ＝ 往後）
for nm, pv in (('砲-船頭', -9.5), ('砲-船尾', -10.5)):
    run(('op', 'work'), ('sub', 'meta'), ('part', 'model'), ('work', W + '-deck-main'), ('persona', 'ame'), ('name', nm), ('meta', json.dumps({'mount': 'pivot', 'ports': '0,45,-45', 'pivot': pv, 'runin': 6})))   # runin：換砲門前往後拉 6 格（不拉 ⇒ 轉到 22° 穿進砲廓牆）
run(('op', 'work'), ('sub', 'model'), ('work', W + '-deck-main'), ('persona', 'ame'), ('name', '舵輪'), ('source_work', 'basecamp-frigate-constitution-01m-wheel'),
    ('at', '650.5,90.5,69'), ('pivot', '50,52,0'), ('rotate', '0,0,0'), ('scale', '0.2'), ('meta', json.dumps({'kind': 'wheel'})))
for side, y in (('S', 146.5), ('P', 34.5)):
    run(('op', 'work'), ('sub', 'model'), ('work', W + '-assembly'), ('persona', 'ame'), ('name', '錨-' + side), ('source_work', 'basecamp-frigate-constitution-01m-anchor'),
        ('at', '790.5,%.1f,68' % y), ('pivot', '23.5,16.5,56.5'), ('rotate', '0,0,0'), ('scale', '0.7'), ('meta', json.dumps({'kind': 'anchor', 'anchor': 'bower'})))
run(('op', 'work'), ('sub', 'anchor'), ('work', W), ('persona', 'ame'), ('name', 'hawse-S'), ('at', '800,129,63'))
run(('op', 'work'), ('sub', 'anchor'), ('work', W), ('persona', 'ame'), ('name', 'hawse-P'), ('at', '800,51,63'))
run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-funnel'), ('persona', 'ame'), ('name', 'smoke'), ('at', '450,90,145'))

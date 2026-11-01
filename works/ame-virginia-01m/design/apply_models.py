# 外部模型：砲（TASK-1155 起各自的通用部件，見下）、舵輪（憲法號元件）、錨（憲法號 bower）；船殼的錨鏈孔、煙囪的排煙點。
import sys, json, subprocess, shutil
S = shutil.which('senate'); W = 'ame-virginia-01m'
def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(('✓ ' if p.returncode == 0 else '✗ ') + ' '.join(v for k, v in a if k in ('sub', 'name', 'work')) + ('' if p.returncode == 0 else '\n' + (p.stdout + p.stderr)[-700:]))
# TASK-1155（ridge-two，2026-11-01）：砲換成各自的通用部件（Ship_Guns §2.2 砲只跟同一種砲共用模型；以前拿餘燼號 32 磅放大 0.55／0.6 暫代）——
#   9d ⇒ ridge-two-centurion-01m-gun-dahlgren9、64b ⇒ -gun-brooke64、7b ⇒ -gun-brooke7（滑軌拆成 -gun-brooke7-mount，雙生「砲-船頭座／砲-船尾座」kind=gunmount、mount_of）；
#   擺法照 place1155.py（新砲口對到舊砲口、零碰撞；迴旋砲每個砲門角度＋換砲門那段都量 0）。迴旋砲的轉軸中心照舊 ⇒ meta pivot −9.5／−10.5 ⇒ −9.2／−10.2。
GUNS = {'9d': ('ridge-two-centurion-01m-gun-dahlgren9', '12.5,42,0'), '64b': ('ridge-two-centurion-01m-gun-brooke64', '10.5,40,0'), '7b': ('ridge-two-centurion-01m-gun-brooke7', '11.5,50,0')}
def gun(nm, code, at, rot, mirror=''):
    work, piv = GUNS[code]
    a = [('op', 'work'), ('sub', 'model'), ('work', W + '-deck-main'), ('persona', 'ame'), ('name', nm), ('source_work', work),
         ('at', '%g,%g,%g' % at), ('pivot', piv), ('rotate', '0,0,%d' % rot), ('scale', '0.5'),
         ('meta', json.dumps({'kind': 'gun', 'gun': code}))]
    if mirror: a.append(('mirror', mirror))
    run(*a)
for row in (
    ('砲-S1', '9d', (330.5, 123.85, 69), 0, ''),
    ('砲-S2', '9d', (420.5, 123.85, 69), 0, ''),
    ('砲-S3', '9d', (510.5, 123.85, 69), 0, ''),
    ('砲-S4', '64b', (600.5, 121.35, 69), 0, ''),
    ('砲-P1', '9d', (375.5, 57.15, 69), 0, 'y'),
    ('砲-P2', '9d', (465.5, 57.15, 69), 0, 'y'),
    ('砲-P3', '9d', (555.5, 57.15, 69), 0, 'y'),
    ('砲-P4', '64b', (645.5, 59.65, 69), 0, 'y'),
    ('砲-船頭', '7b', (696.95, 90.5, 69), -90, ''),
    ('砲-船尾', '7b', (274.05, 90.5, 69), 90, ''),
):
    gun(*row)
# 船頭、船尾的 7 吋砲是迴旋砲（TASK-0626）：3 個砲門（中線、±45°）都從砲廓圓頭的圓心（x 670／302）放射 ⇒ 繞那一點轉；pivot ＝ 從砲尾沿砲軸量幾格（負 ＝ 往後）
for nm, pv in (('砲-船頭', -9.2), ('砲-船尾', -10.2)):
    run(('op', 'work'), ('sub', 'meta'), ('part', 'model'), ('work', W + '-deck-main'), ('persona', 'ame'), ('name', nm), ('meta', json.dumps({'mount': 'pivot', 'ports': '0,45,-45', 'pivot': pv, 'runin': 6})))   # runin：換砲門前往後拉 6 格（不拉 ⇒ 轉到 22° 穿進砲廓牆）
run(('op', 'work'), ('sub', 'model'), ('work', W + '-deck-main'), ('persona', 'ame'), ('name', '舵輪'), ('source_work', 'basecamp-frigate-constitution-01m-wheel'),
    ('at', '650.5,90.5,69'), ('pivot', '50,52,0'), ('rotate', '0,0,0'), ('scale', '0.2'), ('meta', json.dumps({'kind': 'wheel'})))
for side, y in (('S', 146.5), ('P', 34.5)):
    run(('op', 'work'), ('sub', 'model'), ('work', W + '-assembly'), ('persona', 'ame'), ('name', '錨-' + side), ('source_work', 'basecamp-frigate-constitution-01m-anchor'),
        ('at', '790.5,%.1f,68' % y), ('pivot', '23.5,16.5,56.5'), ('rotate', '0,0,0'), ('scale', '0.7'), ('meta', json.dumps({'kind': 'anchor', 'anchor': 'bower'})))
run(('op', 'work'), ('sub', 'anchor'), ('work', W), ('persona', 'ame'), ('name', 'hawse-S'), ('at', '800,129,63'))
run(('op', 'work'), ('sub', 'anchor'), ('work', W), ('persona', 'ame'), ('name', 'hawse-P'), ('at', '800,51,63'))
run(('op', 'work'), ('sub', 'anchor'), ('work', W + '-funnel'), ('persona', 'ame'), ('name', 'smoke'), ('at', '450,90,145'))

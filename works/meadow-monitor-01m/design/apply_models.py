# 外部模型：砲塔（本船元件 -turret，0.05 m、mount=turret）、螺旋槳（-screw，kind=propeller）、舵輪（憲法號元件縮小、放在駕駛塔裡）、
#           錨（憲法號 bower 縮小、收在錨井）、彈藥庫的火藥桶（憲法號元件）。用法：python -I -X utf8 apply_models.py <out 資料夾> [--dry]
import sys, json, subprocess, shutil
out = sys.argv[1]; DRY = '--dry' in sys.argv
M = json.load(open(out + '/monitor_meta.json', encoding='utf-8'))
TM = json.load(open(out + '/turret_meta.json', encoding='utf-8'))
S = shutil.which('senate'); W = 'meadow-monitor-01m'; PER = 'meadow'
MOD = M['models']


def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    if DRY: print('· ' + ' '.join('%s=%s' % kv for kv in a)); return True
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode != 0: print('✗ ' + ' '.join(v for k, v in a if k in ('sub', 'name', 'work')) + '\n' + (p.stdout + p.stderr)[-700:]); sys.exit(1)
    return True


def model(work, nm, src, at, pivot, rot, sc, meta):
    run(('op', 'work'), ('sub', 'model'), ('work', work), ('persona', PER), ('name', nm), ('source_work', src),
        ('at', '%.2f,%.2f,%.2f' % tuple(at)), ('pivot', '%.2f,%.2f,%.2f' % tuple(pivot)), ('rotate', '%g,%g,%g' % tuple(rot)), ('scale', str(sc)),
        ('meta', json.dumps(meta, ensure_ascii=False)))
    print('✓ model %s/%s' % (work, nm))


# 砲塔：pivot ＝ 圓心那一格的底面中心；at ＝ 甲板上的圓心（z ＝ 甲板走路格的底面）；rotate 90 ⇒ 靜止時砲口朝船尾（+y → −x）
t = MOD['turret']; cx, cy, _ = TM['anchors']['turret']['pivot']
model(W + '-deck-main', '砲塔', W + '-turret', t['at'], [cx + 0.5, cy + 0.5, 0], [0, 0, t['rotate_z']], 0.5, t['meta'])
# 螺旋槳：子作品用整船的框、at ＝ pivot ＝ 轉軸中心（光榮號的做法）
s = MOD['screw']
model(W + '-assembly', '螺旋槳', W + '-screw', s['hub'], s['hub'], [0, 0, 0], 1, s['meta'])
# 舵輪：憲法號雙舵輪縮到 0.7 m，固定在駕駛塔裡（Greene：舵輪在駕駛塔裡、固定在前面那一根鐵條上）
w = MOD['wheel']
model(W + '-pilothouse', '舵輪', 'basecamp-frigate-constitution-01m-wheel', w['at'], [50, 52, 0], [0, 0, 0], w['scale'], {'kind': 'wheel'})
# 錨：收進船頭的錨井（錨環在上、靠甲板底）
a = MOD['anchor']
model(W + '-assembly', '錨', 'basecamp-frigate-constitution-01m-anchor', a['at'], [23.5, 16.5, 56.5], [0, 0, a['rotate_z']], a['scale'], {'kind': 'anchor', 'anchor': 'bower'})
# 火藥桶：憲法號元件（scale 0.2、pivot 11,11,0 ⇒ 4.4×4.4×5.4 格），掛在彈藥庫子作品裡
BARREL = 'basecamp-frigate-constitution-01m-powder-barrel'
tot = {}
for nm, P in M['powder'].items():
    n = 0
    for (x, y, zf) in P['spots']:
        n += 1
        run(('op', 'work'), ('sub', 'model'), ('work', W + '-' + nm), ('persona', PER), ('name', '桶-%03d' % n), ('source_work', BARREL),
            ('at', '%.1f,%.1f,%d' % (x, y, zf)), ('pivot', '11,11,0'), ('rotate', '0,0,0'), ('scale', '0.2,0.2,0.2'),
            ('meta', json.dumps({'kind': 'powder', 'powder_lb': 100})))
    tot[nm] = n
print('桶', tot)
for nm, n in tot.items():
    run(('op', 'work'), ('sub', 'meta'), ('work', W + '-assembly'), ('persona', PER), ('part', 'link'), ('name', M['mags'][nm]['link']),
        ('meta', json.dumps({'powder_lb': n * 100})))
print('✓ 彈藥庫 powder_lb 照桶數')

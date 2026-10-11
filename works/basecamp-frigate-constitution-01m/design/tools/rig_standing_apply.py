# 照 design/rig_standing.json 一條一條下 CLI（固定點 overwrite=1、繩 overwrite=1 ⇒ 重跑一樣）
# 用法：python -I rig_standing_apply.py <design 資料夾> <固定點篩選 regex> <繩篩選 regex>　（全部：'.' '.'）
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.abspath(sys.argv.pop(1))
PRE = 'basecamp-frigate-constitution-01m'
WORK = {'main': PRE + '-mast-main', 'fore': PRE + '-mast-fore', 'mizzen': PRE + '-mast-mizzen', 'bowsprit': PRE + '-bowsprit',
        'knee': PRE + '-head-knee', 'hull': PRE, 'channels': PRE + '-channels'}
ASSEMBLY = PRE + '-assembly'
R = json.load(open(os.path.join(HERE, 'rig_standing.json'), encoding='utf-8'))
fa, fr = re.compile(sys.argv[1]), re.compile(sys.argv[2])


def cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'persona=basecamp'] + sum([['--arg', a] for a in args], []),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


ok = bad = 0
for a in R['anchors']:
    key = a['link'] + '/' + a['name']
    if not fa.search(key):
        continue
    rc, out = cli(['sub=anchor', 'work=' + WORK[a['work']], 'name=' + a['name'], 'at=%d,%d,%d' % tuple(a['at']), 'overwrite=1',
                   'note=靜索試掛（世界 %d,%d,%d）' % tuple(a['world'])])
    if rc:
        bad += 1
        print('✗ anchor', key, rc, out[-400:])
    else:
        ok += 1
print('anchors ok', ok, 'bad', bad)
ok = bad = 0
for r in R['ropes']:
    if not fr.search(r['name']):
        continue
    rc, out = cli(['sub=rope', 'work=' + ASSEMBLY, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
                   'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'note=靜索試掛：' + r['group']])
    if rc:
        bad += 1
        print('✗ rope', r['name'], rc, out[-600:])
    else:
        ok += 1
        m = [l for l in out.splitlines() if 'rope_length' in l or 'rope_max_sag' in l]
        print('✓', r['name'], ' '.join(l.strip() for l in m)[:160])
print('ropes ok', ok, 'bad', bad)

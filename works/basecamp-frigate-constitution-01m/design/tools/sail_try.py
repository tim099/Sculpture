# kotoko 的兩點試驗：只改兩面 course 的 fullness 與四條 tack 的 slack，量最鼓與下角高度
# 用法：python -I sail_try.py <design 資料夾> <tack_slack> <course_fullness>
import sys, os, json, subprocess, re
sys.stdout.reconfigure(encoding='utf-8')
D, TS, FU = os.path.abspath(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
ASM = 'basecamp-frigate-constitution-01m-assembly'
J = json.load(open(os.path.join(D, 'sails_test.json'), encoding='utf-8'))
RET = 'D:/Unity/Valhalla/ChatTavern/baton/letters/basecamp/cmd/sculpture_work.md'


def cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'persona=basecamp'] + sum([['--arg', a] for a in args], []),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print('✗', args[:3], (r.stdout + r.stderr)[-400:])
        sys.exit(1)
    return r.stdout


for s in J['sails']:
    if s['name'] in ('fore-course', 'main-course'):
        a = ['sub=sail', 'work=' + ASM, 'name=' + s['name'], 'corners=' + s['corners'], 'corner_names=' + s['corner_names'], 'bind=' + s['bind'],
             'fullness=%g' % FU, 'color=' + s['color'], 'overwrite=1', 'note=' + s['note'], 'free=' + s['free']]
        cli(a)
for r in J['ropes']:
    if '.tack-' in r['name']:
        cli(['sub=rope', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1', 'slack=%g' % TS,
             'color=' + r['color'], 'thickness=%g' % r['thickness'], 'note=' + r['note']])
cli(['sub=sails', 'work=' + ASM])
t = open(RET, encoding='utf-8').read()
for nm in ('fore-course', 'main-course'):
    line = [l for l in t.splitlines() if l.startswith('- ✓ `%s`' % nm) or l.startswith('- ✗ `%s`' % nm) or ('`%s`' % nm in l and l.startswith('- '))][0]
    b = re.search(r'最鼓 (-?[\d.]+)', line).group(1)
    print(nm, 'billow', b)
for l in t.splitlines():
    if re.search(r'`(fore|main)-course\.(tack|sheet)-[SP]`', l):
        m = re.search(r'`([^`]+)`.*?\(([-\d.]+),([-\d.]+),([-\d.]+)\).*?最大下垂 ([-\d.]+)', l)
        print('  %-22s clew z %-6s sag %s' % (m.group(1), m.group(4), m.group(5)))
print('broken', re.findall(r'(sails_broken|ropes_broken)[^\n]*', t)[:2] or 'see stdout')

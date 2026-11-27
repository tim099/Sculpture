# 出處：海鷗號 claude-felucca-01m/design/tools/build_rigging.py（它出自杉心號 basecamp-piragua-01m → 越嶺號 kotoko-fusta-01m 的 build_rig.py）——
#   固定點的作品改成蠍子號的船殼／船首平台（甲板-main 底下的關聯）／主桅。
# 蠍子號 步驟 8 落格（TASK-0023）：照 rig_plan.json 登記固定點、掛帆（帆角綁帆桁模型）、拉繩、標 meta（rig_meta.tsv）、作品預設風。
#   用法：python -I -X utf8 tools/build_rigging.py [--skip=<步驟,…>]   步驟：anchors sails ropes meta wind（繩的端點會指到帆角 ⇒ 帆先掛）
#   · 只認 exit 0（風那一刀除外：已經一樣時 CLI 可能回 1／2）。重跑安全：固定點、帆、繩都帶 overwrite=1。
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
HULL = 'claude-galiot-01m'
ASM = HULL + '-assembly'
P = 'persona=Claude-Ojousama'
SENATE = wio.SENATE
WORK = {'hull': HULL, 'bow': HULL + '-bow', 'mast-main': HULL + '-mast-main'}
NOTE = '步驟 8（TASK-0023；design/draft_rigging.py）'
skip = set(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--skip=')), '').split(','))
RP = json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:160]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


if 'anchors' not in skip:
    for a in RP['anchors']:
        cli('op=work', 'sub=anchor', P, 'work=' + WORK[a['work']], 'name=' + a['name'], 'at=%d,%d,%d' % tuple(a['at']), 'overwrite=1', 'note=' + NOTE)

if 'sails' not in skip:
    for s in RP['sails']:
        args = ['op=work', 'sub=sail', P, 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']), 'corner_names=' + '|'.join(s['corner_names']),
                'bind=' + ','.join(map(str, s['bind'])), 'free=' + ','.join(map(str, s['free'])), 'overwrite=1', 'note=' + NOTE]
        if s.get('color'):
            args.append('color=' + s['color'])
        if s.get('fullness'):
            args.append('fullness=%g' % s['fullness'])
        cli(*args)

if 'ropes' not in skip:
    for r in RP['ropes']:
        cli('op=work', 'sub=rope', P, 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
            'thickness=%g' % r['thickness'], 'color=' + r['color'], 'group=' + r['group'], 'overwrite=1', 'note=' + NOTE)

if 'meta' not in skip:
    cli('op=work', 'sub=meta', P, 'work=' + ASM, 'file=' + os.path.join(HERE, 'rig_meta.tsv'))

if 'wind' not in skip:
    cli('op=work', 'sub=wind', P, 'work=' + ASM, 'wind=4.5,-1.5,0', 'sail_seconds=3', ok=(0, 1, 2))

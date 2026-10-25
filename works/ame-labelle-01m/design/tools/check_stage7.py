# 階段七（TASK-0596）讀數：channels 結果帳、CLI 的 ropes_broken／sails_broken、帆與帆自己的繩的 meta（從 CLI 讀作品裡實際標了什麼）、帆桁 meta 的 sail ＝ 帆名
#   用法：python -I -X utf8 tools/check_stage7.py <design> [--drop=<繩名>]
#   · --drop：反向對照 —— 讀完作品的 meta 之後，在記憶體裡當作那一條沒標，看這把尺報不報（作品一個位元組都不動）
import json, os, re, subprocess, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
drop = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--drop=')), None)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
ASM = 'ame-labelle-01m-assembly'
P = json.load(open(os.path.join(design, 'rigging_plan.json'), encoding='utf-8'))


def cli(*args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout + r.stderr


W = export_list('ame-labelle-01m-channels', None)
D = np.loadtxt(os.path.join(design, 'masks', 'rigging', 'channels.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
print('channels 作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))
vals = {}
for sub in ('ropes', 'sails'):
    out = cli('op=work', 'sub=' + sub, 'work=' + ASM)
    for k in ('rope_count', 'ropes_broken', 'sails_drawn', 'sails_broken'):
        m = re.search(r'🔢 %s = (\d+)' % k, out)
        if m:
            vals[k] = int(m.group(1))
print('CLI：', vals, '（設計：繩 %d、帆 %d）' % (len(P['ropes']), len(P['sails'])))
got = {}
for part in ('sail', 'rope'):
    out = cli('op=work', 'sub=meta', 'work=' + ASM, 'part=' + part)
    for nm, body in re.findall(r'^- `([^`]+)`：(.*)$', out, re.M):
        got[(part, nm)] = dict(kv.split('=', 1) for kv in body.split(', ') if '=' in kv)
if drop:
    got.pop(('rope', drop), None)
sail_names = {s['name'] for s in P['sails']}
miss_sail = sorted(s for s in sail_names if ('sail', s) not in got)
need = [r['name'] for r in P['ropes'] if '.' in r['name'] and r['name'].split('.')[0] in sail_names]
miss_rope = sorted(n for n in need if ('rope', n) not in got)
wrong = sorted(n for n in need if ('rope', n) in got and got[('rope', n)].get('sail') != n.split('.')[0])
print('meta：帆 %d／%d、帆自己的繩 %d／%d；沒有 meta 的帆 %s、繩 %s；sail 標錯的繩 %s' % (len(sail_names) - len(miss_sail), len(sail_names), len(need) - len(miss_rope), len(need), miss_sail or 0, miss_rope or 0, wrong or 0))
YP = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
bad = [(y['name'], y['meta']['sail']) for y in YP if y['meta']['sail'] not in sail_names]
print('帆桁 meta 的 sail 不是任何一面帆的名字：', bad or 0)

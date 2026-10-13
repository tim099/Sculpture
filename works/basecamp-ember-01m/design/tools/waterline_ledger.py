# 水線抬高 結果帳：船殼現在 vs（上甲板clamp:end ＋ waterline.vox.txt 換色）；knee 子作品現在 vs knee.vox.txt
# 用法：python -I waterline_ledger.py <design 資料夾>
import sys, os, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ports import export_mark       # noqa: E402
from draft_ladders import export_hidden   # noqa: E402

F = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['waterline_raise']


def load(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


def cmp(want, have):
    return {'design': len(want), 'work': len(have), 'missing': sum(1 for k in want if k not in have), 'extra': sum(1 for k in have if k not in want),
            'color_diff': sum(1 for k in want if k in have and have[k] != want[k])}


want = {(x, y, z): c for x, y, z, c in export_mark(F['hull'], F['world_mark'])}
want.update(load(os.path.join(D, 'masks', 'paint', 'waterline.vox.txt')))
import draft_profile as DP   # noqa: E402
have = {(x, y, z): c for x, y, z, c in DP.export_list(F['hull'], links='none')}     # 船殼現在（不是重播到標記）
r = {'hull': cmp(want, have)}
now = {(x, y, z): c for x, y, z, c in export_hidden('basecamp-ember-01m-head-knee', [])}
r['knee'] = cmp(load(os.path.join(D, 'masks', 'head', 'knee.vox.txt')), now)
print(json.dumps(r, ensure_ascii=False))
json.dump(r, open(os.path.join(D, 'verify_waterline_ledger.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)

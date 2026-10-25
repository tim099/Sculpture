# 出處：calli-cosecha-01m/design/tools/delta_apply.py（收穫號，照抄後改成藍鯊號 —— TASK-0967）
# 讓一件子作品跟它的清單一致：作品多的格 carvevox（帶現在的顏色守門）、少的 stampvox、顏色不同的 stampvox overwrite=1；每刀讀回 placed
#   用法：python -I -X utf8 tools/delta_apply.py <design> <work> <清單> [--dry]
import os, re, subprocess, sys, tempfile
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design, work, path = sys.argv[1:4]
dry = '--dry' in sys.argv
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list
W = export_list(work, None)
cw = {tuple(r[:3]): r[3] for r in W.tolist()}
cd = {}
for l in open(path, encoding='utf-8'):
    if l.strip() and not l.startswith('#'):
        x, y, z, c = map(int, l.split(','))
        cd[(x, y, z)] = c
extra = sorted(set(cw) - set(cd)); miss = sorted(set(cd) - set(cw)); recol = sorted(k for k in set(cd) & set(cw) if cd[k] != cw[k])
print('%s：多 %d（刻）、少 %d（貼）、換色 %d' % (work, len(extra), len(miss), len(recol)))
if dry:
    sys.exit(0)
def run(op, cells, colors, extra_args=()):
    if not cells:
        return
    d = tempfile.mkdtemp()
    f = os.path.join(d, 'l.vox.txt')
    with open(f, 'w', encoding='utf-8', newline='\n') as h:
        for k in cells:
            h.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], colors[k]))
    args = ['senate', 'cmd', 'sculpture', '--arg', 'op=' + op, '--arg', 'persona=gura', '--arg', 'work=' + work, '--arg', 'voxels=' + f.replace('\\', '/'),
            '--arg', 'at=0,0,0', '--arg', 'expect_pixels=%d' % len(cells), '--arg', 'share=0'] + [a for kv in extra_args for a in ('--arg', kv)]
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', r.stdout + r.stderr)
    got = int(m.group(1).replace(',', '')) if m else None
    print('  %s %d ⇒ exit %d placed %s' % (op, len(cells), r.returncode, got))
    if r.returncode != 0 or got != len(cells):
        print((r.stdout + r.stderr)[-1500:]); sys.exit(1)
run('carvevox', extra, cw)
run('stampvox', miss, cd)
run('stampvox', recol, cd, ('overwrite=1',))

# 作品對清單補差（照收穫號 delta_apply 的做法重寫）：作品現在的格 vs 設計清單 ⇒
#   多的：carvevox（帶刻之前的顏色守門）；少的：stampvox；顏色不同的：stampvox overwrite=1。每一刀讀回筆數。
#   用法：python -I -X utf8 tools/delta_apply.py <work> <清單.vox.txt> [--dry]
import os, sys, re, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
import wio

args = [a for a in sys.argv[1:] if not a.startswith('--')]
dry = '--dry' in sys.argv
work, lst = args[0], args[1]
w = wio.export_list(work, None)
d = np.loadtxt(lst, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
cw = {tuple(r[:3]): r[3] for r in w.tolist()}
cd = {tuple(r[:3]): r[3] for r in d.tolist()}
extra = [(k, cw[k]) for k in cw if k not in cd]
missing = [(k, cd[k]) for k in cd if k not in cw]
recol = [(k, cd[k]) for k in cd if k in cw and cw[k] != cd[k]]
print('%s：多 %d、少 %d、換色 %d' % (work, len(extra), len(missing), len(recol)))
if dry:
    sys.exit(0)


def run(op, rows, extra_args=()):
    if not rows:
        return
    with tempfile.TemporaryDirectory() as dd:
        f = os.path.join(dd, 'd.vox.txt').replace('\\', '/')
        with open(f, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], c) for k, c in rows) + '\n')
        cmd = ['senate', 'cmd', 'sculpture', '--arg', 'op=' + op, '--arg', 'persona=apex-one', '--arg', 'work=' + work, '--arg', 'voxels=' + f,
               '--arg', 'at=0,0,0', '--arg', 'expect_pixels=%d' % len(rows), '--arg', 'draft=0', '--arg', 'share=0'] + [x for a in extra_args for x in ('--arg', a)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        m = re.search(r'(?:placed|carved)\D{0,12}(\d[\d,]*)', out) or re.search(r'(\d[\d,]*) voxels', out)
        n = int(m.group(1).replace(',', '')) if m else None
        print('  %s %d 格 exit=%d 讀回 %s' % (op, len(rows), r.returncode, n))
        if r.returncode != 0 or n != len(rows):
            print(out[-1500:])
            sys.exit(1)


run('carvevox', extra)
run('stampvox', missing)
run('stampvox', recol, ('overwrite=1',))

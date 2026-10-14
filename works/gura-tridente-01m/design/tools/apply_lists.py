# 一份清單一刀：carvevox（帶顏色守門）或 stampvox overwrite=1（換色），讀回 carved／placed 對上清單格數才算。
#   用法：python -I -X utf8 apply_lists.py <work> <draft 0|1> carve:<清單> paint:<清單> …（照順序）
#   ⚠ 引擎的 carve 回報也印成 placed ＝ N（Sculpture_Blueprint_Build §5）⇒ 兩種都讀 placed，再對清單格數
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
work, draft = sys.argv[1], sys.argv[2]
for spec in sys.argv[3:]:
    kind, f = spec.split(':', 1)
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    op = 'carvevox' if kind == 'carve' else 'stampvox'
    cmd = ['senate', 'cmd', 'sculpture', '--arg', 'op=' + op, '--arg', 'persona=gura', '--arg', 'work=' + work,
           '--arg', 'voxels=' + os.path.abspath(f).replace('\\', '/'), '--arg', 'at=0,0,0', '--arg', 'expect_pixels=%d' % n,
           '--arg', 'draft=' + draft, '--arg', 'share=0']
    if kind == 'paint':
        cmd += ['--arg', 'overwrite=1']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    m = re.search(r'(?:placed|carved)\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    print('%s %s cells=%d exit=%d got=%s' % (op, os.path.basename(f), n, r.returncode, got), flush=True)
    if r.returncode != 0 or got != n:
        print(out[-2500:])
        sys.exit(1)

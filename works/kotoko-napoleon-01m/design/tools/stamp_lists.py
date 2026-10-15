# 抄自三叉戟號 gura-tridente-01m/design/tools/stamp_lists.py（gura）；改：persona。
# 把一串 .vox.txt 清單照順序 stampvox 進作品（at 0,0,0），每一刀讀回 placed，對不上就停。
#   用法：python -I -X utf8 stamp_lists.py <work> <draft 0|1> <清單…>
#   · 已經落過的那幾刀不重下：從第一個參數 --from=N 開始（清單的序號，1 起）
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
start = int(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--from=')), '1'))
work, draft, files = args[0], args[1], args[2:]
for i, f in enumerate(files, 1):
    if i < start:
        continue
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    cmd = ['senate', 'cmd', 'sculpture', '--arg', 'op=stampvox', '--arg', 'persona=kotoko', '--arg', 'work=' + work,
           '--arg', 'voxels=' + os.path.abspath(f).replace('\\', '/'), '--arg', 'at=0,0,0', '--arg', 'expect_pixels=%d' % n,
           '--arg', 'draft=' + draft, '--arg', 'share=0']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    placed = int(m.group(1).replace(',', '')) if m else None
    print('%d/%d %s cells=%d exit=%d placed=%s' % (i, len(files), os.path.basename(f), n, r.returncode, placed), flush=True)
    if r.returncode != 0 or placed != n:
        print(out[-2000:])
        sys.exit(1)

# 出處：claude-felucca-01m/design/tools/stamp_lists.py（海鷗號，照抄；蠍子號每個步驟共用）。以下是它原本的出處說明。
# 出處：kotoko-fusta-01m/design/tools/stamp_lists.py（照抄；它抄自皇家號 → 收穫號）。改：persona Claude-Ojousama、senate 用離線包裝絕對路徑。
# 來源：apex-one-reale-01m/design/tools/stamp_lists.py（照抄，persona 改 kotoko；它又抄自 calli-cosecha-01m）
# 把一串 .vox.txt 清單照順序 stampvox 進作品（at 0,0,0），每一刀讀回 placed，對不上就停。
#   用法：python -I -X utf8 stamp_lists.py <work> <draft 0|1> <清單…>
#   · 已經落過的那幾刀不重下：從第一個參數 --from=N 開始（清單的序號，1 起）
import os, re, subprocess, sys
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')

sys.stdout.reconfigure(encoding='utf-8')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
start = int(next((a.split('=')[1] for a in sys.argv[1:] if a.startswith('--from=')), '1'))
work, draft, files = args[0], args[1], args[2:]
for i, f in enumerate(files, 1):
    if i < start:
        continue
    n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
    cmd = [SENATE, 'cmd', 'sculpture', '--arg', 'op=stampvox', '--arg', 'persona=Claude-Ojousama', '--arg', 'work=' + work,
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

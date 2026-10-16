# 把作品現在的格子同步成新清單：刻掉多的（與換色的），補上缺的。用法：python -I -X utf8 sync_part.py [--carve-only] <作品> <新清單> [<新清單2>…]
#   --carve-only：只刻、不補（船殼、機艙：舵與螺旋槳已拆成模型，新清單裡還有它們的格 ⇒ 補了就長回去；apply_links.py 底部的警告）
import sys, subprocess, shutil, os, tempfile
CARVE_ONLY = len(sys.argv) > 1 and sys.argv[1] == '--carve-only'
if CARVE_ONLY: del sys.argv[1]
S = shutil.which('senate'); W = sys.argv[1]


def run(*a):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode: print((p.stdout + p.stderr)[-800:]); sys.exit(1)
    return p.stdout


def fwd(p): return p.replace(os.sep, '/')


tmp = tempfile.mkdtemp(prefix='vsync_'); cur = fwd(os.path.join(tmp, 'cur.txt'))
run(('op', 'export'), ('format', 'list'), ('work', W), ('out', cur), ('links', 'none'))


def load(f):
    d = {}
    for l in open(f, encoding='utf-8'):
        l = l.strip()
        if not l or l[0] == '#': continue
        a = l.split(','); d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


old = load(cur); new = {}
for f in sys.argv[2:]: new.update(load(f))
rm = [k for k, c in old.items() if new.get(k) != c]
add = [k for k, c in new.items() if old.get(k) != c]
print('%s：現在 %d 格、新的 %d 格 ⇒ 刻 %d、補 %d' % (W, len(old), len(new), len(rm), len(add)))
if CARVE_ONLY: print('  --carve-only：補的 %d 格不補' % len(add)); add = []
for name, lst, op in (('rm', rm, 'carvevox'), ('add', add, 'stampvox')):
    for i in range(0, len(lst), 900000):
        part = lst[i:i + 900000]; fn = fwd(os.path.join(tmp, '%s%d.txt' % (name, i)))
        with open(fn, 'w') as f:
            f.write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], old[k] if op == 'carvevox' else new[k]) for k in part) + '\n')
        run(('op', op), ('persona', 'ame'), ('work', W), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(part))))
        print('  %s %d ✓' % (op, len(part)))

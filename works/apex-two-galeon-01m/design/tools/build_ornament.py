# 出處：本船 tools/build_decks.py 的 cli／make／stamp（照抄）—— 康塞普西翁號 步驟 16 裝飾（TASK-0969）
# 落格：建 -ornament 子作品、貼 masks/deco/ornament.vox.txt、組裝件關聯「裝飾-2」
#   用法：python -I -X utf8 tools/build_ornament.py <design>
#   · 每一步讀回 exit 0 才往下；子作品已存在 ⇒ 不重建、不重貼（之後改清單用 tools/delta_apply.py）
import os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-two-galeon-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=apex-two', 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=900,320,700', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=apex-two', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-two', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


w = HULL + '-ornament'
if make(w, '康塞普西翁號 裝飾（側廊第二層、托架、壁柱與窗楣、head rail）'):
    stamp(w, os.path.join(design, 'masks', 'deco', 'ornament.vox.txt'))
cli('op=work', 'sub=link', 'persona=apex-two', 'work=' + ASM, 'name=裝飾-2', 'source_work=' + w, 'at=0,0,0', 'note=步驟 16（TASK-0969）：Tim 2026-10-27「參考模型 圖紙 船身做出一些裝飾 曲線」', ok=(0, 2))
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-30:]))

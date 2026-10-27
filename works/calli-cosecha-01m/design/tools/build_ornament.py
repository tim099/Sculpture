# 出處：apex-two-galeon-01m/design/tools/build_ornament.py（康塞普西翁號步驟 16，照抄 —— 收穫號 TASK-1027）：cli／make／stamp 照本船 tools/build_decks.py
# 收穫號 TASK-1027 新的兩件子作品落格：-ornament（船頭寬帶、cheek、head timber；masks/deco/ornament.vox.txt）、-stern-glass（窗玻璃；masks/glass/stern_glass.vox.txt）
#   用法：python -I -X utf8 tools/build_ornament.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（之後的修正走 tools/delta_apply.py）；關聯已存在 ⇒ CLI 回 2、照樣往下
#   · 玻璃的關聯 meta material=glass（Ship_Materials：遊戲照這一格判透明、打破）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'calli-cosecha-01m'
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
    cli('op=work', 'sub=create', 'persona=calli', 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=800,320,640', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=calli', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=calli', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


PARTS = [
    ('ornament', '收穫號 裝飾（船頭 head 寬帶、cheek、head timber）', os.path.join('masks', 'deco', 'ornament.vox.txt'), '裝飾', None,
     'TASK-1027：船頭的 head 寬帶、cheek、head timber（照 Ship_Ends §4.4、康塞普西翁號步驟 17）'),
    ('stern-glass', '收穫號 窗玻璃（船尾 espejo 的窗＋stern walk 後面兩舷的窗；material=glass）', os.path.join('masks', 'glass', 'stern_glass.vox.txt'), '窗玻璃', {'material': 'glass'},
     'TASK-1027：窗的玻璃（Tim「窗戶可以改玻璃」；Ship_Materials）'),
]
for nm, title, rel, link, meta, note in PARTS:
    w = HULL + '-' + nm
    if make(w, title):
        stamp(w, os.path.join(design, rel))
    args = ['op=work', 'sub=link', 'persona=calli', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'note=' + note]
    if meta:
        args.append('meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    print(cli(*args, ok=(0, 2)).strip().splitlines()[-1])

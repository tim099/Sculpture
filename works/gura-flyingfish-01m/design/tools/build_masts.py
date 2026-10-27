# 抄來的（飛魚號 TASK-0971）：出處 ame-labelle-01m/design/tools/build_masts.py（拉貝爾號；作品 id、persona、船名、作品尺寸已換）
# 飛魚號 步驟 7（TASK-0971）；出處 calli-cosecha-01m/design/tools/build_masts.py（沒有 bonaventure、作品框換本船、孔 0 格就不刻）。
# 原檔頭：階段六落格：船頭牆給艏斜桅開孔（船殼，標記 艏斜桅孔）、建桅／艏斜桅子作品並貼清單、lateen 帆桁子作品（貼＋固定點）、帆桁模型（放在各自的桅子作品裡）、組裝件關聯
#   用法：python -I -X utf8 tools/build_masts.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼；模型同名 ⇒ 交給 CLI（ok 2）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-flyingfish-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
MASTS = [('mast-main', '主桅', '飛魚號 主桅（單桅，後傾 14°）'), ('bowsprit', '艏斜桅', '飛魚號 艏斜桅（10 m，仰 20°）')]   # 飛魚號：單桅


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def exists(w):
    return os.path.exists(os.path.join(WORKS, w, 'work.json'))


def stamp(work, path, extra=()):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if n == 0:
        return
    out = cli('op=stampvox', 'persona=gura', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0', *extra)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  stampvox %s：%d' % (os.path.basename(path), n))


# ① 船頭牆開孔（船殼）
marks = json.load(open(os.path.join(WORKS, HULL, 'marks.json'), encoding='utf-8'))
if not any(m.get('name') == '艏斜桅孔' for m in (marks.get('marks') if isinstance(marks, dict) else marks)):
    path = os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if n == 0:
        print('· 艏斜桅孔 0 格（艏斜桅從艏柱頭上越過去）⇒ 不刻')
    out = None if n == 0 else cli('op=carvevox', 'persona=gura', 'work=' + HULL, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out) if out else None
    if n and (not m or int(m.group(1).replace(',', '')) != n):
        print(out[-1500:]); raise SystemExit('✗ 艏斜桅孔')
    cli('op=work', 'sub=mark', 'persona=gura', 'work=' + HULL, 'name=艏斜桅孔', 'note=步驟 7：船頭牆給艏斜桅開孔 %d 格' % n)
    print('✓ 艏斜桅孔 %d' % n)
# ② 桅與艏斜桅子作品
for key, link, title in MASTS:
    w = '%s-%s' % (HULL, key)
    if not exists(w):
        cli('op=work', 'sub=create', 'persona=gura', 'work=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=400,160,320', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=gura', 'work=' + w, 'meters_per_voxel=0.1')
        stamp(w, os.path.join(design, 'masks', 'masts', key + '.vox.txt'))
        print('✓ 建立', w)
    cli('op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + link, 'source_work=' + w, 'at=0,0,0', 'note=步驟 7（TASK-0971）', ok=(0, 2))
# ③ lateen 帆桁子作品
LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
for key, v in LAT.items():
    w = '%s-yard-%s-lateen' % (HULL, key)
    if exists(w):
        continue
    cli('op=work', 'sub=create', 'persona=gura', 'work=' + w, 'title=飛魚號 帆桁 %s lateen（%.1f m）' % (key, v['len_m']), 'parent_work=' + HULL,
        'size=%d,%d,%d' % tuple(v['size']), 'tags=sub')
    cli('op=work', 'sub=update', 'persona=gura', 'work=' + w, 'meters_per_voxel=0.1')
    stamp(w, os.path.join(design, 'masks', 'yards', 'lateen-%s.vox.txt' % key))
    for an, at in sorted(v['anchors'].items()):
        cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'note=draft_masts.py')
    print('✓ 建立 %s（固定點 %d）' % (w, len(v['anchors'])))
# ④ 帆桁模型（放在各自的桅子作品裡）
P = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
for p in P:
    host = '%s-%s' % (HULL, 'bowsprit' if p['mast'] == 'bowsprit' else 'mast-' + p['mast'])
    cli('op=work', 'sub=model', 'persona=gura', 'work=' + host, 'name=' + p['name'], 'source_work=' + p['work'],
        'at=%g,%g,%g' % tuple(p['at']), 'pivot=%g,%g,%g' % tuple(p['pivot']), 'rotate=%g,%g,%g' % tuple(p['rotate']),
        'scale=%g,%g,%g' % tuple(p['scale']), 'meta=' + json.dumps(p['meta'], ensure_ascii=False, separators=(',', ':')), 'note=步驟 7 帆桁', ok=(0, 2))
print('✓ 帆桁模型 %d 根' % len(P))
print('\n'.join(l for l in cli('op=work', 'sub=links', 'work=' + ASM).splitlines() if l.startswith('- `')))

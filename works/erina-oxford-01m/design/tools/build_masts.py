# 牛津號 階段六落格：桅／艏斜桅子作品、後桅三角帆桁元件、艏斜桅開孔（carvevox 帶顏色守門）、帆桁外部模型、組裝件關聯
#   用法：python -I -X utf8 tools/build_masts.py <design>
#   · 每一步讀回 exit 0 才往下；子作品已存在 ⇒ 不重建、不重貼；模型已存在 ⇒ 跳過
#   · 結構照 calli-cosecha-01m/design/tools/build_masts.py、build_decks.py
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'erina-oxford-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
TITLE = {'main': '主桅（下桅、圓桅樓、上桅、上桅帆桅）', 'fore': '前桅（下桅、圓桅樓、上桅、上桅帆桅）', 'mizzen': '後桅（下桅、圓桅樓、上桅）', 'bowsprit': '艏斜桅'}
LINK = {'main': '主桅', 'fore': '前桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title, size='448,192,384'):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=erina', 'work=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=' + size, 'tags=sub')
    cli('op=work', 'sub=update', 'persona=erina', 'work=' + work, 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def lines_of(path):
    return sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))


def stamp(work, path, op='stampvox'):
    n = lines_of(path)
    out = cli('op=' + op, 'persona=erina', 'work=' + work, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s ≠ %d（%s）' % (got, n, work))
    print('  %s %s：%d' % (op, os.path.basename(path), n))


def anchors_of(work):
    a = json.load(open(os.path.join(WORKS, work, 'anchors.json'), encoding='utf-8'))
    return {x['name']: x['at'] for x in a.get('anchors', a)}


def models_of(work):
    p = os.path.join(WORKS, work, 'models.json')
    if not os.path.exists(p):
        return set()
    m = json.load(open(p, encoding='utf-8'))
    return {x['name'] for x in m.get('models', m)}


# 1. 艏斜桅開孔（先刻、再放艏斜桅 ⇒ 不重疊）
hd = os.path.join(design, 'masks', 'bowsprit_hole')
for f in sorted(os.listdir(hd)):
    w = f[:-len('.vox.txt')]
    marks = json.load(open(os.path.join(WORKS, w, 'marks.json'), encoding='utf-8')) if os.path.exists(os.path.join(WORKS, w, 'marks.json')) else {}
    if '艏斜桅孔' in json.dumps(marks, ensure_ascii=False):
        print('· 已刻過', w)
        continue
    stamp(w, os.path.join(hd, f), op='carvevox')
    cli('op=work', 'sub=mark', 'persona=erina', 'work=' + w, 'name=艏斜桅孔', 'note=階段六：艏斜桅穿過的格 %d（孔由艏斜桅填滿）' % lines_of(os.path.join(hd, f)))
# 2. 桅與艏斜桅
for k in ('main', 'fore', 'mizzen', 'bowsprit'):
    w = '%s-%s' % (HULL, 'bowsprit' if k == 'bowsprit' else 'mast-' + k)
    if make(w, '牛津號 ' + TITLE[k]):
        stamp(w, os.path.join(design, 'masks', 'masts', k + '.vox.txt'))
# 3. 後桅三角帆桁元件
LW = HULL + '-yard-mizzen-lateen'
anc = json.load(open(os.path.join(design, 'yard_lateen_anchors.json'), encoding='utf-8'))
nx = max(int(l.split(',')[0]) for l in open(os.path.join(design, 'masks', 'yards', 'lateen.vox.txt'), encoding='utf-8') if l.strip() and not l.startswith('#')) + 1
if make(LW, '後桅三角帆桁（17 世紀英國船、單根；沿 x、前端 +x；0.1 m）', size='%d,5,5' % nx):
    stamp(LW, os.path.join(design, 'masks', 'yards', 'lateen.vox.txt'))
    for nm, at in anc.items():
        cli('op=work', 'sub=anchor', 'persona=erina', 'work=' + LW, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'note=draft_masts.py')
    print('  固定點 %d' % len(anc))
# 4. 帆桁模型（放在各自的桅子作品裡）
place = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
for p in place:
    host = '%s-%s' % (HULL, 'bowsprit' if p['host'] == 'bowsprit' else 'mast-' + p['host'])
    if p['name'] in models_of(host):
        print('· 已有模型', host, p['name'])
        continue
    piv = p.get('pivot')
    if not piv:
        a = anchors_of(p['source_work'])['pivot']
        piv = [a[0] + 0.5, a[1] + 0.5, a[2] + 0.5]
    cli('op=work', 'sub=model', 'persona=erina', 'work=' + host, 'name=' + p['name'], 'source_work=' + p['source_work'],
        'pivot=%g,%g,%g' % tuple(piv), 'at=%g,%g,%g' % tuple(p['at']), 'rotate=%g,%g,%g' % tuple(p['rotate']), 'scale=%g' % p['scale'],
        'meta=' + json.dumps(p['meta'], ensure_ascii=False), 'note=階段六：帆桁（draft_masts.py）')
    print('  模型', host, p['name'], 'scale', p['scale'])
# 5. 組裝件關聯
for k in ('main', 'fore', 'mizzen', 'bowsprit'):
    w = '%s-%s' % (HULL, 'bowsprit' if k == 'bowsprit' else 'mast-' + k)
    cli('op=work', 'sub=link', 'persona=erina', 'work=' + ASM, 'name=' + LINK[k], 'source_work=' + w, 'at=0,0,0', 'note=階段六', ok=(0, 2))
print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-22:]))

# 塔爾塔納 步驟 7（TASK-1299）：建立三桅與兩根拉丁斜桁子作品、落格、固定點、關聯與模型擺放
#   用法：python -I -X utf8 tools/build_masts.py <design>
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'apex-one-tartane-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
yards_spec = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d：%s' % (r.returncode, ' '.join(args)))
    return out


def make(work, title, size_str, parent=HULL):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', 'persona=apex-one', 'id=' + work, 'title=' + title, 'parent_work=' + parent, 'size=' + size_str)
    cli('op=work', 'sub=update', 'persona=apex-one', 'work=' + work, 'meters_per_voxel=0.1', 'tags=sub')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=apex-one', 'work=' + work,
              'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        raise SystemExit('✗ placed %s != %d (%s)' % (got, n, work))
    print('  stampvox %s: %d' % (os.path.basename(path), n))


# 1. 建兩根帆桁子作品並登記固定點
for yname, ys in sorted(yards_spec.items()):
    w_y = '%s-yard-%s' % (HULL, yname.replace('_', '-'))
    sz = '%d,%d,%d' % tuple(ys['box'])
    if make(w_y, '塔爾塔納 拉丁斜桁 ' + yname, sz):
        stamp(w_y, os.path.join(design, 'masks', 'yards', yname + '.vox.txt'))
        for aname, (ax, ay, az) in sorted(ys['anchors'].items()):
            cli('op=work', 'sub=anchor', 'persona=apex-one', 'work=' + w_y, 'name=' + aname,
                'at=%d,%d,%d' % (ax, ay, az), 'note=步驟 7 帆桁固定點')

# 2. 建三根桅（fore / main / bowsprit）與把兩根帆桁當外部模型放進各自下桅子作品裡
MAST_NAMES = {
    'fore': ('桅-fore', '塔爾塔納 前桅（trinquet）', 'mast-fore'),
    'main': ('桅-main', '塔爾塔納 主桅（mestre）', 'mast-main'),
    'bowsprit': ('桅-bowsprit', '塔爾塔納 船首斜桅（bout-dehors）', 'bowsprit'),
}
for mk, (link_name, title, suffix) in MAST_NAMES.items():
    w_m = '%s-%s' % (HULL, suffix)
    if make(w_m, title, '360,192,320'):
        stamp(w_m, os.path.join(design, 'masks', 'masts', mk + '.vox.txt'))
    # 掛進組裝件（fore / main 帶帆桁標 kind=mast；bowsprit 只掛船首三角帆不標 kind=mast）
    largs = ['op=work', 'sub=link', 'persona=apex-one', 'work=' + ASM, 'name=' + link_name,
             'source_work=' + w_m, 'at=0,0,0', 'note=步驟 7 下桅關聯']
    if mk != 'bowsprit':
        largs.append('meta=' + json.dumps({'kind': 'mast', 'mast': mk}))
    cli(*largs, ok=(0, 2))

# 3. 帆桁擺入對應下桅（Ship_Masts §5：pivot、yard=gaff、rig=lateen、mast 對齊下桅、sail 綁帆）
for yname, ys in sorted(yards_spec.items()):
    mk = ys['mast']
    w_m = '%s-%s' % (HULL, 'mast-' + mk)
    w_y = '%s-yard-%s' % (HULL, yname.replace('_', '-'))
    mname = 'yard-' + ys['sail']
    piv_s = '%.1f,%.1f,%.1f' % tuple(ys['pivot'])
    at_s = '%.2f,%.2f,%.2f' % tuple(ys['at'])
    rot_s = '0,%g,0' % ys['tilt_deg']
    meta_obj = {
        'kind': 'yard', 'mast': mk, 'yard': 'gaff', 'rig': 'lateen', 'sail': ys['sail'],
        'length_m': ys['len_m'], 'diameter_m': ys['diam_m'],
        'pivot_anchor': 'pivot', 'turn_axis': 'z',
        'rotate_y_deg': ys['tilt_deg'], 'rotate_z_deg': 0,
    }
    cli('op=work', 'sub=model', 'persona=apex-one', 'work=' + w_m, 'name=' + mname,
        'source_work=' + w_y, 'pivot=' + piv_s, 'at=' + at_s, 'rotate=' + rot_s, 'scale=1',
        'meta=' + json.dumps(meta_obj), 'note=步驟 7 拉丁斜桁外部模型（pivot 繞桅轉、rig=lateen）', ok=(0, 2))

print(cli('op=work', 'sub=links', 'work=' + ASM))
print(cli('op=work', 'sub=models', 'work=' + ASM))

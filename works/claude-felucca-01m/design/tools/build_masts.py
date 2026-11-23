# 出處：claude-baghlah-01m/design/tools/build_masts.py（星辰號；它出自收穫號 calli-cosecha-01m/design/tools/build_masts.py）——改給海鷗號（TASK-0024 步驟 7）。
# 步驟 7 落格：桅／船頭那根桿的子作品、三角帆桁子作品（＋固定點）、帆桁模型放在它那根桅的子作品裡、組裝件關聯（桅 meta kind=mast＋mast=）。
#   用法：python -I -X utf8 tools/build_masts.py <stage>   stage = parts | yards | links
#   · 只認 exit 0（星辰號步驟 6 學到的：exit 2 會把被擋下的關聯藏起來）；第一個不是 0 就停。
#   · 已經存在的子作品不重建、不重貼。
#   · 船頭那根桿的關聯不標 kind=mast：沒有帆桁綁 bowsprit ⇒ 匯入檢查會報 ⚠（星辰號步驟 14 的教訓，它的 foc 桿同樣不標）。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stage = sys.argv[1]
HULL = 'claude-felucca-01m'
ASM = HULL + '-assembly'
PERSONA = 'Claude-Ojousama'
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
WORKS = os.path.dirname(os.path.dirname(HERE))
NOTE = '步驟 7（TASK-0024；design/draft_masts.py）'
PARTS = [('mast-main', 'main', '190,161,180', '海鷗號 主桅（直立，舷頂以上 8 m）', '主桅', {'kind': 'mast', 'mast': 'main'}),
         ('mast-fore', 'fore', '190,161,180', '海鷗號 前桅（往前傾 8°，平台以上 6 m）', '前桅', {'kind': 'mast', 'mast': 'fore'}),
         ('tack-spar', 'tack_spar', '190,161,180', '海鷗號 船頭那根桿（前帆的 tack，4.6 m）', '船頭桿', None)]


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        print(out[-2000:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args)))
    return out


def exists(w):
    return os.path.exists(os.path.join(WORKS, w, 'work.json'))


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + work, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n)
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d (%s %s)' % (got, n, work, os.path.basename(path)))
    print('  stampvox %s %s: %d' % (work, os.path.basename(path), n))


def create(w, title, size):
    cli('op=work', 'sub=create', 'persona=' + PERSONA, 'id=' + w, 'title=' + title, 'parent_work=' + HULL, 'size=' + size)
    cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=0.1', 'tags=sub')
    print('✓ created', w)


if stage == 'parts':
    for key, fn, size, title, _, _ in PARTS:
        w = '%s-%s' % (HULL, key)
        if exists(w):
            print('· exists', w)
            continue
        create(w, title, size)
        stamp(w, os.path.join(HERE, 'masks', 'masts', fn + '.vox.txt'))
elif stage == 'yards':
    LAT = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))
    for key, v in LAT.items():
        w = '%s-yard-%s' % (HULL, key)
        if exists(w):
            print('· exists', w)
            continue
        create(w, '海鷗號 %s三角帆桁（%.1f m）' % ({'main': '主桅', 'fore': '前桅'}[key], v['len_m']), '%d,%d,%d' % tuple(v['size']))
        stamp(w, os.path.join(HERE, 'masks', 'yards', 'lateen-%s.vox.txt' % key))
        for an, at in sorted(v['anchors'].items()):
            cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'note=' + NOTE + '：帆桁固定點')
        print('  anchors %s: %d' % (w, len(v['anchors'])))
elif stage == 'links':
    for key, fn, size, title, link, meta in PARTS:
        args = ['op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + link, 'source_work=%s-%s' % (HULL, key), 'at=0,0,0',
                'note=%s：%s' % (NOTE, title)]
        if meta:
            args.append('meta=' + json.dumps(meta, separators=(',', ':')))
        cli(*args)
        print('✓ link', link)
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        cli('op=work', 'sub=model', 'persona=' + PERSONA, 'work=%s-%s' % (HULL, p['host']), 'name=' + p['name'], 'source_work=' + p['work'],
            'at=%g,%g,%g' % tuple(p['at']), 'pivot=%g,%g,%g' % tuple(p['pivot']), 'rotate=%g,%g,%g' % tuple(p['rotate']),
            'scale=%g,%g,%g' % tuple(p['scale']), 'meta=' + json.dumps(p['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=%s：三角帆桁（rig=lateen；yard=gaff）' % NOTE)
        print('✓ model', p['host'], p['name'])
    print('\n'.join(cli('op=work', 'sub=links', 'work=' + ASM).splitlines()[-30:]))
else:
    raise SystemExit('stage = parts | yards | links')

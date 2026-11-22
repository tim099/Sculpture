# 步驟 7 落格：建立三桅、6 根 yard=course 主下橫桁與 22 根弧形實體竹篾子作品並掛載進組裝件
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
sys.path.insert(0, HERE)
from wio import cli, PERSONA, HULL, ASM

sys.stdout.reconfigure(encoding='utf-8')


def make(work, title, size='512,256,512'):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', f'persona={PERSONA}', f'work={work}', f'title={title}',
        f'parent_work={HULL}', f'size={size}', 'tags=sub')
    cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={work}', 'meters_per_voxel=0.1')
    print('✓ 建立', work)
    return True


def stamp(work, path):
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if n == 0:
        return
    out = cli('op=stampvox', f'persona={PERSONA}', f'work={work}',
              'voxels=' + os.path.abspath(path).replace('\\', '/'),
              'at=0,0,0', f'expect_pixels={n}', 'draft=0', 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit(f'✗ placed {got} != {n} ({work})')
    print(f'  stampvox {os.path.basename(path)}：{n}')


def fmt_vec(v):
    return ','.join(f'{x:g}' for x in v)


def main():
    spec = json.load(open(os.path.join(DESIGN, 'masts_placement.json'), encoding='utf-8'))
    om = os.path.join(DESIGN, 'masks', 'masts')

    # 1. 建 6 根 yard=course 帆桁子作品＋錨點
    for k, yt in spec['yard_templates'].items():
        w = yt['work']
        if make(w, yt['title'], size=fmt_vec(yt['size'])):
            stamp(w, os.path.join(om, yt['mask']))
            for an_k, an_v in sorted(yt['anchors'].items()):
                cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}',
                    f'name={an_k}', f'at={an_v[0]},{an_v[1]},{an_v[2]}', 'note=步驟 7：帆桁固定點')

    # 2. 建 3 根竹篾通用模板子作品＋錨點＋work meta
    for mk, bt in spec['batten_templates'].items():
        w = bt['work']
        if make(w, bt['title'], size=fmt_vec(bt['size'])):
            stamp(w, os.path.join(om, bt['mask']))
            for an_k, an_v in sorted(bt['anchors'].items()):
                cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}',
                    f'name={an_k}', f'at={an_v[0]},{an_v[1]},{an_v[2]}', 'note=步驟 7：竹篾固定點')
            cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={w}', 'part=work',
                'meta={"material":"bamboo","render":"pole"}', 'note=步驟 7：實體竹篾桿材質與細桿平滑')

    # 3. 建 3 根桅子作品＋錨點，並把帆桁＋竹篾模型掛進去
    for mk, mspec in spec['masts'].items():
        mw = mspec['work']
        if make(mw, mspec['title']):
            stamp(mw, os.path.join(om, mspec['mask']))
            for an_k, an_v in sorted(mspec['anchors'].items()):
                cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={mw}',
                    f'name={an_k}', f'at={an_v[0]},{an_v[1]},{an_v[2]}', 'note=步驟 7：桅固定點')

        pl = spec['placements'][mk]
        for pos in ('upper', 'lower'):
            fr = pl['frames'][pos]
            cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={mw}',
                f"name={fr['label']}", f"source_work={fr['work']}",
                'at=' + fmt_vec(fr['at']), 'pivot=' + fmt_vec(fr['pivot']),
                'rotate=' + fmt_vec(fr['rotate']), 'scale=' + fmt_vec(fr['scale']),
                'meta=' + json.dumps(fr['meta'], ensure_ascii=False, separators=(',', ':')),
                'note=步驟 7：硬骨帆桁 yard=course', ok=(0, 2))
        for rd in pl['rods']:
            cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={mw}',
                f"name={rd['label']}", f"source_work={rd['work']}",
                'at=' + fmt_vec(rd['at']), 'pivot=' + fmt_vec(rd['pivot']),
                'rotate=' + fmt_vec(rd['rotate']), 'scale=' + fmt_vec(rd['scale']),
                'meta=' + json.dumps(rd['meta'], ensure_ascii=False, separators=(',', ':')),
                'note=步驟 7：實體弧形竹篾 yard=batten', ok=(0, 2))
        print(f"  ✓ {mw} 掛載 2 帆桁 + {len(pl['rods'])} 竹篾")

        cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}',
            f"name={mspec['link']}", f'source_work={mw}', 'at=0,0,0',
            'meta=' + json.dumps(mspec['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=步驟 7：桅（kind=mast）', ok=(0, 2))

    print(cli('op=work', 'sub=models', f'work={HULL}-mast-fore'))


if __name__ == '__main__':
    main()

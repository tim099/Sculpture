# 步驟 9c 落格：建立砲具子作品、下 72 枚環錨點、以 kind=gunfittings 掛入組裝件並拉 120 條砲索＋ropecheck
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
sys.path.insert(0, HERE)
from wio import cli, PERSONA, HULL, ASM

sys.stdout.reconfigure(encoding='utf-8')


def main():
    spec = json.load(open(os.path.join(DESIGN, 'gunfittings_spec.json'), encoding='utf-8'))
    w = spec['work']
    gp = os.path.join(DESIGN, 'masks', 'guns', 'gunfittings.vox.txt')

    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', f'persona={PERSONA}', f'work={w}', f"title={spec['title']}",
            f'parent_work={HULL}', 'size=512,256,512', 'tags=sub')
        cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={w}', 'meters_per_voxel=0.1')
        n = spec['cells']
        out = cli('op=stampvox', f'persona={PERSONA}', f'work={w}',
                  'voxels=' + os.path.abspath(gp).replace('\\', '/'),
                  'at=0,0,0', f'expect_pixels={n}', 'draft=0', 'share=0')
        m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
        got = int(m.group(1).replace(',', '')) if m else None
        assert got == n, f'placed {got} != {n}'
        for ak, (x, y, z) in sorted(spec['anchors'].items()):
            cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}',
                f'name={ak}', f'at={x},{y},{z}', 'note=步驟 9：砲環固定點')
        print(f'✓ 建立 {w}：{n} 格, {len(spec["anchors"])} 固定點')

    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}',
        f"name={spec['link']}", f'source_work={w}', 'at=0,0,0',
        'meta={"kind":"gunfittings"}', 'note=步驟 9：砲具（Ship_Guns §4.4）', ok=(0, 2))

    for rp in spec['ropes']:
        cli('op=work', 'sub=rope', f'persona={PERSONA}', f'work={ASM}',
            f"name={rp['name']}", f"from={rp['from']}", f"to={rp['to']}",
            f"slack={rp['slack']}", f"thickness={rp['thickness']}", f"color={rp['color']}",
            f"group={rp['group']}", 'note=步驟 9：砲索', ok=(0, 2))
        cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={ASM}',
            'part=rope', f"name={rp['name']}",
            'meta=' + json.dumps(rp['meta'], ensure_ascii=False, separators=(',', ':')), ok=(0, 2))

    print(f'✓ 掛載 {len(spec["ropes"])} 條砲索')
    print(cli('op=work', 'sub=ropecheck', f'persona={PERSONA}', f'work={ASM}'))


if __name__ == '__main__':
    main()

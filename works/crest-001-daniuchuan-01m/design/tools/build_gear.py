# 步驟 10 落格：建立水線下火藥庫（＋16 火藥桶）、貨艙口蓋、尾樓艙門、廚房灶、杉板小艇、絞盤、羅經櫃與 3 盞船燈
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
    out = cli('op=stampvox', f'persona={PERSONA}', f'work={work}',
              'voxels=' + os.path.abspath(path).replace('\\', '/'),
              'at=0,0,0', f'expect_pixels={n}', 'draft=0', 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    assert got == n, f'placed {got} != {n}'
    print(f'  stampvox {os.path.basename(path)}：{n}')


def fmt_vec(v):
    return ','.join(f'{x:g}' for x in v)


def main():
    spec = json.load(open(os.path.join(DESIGN, 'gear_spec.json'), encoding='utf-8'))
    og = os.path.join(DESIGN, 'masks', 'gear')

    # 1. 火藥庫＋16 火藥桶＋關聯（hoist 待步驟 14 ids 解析後補或更新）
    mag = spec['magazine']
    mw = mag['work']
    if make(mw, mag['title']):
        stamp(mw, os.path.join(og, 'magazine.vox.txt'))
        for ak, (x, y, z) in mag['anchors'].items():
            cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={mw}',
                f'name={ak}', f'at={x},{y},{z}', 'note=步驟 10：火藥庫點位')
        for b in mag['barrels']:
            cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={mw}',
                f"name={b['name']}", f"source_work={b['source']}",
                'at=' + fmt_vec(b['at']), 'pivot=' + fmt_vec(b['pivot']),
                'rotate=' + fmt_vec(b['rotate']), f"scale={b['scale']:g}",
                'meta=' + json.dumps(b['meta'], ensure_ascii=False, separators=(',', ':')),
                'note=步驟 10：火藥桶', ok=(0, 2))
        print(f"  ✓ 掛載 {len(mag['barrels'])} 火藥桶進火藥庫")

    cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}',
        f"name={mag['link']}", f'source_work={mw}', 'at=0,0,0',
        'meta=' + json.dumps(mag['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=步驟 10：水線下火藥庫（步驟 14 跑完 ids 後補 hoist）', ok=(0, 2))

    # 2. 貨艙口蓋子作品＋鉸鏈＋掛載於上戰棚
    ch = spec['cargo_hatch']
    chw = ch['work']
    if make(chw, ch['title'], size=fmt_vec(ch['size'])):
        stamp(chw, os.path.join(og, 'cargo_hatch.vox.txt'))
        for ak, (x, y, z) in ch['anchors'].items():
            cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={chw}',
                f'name={ak}', f'at={x},{y},{z}', 'note=步驟 10：貨艙口蓋鉸鏈')
    mt = ch['mount']
    cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={mt["host"]}',
        f"name={mt['name']}", f'source_work={chw}',
        'at=' + fmt_vec(mt['at']), 'pivot=' + fmt_vec(mt['pivot']),
        'rotate=' + fmt_vec(mt['rotate']), f"scale={mt['scale']:g}",
        'meta=' + json.dumps(mt['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=步驟 10：上戰棚貨艙口蓋', ok=(0, 2))

    # 3. 尾樓門、廚房、小艇、絞盤、羅經櫃、3 盞燈掛進對應甲板
    for it in spec['ext_items']:
        sc_arg = fmt_vec(it['scale']) if isinstance(it['scale'], list) else f"{it['scale']:g}"
        cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={it["host"]}',
            f"name={it['name']}", f"source_work={it['source']}",
            'at=' + fmt_vec(it['at']), 'pivot=' + fmt_vec(it['pivot']),
            'rotate=' + fmt_vec(it['rotate']), f'scale={sc_arg}',
            'meta=' + json.dumps(it['meta'], ensure_ascii=False, separators=(',', ':')),
            f"note=步驟 10：{it['name']}", ok=(0, 2))
    print(f"✓ 掛載 {len(spec['ext_items']) + 1} 件甲板裝備")


if __name__ == '__main__':
    main()

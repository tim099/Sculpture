# 步驟 9b 落格：先刻迴旋砲舷牆淺凹口與坎邊朱漆、重貼 ch-miz 靜索固定點（避開 71..89 切口），再將 30 門火砲（＋6 門座 -mount）全部掛入對應甲板
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, DESIGN)
from wio import cli, export_list, PERSONA, HULL, ASM
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')


def count_lines(p):
    return sum(1 for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#'))


def fmt_vec(v):
    return ','.join(f'{x:g}' for x in v)


def main():
    # 1. 刻除 6 門佛郎機迴旋砲所需的 3 段舷牆淺凹口並補齊坎面朱漆（冪等檢查）
    carve_p = os.path.join(DESIGN, 'masks', 'guns', 'swivel_rail_carve.vox.txt')
    sill_p = os.path.join(DESIGN, 'masks', 'guns', 'swivel_rail_sill.vox.txt')
    cur_hull = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in export_list(HULL, links='none')}
    need_carve = 0
    with open(carve_p, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if l and not l.startswith('#'):
                x, y, z, _ = map(int, l.split(','))
                if (x, y, z) in cur_hull:
                    need_carve += 1
    if need_carve:
        assert need_carve == count_lines(carve_p), f'swivel carve partial {need_carve}'
        cli('op=carvevox', f'persona={PERSONA}', f'work={HULL}',
            'voxels=' + os.path.abspath(carve_p).replace('\\', '/'),
            'at=0,0,0', f'expect_pixels={need_carve}', 'share=0',
            'note=步驟 9：迴旋砲舷牆淺凹口刻除')
        print(f'✓ carve swivel rails: {need_carve}')
    else:
        print('· swivel rails 已刻除')

    cur_hull2 = {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in export_list(HULL, links='none')}
    need_sill = 0
    with open(sill_p, encoding='utf-8') as f:
        for l in f:
            l = l.strip()
            if l and not l.startswith('#'):
                x, y, z, c = map(int, l.split(','))
                if cur_hull2.get((x, y, z)) != c:
                    need_sill += 1
    if need_sill:
        ns = count_lines(sill_p)
        cli('op=stampvox', f'persona={PERSONA}', f'work={HULL}',
            'voxels=' + os.path.abspath(sill_p).replace('\\', '/'),
            'at=0,0,0', 'overwrite=1', f'expect_pixels={ns}', 'draft=0', 'share=0',
            'note=步驟 9：迴旋砲坎緣朱漆')
        print(f'✓ paint swivel sills: {ns}')

    # 2. 更新尾桅 ch-miz 靜索錨點避開 71..89 切口（改到 x=100, 95, 90）
    plan = json.load(open(os.path.join(DESIGN, 'plan.json'), encoding='utf-8'))
    L = HL.Lines(plan)
    YC = int(plan['space']['yc'])
    for i, xw in enumerate((100, 95, 90), 1):
        zt = int(round(float(L.top_z(xw + 0.5)))) - 1
        yo = int(math.floor(float(L.hb(xw + 0.5, zt + 0.5)))) + 1
        for sd, y_v in (('S', YC + yo), ('P', YC - yo)):
            cli('op=work', 'sub=unanchor', f'persona={PERSONA}', f'work={ASM}', f'name=ch-miz-{sd}{i}', ok=(0, 2))
            cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={ASM}',
                f'name=ch-miz-{sd}{i}', f'at={xw},{y_v},{zt}', 'note=步驟 9：避開尾樓迴旋砲缺口')
    print('✓ updated ch-miz shroud anchors to x=100,95,90')

    # 3. 依 guns_placement.json 掛入 30 門砲（含 6 門座 -mount）至對應甲板子作品
    GB = plan['guns_build']
    deck_works = GB['deck_works']
    guns = json.load(open(os.path.join(DESIGN, 'guns_placement.json'), encoding='utf-8'))
    for g in guns:
        dw = deck_works[g['deck']]
        cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={dw}',
            f"name={g['name']}", f"source_work={g['source']}",
            'at=' + fmt_vec(g['at']), 'pivot=' + fmt_vec(g['pivot']),
            'rotate=' + fmt_vec(g['rotate']), f"scale={g['scale']:g}",
            'meta=' + json.dumps(g['meta'], ensure_ascii=False, separators=(',', ':')),
            f"note=步驟 9：{g['type']} 火砲", ok=(0, 2))
        if g['type'] == 'pierrier':
            cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={dw}',
                f"name={g['name']}-mount", f"source_work={g['mount_source']}",
                'at=' + fmt_vec(g['at']), 'pivot=' + fmt_vec(g['pivot']),
                'rotate=' + fmt_vec(g['rotate']), f"scale={g['scale']:g}",
                'meta={"kind":"gunmount"}',
                'note=步驟 9：pierrier 迴旋砲底座', ok=(0, 2))
    print(f'✓ 掛載 {len(guns)} 門火砲 (+ 6 底座)')

    for dk, dw in deck_works.items():
        print(f'--- {dk} ({dw}) ---')
        print('\n'.join(cli('op=work', 'sub=models', f'work={dw}').splitlines()[-12:]))


if __name__ == '__main__':
    main()

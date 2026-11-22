# 步驟 5 落格：建立甲板／梯子／艙房字作品、貼清單、下錨點、建關聯（組裝件 → 甲板 → 梯子／艙房）
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
sys.path.insert(0, HERE)
from wio import cli, PERSONA, HULL, ASM

sys.stdout.reconfigure(encoding='utf-8')


def make(work, title):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', f'persona={PERSONA}', f'work={work}', f'title={title}',
        f'parent_work={HULL}', 'size=512,256,512', 'tags=sub')
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


def main():
    plan = json.load(open(os.path.join(DESIGN, 'plan.json'), encoding='utf-8'))
    decks_meta = json.load(open(os.path.join(DESIGN, 'decks_meta.json'), encoding='utf-8'))
    pts = json.load(open(os.path.join(DESIGN, 'ladder_points.json'), encoding='utf-8'))
    room_pts = json.load(open(os.path.join(DESIGN, 'room_points.json'), encoding='utf-8'))
    names = plan['decks_build']['names']

    for k in plan['decks'].keys():
        w = f'{HULL}-deck-{k}'
        if make(w, f'明鄭一號大鳥船 甲板 {names[k]}'):
            stamp(w, os.path.join(DESIGN, 'masks', 'decks', f'{k}.vox.txt'))

    ups = sorted({v['up'] for v in pts.values()})
    for k in ups:
        w = f'{HULL}-ladders-{k}'
        if make(w, f'明鄭一號大鳥船 梯子（上到{names[k]}）'):
            stamp(w, os.path.join(DESIGN, 'masks', 'ladders', f'{k}.vox.txt'))
            cnt = 0
            for nm, v in sorted(pts.items()):
                if v['up'] != k:
                    continue
                for pk in ('foot', 'lo', 'hi', 'head'):
                    x, y, z = v['points'][pk]
                    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}',
                        f'name={nm}.{pk}', f'at={x},{y},{z}',
                        'note=步驟 5：梯子固定點')
                    cnt += 1
            print(f'  梯子固定點 {cnt}')

    for k, rmap in sorted(room_pts.items()):
        w = f'{HULL}-rooms-{k}'
        if make(w, f'明鄭一號大鳥船 機能艙房 {names[k]}'):
            stamp(w, os.path.join(DESIGN, 'masks', 'rooms', f'{k}.vox.txt'))
            for rname, rv in sorted(rmap.items()):
                for pk in ('min', 'max', 'door'):
                    x, y, z = rv[pk]
                    cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}',
                        f'name={rname}.{pk}', f'at={x},{y},{z}',
                        'note=步驟 5：機能艙房框')
            print(f'  艙房固定點 {len(rmap) * 3}')

    for k in ups:
        cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={HULL}-deck-{k}',
            'name=梯子', f'source_work={HULL}-ladders-{k}', 'at=0,0,0',
            'meta={"kind":"ladders"}', 'note=步驟 5：上到此層的梯子', ok=(0, 2))

    for k in sorted(room_pts.keys()):
        cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={HULL}-deck-{k}',
            'name=艙房', f'source_work={HULL}-rooms-{k}', 'at=0,0,0',
            'meta={"kind":"rooms"}', 'note=步驟 5：機能艙房', ok=(0, 2))

    for k in plan['decks'].keys():
        cli('op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}',
            f'name=甲板-{k}', f'source_work={HULL}-deck-{k}', 'at=0,0,0',
            'meta=' + json.dumps(decks_meta[k], ensure_ascii=False, separators=(',', ':')),
            'note=步驟 5（TASK-1316）', ok=(0, 2))

    print('\n'.join(cli('op=work', 'sub=links', f'work={ASM}').splitlines()[-35:]))


if __name__ == '__main__':
    main()

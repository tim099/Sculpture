# 步驟 6 落格：建立艉樓窗玻璃、艉迴廊＋雙層戰棚女牆、船首繪飾、高尾樓牌匾與 6 具護舷靠墊
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
sys.path.insert(0, HERE)
from wio import cli, PERSONA, HULL, ASM

sys.stdout.reconfigure(encoding='utf-8')


def make(work, title, size='512,256,512', mpv='0.1'):
    if os.path.exists(os.path.join(WORKS, work, 'work.json')):
        print('· 已有', work)
        return False
    cli('op=work', 'sub=create', f'persona={PERSONA}', f'work={work}', f'title={title}',
        f'parent_work={HULL}', f'size={size}', 'tags=sub')
    cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={work}', f'meters_per_voxel={mpv}')
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


def restamp_if_changed(work, mask_path, size_list, mpv='0.05'):
    wjson_p = os.path.join(WORKS, work, 'work.json')
    n = sum(1 for l in open(mask_path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    if not os.path.exists(wjson_p):
        sz = ','.join(map(str, size_list))
        make(work, work, size=sz, mpv=mpv)
        stamp(work, mask_path)
        return
    st_out = cli('op=stats', f'work={work}')
    m_s = re.search(r'space_size\s*=\s*(\d+),(\d+),(\d+)', st_out)
    old_sz = [int(m_s.group(1)), int(m_s.group(2)), int(m_s.group(3))] if m_s else list(size_list)
    m_v = re.search(r'voxels[^\d]*(\d[\d,]*)', st_out)
    old_n = int(m_v.group(1).replace(',', '')) if m_v else -1
    if old_sz == size_list and old_n == n:
        print(f'· 沒變 {work} ({old_n} 格)')
        return
    if old_n != 0:
        cli('op=carve', f'persona={PERSONA}', f'work={work}',
            'x1=0', f'x2={old_sz[0] - 1}', 'y1=0', f'y2={old_sz[1] - 1}', 'z1=0', f'z2={old_sz[2] - 1}')
    if old_sz != size_list:
        cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={work}',
            f"size={','.join(map(str, size_list))}", f'meters_per_voxel={mpv}')
    stamp(work, mask_path)
    print(f'✓ 更新 {work} ({old_n} -> {n} 格, size {old_sz} -> {size_list})')


def main():
    spec = json.load(open(os.path.join(DESIGN, 'deco_spec.json'), encoding='utf-8'))
    od = os.path.join(DESIGN, 'masks', 'deco')

    for lk in spec['links']:
        w = lk['work']
        if make(w, lk['title']):
            stamp(w, os.path.join(od, lk['mask']))
        args = ['op=work', 'sub=link', f'persona={PERSONA}', f'work={ASM}',
                f"name={lk['name']}", f'source_work={w}', 'at=0,0,0',
                'note=步驟 6（TASK-1316）']
        if lk.get('meta'):
            args.append('meta=' + json.dumps(lk['meta'], ensure_ascii=False, separators=(',', ':')))
        cli(*args, ok=(0, 2))
        print(f"  link {lk['name']} -> {w}")

    models_p = os.path.join(WORKS, ASM, 'models.json')
    existing_models = {}
    if os.path.exists(models_p):
        for m in json.load(open(models_p, encoding='utf-8')).get('models', []):
            existing_models[m['name']] = m

    for cm in spec['custom_models']:
        w = cm['work']
        sz = ','.join(map(str, cm['size']))
        mask_p = os.path.join(od, cm['mask'])
        if make(w, cm['title'], size=sz, mpv='0.05'):
            stamp(w, mask_p)
        else:
            restamp_if_changed(w, mask_p, cm['size'], mpv='0.05')
        ex = existing_models.get(cm['name'])
        meta = dict(cm['meta'])
        if ex and isinstance(ex.get('meta'), dict):
            for k_m, v_m in ex['meta'].items():
                if k_m not in meta:
                    meta[k_m] = v_m
        if ex and (ex.get('at') != cm['at'] or ex.get('pivot') != cm['pivot'] or ex.get('rotate') != cm['rotate'] or ex.get('scale') != [cm['scale']] * 3):
            cli('op=work', 'sub=unmodel', f'persona={PERSONA}', f'work={ASM}', f"name={cm['name']}")
        cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={ASM}',
            f"name={cm['name']}", f'source_work={w}',
            'at=' + fmt_vec(cm['at']), 'pivot=' + fmt_vec(cm['pivot']),
            'rotate=' + fmt_vec(cm['rotate']), f"scale={cm['scale']:g}",
            'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')),
            'note=步驟 6：deco=1 裝飾模型', ok=(0, 2))
        print(f"  model {cm['name']} -> {w}")

    for fd in spec['fenders']:
        cli('op=work', 'sub=model', f'persona={PERSONA}', f'work={ASM}',
            f"name={fd['name']}", f"source_work={fd['source']}",
            'at=' + fmt_vec(fd['at']), 'pivot=' + fmt_vec(fd['pivot']),
            'rotate=' + fmt_vec(fd['rotate']), f"scale={fd['scale']:g}",
            'meta=' + json.dumps(fd['meta'], ensure_ascii=False, separators=(',', ':')),
            'note=步驟 6：複用護舷 deco=1', ok=(0, 2))
    print(f"  ✓ 掛載 {len(spec['fenders'])} 具護舷靠墊 (deco=1)")

    print('\n'.join(cli('op=work', 'sub=models', f'work={ASM}').splitlines()[-20:]))


if __name__ == '__main__':
    main()

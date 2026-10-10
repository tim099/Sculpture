# 從作品 events/ 重播出 voxel 表（不經過引擎；拿來獨立核對）。
# replay(work_dir) -> dict[(x,y,z)] = (color, event 檔名)
import glob, json, os


def replay(work_dir, upto=None):
    vox = {}
    for f in sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json'))):
        name = os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f)
        if upto and name >= upto:
            break
        e = json.load(open(f, encoding='utf-8'))
        op = e.get('op')
        if op == 'box':
            c = e.get('color')
            for v in e['placed_voxels']:
                vox[tuple(v[:3])] = (v[3] if len(v) > 3 else c, name)
        elif op == 'carve':
            for v in e['carved_voxels']:
                vox.pop(tuple(v[:3]), None)
        elif op in ('stampimg', 'stamp2d', 'stampvox'):
            for v in e['placed_colored']:
                vox[tuple(v[:3])] = (v[3], name)
        else:
            raise SystemExit('未知 op %s @ %s' % (op, name))
    return vox


if __name__ == '__main__':
    import sys
    v = replay(sys.argv[1])
    print('total', len(v))

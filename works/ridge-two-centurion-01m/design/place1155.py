# TASK-1155 換砲擺法：沿舊砲的砲軸放新砲，新砲口先對到舊砲口的位置，撞到就沿砲軸往裡退（0.5 格一步）到零碰撞（格心＋八角，Ship_Guns §4.2）。
#   樞軸砲（meta mount=pivot）：轉軸中心照舊（舊砲尾 ＋ 砲軸 × 舊 meta pivot），每個 ports 角度都量；換砲門那段（拉進 runin 格、每 2.5° 一步）也量。
#   meta pivot 照新砲尾重算 ⇒ 遊戲轉的中心跟以前同一點。
#   用法：python -I -X utf8 place1155.py <組裝件> <砲種,…> [--apply]   （--apply ⇒ 照結果重掛模型，meta 帶著原本的 id）
import sys, os, json, math, subprocess
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
WORKS = 'D:/Unity/Valhalla/Sculpture/works'
sys.path.insert(0, WORKS + '/ridge-two-centurion-01m/design/tools')
from wio import export_list

ASM, CODES, APPLY = sys.argv[1], sys.argv[2].split(','), '--apply' in sys.argv
V = json.load(open(WORKS + '/ridge-two-centurion-01m/design/verify_guns1155.json', encoding='utf-8'))
SLIDE = json.load(open(WORKS + '/ridge-two-centurion-01m/design/guns1155.json', encoding='utf-8'))['colors']['slide']
OFF = np.array([[0.5, 0.5, 0.5]] + [[a, b, c] for a in (0.001, 0.999) for b in (0.001, 0.999) for c in (0.001, 0.999)])


def anchors(work):
    return {q['name']: q['at'] for q in json.load(open('%s/%s/anchors.json' % (WORKS, work), encoding='utf-8'))['anchors']}


def comp_cells(code):
    p = WORKS + '/ridge-two-centurion-01m/design/masks/guns1155/%s.vox.txt' % code
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def rotz(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.stack([v[..., 0] * c - v[..., 1] * s, v[..., 0] * s + v[..., 1] * c, v[..., 2]], axis=-1)


def xf(Q, at, pivot, scale, phi, mirror):
    """模型座標（連續）⇒ 宿主座標：at ＋ Rz(phi) · mirror_y( scale · (Q − pivot) )。"""
    v = scale * (np.asarray(Q, float) - np.asarray(pivot, float))
    if mirror == 'y':
        v = v * np.array([1, -1, 1])
    return np.asarray(at, float) + rotz(v, phi)


def key(w):
    w = np.floor(w).astype(np.int64)
    return (w[..., 0] * 1000 + w[..., 1]) * 1000 + w[..., 2]


def main():
    links = json.load(open('%s/%s/links.json' % (WORKS, ASM), encoding='utf-8'))['links']
    hostoff = {l['work']: np.array(l.get('at') or [0, 0, 0], float) for l in links if not l.get('mirror')}
    print('匯出組裝件（links 照開關）…', flush=True)
    A = export_list(ASM, None, links=None)
    occ = np.unique(key(A[:, :3].astype(float) + 0.5))
    print('組裝件', len(A), '格', flush=True)
    hosts = sorted(set(l['work'] for l in links))
    todo = []
    for h in hosts:
        p = '%s/%s/models.json' % (WORKS, h)
        if not os.path.exists(p):
            continue
        for m in json.load(open(p, encoding='utf-8'))['models']:
            me = m.get('meta') or {}
            if me.get('kind') == 'gun' and me.get('gun') in CODES and m['work'] != V[me['gun']]['work']:
                todo.append((h, m))
    out = []
    for h, m in todo:
        me = m['meta']
        code = me['gun']
        Vn = V[code]
        oa = anchors(m['work'])
        off = hostoff.get(h, np.zeros(3))
        sc0, phi, mir = m['scale'][0], m['rotate'][2], (m.get('mirror') or '')
        omz = xf(np.array(oa['muzzle']) + 0.5, m['at'], m['pivot'], sc0, phi, mir)
        obr = xf(np.array(oa['breech']) + 0.5, m['at'], m['pivot'], sc0, phi, mir)
        d = (omz - obr) * np.array([1, 1, 0]); d /= np.linalg.norm(d)
        cells = comp_cells(code)
        sl = cells[:, 3] == SLIDE
        pts = cells[:, None, :3].astype(float) + OFF[None]
        sc, piv = 0.5, Vn['pivot']
        na = Vn['anchors']
        pivot_mount = me.get('mount') == 'pivot'
        if pivot_mount:
            C = obr + d * float(me['pivot'])
            ports = [float(a) for a in str(me.get('ports', '0')).split(',')]
            runin = float(me.get('runin', 0) or 0)
        best = None
        side = np.array([-d[1], d[0], 0.0])                     # 沿船長（砲軸的側向）
        for k in range(0, 81):
            b = k * 0.5
            nmz0 = xf(np.array(na['muzzle']) + 0.5, [0, 0, 0], piv, sc, phi, mir)
            at = omz - nmz0 - d * b
            at[2] = m['at'][2]
            if not pivot_mount:
                for dl in (0, 0.5, -0.5, 1, -1, 1.5, -1.5, 2, -2):   # 舷側砲：照作者的搜尋，沿船長挪一點（樞軸砲不挪：轉軸照舊）
                    a2 = at + side * dl
                    W = xf(pts, a2, piv, sc, phi, mir) + off
                    if int(np.isin(key(W), occ).any(axis=1).sum()) == 0:
                        best = (b, a2, 0, {'dl': dl} if dl else {})
                        break
                if best:
                    break
                continue
            W = xf(pts, at, piv, sc, phi, mir) + off
            nbr = xf(np.array(na['breech']) + 0.5, at, piv, sc, phi, mir)
            kpiv = float(np.dot(C - nbr, d))
            Cw = C + off
            hits = {}
            for a in ports:
                Wr = Cw + rotz(W - Cw, a); Wr[..., 2] = W[..., 2]
                hits['port%g' % a] = int(np.isin(key(Wr), occ).any(axis=1).sum())
            sweep = 0
            for a0, a1 in zip(sorted(ports), sorted(ports)[1:]):
                for a in np.arange(a0, a1 + 1e-9, 2.5):
                    Wg = W.copy(); Wg[~sl] -= d * runin
                    Wr = Cw + rotz(Wg - Cw, a); Wr[..., 2] = W[..., 2]
                    sweep += int(np.isin(key(Wr), occ).any(axis=1).sum())
            hits['sweep_runin'] = sweep
            if all(v == 0 for kk, v in hits.items() if kk.startswith('port')):
                best = (b, at, 0, dict(hits, k_pivot=round(kpiv, 3)))
                break
        if best is None:
            print('✗', h, m['name'], code, '退 40 格還是撞', flush=True)
            out.append({'host': h, 'name': m['name'], 'code': code, 'ok': False})
            continue
        b, at, n, extra = best
        nmz = xf(np.array(na['muzzle']) + 0.5, at, piv, sc, phi, mir)
        row = {'host': h, 'name': m['name'], 'code': code, 'ok': True, 'back': b, 'old_at': m['at'], 'at': [round(float(v), 3) for v in at],
               'muzzle_dz': round(float(nmz[2] - omz[2]), 2), 'old_muzzle': [round(float(v), 2) for v in omz], 'muzzle': [round(float(v), 2) for v in nmz]}
        row.update(extra)
        out.append(row)
        print(('✓' if extra.get('sweep_runin', 0) == 0 else '⚠'), h.split('-')[-1], m['name'], code, 'back', b, 'muzzle dz', row['muzzle_dz'], extra, flush=True)
        if APPLY:
            meta = dict(me)
            if pivot_mount:
                meta['pivot'] = extra['k_pivot']
            args = ['op=work', 'sub=model', 'persona=ridge-two', 'work=' + h, 'name=' + m['name'], 'source_work=' + Vn['work'],
                    'at=%s' % ','.join('%g' % round(float(v), 3) for v in at), 'pivot=%s' % ','.join('%g' % v for v in piv), 'scale=0.5',
                    'rotate=%s' % ','.join('%g' % v for v in m['rotate']), 'overwrite=1', 'meta=' + json.dumps(meta, ensure_ascii=False),
                    'note=%s（TASK-1155 換成自己的模型；以前拿餘燼號 32 磅 ×%g 暫代；place1155.py：新砲口對舊砲口、往裡退 %g 格到零碰撞%s）' % (
                        Vn['work'], sc0, b, ('、轉軸中心照舊 ⇒ meta pivot %g' % extra['k_pivot']) if pivot_mount else '')]
            if mir:
                args.append('mirror=' + mir)
            r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in args for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
            print('   掛', r.returncode, next((l for l in (r.stdout + r.stderr).splitlines() if l.startswith(('✓', '✗'))), '')[:120], flush=True)
    json.dump(out, open('C:/Users/Tim/AppData/Local/Temp/claude/D--Unity-Senate/ba2b0442-2186-4351-bb2f-8a3de1232442/scratchpad/gunscan/place_%s.json' % ASM, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()

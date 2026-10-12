# 餘燼號 船身拉長（Tim 2026-10-12「可以嘗試拉長船體嗎（船體中段複製拉伸）」＋截圖紅圈在船中）
#   plan.json stretch：把 [x_from, x_from + length) 那一段複製 copies 份、接在它後面；x ≥ x_from + length 的格往船頭推 length × copies
#   ⇒ masks/stretch/block.vox.txt（世界座標的那一段；stampvox at ＝ length·k,0,0，k ＝ 1..copies）、verify_stretch.json
# 用法：python -I draft_stretch.py <design 資料夾>
import sys, os, json, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402
from draft_ports import export_mark   # noqa: E402

W = 'basecamp-ember-01m'
YC = 160


def build(design):
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    St = plan['stretch']
    a = export_mark(W, St['world_mark'])
    assert len(a) == St['world_voxels'], ('船殼現況跟 plan 記的不一樣', len(a))
    H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
    x0, L, n = St['x_from'], St['length'], St['copies']
    block = {k: c for k, c in H.items() if x0 <= k[0] < x0 + L}
    E = {}
    for (x, y, z), c in H.items():
        E[(x if x < x0 + L else x + L * n, y, z)] = c
    for k in range(1, n + 1):
        for (x, y, z), c in block.items():
            E[(x + L * k, y, z)] = c
    return plan, H, block, E


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan, H, block, E = build(design)
    St = plan['stretch']
    x0, L, n = St['x_from'], St['length'], St['copies']
    v = {'world': len(H), 'block': len(block), 'moved': sum(1 for k in H if k[0] >= x0 + L), 'expect_after': len(E)}
    assert len(E) == len(H) + len(block) * n
    # 接縫：x0+L−1（原本的）與 x0+L（複製來的 x0）兩欄的外緣差（每個 z、右舷）
    def outer(D, x, z):
        ys = [y for y in range(YC + 1, 320) if (x, y, z) in D]
        return max(ys) if ys else None
    steps = {}
    for z in range(0, 165):
        a_, b_ = outer(E, x0 + L - 1, z), outer(E, x0 + L, z)
        if a_ is not None and b_ is not None and a_ != b_:
            steps[z] = b_ - a_
    v['seam_outer_steps'] = {'count_z': len(steps), 'max_abs': max([abs(t) for t in steps.values()] or [0]), 'by_z': steps}
    v['last_seam_outer_steps'] = sum(1 for z in range(165) if outer(E, x0 + (n + 1) * L - 1, z) != outer(E, x0 + (n + 1) * L, z))
    v['last_seam_original_steps'] = sum(1 for z in range(165) if outer(H, x0 + L - 1, z) != outer(H, x0 + L, z))
    v['x_max_after'] = max(k[0] for k in E)
    v['structure_after'] = DP.Ember.structure(None, E)
    out = os.path.join(design, 'masks', 'stretch')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'block.vox.txt')
    rows = sorted((k[0], k[1], k[2], c) for k, c in block.items())
    open(p, 'w', encoding='utf-8', newline='\n').write('# 船中段 x %d..%d 的複製（世界座標；stampvox at ＝ %d·k,0,0，k ＝ 1..%d）（%d 格）\n' % (x0, x0 + L - 1, L, n, len(rows))
                                                       + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
    v['file'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    json.dump(v, open(os.path.join(design, 'verify_stretch.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: (v[k] if k != 'seam_outer_steps' else {kk: vv for kk, vv in v[k].items() if kk != 'by_z'}) for k in v}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()

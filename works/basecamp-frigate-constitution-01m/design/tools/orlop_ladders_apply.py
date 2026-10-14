# berth → orlop 梯子落地（draft_orlop_ladders.py 的產物 ⇒ CLI）：關聯（甲板-orlop/梯子，meta kind=ladders）、梯子格（草稿）、berth 梯口（草稿，帶顏色）、
#   扶手柱頂固定點、扶手繩（組裝件）。每一步讀回；IOException（「無法移除要被取代的檔案」／cannot remove）重試 3 次。
# 用法：python -I orlop_ladders_apply.py <con|emb>
import sys, os, json, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from draft_orlop_ladders import SHIPS   # noqa: E402

ASM = {'con': 'basecamp-frigate-constitution-01m-assembly', 'emb': 'basecamp-ember-01m-assembly'}


def cli(*args):
    for k in range(4):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []),
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode and k < 3 and ('無法移除要被取代的檔案' in out or 'cannot remove' in out.lower() or 'being used by another process' in out):
            time.sleep(0.5)
            continue
        if r.returncode:
            raise SystemExit('✗ %s\n%s' % (' '.join(args), out[-800:]))
        return out


def num(out, key):
    for l in out.splitlines():
        if l.startswith('🔢 %s = ' % key):
            return l.split('=', 1)[1].strip()
    return None


def main():
    ship = sys.argv[1]
    S = SHIPS[ship]
    D = S['design']
    P = 'persona=basecamp'
    # 1. 關聯
    links = json.load(open(os.path.join(os.path.dirname(D), '..', S['deck_orlop'], 'links.json'), encoding='utf-8'))['links']
    if not any(l['name'] == '梯子' for l in links):
        cli('op=work', 'sub=link', 'work=' + S['deck_orlop'], 'name=梯子', 'source_work=' + S['sub'], 'at=0,0,0', P,
            'note=berth → orlop 的梯子（draft_orlop_ladders.py）')
    cli('op=work', 'sub=meta', 'work=' + S['deck_orlop'], 'part=link', 'name=梯子', 'meta={"kind":"ladders"}', P)
    links = json.load(open(os.path.join(os.path.dirname(D), '..', S['deck_orlop'], 'links.json'), encoding='utf-8'))['links']
    L = [l for l in links if l['name'] == '梯子']
    assert len(L) == 1 and L[0]['work'] == S['sub'] and L[0]['at'] == [0, 0, 0] and (L[0].get('meta') or {}).get('kind') == 'ladders', L
    print('✓ 關聯 甲板-orlop/梯子 → %s（meta kind=ladders，讀回）' % S['sub'])
    # 2. 格子（草稿）
    v = json.load(open(os.path.join(D, 'verify_orlop_ladders.json'), encoding='utf-8'))
    n = v['files']['orlop']['cells']
    out = cli('op=stampvox', 'work=' + S['sub'], 'voxels=' + os.path.join(D, 'masks', 'ladders', 'orlop.vox.txt'), 'at=0,0,0',
              'expect_pixels=%d' % n, 'draft=1', P)
    assert int(num(out, 'placed')) == n, out[-400:]
    n2 = v['files']['orlop_carve']['cells']
    out = cli('op=carvevox', 'work=' + S['deck_berth'], 'voxels=' + os.path.join(D, 'masks', 'ladders', 'orlop_carve.vox.txt'), 'at=0,0,0',
              'expect_pixels=%d' % n2, 'draft=1', P)
    assert num(out, 'already_empty') == '0', out[-400:]
    print('✓ 草稿：梯子 %d 格、berth 梯口 %d 格' % (n, n2))
    # 3. 固定點
    pts = json.load(open(os.path.join(D, 'rig_points_orlop_ladders.json'), encoding='utf-8'))['points']
    for p in pts:
        cli('op=work', 'sub=anchor', 'work=' + S['sub'], 'name=' + p['name'], 'at=%d,%d,%d' % tuple(p['world']), P, 'note=扶手柱頂')
    got = {a['name']: a['at'] for a in json.load(open(os.path.join(os.path.dirname(D), '..', S['sub'], 'anchors.json'), encoding='utf-8'))['anchors']}
    assert all(got.get(p['name']) == p['world'] for p in pts), got
    print('✓ 固定點 %d 個（讀回）' % len(pts))
    # 4. 扶手繩
    ropes = json.load(open(os.path.join(D, 'orlop_ladder_ropes.json'), encoding='utf-8'))['ropes']
    for r in ropes:
        cli('op=work', 'sub=rope', 'work=' + ASM[ship], 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'],
            'slack=%s' % r['slack'], 'color=' + r['color'], 'thickness=%s' % r['thickness'], 'group=' + r['group'], 'note=扶手繩（berth → orlop）', P)
    rs = json.load(open(os.path.join(os.path.dirname(D), '..', ASM[ship], 'ropes.json'), encoding='utf-8'))
    rs = rs['ropes'] if isinstance(rs, dict) else rs
    names = {x['name'] for x in rs}
    assert all(r['name'] in names for r in ropes)
    print('✓ 扶手繩 %d 條（讀回）' % len(ropes))


if __name__ == '__main__':
    main()

"""Audit final export against previous portable delivery; no author construction imported."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'audits/20261014/yard_sweep'))
from vxk_decode import unpack, checksum
OUT = ROOT / 'continued_20261015'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before_path = ROOT / 'audits/20261014/yard_sweep/source_after.vxk'
    final_path = OUT / 'final_heads.vxk'
    bh, bv = unpack(before_path.read_bytes())
    ah, av = unpack(final_path.read_bytes())
    assert digest(before_path) == 'a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73'
    assert np.array_equal(bv, av), 'Voxel body/color/order changed'
    body_sum = checksum(av)
    negative = av.copy()
    negative[0, 3] = 1 if negative[0, 3] != 1 else 2
    assert checksum(negative) != body_sum
    report = {'before_sha256': digest(before_path), 'final_sha256': digest(final_path),
              'voxels': len(av), 'checksum': f'{body_sum:08x}',
              'body_color_order_equal': True, 'tampered_checksum': f'{checksum(negative):08x}',
              'models': len(ah['rig']['models']), 'sails': len(ah['rig']['sails']),
              'ropes': len(ah['rig']['ropes']), 'deltas': {}}
    for label in ('models', 'sails', 'ropes'):
        b = {v['name']: v for v in bh['rig'][label]}
        a = {v['name']: v for v in ah['rig'][label]}
        report['deltas'][label] = {
            'added': sorted(set(a)-set(b)), 'removed': sorted(set(b)-set(a)),
            'changed': [{'name': name, 'fields': sorted(k for k in set(a[name])|set(b[name])
                                                     if a[name].get(k)!=b[name].get(k))}
                        for name in sorted(set(a)&set(b)) if a[name]!=b[name]]}
        assert not report['deltas'][label]['removed']
    assert ah['rig']['meshes'] == bh['rig']['meshes'], 'Source mesh changed'
    report['meshes_identical'] = True
    full_design = json.loads((ROOT/'plan.json').read_text('utf8'))
    design = full_design['rig_repair_20261015']
    assembly = ROOT.parent.parent/'sirius-tidegrave-01m-assembly'
    anchors = {v['name']:v['at'] for v in json.loads((assembly/'anchors.json').read_text('utf8'))['anchors']}
    for mast, feet in design['standing_feet'].items():
        for j, point in enumerate(feet):
            assert anchors[f'{mast}-standing-chain-P{j}'] == point
            assert anchors[f'{mast}-standing-chain-S{j}'] == [point[0],240-point[1],point[2]]
    report['design_standing_feet_match_cli_readback'] = True
    models = {m['name']:m for m in ah['rig']['models']}
    mast_x = {m['id']:m['x'] for m in full_design['masts']}
    for mast, yard, z, length, drop in full_design['rig_layout']['square_yards']:
        m = models[f'{mast}/yard-{mast}-{yard}']
        assert m['points']['pivot'] == [mast_x[mast]+.5,120.5,z+.5]
        assert m['meta']['turn_axis'] == 'z'
        source = json.loads((ROOT.parent.parent/('sirius-tidegrave-01m-mast-'+mast)/'models.json').read_text('utf8'))
        src = next(v for v in source['models'] if v['name']==f'yard-{mast}-{yard}')
        assert src['scale']==[1,1,1] and src['rotate']==[0,0,-18]
    for yard in ('gaff','boom'):
        assert models[f'mizzen/yard-mizzen-{yard}']['points']['pivot'] == full_design['rig_layout'][yard]['pivot']
    for mast in full_design['masts']:
        assert np.any(np.all(av[:,:3]==[mast['x'],120,mast['top_z']],axis=1))
    report['all_square_yard_pivots_scale_rotation_and_mast_tops_match_plan'] = True
    assert report['models'] == 116 and report['sails'] == 10 and report['ropes'] == 302
    assert report['deltas']['sails']['changed'][0]['name'] == 'mizzen-topsail'
    (OUT / 'delta_audit.json').write_text(json.dumps(report, indent=2)+'\n', 'utf8')
    # Diagram comes from the independently decoded exports. It shows observation,
    # not an independent source of intended geometry.
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGB', (1900, 1260), '#102630')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 23)
    small = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 17)
    draw.text((35, 20), '潮墓號 / 索具修正觀測圖 2026-10-15  |  X-Z 側投影 / 0.1 m 每格', font=font, fill='#d9e2d0')
    for ox, title, h in [(35, '修正前 a5994eee', bh), (985, '修正後 '+report['final_sha256'][:8], ah)]:
        draw.text((ox, 68), title, font=font, fill='#d5b573')
        T = lambda p: (ox+40+(p[0]-90)*1.6, 1150-p[2]*1.9)
        for z in range(0, 551, 50):
            draw.line([T((90,0,z)), T((620,0,z))], fill='#254752')
            draw.text(T((90,0,z)), str(z/10)+'m', font=small, fill='#72b2ae')
        for x, top in [(205,405),(355,510),(510,465)]:
            draw.line([T((x,0,128)), T((x,0,top))], fill='#d9e2d0', width=4)
        for r in h['rig']['ropes']:
            if not any(k in r['name'] for k in ('.lift-', '.brace-', '-shroud-', '-backstay-', '.robband-')):
                continue
            pts=np.array(r['pts']).reshape(-1,3)
            c = '#d5b573' if '.lift-' in r['name'] else '#72b2ae' if '.brace-' in r['name'] else '#b4bdad'
            draw.line([T(p) for p in pts], fill=c, width=2)
        draw.text((ox, 1180), '金：吊索   青：轉桁索   灰：支索（左右舷側投影重合）', font=small, fill='#d9e2d0')
    image.save(OUT / 'rig_comparison.png')
    print(json.dumps({k:v for k,v in report.items() if k!='deltas'}, indent=2))


if __name__ == '__main__':
    main()

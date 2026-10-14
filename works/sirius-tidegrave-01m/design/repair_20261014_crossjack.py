"""Guarded, repeatable placement repair. Source geometry is never rewritten."""
from pathlib import Path
import json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_structure import cli, BASE, ROOT

def main():
    path=ROOT.parent.parent/(BASE+'-mast-mizzen')/'models.json'
    models=json.loads(path.read_text(encoding='utf-8'))['models']
    m=next(m for m in models if m['name']=='yard-mizzen-crossjack')
    target=[205.5,120.5,224.5]
    if m['at']==target:
        print('Crossjack already at guarded target; no mutation');return
    if m['at'] not in ([205.5,120.5,255.5],[205.5,120.5,226.5]) or m['work']!=BASE+'-yard-mizzen-crossjack' or m['pivot']!=[4.5,120.5,4.5] or m['rotate']!=[0,0,-18] or m['scale']!=[1,1,1]:
        raise RuntimeError('Placement baseline differs; inspect before moving')
    if '--apply' not in sys.argv:
        print('Plan: crossjack Z ->224.5; add --apply to use Senate CLI');return
    cli(op='work',sub='model',work=BASE+'-mast-mizzen',name=m['name'],source_work=m['work'],
        at=','.join(map(str,target)),pivot='4.5,120.5,4.5',rotate='0,0,-18',scale=1,overwrite=1)
    after=next(v for v in json.loads(path.read_text(encoding='utf-8'))['models'] if v['name']==m['name'])
    if after['at']!=target or after.get('meta')!=m.get('meta'):
        raise RuntimeError('Placement/meta readback mismatch')
    print('CLI placement and metadata read back')

if __name__=='__main__':main()

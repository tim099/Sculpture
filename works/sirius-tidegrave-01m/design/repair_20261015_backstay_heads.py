"""Lead backstays to existing aft mast-tip cells rather than through tip centers."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from build_structure import cli,BASE


def main():
    for mast,x,z in [('main',355,510),('fore',510,465)]:
        work=BASE+'-mast-'+mast
        path=ROOT.parent.parent/work
        # Source events are explicitly inspected, independent of cached geometry.
        wanted=(x-1,120,z)
        found=False
        for ep in sorted((path/'events').rglob('*.json')):
            e=json.loads(ep.read_text('utf8'))
            for item in e.get('placed_colored',[]):
                if tuple(item[:3])==wanted:found=True
        assert found, ('Missing actual aft tip cell',work,wanted)
        if '--apply' not in sys.argv:
            print(work,wanted)
            continue
        cli(op='work',sub='anchor',work=work,name='backstay-head',at=','.join(map(str,wanted)),overwrite=1,
            note='Aft timber face at mast tip: backstay avoids entering center of mast')
        rp=ROOT.parent.parent/(BASE+'-assembly')/'ropes.json'
        by={r['name']:r for r in json.loads(rp.read_text('utf8'))['ropes']}
        for side in ('P','S'):
            r=by[f'{mast}-backstay-{side}']
            assert r['from'] in (mast+'/truck',mast+'/backstay-head')
            if r['from']!=mast+'/backstay-head':
                cli(op='work',sub='rope',work=BASE+'-assembly',name=r['name'],
                    **{'from':mast+'/backstay-head','to':r['to']},overwrite=1)
    print('Existing aft tip cells and backstay targets processed.')


if __name__=='__main__':main()

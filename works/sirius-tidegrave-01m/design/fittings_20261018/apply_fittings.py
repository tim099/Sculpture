"""Write only the additive models in placement.json, through Senate CLI."""
from pathlib import Path
import json, subprocess, sys, hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PARENT='sirius-tidegrave-01m-assembly'
FRAMES={'weather':'sirius-tidegrave-01m-deck-weather','forecastle':'sirius-tidegrave-01m-deck-forecastle','poop':'sirius-tidegrave-01m-deck-poop'}

def run(args):
    r=subprocess.run(['senate','cmd','sculpture','--arg','persona=Sirius']+args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if r.returncode: raise RuntimeError(r.stdout+'\n'+r.stderr)
    return r.stdout

if __name__=='__main__':
    plan=json.loads((HERE/'placement.json').read_text(encoding='utf-8'))
    logs=[]
    for i,p in enumerate(plan['placements']):
        work=FRAMES[p['frame']]
        meta=HERE/('meta_'+('deco' if p['meta'].get('deco') else p['meta']['kind'])+'.json')
        meta.write_text(json.dumps(p['meta'],ensure_ascii=False),encoding='utf-8')
        args=['--arg','op=work','--arg','sub=model','--arg','work='+work,'--arg','name='+p['name'],
              '--arg','source_work='+p['source'],'--arg','at='+','.join(map(str,p['at'])),
              '--arg','pivot='+','.join(map(str,p['pivot'])),'--arg','scale='+str(p['scale']),
              '--arg','rotate='+','.join(map(str,p['rotate'])),'--arg-file','meta='+str(meta)]
        out=run(args); logs.append({'model':p['name'],'result':out})
        (HERE/'apply_receipts.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'{i+1}/{len(plan["placements"])} {p["name"]}: CLI success',flush=True)
    print('All models written. Re-export parts and verify independently.',flush=True)

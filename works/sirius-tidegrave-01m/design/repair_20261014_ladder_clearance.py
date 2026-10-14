"""Audited exact clearance cuts, applied only through the Senate engine.
No stair voxel or landing support is removed. Default only draws the plan.
"""
from pathlib import Path
import json,sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_structure import cli,BASE,ROOT
from PIL import Image,ImageDraw,ImageFont
DIR=ROOT/'ladder_clearance_20261014'

def main():
    r=json.loads((DIR/'candidate.json').read_text(encoding='utf-8'))
    if r['protected_conflict_count'] or r['proposed_remove_count']!=1799:
        raise RuntimeError('Unexpected corridor design/protected support conflict')
    masks={}
    for work,count in ((BASE,1771),(BASE+'-deck-quarter',14),(BASE+'-deck-poop',14)):
        p=DIR/(work+'.color_guard.vox.txt')
        rows=[tuple(map(int,l.replace(',',' ').split())) for l in p.read_text().splitlines() if l and not l.startswith('#')]
        if len(rows)!=count:raise RuntimeError('Guard count mismatch')
        p.write_text(''.join(','.join(map(str,row))+'\n' for row in rows),encoding='utf-8')
        masks[work]=(p,rows)
    im=Image.new('RGB',(1400,1260),'#102630');d=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18)
    d.text((25,14),'潮墓號 — 七梯淨空施工圖 | lift 3 / 淨高 1.8m / 橫向 y117..123 (0.7m)',font=font,fill='#d9e2d0')
    d.text((25,42),'精確守門刻除1799格；紅＝開孔，金＝腳路徑，青＝路徑上方18格；全部梯件與14落腳地板保留',font=font,fill='#72b2ae')
    for i,l in enumerate(r['per_ladder']):
        col=i%2;row=i//2;ox=25+col*695;oy=90+row*286
        pts=l['path'];xmin=min(p[0] for p in pts)-3;zmin=min(p[2] for p in pts)-3
        T=lambda x,z:(ox+30+(x-xmin)*10,oy+245-(z-zmin)*5)
        d.text((ox,oy),l['name'],font=font,fill='#d9e2d0')
        for work,(_,cells) in masks.items():
            for x,y,z,c in cells:
                if y==120 and xmin<=x<=max(p[0] for p in pts)+3 and zmin<=z<=max(p[2] for p in pts)+19:
                    a=T(x,z+1);b=T(x+1,z);d.rectangle((a,b),fill='#bc5c60')
        d.line([T(p[0],p[2]) for p in pts],fill='#d5b573',width=3)
        d.line([T(p[0],p[2]+18) for p in pts],fill='#72b2ae',width=2)
    plan=DIR/'clearance_plan.png';im.save(plan)
    manifest={'design':r['design'],'plannedRemoved':1799,'protectedConflicts':0,'drawingSha256':hashlib.sha256(plan.read_bytes()).hexdigest(),'guards':{w:{'cells':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for w,(p,rows) in masks.items()}}
    (DIR/'plan.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    if '--apply' not in sys.argv:
        print('Plan saved; --apply executes the three guarded cuts');return
    results={}
    for w,(p,rows) in masks.items():
        results[w]=cli(op='carvevox',work=w,voxels=p,at='0,0,0',expect_pixels=len(rows),share=0)
    (DIR/'applied.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('All three guarded cuts accepted. Independent actual verification still required.')

if __name__=='__main__':main()

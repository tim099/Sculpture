"""Stage2 correction: drill full cannon ports through previously placed frames."""
import json
from build_structure import cli,get_actual,ROOT,BASE
from draft_general import P,width,CY
def main():
    old=get_actual(BASE);cut={}
    for dz in P['guns']['decks']:
        for x in P['guns']['x']:
            for xx in range(x-8,x+9):
                for z in range(dz+5,dz+20):
                    w=width(xx,z)
                    for y in range(241):
                        q=(xx,y,z)
                        if q in old and abs(y-CY)>w-7:cut[q]=old[q]
    f=ROOT/'ports_frame_correction.vox.txt';f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(cut.items())),encoding='utf-8')
    if cut:cli(op='carvevox',work=BASE,voxels=f,at='0,0,0',expect_pixels=len(cut))
    now=get_actual(BASE)
    if set(old)-set(now)!=set(cut):raise RuntimeError('unexpected carved positions')
    rays=[]
    for dz in P['guns']['decks']:
        for x in P['guns']['x']:
            z=dz+12;blocked=[y for y in range(241) if (x,y,z) in now]
            rays.append({'x':x,'z':z,'blocked_y':blocked})
    r={'stage':'shell-v2-ports','removed':len(cut),'retained_color_changed':sum(now.get(q)!=c for q,c in old.items() if q not in cut),'48_side_rays':rays,'original_skeleton_modified_intentionally':len(cut)}
    (ROOT/'verify_ports_correction.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    if any(q['blocked_y'] for q in rays):raise RuntimeError(r)
    cli(op='stats',work=BASE,structure=1,mirror='y:120')
    print(json.dumps(r))
if __name__=='__main__':main()

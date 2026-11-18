"""Physical junk-sail battens for the current Ship_Battens workflow (TASK-1320).

Run after rig.py. Uses the existing CLI, never edits the sculpture data files.
The three asymmetric spar lengths need their own pivot at the mast axis;
the symmetric 4.1m Tekpai part cannot preserve these spans and pivot by scaling.
Pattern based on pinnacle-tekpai-01m/design/draft_battens.py. Level spars allow
the current core to stack each batten and its entire cloth row without a gap.
"""
import json,math,sys
from pathlib import Path
from PIL import Image,ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parent))
from draft_hull import PLAN,DESIGN,CENTER
from draft_decks import write_mask
from sculpt_cli import HULL,ASSEMBLY,WORKS,anchor,component,entries,model,sculpt

def vecadd(a,b): return [x+y for x,y in zip(a,b)]
def lerp(a,b,v): return [x+(y-x)*v for x,y in zip(a,b)]

rows=[]
apply='--apply' in sys.argv
for name,spec in PLAN['rig'].items():
    host=f'{HULL}-mast-{name}'
    frames={}
    for pos in ('upper','lower'):
        obj=entries(host,'models')['yard-'+pos]
        pts=entries(obj['work'],'anchors')
        pivot=pts['pivot']['at'][:]
        pivot[1]=1; pivot[2]=2
        span=pts['earing-fore']['at'][0]-pts['earing-aft']['at'][0]
        frame_label=f'yard-{name}-{pos}'
        write_mask(frame_label,{(x,y,z):136 for x in range(2,span+3) for y in (1,2) for z in (2,3)})
        if apply:
            component(frame_label,f'{name} 水平硬篷{pos}桁')
            anchor(obj['work'],'earing-aft',(2,1,2))
            anchor(obj['work'],'earing-fore',(span+2,1,2))
            anchor(obj['work'],'sling',(pivot[0],1,2))
        pv=[v+.5 if isinstance(v,int) else v for v in pivot]
        at=[spec['x']+.5,CENTER+.5,spec['upper_z' if pos=='upper' else 'lower_z']+.5]
        ends=[]
        for an in ('earing-aft','earing-fore'):
            p=pts[an]['at'][:];p[2]=2;p=[v+.5 if isinstance(v,int) else v for v in p]
            ends.append([a+x-y for a,x,y in zip(at,p,pv)])
        frames[pos]={'at':at,'ends':ends,'pivot':pivot}
        if apply:
            anchor(obj['work'],'pivot',pivot)
            model(host,'yard-'+pos,obj['work'],at,pv,
                  {**obj['meta'],'yard':'course'},scale=obj.get('scale',1),rotate=obj.get('rotate',[0,0,0]))
    count=spec['battens']
    lo,hi=spec['aft']-4,spec['fore']+4
    pivot_x=2-lo
    length=hi-lo
    cells={(x,2,2):(104 if x%12==0 else 177) for x in range(2,length+3)}
    label='batten-'+name
    write_mask(label,cells)
    if apply:
        source=component(label,f'通用硬篷竹篾（{length*.1:.1f}m，偏置軸）',(length+5,5,5))
        for key,point in {'pivot':(pivot_x,2,2),'arm-P':(2,2,2),'arm-S':(length+2,2,2)}.items():anchor(source,key,point)
        sculpt('work',sub='meta',work=source,part='work',meta={'material':'bamboo','render':'pole'})
    for m in range(1,count+1):
        v=m/(count+1)
        a=lerp(frames['upper']['ends'][0],frames['lower']['ends'][0],v)
        b=lerp(frames['upper']['ends'][1],frames['lower']['ends'][1],v)
        t=(spec['x']+.5-a[0])/(b[0]-a[0])
        at=lerp(a,b,t)
        angle=-math.degrees(math.atan2(b[2]-a[2],b[0]-a[0]))
        c=math.cos(math.radians(angle))
        over=[a[0]-(at[0]+lo*c),(at[0]+hi*c)-b[0]]
        assert min(over)>1,(name,m,over)
        rows.append({'mast':name,'batten':m,'at':at,'rotate_y':angle,'overhang':over})
        if apply:
            model(host,f'batten-{m:02d}',source,at,(pivot_x+.5,2.5,2.5),
                  {'kind':'yard','yard':'batten','batten':m,'sail':name+'-junk','mast':name,
                   'pivot_anchor':'pivot','turn_axis':'z','rotate_z_deg':0,'length_ft':round(length*.1/.3048,2),'diameter_in':4},
                  rotate=(0,angle,0))
    # N interior stripes, N+1 panels, faint seams; physical rods supply the ribs.
    height=(count+1)*12
    im=Image.new('RGB',(128,height),'#c9b18b');d=ImageDraw.Draw(im)
    for y in range(1,height,4):d.line((0,y,127,y),fill='#c5aa80')
    for x in range(3,128,8):d.line((x,0,x,height-1),fill='#c3a77c')
    for m in range(1,count+1):d.line((0,m*12,127,m*12),fill='#9a8058',width=1)
    d.rectangle((0,0,127,height-1),outline='#6a553a',width=2)
    path=DESIGN/'textures'/f'{name}-battens.png';im.save(path)
    if apply:
        sail=name+'-junk';upper=f'model:mast-{name}/yard-upper/';lower=f'model:mast-{name}/yard-lower/'
        sculpt('work',sub='sail',work=ASSEMBLY,name=sail,
               corners=f'{upper}earing-aft|{upper}earing-fore|{lower}earing-fore|{lower}earing-aft',
               corner_names='peak|throat|tack|clew',bind='0,2',color='#ffffff',fullness=1.025,
               res=max(24,(count+1)*4),texture=path,overwrite=1)
        sculpt('work',sub='meta',work=ASSEMBLY,part='sail',name=sail,
               meta={'kind':'sail','mast':name,'sail':'course','set':spec['set'],'battens':count})
(DESIGN/'battens_placement.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps({'physical_rods':len(rows),'applied':apply,'min_overhang':min(min(r['overhang']) for r in rows)},indent=2))
if '--game' in sys.argv:
    game=Path(sys.argv[sys.argv.index('--game')+1]).resolve()
    sys.path.insert(0,str(game/'src'))
    import admin
    cfg=admin.load()
    ship=next(s for s in cfg['ships'] if s['id']=='tungning_trader')
    # Current core gives the independent tiller its helmsman. Keep 100 total.
    ship['crew']['hands']=25
    assert not admin.validate(cfg),admin.validate(cfg)
    admin.save(cfg)
    print('Configured 25 reserve hands plus the current-core tiller helmsman (100 total)')

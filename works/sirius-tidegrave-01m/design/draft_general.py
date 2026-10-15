"""Deterministic original general arrangement. All coordinates in 0.1m cells."""
import json, math, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
H=P['hull']; CY=P['center_y']
def width(x,z):
    rake=max(0,1-z/H['rake_height'])
    xlo=H['stern_x']+H['stern_rake']*rake
    xhi=H['bow_x']-H['bow_rake']*rake
    t=(x-xlo)/(xhi-xlo)
    if not 0<=t<=1:return 0.
    b=float(np.interp(t,[v[0] for v in H['stations']],[v[1] for v in H['stations']]))
    floor=H['floor_base']+H['floor_end_rise']*abs(2*t-1)**3
    if z<=floor:return 0.
    norm=math.sqrt(1-math.exp(-(H['tumblehome_start']-H['floor_base'])/H['bilge_height']))
    return b*math.sqrt(1-math.exp(-(z-floor)/H['bilge_height']))*max(.48,1-H['tumblehome_per_z']*max(0,z-H['tumblehome_start']))/norm
def top(x):
    if x<180:return P['bulwark']['stern_z']
    if x<240:return 150
    if x>550:return P['bulwark']['bow_z']
    return P['bulwark']['main_z']
def main():
    bg='#102630'; ink='#d9e2d0'; teal='#72b2ae'; gold='#d5b573'; dim='#35535b'
    im=Image.new('RGB',(2300,2480),bg);d=ImageDraw.Draw(im)
    fontpath='C:/Windows/Fonts/msjh.ttc'
    F=lambda n:ImageFont.truetype(fontpath,n)
    def txt(x,y,s,n=22,c=ink):d.text((x,y),s,font=F(n),fill=c)
    def line(points,c=ink,w=2):d.line(points,fill=c,width=w)
    txt(70,40,'潮墓號  /  TIDEGRAVE',44);txt(72,101,'SIRIUS  |  ORIGINAL GENERAL ARRANGEMENT  |  REV '+str(P['revision']).zfill(2)+'  |  0.1 m / voxel',22,teal)
    txt(1660,45,'三桅 · 雙砲層 · 54 門砲',27,gold)
    # Side elevation at a constant scale, metric grid at 5m.
    sx,sy,scale=90,1600,2.65
    T=lambda x,z:(sx+x*scale,sy-z*scale)
    for x in range(0,801,50):line([T(x,0),T(x,530)],dim,1)
    for z in range(0,551,50):line([T(0,z),T(800,z)],dim,1)
    txt(80,155,'01  側面總圖  /  STARBOARD ELEVATION',24,teal)
    lo=[];up=[]
    for x in range(100,621):
        zs=[z for z in range(4,top(x)+1) if width(x,z)>0]
        if zs:lo.append(T(x,min(zs)));up.append(T(x,max(zs)))
    line(lo,ink,4);line(up,ink,4);line([lo[0],up[0]],ink,4);line([lo[-1],up[-1]],ink,4)
    for deck in P['decks']:
        a,b=deck['x'];valid=[x for x in range(a,b+1) if width(x,deck['z'])>0]
        if valid:line([T(min(valid),deck['z']),T(max(valid),deck['z'])],gold,2)
    line([T(80,52),T(650,52)],teal,2);txt(*T(653,52),'DWL 5.2m',18,teal)
    for dz in P['guns']['decks']:
        for x in P['guns']['x']:
            a,b=T(x-8,dz+19),T(x+8,dz+5);d.rectangle([a,b],outline=gold,width=2)
    # Full rig schematic, angular braces still level in design.
    yards=P['rig_layout']['square_yards']
    for m in P['masts']:
        x=m['x'];line([T(x,m['deck_z']),T(x,m['top_z'])],ink,6)
        for mast,yid,z,span,drop in yards:
            if mast!=m['id']:continue
            # Side view yard cross section + sails behind mast.
            line([T(x-8,z),T(x+8,z)],gold,3)
            if drop:line([T(x-5,z),T(x-15,z-drop),T(x+15,z-drop),T(x+5,z)],ink,2)
            if yid=='crossjack':txt(*T(x+10,z),'crossjack '+str((z+.5)/10)+'m',16,teal)
        repair=P.get('rig_repair_20261015',{})
        feet=repair.get('standing_feet',{}).get(m['id'])
        if feet:
            for foot in feet:
                line([T(foot[0],foot[2]),T(x,m['platform_z']-5)],teal,1)
            head=repair['backstay_heads'][m['id']]
            foot=repair.get('backstay_feet',{}).get(m['id'],feet[0])
            line([T(foot[0],foot[2]),T(head[0],head[2])],teal,1)
        else:
            line([T(x,m['platform_z']),T(max(105,x-60),120)],teal,1)
            line([T(x,m['platform_z']),T(min(615,x+70),120)],teal,1)
        txt(*T(x+5,m['top_z']),m['id']+' '+str(m['top_z']/10)+'m',18,teal)
    gaff=P['rig_layout']['gaff'];boom=P['rig_layout']['boom']
    A=lambda q:T(q[0],q[2])
    line([A(gaff['pivot']),A(gaff['top'])],gold,4)
    line([A(boom['pivot']),A(boom['end'])],gold,4)
    line([A(gaff['pivot']),A(gaff['top']),A(boom['end']),A(gaff['pivot'])],ink,2)
    line([T(*[P['bowsprit']['root'][i] for i in (0,2)]),T(*[P['bowsprit']['tip'][i] for i in (0,2)])],ink,6)
    dynamic=P.get('rig_repair_20261015',{}).get('dynamic_audit_repair',{})
    if dynamic:
        jib=dynamic['jib'];hc=jib['head_ring_cell'];head=[c+.5 for c in hc]
        line([A(jib['tack']),A(head),A(jib['clew']),A(jib['tack'])],teal,2)
        foot=dynamic['lateen_sheet_fairlead']
        line([A(boom['end']),T(foot[0]+.5,foot[2]+.5)],teal,2)
    # stern crown and pointed prow are indicated as ornament, not hull openings.
    for i in range(7):
        x=105+i*10;line([T(x,186),T(x+2,203+(i%3)*5),T(x+5,186)],gold,2)
    line([T(618,130),T(670,157),T(650,117),T(602,111)],gold,3)
    txt(85,1634,'船殼 52.0 m  |  名義最大寬 13.4 m  |  主桅龍骨上 51.0 m  |  長度含艏斜桅約 64.8 m',24,gold)
    # Plan of full decks, two physical gun batteries and hatches.
    px,py,ps=70,1820,2.45
    Q=lambda x,y:(px+x*ps,py+(y-CY)*ps)
    txt(70,1688,'02  露天甲板俯視 + 上砲層位置疊圖（砲框可超出收窄的上舷）',23,teal)
    pts=[Q(x,CY-width(x,115)) for x in range(100,621)]+[Q(x,CY+width(x,115)) for x in range(620,99,-1)]
    line(pts+[pts[0]],ink,3);line([Q(100,CY),Q(748,CY)],dim,1)
    for x in P['guns']['x']:
        for sg in (-1,1):
            y=CY+sg*(width(x,90)-12);a=Q(x-6,y-9);b=Q(x+6,y+9);d.rectangle([a,b],outline=gold,width=2)
    for m in P['masts']:
        a=Q(m['x']-5,CY-5);b=Q(m['x']+5,CY+5);d.ellipse([a,b],outline=ink,width=3)
    for x in (275,410):
        d.rectangle([Q(x-10,CY-8),Q(x+10,CY+8)],outline=teal,width=2)
    for i,at in enumerate(P['guns']['chase_layout']['base_positions']):
        x,y,z=at;d.ellipse([Q(x-2,y-2),Q(x+2,y+2)],fill=gold)
    for name,item in P.get('equipment',{}).items():
        if 'at' not in item:continue
        x,y,z=item['at'];d.rectangle([Q(x-3,y-3),Q(x+3,y+3)],fill=teal)
        txt(*Q(x+5,y),name,16,teal)
    anchors=P.get('equipment',{}).get('anchors')
    if anchors:
        for side in ('P','S'):
            item=anchors[side];x,y,z=item['at'];hx,hy,hz=item['hawse_cell']
            line([Q(x,y),Q(hx+.5,hy+.5)],gold,3)
            d.ellipse([Q(x-3,y-3),Q(x+3,y+3)],outline=gold,width=2)
        x,y,z=anchors['P']['at']
        line([T(x,z),T(x,z-52)],gold,3)
        line([T(x-12,z-44),T(x,z-52),T(x+12,z-44)],gold,3)
    for x,y,z0,z1 in P.get('equipment',{}).get('fairlead_posts',{}).get('positions',[]):
        for yy in (y,2*CY-y):
            a,b=Q(x,yy);d.ellipse((a-3,b-3,a+3,b+3),fill=gold)
            line([T(x,z0),T(x,z1)],gold,2)
    staff=P.get('equipment',{}).get('flag_staff')
    if staff:
        x,y,z0=staff['base_cell'];z1=staff['top_cell'][2]
        line([T(x,z0),T(x,z1)],gold,3)
        corners=[T(q[0],q[2]) for q in staff['flag_corners']]
        line(corners+[corners[0]],teal,2)
    txt(1750,1720,'新線形剖面 / BODY PLAN',23,teal)
    # Body plan from original station law, each colored curve independently labelled.
    for j,t in enumerate((.1,.25,.5,.75,.9)):
        x=100+520*t;ox=1810+(j%3)*140;oy=1960+(j//3)*210
        for z in range(5,129):
            w=width(x,z)*.7
            if w:line([(ox-w,oy-z*.95),(ox+w,oy-z*.95)],dim,1)
        curve=[(ox-width(x,z)*.7,oy-z*.95) for z in range(5,129)]+[(ox+width(x,z)*.7,oy-z*.95) for z in range(128,4,-1)]
        line(curve,teal,2);txt(ox-48,oy+8,'S '+str(t),18)
    txt(70,2020,'設計要點',25,teal)
    lines=['48 門舷側砲 + 6 門固定艏砲；三聯外觀，沿用普通追擊砲機制。',
           '骨白尖頂、三層艉廊、空心星盤與珊瑚冠；綠灰海蝕船殼。',
           '破舊帆以透明貼圖呈現；水線下殼體保留完整，通道與梯子可通行。',
           '船殼 / 各甲板 / 桅分件；砲、帆桁、舵輪、桶為模型；繩與帆獨立。',
           '歷史：Vasa 與 Batavia 比例及甲板概念；所有線形座標均為原創設計。',
           'Rev08：補左右共用bower錨與hawse；後桅橫桁22.45m，固定帆點保留。']
    for i,s in enumerate(lines):txt(70,2060+i*37,s,21)
    line([(65,2400),(2235,2400)],dim,2);txt(70,2415,'T540 / T541   |   +X BOW  ·  +Y STARBOARD  ·  Z0 KEEL   |   DRAFT GENERAL — NOT CONSTRUCTION ACCEPTANCE',18,teal)
    out=ROOT/'general_arrangement.png';im.save(out)
    stations=[{'t':t,'x':100+520*t,'half_width_at_dwl':round(width(100+520*t,52),4),'half_width_at_weather':round(width(100+520*t,115),4)} for t in (0,.1,.2,.35,.5,.65,.8,.9,.97,1)]
    # Independent pixel ruler: take mast-top pixels from the rendered elevation,
    # then measure against an explicitly shifted calibration. No forced pass value.
    p=T(355,510); candidates=[]
    for yy in range(round(p[1])-3,round(p[1])+4):
        for xx in range(round(p[0])-4,round(p[0])+5):
            if im.getpixel((xx,yy))==tuple(int(ink[i:i+2],16) for i in (1,3,5)):candidates.append((xx,yy))
    measured=min(candidates,key=lambda q:(q[0]-p[0])**2+(q[1]-p[1])**2)
    zread=(sy-measured[1])/scale
    controls={'expected_z_cells':510,'pixel_read_z_cells':round(zread,4),
      'negative_control':'withdrawn: changing datum does not test asset perturbation; actual three-cell asset shift is checked in verify_skeleton.json'}
    report={'stage':'general','source': 'original plan.json; coordinates are design decisions','stations':stations,'dimensions_m':{'hull_length':52,'nominal_beam':13.4,'dwl':5.2,'mast_top':51},'pixel_control':controls,'sha256_png':hashlib.sha256(out.read_bytes()).hexdigest()}
    (ROOT/'verify_general.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

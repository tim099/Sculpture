"""54-gun installation schedule. Reads model placements and the original design separately."""
import csv, json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/Unity/Valhalla/Sculpture/works')
DES=ROOT/'sirius-tidegrave-01m/design'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
p=read(DES/'plan.json');rows=[]
parts=read(HERE/'shared/parts.json')
by_path={m['path']:m for m in parts['models']}
for level in ('lower','upper','weather'):
    source=ROOT/('sirius-tidegrave-01m-deck-'+level)/'models.json'
    for m in read(source)['models']:
        if m.get('meta',{}).get('kind')!='gun':continue
        path='甲板-'+level+'/'+m['name'];q=by_path[path]
        rows.append({'path':path,'deck':level,'gun':m['meta']['gun'],
            'x':m['at'][0],'y':m['at'][1],'z':m['at'][2],
            'pivot':json.dumps(m['pivot']),'scale':json.dumps(m['scale']),
            'rotate':json.dumps(m['rotate']),'source':m['work'],
            'muzzle':json.dumps(q['points']['muzzle']),
            'breech':json.dumps(q['points']['breech'])})
rows.sort(key=lambda r:r['path'])
assert len(rows)==54
assert sum(r['gun']=='24l' for r in rows)==48
assert sum(r['gun']=='18chase' for r in rows)==6
for level,z in zip(('lower','upper'),p['guns']['decks']):
    for x in p['guns']['x']:
        found=[r for r in rows if r['deck']==level and r['x']==x+.5 and r['z']==z+1]
        assert len(found)==2
        assert abs(sum(r['y'] for r in found)-241)<1e-9
assert sorted((r['x'],r['y'],r['z']) for r in rows if r['gun']=='18chase')==sorted(tuple(a) for a in p['guns']['chase_layout']['base_positions'])
with (HERE/'gun_schedule.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
im=Image.new('RGB',(1600,1050),'#102630');d=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',n)
d.text((35,20),'潮墓號 54砲施工定位表 / 2026-10-21',font=font(30),fill='#d9e2d0')
d.text((35,65),'0.1m/格；+X艏，+Y右舷；來源座標與plan設計獨立核對。48舷砲+6固定艏砲。',font=font(20),fill='#72b2ae')
for level,z,yp in [('lower',66,310),('upper',91,580),('weather',116,850)]:
    d.text((35,yp-170),f'{level}   floor {z}',font=font(23),fill='#72b2ae')
    for x in range(100,651,50):
        xx=160+(x-100)*2.3;d.line((xx,yp-130,xx,yp+115),fill='#35535b');d.text((xx,yp+120),str(x),font=font(16),fill='#d9e2d0')
    d.line((160,yp,1425,yp),fill='#35535b')
    for r in rows:
        if r['deck']!=level:continue
        xx=160+(r['x']-100)*2.3;yy=yp+(r['y']-120.5)*1.6
        d.rectangle((xx-7,yy-7,xx+7,yy+7),outline='#d5b573',width=2)
        name=r['path'].split('/')[-1];d.text((xx-20,yy+10 if r['y']>120.5 else yy-28),name,font=font(14),fill='#d9e2d0')
d.text((35,1010),'本圖是安裝位置表；碰撞、54條20m射線與Y+3負控見hardware/REPORT.md。',font=font(18),fill='#72b2ae')
im.save(HERE/'gun_schedule.png')
report={'guns':54,'broadside':48,'chase':6,'plan_matched_broadside':48,'plan_matched_chase':6,
        'scope':'Placement coordinates/source and exported muzzle/breech; collision measured independently in hardware report.',
        'plan_sha256':hashlib.sha256((DES/'plan.json').read_bytes()).hexdigest(),
        'csv_sha256':hashlib.sha256((HERE/'gun_schedule.csv').read_bytes()).hexdigest()}
(HERE/'gun_schedule_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))

# TASK-0747: run the actual game's public debug API; no source changes.
import sys,subprocess,tempfile,shutil,re,html,json
from pathlib import Path
root=Path(__file__).parent;page=Path(sys.argv[1])
probe=r'''<script>
(function poll(){try{if(!window.__game||!__game.ships().length)return setTimeout(poll,100);
__game.start('pve',2000);
const sh=__game.ships().find(s=>s.T.id==='tidegrave');if(!sh)return setTimeout(poll,100);
const i=sh.i;__game.gfx({deco:1,port:1});__game.portsForce(i,1);__game.tick(1);__game.run(12);__game.tick(1);
const open=__game.ports(i);__game.portsForce(i,0);__game.run(12);__game.tick(1);const closed=__game.ports(i);
const finite=sh.decos.filter(d=>d.meta.kind==='portlid').every(d=>!d.L||Array.from(d.L).every(Number.isFinite));
const m=sh.M,P=[355,120.5,95],t=[m[0]*P[0]+m[4]*P[1]+m[8]*P[2]+m[12],m[1]*P[0]+m[5]*P[1]+m[9]*P[2]+m[13],m[2]*P[0]+m[6]*P[1]+m[10]*P[2]+m[14]];__game.cam({mode:0,track:false,tgt:t,yaw:-sh.yaw+Math.PI/2,pitch:.14,dist:53});
const pre=document.createElement('pre');pre.id='portprobe';pre.textContent=JSON.stringify({open,closed,finite});document.body.appendChild(pre);
}catch(e){const pre=document.createElement('pre');pre.id='portprobe';pre.textContent=JSON.stringify({error:String(e),stack:e.stack});document.body.appendChild(pre);}})();
</script>'''
# Temporary large page stays in scratch, rather than version control.
out=page.parent/'portprobe_tmp.html';out.write_text(page.read_text(encoding='utf-8')+probe,encoding='utf-8')
prof=tempfile.mkdtemp(prefix='portprobe_')
try:
 r=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--no-first-run','--user-data-dir='+prof,'--use-angle=swiftshader','--enable-unsafe-swiftshader','--window-size=1500,950','--screenshot='+str(root/'closed.png'),'--virtual-time-budget=60000','--dump-dom',out.as_uri()+'?demo=0&ship=tidegrave,constitution&debug=1&cache=0&prefs=0&seed=3&g_deco=1&g_port=1'],capture_output=True,timeout=180)
 dom=r.stdout.decode('utf-8','replace');m=re.search(r'<pre id="portprobe">(.*?)</pre>',dom,re.S);assert m,'probe missing'
 data=json.loads(html.unescape(m.group(1)));(root/'browser.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 assert data['finite'] and data['open']['n']==data['closed']['n']==48,data
 assert all(x['s']==2 and not x['gone'] for x in data['open']['L']), 'open failed'
 assert all(x['s']==0 and not x['gone'] for x in data['closed']['L']), 'close failed'
 print('48 open and 48 closed; finite transforms; no lids lost')
finally:
 shutil.rmtree(prof,ignore_errors=True);out.unlink(missing_ok=True)


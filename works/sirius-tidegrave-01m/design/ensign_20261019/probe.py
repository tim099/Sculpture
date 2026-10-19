import sys,subprocess,tempfile,shutil,re,html,json
from pathlib import Path
root=Path(__file__).parent;page=Path(sys.argv[1]);tag=sys.argv[2]
probe=r"""<script>
(function poll(){try{if(!window.__game||!__game.ships().length)return setTimeout(poll,100);
const sh=__game.ships().find(s=>s.T.id==='tidegrave');if(!sh)return setTimeout(poll,100);
__game.phx('full');__game.run(0.1);
function snap(){const k=sh.T.rig.sails.findIndex(s=>s.name==='ensign'),s=sh.T.rig.sails[k],T=sh.T.cloth[k].sim,c=sh.cl[k];
let finite=Array.from(c.p).every(Number.isFinite),poleError=0;for(let j=0;j<=s.recipe.res;j++){let i=j*(s.recipe.res+1),o=i*3;poleError=Math.max(poleError,Math.hypot(c.p[o]-T.p0[o],c.p[o+1]-T.p0[o+1],c.p[o+2]-T.p0[o+2]));}
return {bind:s.recipe.bind,pin:s.recipe.pin,finite,poleErrorCells:poleError,corners:s.cornerIdx.map(i=>({i,pin:c.pin[i],hk:T.hk[i],p:Array.from(c.p.slice(i*3,i*3+3))}))};}
const samples=[];samples.push(snap());for(let j=0;j<4;j++){__game.run(5);samples.push(snap());}
const m=sh.M,P=[90,120.5,223.5],t=[m[0]*P[0]+m[4]*P[1]+m[8]*P[2]+m[12],m[1]*P[0]+m[5]*P[1]+m[9]*P[2]+m[13],m[2]*P[0]+m[6]*P[1]+m[10]*P[2]+m[14]];__game.cam({mode:0,track:false,tgt:t,yaw:-sh.yaw+Math.PI/2,pitch:0.1,dist:8});const pre=document.createElement('pre');pre.id='lateenprobe';pre.textContent=JSON.stringify(samples);document.body.appendChild(pre);
}catch(e){const pre=document.createElement('pre');pre.id='lateenprobe';pre.textContent=JSON.stringify({error:String(e),stack:e.stack});document.body.appendChild(pre);}})();
</script>"""
out=root/(tag+'_probe.html');out.write_text(page.read_text(encoding='utf-8')+probe,encoding='utf-8')
prof=tempfile.mkdtemp(prefix='lateenprobe_')
try:
 r=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--no-first-run','--user-data-dir='+prof,'--use-angle=swiftshader','--enable-unsafe-swiftshader','--window-size=1280,900','--screenshot='+str(root/(tag+'_flag.png')),'--virtual-time-budget=60000','--dump-dom',out.as_uri()+'?demo=0&ship=tidegrave,constitution&debug=1&cache=0&prefs=0&seed=3'],capture_output=True,timeout=180)
 dom=r.stdout.decode('utf-8','replace');m=re.search(r'<pre id="lateenprobe">(.*?)</pre>',dom,re.S)
 assert m,'probe missing'
 data=json.loads(html.unescape(m.group(1)));(root/(tag+'_browser.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(data,ensure_ascii=False))
finally:shutil.rmtree(prof,ignore_errors=True)

import sys,subprocess,tempfile,shutil,re,html,json
from pathlib import Path
root=Path(__file__).parent;page=Path(sys.argv[1]);tag=sys.argv[2]
probe=r"""<script>
(function poll(){try{if(!window.__game||!__game.ships().length)return setTimeout(poll,100);
const sh=__game.ships().find(s=>s.T.id==='tidegrave');if(!sh)return setTimeout(poll,100);
__game.phx('full');__game.run(0.1);
function snap(){const k=sh.T.rig.sails.findIndex(s=>s.name==='mizzen-lateen'),s=sh.T.rig.sails[k],T=sh.T.cloth[k].sim,c=sh.cl[k];
let frozen=0,fin=true,maxCorner=0;for(let i=0;i<T.n;i++){if(T.hk[i]&&T.yk[i]<0)frozen++;for(let j=0;j<3;j++)if(!Number.isFinite(c.p[i*3+j]))fin=false;}
for(const i of s.cornerIdx){const m=sh.models[T.yk[i]],o=i*3,x=T.p0[o]-m.piv[0],y=T.p0[o+1]-m.piv[1],a=m.rot||0,wx=m.piv[0]+x*Math.cos(a)-y*Math.sin(a),wy=m.piv[1]+x*Math.sin(a)+y*Math.cos(a);maxCorner=Math.max(maxCorner,Math.hypot(c.p[o]-wx,c.p[o+1]-wy));}
return {frozenInteriorPins:frozen,finite:fin,maxCornerErrorCells:maxCorner,bind:s.recipe.bind,pin:s.recipe.pin,yards:s.cornerIdx.map(i=>({id:sh.models[T.yk[i]].meta.id,angle:sh.models[T.yk[i]].rot||0}))};}
const samples=[];samples.push(snap());for(let j=0;j<4;j++){__game.run(5);samples.push(snap());}
const pre=document.createElement('pre');pre.id='lateenprobe';pre.textContent=JSON.stringify(samples);document.body.appendChild(pre);
}catch(e){const pre=document.createElement('pre');pre.id='lateenprobe';pre.textContent=JSON.stringify({error:String(e),stack:e.stack});document.body.appendChild(pre);}})();
</script>"""
out=root/(tag+'_probe.html');out.write_text(page.read_text(encoding='utf-8')+probe,encoding='utf-8')
prof=tempfile.mkdtemp(prefix='lateenprobe_')
try:
 r=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--no-first-run','--user-data-dir='+prof,'--use-angle=swiftshader','--enable-unsafe-swiftshader','--virtual-time-budget=60000','--dump-dom',out.as_uri()+'?demo=0&ship=tidegrave,constitution&debug=1&cache=0&prefs=0&seed=3'],capture_output=True,timeout=180)
 dom=r.stdout.decode('utf-8','replace');m=re.search(r'<pre id="lateenprobe">(.*?)</pre>',dom,re.S)
 assert m,'probe missing'
 data=json.loads(html.unescape(m.group(1)));(root/(tag+'_browser.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(data,ensure_ascii=False))
finally:shutil.rmtree(prof,ignore_errors=True)

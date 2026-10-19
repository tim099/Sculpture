import sys, subprocess, tempfile, shutil, re, html, json, hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
page,tag=sys.argv[1:3]
root=Path(__file__).parent
for seed in (3,7):
 prof=tempfile.mkdtemp(prefix='sirius_ports_')
 try:
  q=f'demo=30&dump=1&ship=tidegrave,constitution&seed={seed}'
  r=subprocess.run([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--no-first-run','--user-data-dir='+prof,'--use-angle=swiftshader','--enable-unsafe-swiftshader','--virtual-time-budget=90000','--dump-dom',Path(page).as_uri()+'?'+q],capture_output=True,timeout=180)
  dom=r.stdout.decode('utf-8','replace')
  m=re.search(r'<pre id="dump"[^>]*>(.*?)</pre>',dom,re.S)
  if not m:
   (root/(tag+'.failed.html')).write_text(dom,encoding='utf-8')
   raise SystemExit('dump missing: '+tag)
  body=html.unescape(m.group(1)); json.loads(body)
  (root/f'{tag}_{seed}.json').write_text(body,encoding='utf-8')
  print(tag,seed,hashlib.sha256(body.encode()).hexdigest())
 finally: shutil.rmtree(prof,ignore_errors=True)

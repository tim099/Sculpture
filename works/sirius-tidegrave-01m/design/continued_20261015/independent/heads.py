import pathlib,sys,json,zlib,struct,hashlib
OUT=pathlib.Path(__file__).parent
s=(OUT/'check.py').read_text(encoding='utf8'); a=s.index('sel=[r');b=s.index('angles=',a)
s=s[:a]+"sel=[r for r in rig['ropes'] if r['name'].startswith(('main-backstay','fore-backstay'))]\n"+s[b:]
sys.argv=[str(OUT/'check.py'),'final_heads.vxk']
exec(s.replace("OUT/'results.json'","OUT/'heads_sweep.json'"))
payloads=[]
for name in ['after_robbands.vxk','final_rig.vxk','final_heads.vxk']:
    p=ROOT/'sirius-tidegrave-01m/design/continued_20261015'/name
    raw=zlib.decompress(p.read_bytes(),-15);n=struct.unpack_from('<I',raw,4)[0];payloads.append((name,hashlib.sha256(raw[8+n:]).hexdigest()))
(OUT/'body_payloads.json').write_text(json.dumps(payloads),encoding='utf8')
print('body payloads identical',len(set(h for n,h in payloads))==1)

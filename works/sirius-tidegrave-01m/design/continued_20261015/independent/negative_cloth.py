import pathlib,sys
OUT=pathlib.Path(__file__).parent
sys.argv=[str(OUT/'check.py'),'final_heads.vxk']
exec((OUT/'check.py').read_text(encoding='utf8').split('sel=[r')[0])
s=(OUT/'cloth.py').read_text(encoding='utf8');exec(s[s.index('def clip('):s.index('s=next(s')])
oldpath=OUT/'snapshots/old_source_after.vxk';rr=zlib.decompress(oldpath.read_bytes(),-15);n=struct.unpack_from('<I',rr,4)[0];old=json.loads(rr[8:8+n]);s=next(q for q in old['rig']['sails'] if q['name']=='mizzen-topsail')
hits=checktris(np.array(s['verts']).reshape(-1,3),np.array(s['tris']).reshape(-1,3),body)
(OUT/'negative_cloth.json').write_text(json.dumps({'source':str(oldpath),'body_reference':str(SRC),'hits':hits}),encoding='utf8')
print('old triangle96 at (207,120,336)',[h for h in hits if h['triangle']==96 and h['cube']==[207,120,336]])

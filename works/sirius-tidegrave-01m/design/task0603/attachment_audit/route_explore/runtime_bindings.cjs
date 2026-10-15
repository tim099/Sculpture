const fs=require('fs'),path=require('path'),zlib=require('zlib'),vm=require('vm'),crypto=require('crypto');
const Q=__dirname,root='D:/Unity/Valhalla/Blockside',out=Q+'/rope_runtime';fs.mkdirSync(out,{recursive:true});const src={},hashes={};
for(const f of ['00_core.js','10_ship.js','21_gunnery.js','30_rig_physics.js']){let b=fs.readFileSync(root+'/src/js/'+f);fs.writeFileSync(out+'/'+f,b);src[f]=b.toString();hashes[f]=crypto.createHash('sha256').update(b).digest('hex');}
const C={console,Uint8Array,Float32Array,Math};vm.createContext(C);
function take(file,name){let s=src[file],st=s.indexOf('function '+name+'('),i=s.indexOf('{',st),n=1,j=i+1;for(;n;j++){if(s[j]==='{')n++;if(s[j]==='}')n--;}vm.runInContext(s.slice(st,j),C);}
for(const n of ['norm','cross','len','sub'])take('00_core.js',n);take('21_gunnery.js','meshOcc');take('10_ship.js','yardNear');take('10_ship.js','ropeYards');
const input=fs.readFileSync(Q+'/manual_candidate.vxk'),raw=zlib.inflateRawSync(input),hn=raw.readUInt32LE(4),rig=JSON.parse(raw.subarray(8,8+hn)).rig,T={rig,meshes:rig.meshes.map(x=>({occ:C.meshOcc(x)}))},sh={T,ropes:rig.ropes.map(r=>({pts:r.pts}))};C.ropeYards(sh);
const rows=rig.ropes.map((r,i)=>({name:r.name,ya:sh.ropes[i].ya,yb:sh.ropes[i].yb,ends:r.ends}));fs.writeFileSync(Q+'/runtime_bindings.json',JSON.stringify({vxkSHA:crypto.createHash('sha256').update(input).digest('hex'),hashes,rows},null,2));console.log('ropes',rows.length,'moving',rows.filter(x=>x.ya>=0||x.yb>=0).length,'multiple yards',rows.filter(x=>x.ya>=0&&x.yb>=0&&x.ya!==x.yb));

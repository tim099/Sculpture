const fs=require('fs'),vm=require('vm'),zlib=require('zlib'),path=require('path');const P=process.env.ROPE_OUTPUT||__dirname,F=path.join(P,'frozen');
function original(file,name){const s=fs.readFileSync(path.join(F,file),'utf8'),st=s.indexOf('function '+name+'(');if(st<0)throw name;let p=s.indexOf('{',st),d=1,i=p+1;for(;d;i++){if(s[i]==='{')d++;if(s[i]==='}')d--;}return s.slice(st,i);}
let ctx={Math,Float32Array,Uint8Array,Map,console,clamp:(x,a,b)=>Math.max(a,Math.min(b,x))};vm.createContext(ctx);
for(const [f,names] of [['00_core.js',['norm','sub','dot','cross','len']],['21_gunnery.js',['rotZ','meshOcc']],['10_ship.js',['yardNear','ropeYards']],['30_rig_physics.js',['braceYards','yardRopes']]])for(const name of names)vm.runInContext(original(f,name),ctx);
vm.runInContext('var BRACE_MAX=.70, BOOM_MIN=.14, BOOM_MAX=1.40, BRACE_RATE=.14, BRACE_HYST=2.7;function ropeBox(p){return null}',ctx);
let raw=zlib.inflateRawSync(fs.readFileSync(path.join(F,process.env.ROPE_VXK||'final_heads.vxk'))),H=JSON.parse(raw.subarray(8,8+raw.readUInt32LE(4))),T={rig:H.rig,meshes:H.rig.meshes.map(m=>({occ:ctx.meshOcc(m)}))};
let models=T.rig.models.map((m,k)=>({k,name:m.name,alive:true,rot:0,r0:(+(m.meta||{}).rotate_z_deg||0)*Math.PI/180,piv:(m.points||{}).pivot,yk:(m.meta||{}).yard})),sh={T,models,ropes:T.rig.ropes.map(r=>({...r,pts:Float32Array.from(r.pts)})),yards:models.filter((m,k)=>T.rig.models[k].meta?.kind==='yard'&&m.piv)};ctx.ropeYards(sh);
fs.writeFileSync(path.join(P,'bindings.json'),JSON.stringify(sh.ropes.map(r=>({name:r.name,ya:r.ya,yb:r.yb}))));
// Physical on/off initial rot=0, settling, both tack crossings, hysteresis boundaries, and abrupt wind reversals.
const legs=[{psi:0,s:12},{psi:1.4,s:16},{psi:-1.4,s:16},{psi:2.85,s:16},{psi:-2.85,s:16},{psi:-2.69,s:16},{psi:2.69,s:16},{psi:0,s:16}],dt=1/60;let time=0,frames=[],index=0;
function frame(){frames.push({time,angles:sh.yards.map(m=>m.rot),ropes:sh.ropes.map(r=>Array.from(r.pts))});}
frame();for(const leg of legs)for(let j=0;j<leg.s/dt;j++){ctx.braceYards(sh,[Math.cos(leg.psi),Math.sin(leg.psi),0],dt);ctx.yardRopes(sh,true);time+=dt;if(++index%6===0)frame();}
fs.writeFileSync(path.join(P,'trajectory.json'),JSON.stringify({dt,frame_dt:.1,legs,yards:sh.yards.map(m=>({k:m.k,name:m.name,r0:m.r0})),frames}));console.log('frames',frames.length,'bindings',sh.ropes.filter(r=>r.ya>=0||r.yb>=0).length);

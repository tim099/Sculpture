// Read-only execution of the actual game's meshOcc / yardNear / braceYards.
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto');
const out=__dirname,input=JSON.parse(fs.readFileSync(path.join(out,'input.json'),'utf8'));
const game=(fs.existsSync(path.join(out,'game_snapshot'))?path.join(out,'game_snapshot'):'D:/Unity/Valhalla/ArtGallery/HtmlGames/_build/ame_constitution_broadside/js');
const gun=fs.readFileSync(game+'/21_gunnery.js','utf8'),ship=fs.readFileSync(game+'/10_ship.js','utf8'),phys=fs.readFileSync(game+'/30_rig_physics.js','utf8');
function section(s,a,b){return s.slice(s.indexOf(a),s.indexOf(b,s.indexOf(a)));}
const ctx={Math,Uint8Array,Float32Array,clamp:(a,l,h)=>Math.max(l,Math.min(h,a)),norm:a=>{let n=Math.hypot(...a);return n?a.map(x=>x/n):[0,0,0]},len:a=>Math.hypot(...a),sub:(a,b)=>a.map((x,i)=>x-b[i]),cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]};vm.createContext(ctx);
vm.runInContext(section(gun,'function meshOcc(m)','/** 模型整個飛出去'),ctx);
vm.runInContext(section(ship,'function yardNear(T, P, r)','/** 繩的兩端'),ctx);
const constants=phys.match(/var BRACE_MAX[^;]+;/)[0];vm.runInContext(constants+section(phys,'function braceYards(sh, wl, dt)','/** 綁在帆桁上的繩重算形狀'),ctx);
const T={rig:input.header.rig,meshes:[]};let done=new Set;
for(const m of T.rig.models){if(m.meta?.kind!=='yard'||done.has(m.mesh))continue;T.meshes[m.mesh]={occ:ctx.meshOcc(T.rig.meshes[m.mesh])};done.add(m.mesh);}
let bindings=T.rig.ropes.map(r=>({name:r.name,ya:ctx.yardNear(T,r.pts.slice(0,3),3),yb:ctx.yardNear(T,r.pts.slice(-3),3)}));
let samples=[];for(let deg=-180;deg<=180;deg+=1){let sh={braceSide:1,yards:input.yards.map(y=>({alive:true,yk:T.rig.models[y.model_index].meta.yard,r0:y.r0,rot:0}))};ctx.braceYards(sh,[Math.cos(deg*Math.PI/180),Math.sin(deg*Math.PI/180)],100);samples.push({wind_deg:deg,absolute_angles:sh.yards.map(y=>y.r0+y.rot)});}
let trajectories=[];for(const sequence of [[0,180,-90,90,0],[90,-90,180,0],[-180,0,180]]){let sh={braceSide:1,yards:input.yards.map(y=>({alive:true,yk:T.rig.models[y.model_index].meta.yard,r0:y.r0,rot:0}))};for(const deg of sequence){for(let step=0;step<240;step++){ctx.braceYards(sh,[Math.cos(deg*Math.PI/180),Math.sin(deg*Math.PI/180)],.125);trajectories.push({wind_deg:deg,absolute_angles:sh.yards.map(y=>y.r0+y.rot)});}}}
const codeHashes={};for(const [name,code] of Object.entries({'21_gunnery.js':gun,'10_ship.js':ship,'30_rig_physics.js':phys}))codeHashes[name]=crypto.createHash('sha256').update(code).digest('hex');
fs.writeFileSync(path.join(out,'game_bindings.json'),JSON.stringify({source_sha256:input.source_sha256,constants,codeHashes,bindings,samples,trajectories}));console.log('actual game bindings',bindings.filter(x=>x.ya>=0||x.yb>=0).length,'sample states',samples.length,'trajectory states',trajectories.length);

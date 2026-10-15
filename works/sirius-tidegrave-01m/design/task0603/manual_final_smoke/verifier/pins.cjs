const fs=require('fs'),vm=require('vm'),zlib=require('zlib'),crypto=require('crypto');
const root=(process.env.CLOTH_SOURCE||'D:/Unity/Valhalla/Blockside').replace(/\/$/,'')+'/',out=process.env.CLOTH_OUT||__dirname;fs.mkdirSync(out,{recursive:true});
let ctx={console,TextDecoder,Uint8Array,Float32Array,Int8Array,Int16Array,Int32Array,Uint16Array,Uint32Array,Map,Set,Math,atob,Q:new URLSearchParams(),performance:require("perf_hooks").performance};ctx.window=ctx;vm.createContext(ctx);
const hashes={},sourceCache={};
function source(p){if(sourceCache[p])return sourceCache[p];let b=fs.readFileSync(root+p);hashes[p]=crypto.createHash('sha256').update(b).digest('hex');let dest=out+'/frozen_source/'+p;fs.mkdirSync(require('path').dirname(dest),{recursive:true});fs.writeFileSync(dest,b);return sourceCache[p]=b.toString()}
vm.runInContext(source('VoxelKit/voxelkit.js'),ctx);ctx.VK=ctx.VoxelKit;
function funcs(p,names){let s=source(p), clean=s.replace(/\/\*[\s\S]*?\*\/|\/\/[^\r\n]*|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"/g,x=>' '.repeat(x.length));for(const name of names){let st=s.indexOf('function '+name+'(');if(st<0)throw Error(name);let first=clean.indexOf('{',st),level=1,end=first+1;for(;level&&end<clean.length;end++){if(clean[end]==='{')level++;if(clean[end]==='}')level--}vm.runInContext(s.slice(st,end),ctx)}}
funcs('src/js/00_core.js',['norm','add','sub','mul','dot','cross','len','clamp']);
funcs('src/js/21_gunnery.js',['meshOcc','segDist2','rotZ']);
funcs('src/js/10_ship.js',['yardNear','anchorNear','sailRope','sailRopeName','ropeBox']);
funcs('src/js/31_sailing.js',['isFlag']);
vm.runInContext(source('src/js/30_rig_physics.js'),ctx);vm.runInContext(source('src/js/11_rig_gpu.js'),ctx);
let file=process.argv[2]||'D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m/design/continued_20261015/final_heads.vxk',b=fs.readFileSync(file),m=ctx.VK.parse(new Uint8Array(zlib.inflateRawSync(b))),H={rig:m.header.rig,base:ctx.VK.Grid.fromModel(m)};
H.meshes=H.rig.meshes.map(x=>({occ:ctx.meshOcc(x)}));H.rbox=H.rig.ropes.map(x=>ctx.ropeBox(x.pts));
ctx.DT=1/60;ctx.rigLv=()=>({every:2,it:4});ctx.SIMT=0;
let rows=[];
for(const s of H.rig.sails){let T=ctx.clothTemplate(H,s),c={T};ctx.clothInit(c);let fine=ctx.clothFine(c,new Float32Array(T.n*3));let max=0,at=-1;for(let i=0;i<fine.length;i++)if(Math.abs(fine[i]-T.p0[i])>max){max=Math.abs(fine[i]-T.p0[i]);at=i}
let pins=[];for(let i=0;i<T.sim.n;i++)if(T.sim.hk[i])pins.push({coarse:i,fine:T.sim.fine[i],hk:T.sim.hk[i],hv:T.sim.hv[i],yk:T.sim.yk[i],p:Array.from(T.sim.p0.slice(i*3,i*3+3))});
rows.push({name:s.name,templateSHA:crypto.createHash('sha256').update(JSON.stringify(T)).digest('hex'),meta:s.meta,n:T.n,coarse:T.sim.n,grid:T.grid,sides:T.sides,pins,fineInitMaxError:max,errorAt:at});}
fs.writeFileSync(out+'/pins.json',JSON.stringify({file,vxkSHA:crypto.createHash('sha256').update(b).digest('hex'),hashes,rows},null,2));
fs.writeFileSync(out+'/fine_topology.json',JSON.stringify(H.rig.sails.map(s=>{let T=ctx.clothTemplate(H,s);return {name:s.name,n:T.n,tris:Array.from(T.tris),texture:s.texture||null}})));
console.log(JSON.stringify(rows.map(x=>({name:x.name,n:x.n,coarse:x.coarse,pins:x.pins.length,fineInitMaxError:x.fineInitMaxError})),null,2));
if(process.argv.includes('--dynamic')){
let results=[];ctx.CACC=new Float32Array(10000);ctx.CCNT=new Uint16Array(10000);
for(const scenario of [{name:'beamS',wind:[0,100,0]},{name:'beamP',wind:[0,-100,0]},{name:'head',wind:[-100,0,0]},{name:'following',wind:[100,0,0]},{name:'stormS',wind:[0,220,0]},{name:'tack',wind:[0,100,0]}]){
let sh={grid:H.base,models:H.rig.models.map(m=>({rot:0,r0:(+(m.meta||{}).rotate_z_deg||0)*Math.PI/180,piv:(m.points||{}).pivot,yk:(m.meta||{}).yard,alive:true})),ropes:H.rig.ropes.map(r=>({dead:false}))};sh.yards=sh.models.filter(m=>m.piv);
let cls=H.rig.sails.map(s=>{let T=ctx.clothTemplate(H,s),c={T,ev:2};ctx.clothInit(c);return c}),hits=[],count=0,near=new Map();
for(let step=0;step<=1800;step++){
ctx.SIMT=step/60;let wl=scenario.name==='tack'&&step>=900?[0,-100,0]:scenario.wind;ctx.braceYards(sh,wl,1/60);
cls.forEach((c,k)=>{ctx.yardPins(sh,c);if((step+k+1)%2===0)ctx.clothStep(sh,c,wl,[0,0,-9.81/m.header.meters_per_voxel]);if(step%60)return;
let f=ctx.clothFine(c,new Float32Array(c.T.n*3)),T=c.T;
for(let ti=0;ti<T.tris.length;ti+=3){let vs=[T.tris[ti],T.tris[ti+1],T.tris[ti+2]],xyz=[0,0,0];for(let v of vs)for(let a=0;a<3;a++)xyz[a]+=f[v*3+a]/3;let q=xyz.map(Math.floor);if(!sh.grid.get(...q))continue;count++;let key=k+':'+ti;if(!near.has(key)){near.set(key,true);hits.push({sail:H.rig.sails[k].name,time:step/60,tri:ti/3,xyz,pinnedFine:vs.map(v=>T.hk[v]),kind:vs.every(v=>T.hk[v])?'attachment':'interior-candidate'});}
}});
}
results.push({scenario:scenario.name,samples:31,centroidInsideBody:count,uniqueHits:hits});console.log(scenario.name,count,hits.slice(0,5));
}
fs.writeFileSync(out+'/body_dynamics.json',JSON.stringify({hashes,results},null,2));}
module.exports={ctx,H,m,hashes,funcs,source,file};

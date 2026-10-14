const fs=require('fs');
const root=process.env.VERIFY_FROZEN==='1'?__dirname+'/frozen_game/':'D:/Unity/Valhalla/Blockside/src/js/';
const H=JSON.parse(fs.readFileSync(__dirname+'/header.json','utf8'));
const T={rig:H.rig,meshes:H.rig.meshes};
const sub=(a,b)=>a.map((v,k)=>v-b[k]),dot=(a,b)=>a.reduce((s,v,k)=>s+v*b[k],0),len=a=>Math.sqrt(dot(a,a)),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm=a=>a.map(v=>v/(len(a)||1));
let gun=fs.readFileSync(root+'21_gunnery.js','utf8'),ship=fs.readFileSync(root+'10_ship.js','utf8');
eval(gun.substring(gun.indexOf('function meshOcc('),gun.indexOf('/** 模型整個飛出去')));
eval(ship.substring(ship.indexOf('function yardNear('),ship.indexOf('/** 繩的兩端各跟著')));
for(const m of T.rig.models)if(m.meta?.kind==='yard'&&!T.meshes[m.mesh].occ)T.meshes[m.mesh].occ=meshOcc(T.meshes[m.mesh]);
let records=[];
for(const r of T.rig.ropes){
 if(!/^(main|fore)-.*(ratline|shroud|backstay)|^(main|fore)-(course|topsail)\.lift-|\.(brace|robband)-/.test(r.name))continue;
 let P=r.pts, n=P.length, j=[yardNear(T,P.slice(0,3),3),yardNear(T,P.slice(n-3),3)];
 records.push({name:r.name,ends:r.ends,yards:j.map(k=>k<0?null:T.rig.models[k].name)});
}
fs.writeFileSync(__dirname+'/bindings.json',JSON.stringify(records,null,2));
console.log(JSON.stringify(records.filter(r=>r.yards.some(Boolean)),null,2));

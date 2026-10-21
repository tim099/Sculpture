const fs=require('fs'),vm=require('vm'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const dir=__dirname,src='D:/Unity/Valhalla/Blockside/src/js/26_spin.js';
const parts=JSON.parse(fs.readFileSync(path.join(dir,'shared/after_parts.json'),'utf8').replace(/^\uFEFF/,''));
const kinds=JSON.parse(fs.readFileSync('D:/Unity/Valhalla/Blockside/src/config/meta_kinds.json','utf8').replace(/^\uFEFF/,''));
const ctx={len:a=>Math.hypot(...a),sub:(a,b)=>a.map((v,i)=>v-b[i]),norm:a=>a.map(v=>v/Math.hypot(...a)),clamp:(v,a,b)=>Math.max(a,Math.min(b,v)),kindProp:(k,p)=>((kinds.kinds||kinds)[k]||{})[p]};
vm.createContext(ctx);vm.runInContext(fs.readFileSync(src,'utf8'),ctx);
const ids=['rudder-1','rudder-bearing-moving-1','rudder-bearing-fixed-1'];
const sh={rudder:0,models:parts.models.filter(m=>ids.includes(m.meta?.id)).map(m=>({path:m.path,pts:m.points,meta:m.meta,kind:m.meta.kind||'',alive:true}))};
assert.equal(sh.models.length,3);ctx.spinShip(sh);assert.equal(sh.spins.length,2);
const issues=[];ctx.spinIssues(sh,(...a)=>issues.push(a));assert.equal(issues.length,0);
const rows=[];for(const v of [-1,-.5,0,.5,1,0]){sh.rudder=v;for(let i=0;i<600;i++)ctx.spinStep(sh,1/60);const [a,b]=sh.spins;assert(Math.abs(a.sw-b.sw)<1e-12);assert(Math.abs(a.spinB.deg-30*v)<1e-9);assert.deepEqual(Array.from(a.spv),Array.from(b.spv));assert.deepEqual(Array.from(a.sax),Array.from(b.sax));rows.push({rudder:v,degrees:a.spinB.deg,axis:Array.from(a.sax),pivot:Array.from(a.spv)});}
// Same shipped functions, actual metadata: omitting explicit axis must produce an issue.
const mutant=JSON.parse(JSON.stringify(sh.models.find(m=>m.meta.id==='rudder-bearing-moving-1')));for(const k of Object.keys(mutant.meta))if(k.startsWith('spin_axis_'))delete mutant.meta[k];const neg=[];ctx.spinIssues({models:[mutant]},(...a)=>neg.push(a));assert.equal(neg.length,1);
const report={method:'Node VM executes current unmodified 26_spin.js on exported model metadata; vector helpers supplied by harness. No full scene, loader or renderer run.',source:src,source_sha256:crypto.createHash('sha256').update(fs.readFileSync(src)).digest('hex'),spin_bound:2,fixed_unbound:true,issues,rows,negative_missing_axis_issues:neg.length};
fs.writeFileSync(path.join(dir,'spin_readback.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({spin_bound:2,issues:issues.length,drives:rows.length,negative_issues:neg.length}));

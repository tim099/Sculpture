// Complete triangle/closed-mesh intersection vertex collection, including coplanar faces.
const sub=(a,b)=>a.map((x,i)=>x-b[i]),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],len=a=>Math.hypot(...a);
function seg(a,b,v){let d=sub(b,a),e=sub(v[1],v[0]),f=sub(v[2],v[0]),p=cross(d,f),det=dot(e,p);if(Math.abs(det)<1e-12)return null;let s=sub(a,v[0]),u=dot(s,p)/det,q=cross(s,e),w=dot(d,q)/det,t=dot(f,q)/det;return u>=-1e-9&&w>=-1e-9&&u+w<=1+1e-9&&t>=-1e-9&&t<=1+1e-9?{t,bary:[1-u-w,u,w]}:null;}
function inside(p,tris){let end=p.map((x,a)=>x+[10000,.00141421356,.00173205081][a]),hits=[];for(let v of tris){let h=seg(p,end,v);if(h&&h.t>1e-10)hits.push(h.t);}hits.sort((a,b)=>a-b);return hits.filter((t,i)=>!i||Math.abs(t-hits[i-1])>1e-9).length%2===1;}
function clip(poly,fn){let out=[];if(!poly.length)return out;for(let i=0;i<poly.length;i++){let a=poly[i],b=poly[(i+1)%poly.length],u=fn(a),v=fn(b);if(u>=-1e-10)out.push(a);if((u>=0)!==(v>=0))out.push(a.map((x,j)=>x+(b[j]-x)*u/(u-v)));}return out;}
function collect(v,triangles){let polys=[],rows=[],base=v.map((p,i)=>p.concat([+(i===0),+(i===1),+(i===2)]));for(let i=0;i<3;i++)if(inside(v[i],triangles))rows.push(base[i]);for(let face of triangles){let normal=cross(sub(face[1],face[0]),sub(face[2],face[0])),nl=len(normal);if(nl<1e-10)continue;
if(v.every(p=>Math.abs(dot(sub(p,face[0]),normal))/nl<1e-7)){let poly=base;for(let e=0;e<3;e++){let a=face[e],d=sub(face[(e+1)%3],a);poly=clip(poly,p=>dot(cross(d,sub(p.slice(0,3),a)),normal));}rows.push(...poly);continue;}
for(let e=0;e<3;e++){let j=(e+1)%3,h=seg(v[e],v[j],face);if(h){let bary=[0,0,0];bary[e]=1-h.t;bary[j]=h.t;rows.push(v[e].map((x,a)=>x+(v[j][a]-x)*h.t).concat(bary));}h=seg(face[e],face[j],v);if(h)rows.push(face[e].map((x,a)=>x+(face[j][a]-x)*h.t).concat(h.bary));}}
return rows.filter((p,i)=>rows.findIndex(q=>len(sub(p.slice(0,3),q.slice(0,3)))<1e-7)===i);}
module.exports={collect};

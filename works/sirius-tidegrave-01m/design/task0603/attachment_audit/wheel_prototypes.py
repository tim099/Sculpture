from prototype import *
rr=json.loads((P/'wheel_route.json').read_text(encoding='utf8'));pp=np.array(rr['route']);out=[]
for i,floor in [(1,151),(2,139)]:
 inc=pp[i]-pp[i-1];outg=pp[i+1]-pp[i];nn=inc/np.linalg.norm(inc)+outg/np.linalg.norm(outg);cells=ring(pp[i],nn,floor);origin=cells.min(axis=0);ind=np.rint((cells-origin)*2).astype(int);name='wheel_fairlead_'+str(i);(P/(name+'.vox.txt')).write_text(''.join(f'{x},{y},{z},36\n'for x,y,z in ind));pivot=(pp[i]-origin)*2;out.append({'name':name,'size':(ind.max(axis=0)+1).tolist(),'source_pivot':pivot.tolist(),'anchor_at':(pivot-.5).tolist(),'at':pp[i].tolist(),'scale':.5,'cells':len(cells),'components':connected(cells),'world_origin':origin.tolist()});np.save(P/(name+'_world.npy'),cells)
(P/'wheel_prototypes.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))

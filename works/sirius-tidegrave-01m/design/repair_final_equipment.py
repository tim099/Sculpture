from build_structure import cli,get_actual,ROOT,BASE
from build_decks import ASSEMBLY
def cut(work,cells,label):
    now=get_actual(work); found={q:now[q] for q in cells if q in now}
    f=ROOT/(label+'.vox.txt');f.write_text(''.join(f'{x},{y},{z},{c}\n' for (x,y,z),c in sorted(found.items())),encoding='utf-8')
    if found:cli(op='carvevox',work=work,voxels=f,at='0,0,0',expect_pixels=len(found))
    return len(found)
def main():
    for model,source,pivot,at,kind in [('舵輪','basecamp-frigate-constitution-01m-wheel','50,52,0','195.5,151.5,139','wheel'),('羅經櫃','summit-night-falcon-01m-binnacle','9,13,0','215.5,151.5,139','binnacle')]:
        cli(op='work',sub='model',work=BASE+'-deck-quarter',name=model,source_work=source,pivot=pivot,at=at,scale=.2,meta='{"kind":"'+kind+'"}',overwrite=1,note='Starboard steering station clear of centre companionway; credit original source author')
    n=cut(BASE,[(x,y,133) for x in range(609,614) for y in (114,126)],'final_floating_strips')
    for pos in ('aft','fore'):
        n+=cut(BASE+'-magazine-'+pos,[(x,y,z) for x in (43,44) for y in range(17,24) for z in range(18,23)],'magazine_door_'+pos)
    cli(op='stats',work=ASSEMBLY,structure=1,mirror='y:120')
    cli(op='export',work=ASSEMBLY,format='vxk',include='rig,models,parts,meta,ends',out=ROOT.parent.parent/(BASE+'-assembly')/'exports'/'tidegrave_preview.vxk')
    print('Final equipment repair removed',n)
if __name__=='__main__':main()

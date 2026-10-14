"""Rebuild disposable caches from the two portable snapshots and frozen yard sources."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT));import vxk_decode as V
blob=(OUT/'source.vxk').read_bytes();sha=hashlib.sha256(blob).hexdigest();assert sha=='5e92885eb98c095b41f21d80e0f69e287206e55be7815fe27c6a4e8abc42f8d1';h,v=V.unpack(blob);yards=json.loads((OUT/'yard_sources.json').read_text('utf8'));(OUT/'input.json').write_text(json.dumps({'source_sha256':sha,'checksum':hex(V.checksum(v)),'header':h,'yards':yards},ensure_ascii=False),'utf8');np.save(OUT/'body.npy',v)
print('rebuilt input.json/body.npy',len(v),hex(V.checksum(v)))

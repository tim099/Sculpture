"""Portable read-only VXK1 decoder. Format/algorithm source:
D:/Unity/Valhalla/ArtGallery/VoxelKit/voxel_export.py unpack/checksum.
No author verification code is used. Requires numpy only.
"""
import zlib,struct,json
import numpy as np
def unpack(blob):
    raw=zlib.decompress(blob,-15)
    if raw[:4]!=b'VXK1':raise ValueError('not VXK1')
    n=struct.unpack('<I',raw[4:8])[0];h=json.loads(raw[8:8+n]);p=8+n
    chunks=np.frombuffer(raw,'<u2',h['nchunks']*3,p).reshape(-1,3).astype(np.int32);p+=h['nchunks']*6
    data=np.frombuffer(raw,np.uint8,h['nchunks']*4096,p).reshape(h['nchunks'],4096);ci,li=np.nonzero(data)
    vox=np.stack([chunks[ci,0]*16+li%16,chunks[ci,1]*16+(li//16)%16,chunks[ci,2]*16+li//256,data[ci,li]],1).astype(np.int32)
    return h,vox
def checksum(a):
    x,y,z,c=(a[:,j].astype(np.uint64) for j in range(4));mask=0xffffffff
    return int((((x*73856093)&mask)^((y*19349663)&mask)^((z*83492791)&mask)^((c*2654435761)&mask)).sum()&mask)

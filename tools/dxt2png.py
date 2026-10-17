import struct, sys, io
from PIL import Image

def dds_wrap(w, h, fourcc, data):
    hdr = b'DDS ' + struct.pack('<7I', 124, 0x1007, h, w, 0, 0, 1) + b'\0'*44
    hdr += struct.pack('<2I4s5I', 32, 4, fourcc, 0,0,0,0,0)
    hdr += struct.pack('<5I', 0x1000, 0,0,0,0)
    return hdr + data

def load(path, fourcc=None):
    d = open(path,'rb').read()
    n = struct.unpack('<i', d[:4])[0]
    p = 4+n
    assert d[p:p+3] == b'NTF'
    w, h = struct.unpack('<ii', d[p+4:p+12])
    fmt = d[p+12:p+16]
    mip = struct.unpack('<i', d[p+16:p+20])[0]
    data = d[p+20:]
    return w, h, fmt, mip, data

if __name__ == '__main__':
    src, dst, fc = sys.argv[1], sys.argv[2], sys.argv[3].encode()
    w,h,fmt,mip,data = load(src)
    bs = 8 if fc==b'DXT1' else 16
    size = ((w+3)//4)*((h+3)//4)*bs
    im = Image.open(io.BytesIO(dds_wrap(w,h,fc,data[:size]))).convert('RGB')
    im.save(dst)
    print(src, w, h, fmt, mip, len(data), 'first-level', size, '->', dst)

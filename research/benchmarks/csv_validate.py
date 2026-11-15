"""Exact serialization byte oracle and unchanged-upstream compatibility."""
import ctypes as c
import itertools
import random
import sys

def load(p):
    lib=c.CDLL(p)
    lib.csv_write2.argtypes=[c.c_void_p,c.c_size_t,c.c_void_p,c.c_size_t,c.c_ubyte]
    lib.csv_write2.restype=c.c_size_t
    return lib
lib=load(sys.argv[1]);up=load(sys.argv[2]);rng=random.Random(641)
count=0
data=[b'',b'"',b'abc',b'""',b'a,b\nc',b'\0\xff"',*map(bytes,itertools.product([0,34,255],repeat=4))]
data += [rng.randbytes(rng.randrange(0,5000)) for _ in range(600)]
for s in data:
    for q in [0,34,39,255]:
        quote=bytes([q]);expected=quote+s.replace(quote,quote*2)+quote
        src=c.create_string_buffer(s)
        for size in sorted({0,1,2,3,len(expected)//2,len(expected)-1,len(expected),len(expected)+2}):
            outputs=[]
            for impl in [lib,up]:
                dest=c.create_string_buffer(b'\xa5'*(size+16),size+16)
                got=impl.csv_write2(dest,size,src,len(s),q)
                assert got==len(expected)
                assert dest.raw[:min(size,len(expected))]==expected[:size]
                assert dest.raw[min(size,len(expected)):]==b'\xa5'*(size+16-min(size,len(expected)))
                outputs.append(dest.raw)
            assert outputs[0]==outputs[1]
            count+=1
        for size in [0,100]:
            assert lib.csv_write2(None,size,src,len(s),q)==len(expected)
            count+=1
for dest_size in [0,1,100]:
    assert lib.csv_write2(None,dest_size,None,123,34)==0
    count+=1
print(f'{count} exact-byte, bounded-buffer, null and custom-quote cases passed')

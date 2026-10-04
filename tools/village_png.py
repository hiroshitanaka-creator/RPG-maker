"""OSの圧縮ライブラリに依存しないPNG保存。採用原画には適用しない。"""
import binascii
from pathlib import Path
import struct

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',binascii.crc32(kind+data)&0xffffffff)

def save(image,path):
    if image.mode not in ('L','RGB','RGBA'):raise ValueError('未対応のPNG形式: '+image.mode)
    width,height=image.size
    channels={'L':1,'RGB':3,'RGBA':4}[image.mode]
    color_type={'L':0,'RGB':2,'RGBA':6}[image.mode]
    pixels=image.tobytes();stride=width*channels
    raw=b''.join(b'\0'+pixels[y*stride:(y+1)*stride] for y in range(height))
    # zlibの保存ブロックを規格通りに固定長で構成する。各行のfilterは0。
    parts=[b'\x78\x01']
    for start in range(0,len(raw),65535):
        block=raw[start:start+65535];size=len(block)
        parts.extend((bytes([int(start+size==len(raw))]),struct.pack('<HH',size,65535-size),block))
    a,b=1,0
    for start in range(0,len(raw),5552):
        for value in raw[start:start+5552]:a+=value;b+=a
        a%=65521;b%=65521
    parts.append(struct.pack('>I',(b<<16)|a))
    header=struct.pack('>IIBBBBB',width,height,8,color_type,0,0,0)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'IDAT',b''.join(parts))+chunk(b'IEND',b''))

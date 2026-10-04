"""確認用の格子・通行表示だけを固定整数合成と3×5の数字で描く。"""
import numpy as np
from PIL import Image

GLYPHS={
 '0':['111','101','101','101','111'], '1':['010','110','010','010','111'],
 '2':['111','001','111','100','111'], '3':['111','001','111','001','111'],
 '4':['101','101','111','001','001'], '5':['111','100','111','001','111'],
 '6':['111','100','111','101','111'], '7':['111','001','010','010','010'],
 '8':['111','101','111','101','111'], '9':['111','101','111','001','111'],
 ',':['000','000','000','010','100']}

def blend(pixels,color,alpha):
    return ((pixels.astype(np.int32)*(255-alpha)+np.array(color,dtype=np.int32)*alpha+127)//255).astype('uint8')

def label(pixels,x,y,text,color):
    for character in text:
        for dy,row in enumerate(GLYPHS[character]):
            for dx,bit in enumerate(row):
                if bit=='1':pixels[y+dy*2:y+dy*2+2,x+dx]=color
        x+=4

def grid(image,columns,rows,zoom=1):
    assert zoom==1 and image.size==(columns*32,rows*32)
    pixels=np.array(image.convert('RGB'))
    for y in range(rows):
        for x in range(columns):
            tile=pixels[y*32:(y+1)*32,x*32:(x+1)*32]
            edge=np.zeros((32,32),bool);edge[0]=edge[-1]=True;edge[:,0]=edge[:,-1]=True
            tile[edge]=blend(tile[edge],(255,255,0),90)
            label(pixels,x*32+2,y*32+1,f'{x},{y}',(255,255,0))
    return Image.fromarray(pixels)

def overlay(image,layout,marks,zoom=1):
    rows,columns=len(layout),len(layout[0])
    assert zoom==1 and image.size==(columns*32,rows*32)
    pixels=np.array(image.convert('RGB'))
    for y,row in enumerate(layout):
        for x,cell in enumerate(row):
            mark=marks.get((x,y))
            if mark=='npc':color,alpha,border,width=(40,120,255),110,255,2
            elif mark=='door':color,alpha,border,width=(255,220,0),90,255,2
            elif cell=='.':color,alpha,border,width=(40,220,80),70,200,1
            else:color,alpha,border,width=(230,40,40),55,120,1
            tile=pixels[y*32:(y+1)*32,x*32:(x+1)*32]
            edge=np.zeros((32,32),bool);edge[:width]=edge[-width:]=True;edge[:,:width]=edge[:,-width:]=True
            original=tile.copy();tile[:]=blend(original,color,alpha);tile[edge]=blend(original[edge],color,border)
            label(pixels,x*32+2,y*32+1,f'{x},{y}',(255,255,255))
    return Image.fromarray(pixels)

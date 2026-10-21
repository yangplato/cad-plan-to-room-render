from pathlib import Path
from PIL import Image,ImageDraw
import json,math
root=Path('/Users/huaceyang/Documents/1.Projects/宜宾工作/04-AI数字转型和制度研究/AI制图部/04-多平面测试/20261021-v1.4.1跨户型复测')
def hull(ps):
 ps=sorted(set(tuple(p) for p in ps))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 low=[]
 for p in ps:
  while len(low)>=2 and cross(low[-2],low[-1],p)<=0:low.pop()
  low.append(p)
 high=[]
 for p in reversed(ps):
  while len(high)>=2 and cross(high[-2],high[-1],p)<=0:high.pop()
  high.append(p)
 return low[:-1]+high[:-1]
for c in ['P2','D3']:
 p=root/'布局复核'/c;data=json.loads((p/'过程/模型投影.json').read_text());im=Image.open(root/c/'输入/整理平面.png').convert('RGB').resize((data['W'],data['H']))
 ov=Image.new('RGBA',im.size,(0,0,0,0));draw=ImageDraw.Draw(ov,'RGBA')
 for obj in data['objects']:
  col=(0,150,210,180) if obj['mat'] in ['wall','frame'] else (230,90,0,175)
  points=hull(obj['xy'])
  if len(points)>2:draw.polygon(points,fill=col[:3]+(35,),outline=col,width=2)
 for name,cam in data['cameras'].items():
  x,y=cam['xy'];tx,ty=cam['target'];dx,dy=tx-x,ty-y;d=math.hypot(dx,dy);end=(x+80*dx/d,y+80*dy/d)
  draw.line([(x,y),end],fill=(160,0,170,255),width=4);draw.ellipse((x-7,y-7,x+7,y+7),fill=(160,0,170,255));draw.text((x+10,y),name.split('-')[-1],fill=(160,0,170,255))
 ov=Image.alpha_composite(im.convert('RGBA'),ov);ov.save(p/'过程/整理平面与简模叠合.png')
 ims=[]
 for n in ['客厅-M01','客厅-M02','主卧-M01']:
  x=Image.open(p/'空间约束图'/f'{n}.png');x.thumbnail((800,600));ims.append(x)
 panel=Image.new('RGB',(1600,1200),'white')
 panel.paste(ims[0],(0,0));panel.paste(ims[1],(800,0));panel.paste(ims[2],(0,600));panel.save(p/'过程/机位总览.png')

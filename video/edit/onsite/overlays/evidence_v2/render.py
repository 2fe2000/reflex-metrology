"""REFLEX stable 30s full-frame evidence chapter, 1080p24, silent.
Actual query curves copied unchanged from prior evidence/curve_data.json.
Caption-safe bottom 140px remains blank ivory throughout.
"""
from pathlib import Path
from functools import lru_cache
import json, math, subprocess
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'curve_data.json').read_text())
W,H,FPS,DURATION=1920,1080,24,30
BG='#F4F1E9';INK='#142838';BLUE='#225DFF';MUTED='#61717D';LINE='#D2D8D8';AMBER='#B66C2B'
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf';BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
@lru_cache(maxsize=80)
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def txt(d,xy,s,size=32,color=INK,bold=False):d.text(xy,s,font=font(size,bold),fill=color)
def ease(x):
 x=max(0.,min(1.,x));return x*x*(3-2*x)
def reveal(im,t,delay,draw):
 a=ease((t-delay)/.6)
 if a<=0:return
 layer=im.copy();draw(ImageDraw.Draw(layer),round((1-a)*12));im.paste(Image.blend(im,layer,a))
def base(label):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 txt(d,(100,49),'REFLEX',29,INK,True);txt(d,(1360,51),label,25,MUTED)
 d.line((100,109,1820,109),fill=LINE,width=2)
 return im,d
def first(t):
 im,d=base('PROCESS PREDICTION')
 txt(d,(100,172),'Across four delayed settings.',64,INK,True)
 reveal(im,t,.15,lambda d,o:txt(d,(90,320+o),'~1.0%',178,BLUE,True))
 reveal(im,t,.45,lambda d,o:txt(d,(103,534+o),'mean RMSE improvement',60,INK,True))
 reveal(im,t,.85,lambda d,o:txt(d,(105,648+o),'Same measurement budget. Two datasets. Delays of 5 and 20.',36,MUTED))
 txt(ImageDraw.Draw(im),(105,826),'Exploratory reused streams · no independent confirmation',31,MUTED)
 return im
def partial(d,points,p,color):
 n=(len(points)-1)*max(0,min(1,p));c=int(n);pts=points[:c+1]
 if c<len(points)-1:
  a,b=points[c],points[c+1];f=n-c;pts.append((a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f))
 if len(pts)>1:d.line(pts,fill=color,width=5,joint='curve')
 if pts:
  x,y=pts[-1];d.ellipse((x-6,y-6,x+6,y+6),fill=color)
def second(t):
 im,d=base('DEVICE DESIGN / SIMULATION')
 txt(d,(100,164),'Match a target. Learn which design to try next.',56,INK,True)
 ratio=DATA['curves']['random'][-1][1]/DATA['curves']['expected_improvement'][-1][1]
 reveal(im,t,.1,lambda d,o:txt(d,(91,301+o),f'{ratio:.1f}×',142,BLUE,True))
 reveal(im,t,.35,lambda d,o:txt(d,(103,474+o),'lower mean target loss',42,INK,True))
 reveal(im,t,.65,lambda d,o:txt(d,(104,544+o),'97.2% reduction',39,BLUE,True))
 reveal(im,t,.95,lambda d,o:txt(d,(105,630+o),'DEVSIM silicon diode',31,INK,True))
 reveal(im,t,1.1,lambda d,o:txt(d,(105,681+o),'5 seeds · 32 queried designs',30,MUTED))
 x0,x1,y0,y1=950,1755,340,735
 txt(d,(922,269),'Mean best target log-current MSE · log scale',26,INK,True)
 def point(q,loss):return(x0+(q-8)/24*(x1-x0),y1-(math.log10(loss)+4)/4*(y1-y0))
 for exp in [0,-1,-2,-3,-4]:
  y=y1-(exp+4)/4*(y1-y0);d.line((x0,y,x1,y),fill=LINE,width=1)
  txt(d,(864,y-15),['1','0.1','0.01','0.001','1e−4'][-exp],23,MUTED)
 for q in [8,16,24,32]:
  x=x0+(q-8)/24*(x1-x0);txt(d,(x-14,y1+17),str(q),25,MUTED)
 txt(d,(1553,789),'Queried designs',26,MUTED)
 p=ease((t-1)/5)
 for method,color in [('random',AMBER),('expected_improvement',BLUE)]:
  partial(d,[point(q,v) for q,v in DATA['curves'][method]],p,color)
 if t>=6.3:
  reveal(im,t,6.3,lambda d,o:txt(d,(1570,486+o),'1.24 × 10⁻²',25,AMBER,True))
  reveal(im,t,6.3,lambda d,o:txt(d,(1570,639+o),'3.48 × 10⁻⁴',25,BLUE,True))
  d=ImageDraw.Draw(im)
 d.line((1090,842,1130,842),fill=AMBER,width=5);txt(d,(1142,824),'Random',27,AMBER)
 d.line((1360,842,1400,842),fill=BLUE,width=5);txt(d,(1412,824),'GP expected improvement',27,BLUE)
 txt(d,(104,847),'Standard GP · simulation, not measured chip performance',26,MUTED)
 return im
def third(t):
 im,d=base('PROPOSED BUSINESS / R&D')
 txt(d,(100,168),'Turn experiments into a learning loop.',62,INK,True)
 txt(d,(103,291),'PROPOSED BUSINESS MODEL',28,MUTED,True)
 reveal(im,t,.2,lambda d,o:txt(d,(101,352+o),'Paid equipment pilots',57,BLUE,True))
 reveal(im,t,.5,lambda d,o:txt(d,(784,348+o),'→',64,BLUE))
 reveal(im,t,.8,lambda d,o:txt(d,(907,352+o),'On-premise model licenses',57,INK,True))
 txt(d,(103,526),'RESEARCH DIRECTION',28,MUTED,True)
 for i,(s,x) in enumerate([('Propose parameters',103),('Simulate',677),('Measure',1081),('Learn',1510)]):
  reveal(im,t,.9+i*.22,lambda d,o,s=s,x=x:txt(d,(x,598+o),s,43,INK,True))
  if i<3:txt(ImageDraw.Draw(im),([561,961,1385][i],594),'→',49,BLUE)
 reveal(im,t,1.9,lambda d,o:txt(d,(105,758+o),'Seeking a fab or equipment pilot partner.',37,INK,True))
 txt(ImageDraw.Draw(im),(105,842),'Proposed model · advanced-device design and physical validation next',29,MUTED)
 return im
def frame(t):
 if t<8:im=first(t)
 elif t<23:im=second(t-8)
 else:im=third(t-23)
 if 8<=t<8.3:im=Image.blend(first(8),im,ease((t-8)/.3))
 if 23<=t<23.3:im=Image.blend(second(15),im,ease((t-23)/.3))
 return im
def main():
 times=[3,11,20,27]
 sheet=Image.new('RGB',(1920,1080),BG)
 for i,t in enumerate(times):
  im=frame(t);im.save(HERE/f'frame_{t:02d}.png');sheet.paste(im.resize((960,540)),((i%2)*960,(i//2)*540))
 sheet.save(HERE/'contact_sheet.png')
 p=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','16','-threads','3','-pix_fmt','yuv420p','-movflags','+faststart',str(HERE/'evidence_chapter.mp4')],stdin=subprocess.PIPE)
 try:
  for n in range(FPS*DURATION):
   p.stdin.write(frame(n/FPS).tobytes())
   if n%144==0:print(f'{n}/720',flush=True)
 finally:p.stdin.close()
 if p.wait():raise SystemExit('ffmpeg failed')
 print('Done',flush=True)
if __name__=='__main__':main()

"""REFLEX evidence outro. Reproducible PIL vector motion, 24 seconds, no audio."""
from pathlib import Path
import json, math, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
W,H,FPS,DURATION=1920,1080,30,24
BG='#F7F8F5';INK='#17202B';BLUE='#2563EB';MUTED='#5D6978';LINE='#DCDDD8';PALE='#DDE5FC'
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
MONO='/System/Library/Fonts/Menlo.ttc'
from functools import lru_cache
@lru_cache(maxsize=100)
def font(size,bold=False,mono=False):return ImageFont.truetype(MONO if mono else (BOLD if bold else FONT),size,index=0)
def ease(x):x=max(0.,min(1.,x));return 1-(1-x)**3
def txt(d,xy,s,size=40,color=INK,bold=False,mono=False):d.text(xy,s,font=font(size,bold,mono),fill=color)
def base(label,step):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,16,H),fill=BLUE)
 txt(d,(96,52),'REFLEX',30,bold=True)
 txt(d,(1430,55),label,23,MUTED,mono=True)
 d.line((96,112,1824,112),fill=LINE,width=2)
 for i in range(3):d.rectangle((96+i*48,991,128+i*48,996),fill=BLUE if i<=step else LINE)
 txt(d,(1640,978),f'{step+1:02d} / 03',22,MUTED,mono=True)
 return im,d
def scene0(t):
 im,d=base('EVIDENCE / 01',0)
 txt(d,(96,148),'Same measurement budget.',66,bold=True)
 txt(d,(100,243),'88 measurements. 542 samples. Dataset 1.',32,MUTED)
 txt(d,(96,355),'23.4%',174,BLUE,bold=True)
 txt(d,(105,553),'lower RMSE',47,bold=True)
 txt(d,(105,624),'versus uniform measurement timing',29,MUTED)
 x0=970;maxw=720
 for j,(name,v,c,delay) in enumerate([('Uniform timing',.2856041832,INK,.3),('REFLEX burst timing',.2186616159,BLUE,1.0)]):
  y=366+j*200;txt(d,(x0,y),name,32,bold=True)
  width=maxw*(v/.31)*ease((t-delay)/1.4)
  d.rectangle((x0,y+67,x0+maxw,y+112),fill=LINE)
  d.rectangle((x0,y+67,x0+max(1,width),y+112),fill=c)
  txt(d,(x0+maxw+22,y+61),f'{v:.3f}',39,c,bold=True)
 txt(d,(970,782),'LOWER ERROR IS BETTER',22,MUTED,mono=True)
 txt(d,(96,873),'Exploratory comparison after prior holdout inspection.',29,INK)
 txt(d,(96,918),'GRAPE-based model updates · scheduling experiment · not production validation',25,MUTED)
 return im
def scene1(t):
 im,d=base('BOUNDARY / 02',1)
 txt(d,(96,158),'The result has a boundary.',70,bold=True)
 txt(d,(99,274),'Dataset 2',34,MUTED)
 txt(d,(88,335),'1.0%',160,BLUE,bold=True)
 txt(d,(104,537),'lower RMSE',43,bold=True)
 txt(d,(103,610),'Advantage unconfirmed.',40,INK,bold=True)
 # Confidence interval intentionally crosses the zero reference.
 left,right=1070,1770;y=478
 d.line((left,y,right,y),fill=LINE,width=4)
 def xx(v):return left+(v+1)/4*(right-left)
 zero=xx(0);d.line((zero,388,zero,580),fill=MUTED,width=2)
 for val,label in [(-1,'-1%'),(0,'0'),(1,'1%'),(2,'2%'),(3,'3%')]:txt(d,(xx(val)-20,600),label,24,MUTED,mono=True)
 a,b=xx(-.6810944),xx(2.7604053);d.line((a,y,b,y),fill=BLUE,width=8)
 for x in [a,b]:d.line((x,y-18,x,y+18),fill=BLUE,width=5)
 center=xx(.9904088);d.ellipse((center-12,y-12,center+12,y+12),fill=BLUE)
 txt(d,(1070,305),'95% block-bootstrap interval',31,bold=True)
 txt(d,(1070,670),'Interval includes zero.',29,MUTED)
 txt(d,(96,754),'5-sample feedback delay removes the Dataset 1 advantage.',34,INK,bold=True)
 txt(d,(96,823),'Next: delay-aware adaptation + fresh holdout.',34,INK,bold=True)
 txt(d,(96,910),'Both dataset results are exploratory. General superiority is not established.',26,MUTED)
 return im
def scene2(t):
 im,d=base('NEXT / 03',2)
 txt(d,(91,184),'REFLEX',156,bold=True)
 txt(d,(98,386),'Adaptive metrology, locally.',68,BLUE,bold=True)
 txt(d,(103,540),'FIRST CUSTOMER HYPOTHESIS',24,MUTED,mono=True)
 txt(d,(100,590),'CMP process-development teams',43,bold=True)
 txt(d,(104,693),'Seeking a data-validation partner.',40,INK)
 # Sparse dots turn denser near a process-change illustration.
 for i in range(26):
  x=112+i*63;y=837
  active=i in [0,6,11,12,13,14,15,20,25]
  r=7 if active else 4
  d.ellipse((x-r,y-r,x+r,y+r),fill=BLUE if active else '#CAD0D8')
 txt(d,(103,910),'Research prototype · local inference · no autonomous production release',26,MUTED)
 return im
def frame(t):
 if t<9:im=scene0(t)
 elif t<16:im=scene1(t-9)
 else:im=scene2(t-16)
 # Short dissolves keep the information stable for nearly all of each scene.
 if 9<=t<9.35:im=Image.blend(scene0(9),im,ease((t-9)/.35))
 if 16<=t<16.35:im=Image.blend(scene1(7),im,ease((t-16)/.35))
 if t<.4:im=Image.blend(Image.new('RGB',(W,H),BG),im,ease(t/.4))
 return im
def main():
 HERE.mkdir(parents=True,exist_ok=True)
 for t in [3,8,12,15,18,23]:frame(t).save(HERE/f'check_{t:02d}.png')
 cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-pix_fmt','yuv420p','-movflags','+faststart',str(HERE/'evidence.mp4')]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for n in range(FPS*DURATION):
   p.stdin.write(frame(n/FPS).tobytes())
   if n%180==0:print(f'{n}/{FPS*DURATION}',flush=True)
 finally:p.stdin.close()
 if p.wait()!=0:raise SystemExit('ffmpeg failed')
 print('Rendered',HERE/'evidence.mp4',flush=True)
if __name__=='__main__':main()

"""REFLEX v7: illustrative delayed-metrology opening, never equipment footage."""
from pathlib import Path
import math, subprocess
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
W,H,FPS,DURATION=1920,1080,30,18
BG=(241,241,233); INK=(23,36,43); BLUE=(23,89,222); MUTED=(95,107,117); LINE=(209,215,215)
SANS='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
GEORGIA='/System/Library/Fonts/Supplemental/Georgia Bold.ttf'
MONO='/System/Library/Fonts/Menlo.ttc'
def font(sz,kind='sans'):return ImageFont.truetype({'sans':SANS,'bold':BOLD,'serif':GEORGIA,'mono':MONO}[kind],sz)
def ease(x):x=max(0.,min(1.,x));return 1-(1-x)**3
def text(d,xy,value,size=28,color=INK,kind='sans'):d.text(xy,value,font=font(size,kind),fill=color)
def base():
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,12,H),fill=BLUE)
 text(d,(108,65),'REFLEX',30,INK,'bold')
 text(d,(1360,71),'RESEARCH PROTOTYPE',20,MUTED,'mono')
 return im,d
def arrow(d,x0,y,x1,color=LINE,width=3):
 d.line((x0,y,x1-11,y),fill=color,width=width)
 d.polygon([(x1,y),(x1-14,y-7),(x1-14,y+7)],fill=color)
def wafer(d,x,y,r,color=INK,fill=BG):
 d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=color,width=3)
 for a in [-.45,0,.45]:
  half=math.sqrt(1-a*a)*r*.9
  d.line((x+a*r,y-half,x+a*r,y+half),fill=LINE,width=1)
  d.line((x-half,y+a*r,x+half,y+a*r),fill=LINE,width=1)
 d.line((x-6,y+r-1,x+6,y+r-1),fill=fill,width=5)

def scene(s,t):
 im,d=base();off=int((1-ease(t/.85))*18)
 if s==0:
  text(d,(108,181+off),'Metrology is late.',98,INK,'serif')
  text(d,(112,333+off),'The process moves on before the measurement arrives.',37,MUTED)
  text(d,(112,478),'PROCESS SAMPLES',21,MUTED,'mono')
  xs=[186,446,706,966,1226]
  for i,x in enumerate(xs):
   a=ease((t-.4-i*.26)/.75)
   if a<=0:continue
   wafer(d,x,632,49,BLUE if i==0 else INK)
   text(d,(x-18,707),str(i+1),22,MUTED,'mono')
   if i<4:arrow(d,x+68,632,xs[i+1]-68,LINE,3)
  if t>2:
   a=ease((t-2)/1.2);xx=1350+int(a*144)
   arrow(d,1296,632,xx,BLUE,4)
   if a>.85:
    d.rounded_rectangle((1520,578,1775,686),radius=10,fill=BLUE)
    text(d,(1552,610),'MEASUREMENT',23,BG,'mono')
    text(d,(1530,715),'ARRIVES LATER',20,MUTED,'mono')
  text(d,(112,872),'ILLUSTRATION · not equipment footage',21,MUTED,'mono')
 elif s==1:
  text(d,(108,177+off),'A label has a journey.',88,INK,'serif')
  text(d,(112,305+off),'Sample t is observed now. Its label arrives at t + 5.',36,MUTED)
  xs=[190+290*i for i in range(6)];y=550
  text(d,(112,425),'OBSERVATION TIME',20,MUTED,'mono')
  progress=ease(t/3.2)
  d.line((xs[0],y,xs[-1],y),fill=LINE,width=3)
  d.line((xs[0],y,xs[0]+progress*(xs[-1]-xs[0]),y),fill=BLUE,width=5)
  for i,x in enumerate(xs):
   active=progress>=i/5
   d.ellipse((x-12,y-12,x+12,y+12),fill=BLUE if active else BG,outline=BLUE if active else MUTED,width=3)
   label='t' if i==0 else f't + {i}'
   text(d,(x-34 if i else x-8,y+37),label,25,INK,'mono')
   if i<5:
    if t>.65+i*.22:
     d.rounded_rectangle((x-54,691,x+54,756),radius=6,outline=LINE,width=2)
     text(d,(x-25,709),f'{i+1:02d}',24,MUTED,'mono')
   elif active:
    d.rounded_rectangle((x-95,682,x+95,765),radius=6,fill=BLUE)
    text(d,(x-64,707),'LABEL',27,BG,'mono')
  text(d,(112,810),'PENDING LABELS',21,MUTED,'mono')
  text(d,(1410,810),'FEEDBACK AVAILABLE',21,BLUE,'mono')
  text(d,(112,886),'ILLUSTRATION · five-sample delay',21,MUTED,'mono')
 else:
  text(d,(105,169+off),'REFLEX',136,INK,'bold')
  text(d,(111,363+off),'Adapt while measurements',71,INK,'serif')
  text(d,(111,451+off),'are in flight.',71,INK,'serif')
  text(d,(114,602),'Local model · delayed labels · fixed measurement budget',33,MUTED)
  # One sparse abstract queue motif; not a fabricated performance trace.
  xx=116;yy=773
  for i in range(13):
   if t<.8+i*.08:continue
   x=xx+i*126
   if i in [0,5,10]:
    d.rectangle((x,yy-14,x+28,yy+14),fill=BLUE)
   else:d.ellipse((x+6,yy-8,x+22,yy+8),fill=LINE)
  text(d,(114,844),'OBSERVE',20,MUTED,'mono')
  text(d,(744,844),'WAIT FOR FEEDBACK',20,MUTED,'mono')
  text(d,(1374,844),'UPDATE LOCALLY',20,BLUE,'mono')
 return im

def frame(t):
 s=min(2,int(t//6));local=t-s*6;im=scene(s,local)
 if s and local<.4:im=Image.blend(scene(s-1,5.99),im,ease(local/.4))
 return im

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 for t in [2.,5.8,8.,11.8,14.,17.9]:frame(t).save(OUT/f'preview-{t:04.1f}.png')
 command=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'opening.mp4')]
 p=subprocess.Popen(command,stdin=subprocess.PIPE)
 for i in range(FPS*DURATION):p.stdin.write(frame(i/FPS).tobytes())
 p.stdin.close();assert p.wait()==0
 probe=subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,r_frame_rate,pix_fmt','-of','json',str(OUT/'opening.mp4')],text=True)
 (OUT/'verification.json').write_text(probe);print(probe)

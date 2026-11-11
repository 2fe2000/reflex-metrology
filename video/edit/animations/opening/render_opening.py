"""Reproducible, illustrative opening for REFLEX. No measured results depicted."""
from pathlib import Path
import math, subprocess, json
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
W,H,FPS,DURATION=1920,1080,30,18
BG=(247,248,245); INK=(23,32,43); BLUE=(37,99,235); MUTED=(93,105,120); LINE=(215,222,229)
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
MONO='/System/Library/Fonts/Menlo.ttc'
def font(sz,bold=False,mono=False):return ImageFont.truetype(MONO if mono else BOLD if bold else FONT,sz)
def ease(t):
 t=max(0,min(1,t));return 1-(1-t)**3
def text(d,xy,txt,size,color=INK,bold=False,mono=False):d.text(xy,txt,font=font(size,bold,mono),fill=color)
def trace_value(u):
 pre=.33+.028*math.sin(u*57)+.014*math.sin(u*143)
 change=.34/(1+math.exp(-(u-.49)*60))
 return pre+change+.025*math.sin(u*29)
def base(num):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,14,H),fill=BLUE)
 text(d,(106,62),'REFLEX',32,bold=True)
 text(d,(1355,70),'RESEARCH PROTOTYPE',20,MUTED,mono=True)
 text(d,(107,946),'SELECTIVE METROLOGY',19,MUTED,mono=True)
 text(d,(1710,946),f'{num:02d} / 03',19,MUTED,mono=True)
 return im,d

def draw_trace(d,box,progress=1.,sparse=False,shift_label=True):
 x0,y0,x1,y1=box
 for j in range(5):
  y=y0+j*(y1-y0)/4;d.line((x0,y,x1,y),fill=LINE,width=1)
 for j in range(9):
  x=x0+j*(x1-x0)/8;d.line((x,y0,x,y1),fill=LINE,width=1)
 pts=[]
 for i in range(int(600*progress)+1):
  u=i/600;pts.append((x0+u*(x1-x0),y1-trace_value(u)*(y1-y0)))
 if len(pts)>1:d.line(pts,fill=BLUE,width=5,joint='curve')
 if pts:
  x,y=pts[-1];d.ellipse((x-6,y-6,x+6,y+6),fill=BLUE)
 if shift_label and progress>.5:
  xx=x0+.49*(x1-x0)
  for y in range(int(y0),int(y1),14):d.line((xx,y,xx,y+6),fill=(155,170,190),width=2)
  text(d,(xx+18,y0+8),'PROCESS SHIFT',18,MUTED,mono=True)
 if sparse:
  for u in [.08,.32,.49,.525,.56,.74,.92]:
   if u>progress:continue
   xx=x0+u*(x1-x0);yy=y1-trace_value(u)*(y1-y0)
   d.ellipse((xx-11,yy-11,xx+11,yy+11),fill=BG,outline=INK,width=4)

def scene(s,t):
 im,d=base(s+1)
 if s==0:
  off=int(22*(1-ease(t/1.1)))
  text(d,(102,204+off),'REFLEX',184,bold=True)
  text(d,(112,452+off),'Measure when',72,bold=True)
  text(d,(112,535+off),'the process changes.',72,bold=True)
  d.line((1190,281,1750,281),fill=LINE,width=2)
  for j in range(35):
   x=1190+j*16;y=281+math.sin(j*.31)*26
   if j<ease((t-.4)/2.4)*35:d.ellipse((x-3,y-3,x+3,y+3),fill=BLUE)
  text(d,(1190,367),'PREDICT',22,MUTED,mono=True)
  text(d,(1190,413),'MEASURE',22,MUTED,mono=True)
  text(d,(1190,459),'ADAPT',22,MUTED,mono=True)
  text(d,(114,722),'A local learning loop for changing processes.',29,MUTED)
 elif s==1:
  text(d,(109,164),'Same settings.',72,bold=True)
  text(d,(109,247),'A changing process.',72,bold=True)
  text(d,(112,376),'An old prediction can become the wrong prediction.',29,MUTED)
  draw_trace(d,(112,486,1780,811),ease(t/3.7))
  text(d,(113,846),'Illustration — not equipment footage',22,MUTED)
 else:
  text(d,(109,170),'Most wafers need a prediction.',68,bold=True)
  text(d,(109,255),'Some need a measurement.',68,BLUE,bold=True)
  text(d,(112,378),'Request feedback. Update locally. Predict the next sample.',29,MUTED)
  draw_trace(d,(112,487,1780,811),ease(t/2.4),sparse=True,shift_label=False)
  d.ellipse((1340,846,1356,862),outline=INK,width=3)
  text(d,(1372,839),'Selected measurements',22,MUTED)
  text(d,(113,846),'Illustration — not equipment footage',22,MUTED)
 return im

def frame(t):
 s=min(2,int(t//6));local=t-s*6;im=scene(s,local)
 if s and local<.45:im=Image.blend(scene(s-1,5.99),im,ease(local/.45))
 return im

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 for t in [1,5.8,6.5,10,12.6,16,17.9]:frame(t).save(OUT/f'preview-{t:04.1f}.png')
 cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'opening.mp4')]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(FPS*DURATION):p.stdin.write(frame(i/FPS).tobytes())
 p.stdin.close();assert p.wait()==0
 probe=subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,r_frame_rate,pix_fmt','-of','json',str(OUT/'opening.mp4')],text=True)
 (OUT/'verification.json').write_text(probe)
 print(probe)

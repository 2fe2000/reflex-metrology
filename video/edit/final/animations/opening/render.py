"""REFLEX opening: semiconductor process, delayed metrology, timestamped ensemble.
All process drawings are explicitly illustrative; no factory performance is claimed.
"""
from pathlib import Path
import math,subprocess,json
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
W,H,FPS,DURATION=1920,1080,30,38
BG=(244,241,233);NAVY=(20,40,56);BLUE=(34,93,255);AMBER=(182,108,43)
MUTED=(94,111,123);LINE=(207,213,213);PALE=(232,237,242);WHITE=(255,255,251)
FONTS={'sans':'/Users/2fe/Library/Fonts/Pretendard-Regular.otf','bold':'/Users/2fe/Library/Fonts/Pretendard-Bold.otf','serif':'/System/Library/Fonts/Supplemental/Georgia Bold.ttf','mono':'/System/Library/Fonts/Menlo.ttc'}
CACHE={}
def font(sz,kind='sans'):
 key=(sz,kind)
 if key not in CACHE:CACHE[key]=ImageFont.truetype(FONTS[kind],sz)
 return CACHE[key]
def tx(d,xy,value,size=28,color=NAVY,kind='sans'):
 d.text(xy,value,font=font(size,kind),fill=color)
def center(d,x,y,value,size=28,color=NAVY,kind='sans'):
 f=font(size,kind);box=d.textbbox((0,0),value,font=f);d.text((x-(box[2]-box[0])/2,y),value,font=f,fill=color)
def ease(x):x=max(0.,min(1.,x));return 1-(1-x)**3
def sigmoid(x):return 1/(1+math.exp(-x))
def arrow(d,x0,y0,x1,y1,color=LINE,width=3,head=11):
 d.line((x0,y0,x1,y1),fill=color,width=width)
 a=math.atan2(y1-y0,x1-x0)
 pts=[(x1,y1),(x1-head*math.cos(a-.55),y1-head*math.sin(a-.55)),(x1-head*math.cos(a+.55),y1-head*math.sin(a+.55))]
 d.polygon(pts,fill=color)
def wafer(d,x,y,r,color=BLUE,filled=False):
 d.ellipse((x-r,y-r,x+r,y+r),fill=WHITE if not filled else PALE,outline=color,width=3)
 for a in [-.5,-.25,0,.25,.5]:
  half=math.sqrt(1-a*a)*r*.91
  d.line((x+a*r,y-half,x+a*r,y+half),fill=LINE,width=1)
  d.line((x-half,y+a*r,x+half,y+a*r),fill=LINE,width=1)
 d.line((x-6,y+r-1,x+6,y+r-1),fill=BG,width=4)
def base(kicker):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,12,990),fill=BLUE)
 d.rectangle((0,990,W,H),fill=NAVY)
 tx(d,(105,56),'REFLEX',34,NAVY,'bold')
 tx(d,(1040,64),kicker,21,MUTED,'mono')
 return im,d
def footer(d,txt='ILLUSTRATION · simplified process schematic'):
 tx(d,(108,930),txt,20,MUTED,'mono')

def process_symbol(d,stage,x,y,t):
 # Compact cross-sections reveal each operation's different physical role.
 if stage==0:
  d.rectangle((x-74,y+28,x+74,y+46),fill=NAVY)
  for j in range(3):
   yy=y+14-j*12;d.rectangle((x-74,yy,x+74,yy+7),fill=BLUE if j==2 else LINE)
  for i in range(5):
   xx=x-60+i*30;yy=y-44+((t*22+i*11)%38);d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=BLUE)
 elif stage==1:
  d.rectangle((x-74,y+25,x+74,y+44),fill=NAVY)
  d.rectangle((x-74,y+10,x+74,y+20),fill=LINE)
  for j in [-1,0,1]:d.rectangle((x+j*45-12,y-16,x+j*45+12,y+8),fill=BLUE)
  scan=x-75+(t*.35%1)*150;d.line((scan,y-42,scan,y+15),fill=BLUE,width=3)
 elif stage==2:
  d.rectangle((x-74,y+25,x+74,y+44),fill=NAVY)
  for j in [-1,0,1]:d.rectangle((x+j*45-13,y-6,x+j*45+13,y+25),fill=BLUE)
  for j in [-.5,.5]:
   xx=x+j*45;arrow(d,xx,y-40,xx,y+16,AMBER,2,7)
 elif stage==3:
  d.rectangle((x-74,y+23,x+74,y+44),fill=NAVY)
  d.rectangle((x-74,y+8,x+74,y+22),fill=BLUE)
  dx=math.sin(t*3)*18;d.rounded_rectangle((x-80+dx,y-22,x+80+dx,y-6),radius=4,fill=LINE)
  arrow(d,x-34,y-40,x+34,y-40,BLUE,2,8)
 else:
  wafer(d,x,y+5,48,BLUE)
  dx=math.sin(t*1.7)*37;d.line((x+dx,y-44,x+dx,y+50),fill=AMBER,width=3)
  d.line((x-74,y+67,x+74,y+67),fill=LINE,width=2)

def scene0(t):
 im,d=base('PROCESS / A SIMPLIFIED VIEW')
 tx(d,(105,164),'Delay-aware',86,NAVY,'serif')
 tx(d,(105,266),'virtual metrology.',86,NAVY,'serif')
 tx(d,(108,389),'Predict quality from process signals. Learn from measured feedback.',34,MUTED)
 labels=['DEPOSITION','PATTERNING','ETCH','CMP','METROLOGY']
 xs=[240+360*i for i in range(5)]
 cycle=max(0,t-.6)/9.4;position=min(cycle,1)*4
 for i,x in enumerate(xs):
  active=abs(position-i)<.48
  d.rounded_rectangle((x-132,478,x+132,702),radius=10,fill=WHITE,outline=BLUE if active else LINE,width=3 if active else 2)
  center(d,x,498,labels[i],22,BLUE if active else MUTED,'mono')
  process_symbol(d,i,x,602,t)
  if i<4:arrow(d,x+141,592,xs[i+1]-143,592,LINE,3)
 # A moving wafer makes the process flow concrete; a second wafer enters behind it.
 d.line((112,775,1795,775),fill=LINE,width=3)
 px=xs[0]+min(cycle,1)*(xs[-1]-xs[0]);wafer(d,px,775,30,BLUE)
 if t>4:
  px2=xs[0]+max(0,min(1,(t-4)/9.4))*(xs[-1]-xs[0]);wafer(d,px2,775,21,MUTED)
 d.line((1795,775,1795,859,112,859,112,814),fill=LINE,width=2)
 arrow(d,112,845,112,814,LINE,2,8)
 tx(d,(390,820),'Fabrication repeats many process steps.',25,MUTED)
 footer(d)
 return im

def scene1(t):
 im,d=base('PROBLEM / DELAYED FEEDBACK')
 tx(d,(105,164),'Measurements arrive late.',75,NAVY,'serif')
 tx(d,(105,257),'Production keeps moving.',75,NAVY,'serif')
 tx(d,(109,377),'A result describes the earlier sample—not necessarily the current state.',31,MUTED)
 # Continuous production conveyor at the upper level.
 d.line((120,544,1774,544),fill=LINE,width=3)
 for j in range(7):
  x=140+((j*240+t*80)%1620)
  wafer(d,x,544,29,BLUE if j==0 else MUTED)
 tx(d,(120,454),'PROCESS STREAM',20,MUTED,'mono')
 # Lower feedback path with explicit transport delay.
 d.line((256,590,256,788,1670,788,1670,590),fill=AMBER,width=3)
 arrow(d,1670,630,1670,590,AMBER,3,10)
 start=(256,788);progress=ease(max(0,t-1)/7.6);mx=256+progress*(1670-256)
 d.rounded_rectangle((mx-64,753,mx+64,823),radius=6,fill=AMBER)
 center(d,mx,773,'LABEL',22,BG,'mono')
 tx(d,(142,622),'SAMPLE t',22,NAVY,'mono')
 tx(d,(1475,622),'ARRIVAL t+5',22,AMBER,'mono')
 tx(d,(565,833),'FEEDBACK IS STILL IN FLIGHT' if progress<.995 else 'FEEDBACK ARRIVES AFTER FIVE SAMPLES',23,AMBER,'mono')
 # A stylized change marker: explicitly not an identified maintenance event.
 if t>3:
  x=1000;d.line((x,467,x,606),fill=AMBER,width=2)
  tx(d,(x+17,470),'ILLUSTRATIVE SHIFT',19,AMBER,'mono')
  d.line((x-77,648,x-34,648,x-12,638,x+12,660,x+36,650,x+80,650),fill=AMBER,width=3)
 footer(d,'ILLUSTRATION · not a real maintenance event or factory recording')
 return im

def scene2(t):
 im,d=base('MECHANISM / TIMESTAMPED ENSEMBLE')
 tx(d,(105,150),'Adapt when the right',74,NAVY,'serif')
 tx(d,(105,241),'evidence arrives.',74,NAVY,'serif')
 tx(d,(109,354),'Retain the original prediction. Update only after its label arrives.',31,MUTED)
 # Two timestamped state cards above the three experts.
 d.rounded_rectangle((109,434,674,555),radius=8,fill=WHITE,outline=LINE,width=2)
 tx(d,(134,451),'SOURCE t',20,MUTED,'mono')
 tx(d,(134,492),'Store sample + original prediction',27,NAVY,'bold')
 arrow(d,702,494,1185,494,AMBER,3,12)
 tx(d,(755,453),'DELAYED LABEL',20,AMBER,'mono')
 progress=ease((t-.7)/3.4)
 mx=705+progress*475;d.ellipse((mx-7,487,mx+7,501),fill=AMBER)
 arrived=t>=4.1
 d.rounded_rectangle((1220,434,1796,555),radius=8,fill=WHITE,outline=AMBER if arrived else LINE,width=3 if arrived else 2)
 tx(d,(1247,451),'ARRIVAL t + 5',20,AMBER,'mono')
 tx(d,(1247,492),'Compare against stored prediction',27,NAVY,'bold')
 # The experts share the same arrived labels; only their weighting changes.
 names=['GRAPE baseline','Timestamped drift filter','Bounded regime model']
 subs=['Public model','Source-time correction','Up to 32 hypotheses']
 xs=[390,960,1530]
 for i,x in enumerate(xs):
  d.rounded_rectangle((x-258,622,x+258,779),radius=9,fill=WHITE,outline=BLUE if arrived else LINE,width=2)
  center(d,x,644,names[i],29,NAVY,'bold')
  center(d,x,690,subs[i],23,MUTED)
  # Qualitative weight animation has no percentages and no empirical performance claim.
  w0=[.55,.27,.18][i];w1=[.28,.43,.29][i]
  a=ease((t-4.1)/2);w=w0+(w1-w0)*a
  d.rounded_rectangle((x-213,739,x+213,748),radius=4,fill=LINE)
  d.rounded_rectangle((x-213,739,x-213+w*426,748),radius=4,fill=BLUE)
  arrow(d,x,780,x,814,LINE,2,8)
 d.line((390,813,1530,813),fill=LINE,width=2)
 d.rounded_rectangle((625,835,1295,904),radius=7,fill=BLUE if arrived else NAVY)
 center(d,960,854,'WEIGHTS UPDATE AFTER ARRIVAL' if arrived else 'WAIT FOR ARRIVED EVIDENCE',23,BG,'mono')
 footer(d,'GRAPE (2026) + delayed ensemble · illustration; not a foundation-model claim')
 return im

def frame(t):
 if t<12:s=0;local=t
 elif t<24:s=1;local=t-12
 else:s=2;local=t-24
 fn=[scene0,scene1,scene2];im=fn[s](local)
 if s and local<.45:im=Image.blend(fn[s-1](11.99),im,ease(local/.45))
 return im

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 for t in [3.,9.,11.8,15.,20.,23.8,26.,30.,36.8,37.9]:frame(t).save(OUT/f'preview-{t:04.1f}.png')
 cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'opening.mp4')]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(FPS*DURATION):p.stdin.write(frame(i/FPS).tobytes())
 p.stdin.close();assert p.wait()==0
 probe=subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,r_frame_rate,pix_fmt','-of','json',str(OUT/'opening.mp4')],text=True)
 (OUT/'verification.json').write_text(probe);print(probe)

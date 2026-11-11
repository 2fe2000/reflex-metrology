"""REFLEX v7 evidence outro; source numbers read directly from v7 summary."""
from pathlib import Path
from functools import lru_cache
import json,subprocess
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SUMMARY=json.loads((ROOT/'results/v7/summary.json').read_text())
RESULT=next(x for x in SUMMARY['comparisons'] if x['dataset']==1 and x['delay']==5 and x['method']=='delayed_ensemble')
REGRESSION=next(x for x in SUMMARY['comparisons'] if x['dataset']==1 and x['delay']==20 and x['method']=='delayed_ensemble')
W,H,FPS,DURATION=1920,1080,30,24
BG='#f1f1e9';INK='#17242b';BLUE='#1759de';MUTED='#5c6971';LINE='#d4d8d6'
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
MONO='/System/Library/Fonts/Menlo.ttc'
@lru_cache(maxsize=100)
def font(size,bold=False,mono=False):return ImageFont.truetype(MONO if mono else (BOLD if bold else FONT),size,index=0)
def ease(v):v=max(0.,min(1.,v));return 1-(1-v)**3
def txt(d,xy,s,size=40,color=INK,bold=False,mono=False):d.text(xy,s,font=font(size,bold,mono),fill=color)
def reveal(im,t,delay,draw,duration=.55):
 a=ease((t-delay)/duration)
 if a<=0:return
 layer=Image.new('RGB',(W,H),BG);layer.paste(im)
 draw(ImageDraw.Draw(layer),round((1-a)*16))
 im.paste(Image.blend(im,layer,a))
def base(label,step):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,16,H),fill=BLUE)
 txt(d,(96,46),'REFLEX',30,bold=True)
 txt(d,(1420,49),label,23,MUTED,mono=True)
 d.line((96,105,1824,105),fill=LINE,width=2)
 for i in range(3):d.rectangle((96+i*48,947,128+i*48,952),fill=BLUE if i<=step else LINE)
 txt(d,(1650,928),f'{step+1:02d} / 03',22,MUTED,mono=True)
 return im,d
def first(t):
 im,d=base('EVIDENCE / 01',0)
 txt(d,(96,147),'Equal measurement budget. Delayed feedback.',56,bold=True)
 txt(d,(99,240),'Dataset 1 · 5-sample delay · equal 20% measurement budget',31,MUTED)
 txt(d,(100,286),'Mean of 5 measurement offsets',29,MUTED)
 reveal(im,t,.1,lambda d,o:txt(d,(88,366+o),f"{RESULT['p90_improvement_pct']:.2f}%",158,BLUE,True))
 reveal(im,t,.5,lambda d,o:txt(d,(100,555+o),'lower P90 error',52,INK,True))
 reveal(im,t,.8,lambda d,o:txt(d,(101,632+o),'90th percentile of absolute prediction error',27,MUTED))
 x0=1010;maxw=660
 d=ImageDraw.Draw(im)
 for j,(name,value,color,delay) in enumerate([('GRAPE baseline',RESULT['p90_baseline'],INK,1.),('Delay-aware ensemble',RESULT['p90_candidate'],BLUE,1.65)]):
  y=388+j*177
  reveal(im,t,delay,lambda d,o,n=name,y=y:txt(d,(x0,y+o),n,31,INK,True))
  d=ImageDraw.Draw(im);width=maxw*value/.43*ease((t-delay)/1.2)
  d.rectangle((x0,y+66,x0+maxw,y+111),fill=LINE)
  if width>0:d.rectangle((x0,y+66,x0+width,y+111),fill=color)
  reveal(im,t,delay+.3,lambda d,o,y=y,v=value,c=color:txt(d,(x0+maxw+20,y+66+o),f'{v:.3f}',37,c,True))
 reveal(im,t,2.2,lambda d,o:txt(d,(96,805+o),f"Conditional 95% interval: {RESULT['p90_ci95'][0]:.2f}–{RESULT['p90_ci95'][1]:.2f}% / exploratory",32,INK))
 txt(ImageDraw.Draw(im),(96,879),'Previously inspected data; intervals do not correct model-selection bias.',26,MUTED)
 return im
def second(t):
 im,d=base('LIMITS / 02',1)
 txt(d,(96,152),'The primary target was not met.',63,bold=True)
 txt(d,(99,253),'Mean across 4 delayed conditions',31,MUTED)
 reveal(im,t,.1,lambda d,o:txt(d,(87,343+o),f"{SUMMARY['primary_gate']['mean_rmse_improvement_pct']:.2f}%",163,BLUE,True))
 reveal(im,t,.45,lambda d,o:txt(d,(99,551+o),'mean RMSE improvement',47,INK,True))
 reveal(im,t,.8,lambda d,o:txt(d,(1170,348+o),'10%',135,INK,True))
 reveal(im,t,1.15,lambda d,o:txt(d,(1182,522+o),'target not met',42,INK,True))
 reveal(im,t,1.6,lambda d,o:txt(d,(101,707+o),f"Dataset 1, delay 20: {abs(REGRESSION['rmse_improvement_pct']):.2f}% regression.",37,INK,True))
 txt(ImageDraw.Draw(im),(96,878),'Previously inspected data. No independent confirmation.',29,MUTED)
 return im
def third(t):
 im,d=base('NEXT / 03',2)
 txt(d,(90,183),'REFLEX',157,bold=True)
 reveal(im,t,.55,lambda d,o:txt(d,(99,421+o),'Seeking a semiconductor',59,BLUE,True))
 reveal(im,t,.8,lambda d,o:txt(d,(99,498+o),'process-data partner.',59,BLUE,True))
 reveal(im,t,1.8,lambda d,o:txt(d,(102,684+o),'Next: fresh stream, real metrology timestamps,',34,INK))
 reveal(im,t,2.15,lambda d,o:txt(d,(102,734+o),'paid validation.',34,INK))
 txt(ImageDraw.Draw(im),(100,880),'Research prototype · no production validation',28,MUTED)
 return im
def frame(t):
 im=first(t) if t<8 else second(t-8) if t<16 else third(t-16)
 if 8<=t<8.3:im=Image.blend(first(8),im,ease((t-8)/.3))
 if 16<=t<16.3:im=Image.blend(second(8),im,ease((t-16)/.3))
 if t<.3:im=Image.blend(Image.new('RGB',(W,H),BG),im,ease(t/.3))
 return im
def main():
 HERE.mkdir(parents=True,exist_ok=True)
 for t in [3,7,11,15,19,23]:frame(t).save(HERE/f'check_{t:02d}.png')
 p=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-pix_fmt','yuv420p','-movflags','+faststart',str(HERE/'evidence.mp4')],stdin=subprocess.PIPE)
 try:
  for n in range(FPS*DURATION):
   p.stdin.write(frame(n/FPS).tobytes())
   if n%180==0:print(n,flush=True)
 finally:p.stdin.close()
 if p.wait()!=0:raise SystemExit('ffmpeg failed')
 print('Done',flush=True)
if __name__=='__main__':main()

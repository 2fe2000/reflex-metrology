"""Prepare three reviewable English segments; captions are composited last."""
from pathlib import Path
import json,subprocess,textwrap
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
W,H,FPS=1920,1080,24
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def run(c):subprocess.run(c,check=True)
def image_label(path,title,subtitle=''):
 im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
 d.rounded_rectangle((52,44,770,270),24,fill=(8,18,28,222))
 d.text((82,68),title,font=ImageFont.truetype(BOLD,72),fill='white',spacing=2)
 if subtitle:d.text((84,235),subtitle,font=ImageFont.truetype(FONT,18),fill=(181,200,214,255))
 im.save(path)
def captions(name):
 p=R/'transcripts'/f'generated_{name}.words.json'; words=json.loads(p.read_text())['words'];groups=[];current=[]
 for w in words:
  current.append(w)
  if len(current)>=7 or w['text'].endswith(('.', '?', '!')):
   groups.append(current);current=[]
 if current:groups.append(current)
 # Raw ASR is kept verbatim; only project/person proper-noun spelling is corrected in display.
 corrections={'Reflex':'REFLEX','REFLEX.':'REFLEX.'}
 frames=R/'captions'/name;frames.mkdir(parents=True,exist_ok=True)
 base=Image.new('RGBA',(W,140));font=ImageFont.truetype(BOLD,36)
 cues=[]
 for g in groups:
  t=' '.join(w['text'] for w in g)
  t=t.replace('Reflex','REFLEX').replace('Icheol','Ichel').replace('Michel','Ichel').replace('1 waste in 5','one wafer in five').replace('Icho,','Ichel,').replace('Graypy','GRAPE').replace('GRAP;','GRAPE;').replace('runable','runnable')
  cues.append({'start':max(0,g[0]['start']-.03),'end':min(30,g[-1]['end']+.13),'text':t})
 (frames/'cues.json').write_text(json.dumps(cues,indent=2))
 # 24 fps caption strip, no timing assumptions from requested script.
 proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgba','-video_size','1920x140','-framerate','24','-i','-','-c:v','qtrle','-pix_fmt','argb',str(R/'captions'/f'{name}.mov')],stdin=subprocess.PIPE)
 for i in range(720):
  t=i/FPS;im=base.copy();d=ImageDraw.Draw(im)
  cue=next((c for c in cues if c['start']<=t<c['end']),None)
  if cue:
   lines=textwrap.wrap(cue['text'],76); hh=len(lines)*44+24;y=130-hh
   width=max(d.textlength(l,font=font)for l in lines)+48;x=(W-width)/2
   d.rounded_rectangle((x,y,x+width,136),12,fill=(4,11,19,225))
   for j,l in enumerate(lines):d.text(((W-d.textlength(l,font=font))/2,y+10+44*j),l,font=font,fill='white')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
 return R/'captions'/f'{name}.mov'
def assemble():
 (R/'clips').mkdir(exist_ok=True);(R/'captions').mkdir(exist_ok=True)
 image_label(R/'verify'/'hook.png',"THE WAFER\nWON'T WAIT.","REFLEX / SEMICONDUCTOR PROCESS INTELLIGENCE")
 im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im);d.rounded_rectangle((1390,25,1885,67),8,fill=(0,0,0,155));d.text((1402,34),'AI-generated process visualization',font=ImageFont.truetype(FONT,22),fill='white');im.save(R/'verify/label.png')
 font=FONT
 for name in ['opening','demo','evidence']:
  src=R/'sources'/f'generated_{name}.mp4';cap=captions(name)
  inputs=['ffmpeg','-y','-v','error','-i',str(src)]
  if name=='demo':
   inputs+=['-i',str(R/'overlays/demo/demo.mp4'),'-i',str(cap)]
   filters="[1:v]fps=24,format=yuv420p[base];[base][2:v]overlay=0:940:shortest=1[v]"
  elif name=='evidence':
   inputs+=['-i',str(R/'overlays/evidence/evidence_alpha.mov'),'-i',str(cap),'-loop','1','-i',str(R/'verify/label.png')]
   filters=f"[0:v]scale=1920:1080,fps=24[src];[src][3:v]overlay=0:0[base];[base][1:v]overlay=0:0:shortest=1[graphic];[graphic][2:v]overlay=0:940:shortest=1[v]"
  else:
   inputs+=['-loop','1','-i',str(R/'verify/hook.png'),'-i',str(cap),'-loop','1','-i',str(R/'verify/label.png')]
   filters=f"[0:v]scale=1920:1080,fps=24[src];[src][3:v]overlay=0:0[base];[1:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st=3.7:d=0.3:alpha=1[hook];[base][hook]overlay=0:0:enable='lt(t,4)'[graphic];[graphic][2:v]overlay=0:940:shortest=1[v]"
  filters+=';[0:a]aresample=48000,afade=t=in:st=0:d=0.03,afade=t=out:st=29.97:d=0.03,loudnorm=I=-16:TP=-1.5:LRA=11[a]'
  out=R/'clips'/f'{name}.mp4'
  run(inputs+['-filter_complex',filters,'-map','[v]','-map','[a]','-t','30','-r','24','-c:v','libx264','-threads','4','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',str(out)])
 concat=R/'clips/concat.txt';concat.write_text(''.join("file '"+str(R/'clips'/f'{n}.mp4')+"'\n"for n in ['opening','demo','evidence']))
 run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(R/'REFLEX_founder_90s_preview.mp4')])
if __name__=='__main__':assemble()

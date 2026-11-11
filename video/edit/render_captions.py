"""Raster caption strip fallback for FFmpeg builds without libass. Applied LAST."""
import json,textwrap,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;out=ROOT/'captions';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/Users/2fe/Library/Fonts/Pretendard-Regular.otf',30)
cues=json.loads((ROOT/'caption_timing.json').read_text());entries=[];cursor=0.
def make(name,text):
 im=Image.new('RGB',(1920,90),'#17202B');d=ImageDraw.Draw(im);lines=textwrap.wrap(text,100) if text else []
 top=(90-len(lines)*36)//2
 for j,line in enumerate(lines):
  box=d.textbbox((0,0),line,font=font);w=box[2]-box[0];d.text(((1920-w)/2,top+j*36-4),line,fill='white',font=font)
 p=out/f'{name}.png';im.save(p);return p
blank=make('blank','')
for i,c in enumerate(cues):
 if c['start']>cursor:entries.append((blank,c['start']-cursor))
 entries.append((make(f'caption_{i:02}',c['text']),c['end']-c['start']));cursor=c['end']
if cursor<90:entries.append((blank,90-cursor))
lst=out/'concat.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\nduration {d:.9f}\n" for p,d in entries)+f"file '{blank.as_posix()}'\n")
subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(lst),'-t','90','-vf','fps=30','-c:v','libx264','-threads','2','-preset','fast','-crf','16','-pix_fmt','yuv420p',str(ROOT/'caption_strip.mp4')],check=True)
print('Caption strip rendered, 90 seconds')

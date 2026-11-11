"""Assemble prepared clips, apply final captions last, and extract QA frames."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parent;project=r.parents[2];dest=project/'deliverables/REFLEX_final_90s.mp4'
def run(cmd):subprocess.run(cmd,check=True)
clips=[r/'animations/opening/opening.mp4',r/'clips/live.mp4',r/'animations/evidence/evidence.mp4']
(r/'video_concat.txt').write_text(''.join("file '"+str(p)+"'\n" for p in clips))
run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(r/'video_concat.txt'),'-c','copy',str(r/'assembled_silent.mp4')])
run(['ffmpeg','-y','-v','error','-i',str(r/'assembled_silent.mp4'),'-i',str(r/'narration.wav'),'-i',str(r/'caption_strip.mp4'),'-filter_complex','[0:v][2:v]overlay=0:990:shortest=1[v]','-map','[v]','-map','1:a','-t','90','-r','30','-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(dest)])
out=r/'verify';out.mkdir(exist_ok=True)
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]));(out/'ffprobe.json').write_text(json.dumps(meta,indent=2));assert abs(float(meta['format']['duration'])-90)<.05
times=[2,10,11.8,12.2,23.8,24.2,32,37.8,38.2,50,57.8,58.2,65,67.8,68.2,75.8,76.2,84.8,85.2,89]
for i,t in enumerate(times):
    p=out/f'frame_{t:04.1f}.png';run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(dest),'-frames:v','1',str(p)])
# Five rows are required for20 frames.
sheet2=Image.new('RGB',(1280,5*204),'white');d=ImageDraw.Draw(sheet2)
for i,t in enumerate(times):
    im=Image.open(out/f'frame_{t:04.1f}.png');im.thumbnail((320,180));x=(i%4)*320;y=(i//4)*204;sheet2.paste(im,(x,y));d.text((x+5,y+183),f'{t:.1f}s',fill='black')
sheet2.save(out/'contact_sheet.png');print(dest,float(meta['format']['duration']),dest.stat().st_size)

"""Compose from original sources, graphics once, captions last; preserve 90 seconds."""
from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;D=R/'polished';D.mkdir(exist_ok=True)
F='/Users/2fe/Library/Fonts/Pretendard-Regular.otf';B=F.replace('Regular','Bold')
def tx(d,x,y,s,n=36,b=False,c='#152936'):d.text((x,y),s,font=ImageFont.truetype(B if b else F,n),fill=c)
im=Image.new('RGBA',(1920,1080),(244,243,237,255));d=ImageDraw.Draw(im)
tx(d,96,70,'REFLEX   /   PROCESS PREDICTION',25,True);d.line((96,123,1824,123),fill='#C2C8C9',width=2)
tx(d,96,174,'18.8%',152,True);tx(d,100,355,'fewer large prediction errors',66,True)
tx(d,100,500,'15.50%',78);tx(d,700,500,'→',78);tx(d,925,500,'12.58%',78,True,c='#235ED8')
tx(d,100,602,'GRAPE',26);tx(d,925,602,'REFLEX',26,True,c='#235ED8');d.line((96,672,1824,672),fill='#C2C8C9',width=2)
tx(d,100,718,'Dataset 1  /  20% measured  /  five-step delay',31);tx(d,100,774,'Mean over all five sampling offsets · same measurement budget',29)
tx(d,100,856,'Public-data prediction result. Factory yield impact remains untested.',25,c='#526372');im.save(D/'result.png')
def render(name,inputs,vf):
 cmd=['ffmpeg','-y','-v','error','-i',str(R/'sources'/f'generated_{name}.mp4')]+inputs
 af='[0:a]aresample=48000,afade=t=in:st=0:d=0.03,afade=t=out:st=29.97:d=0.03,loudnorm=I=-16:TP=-1.5:LRA=11[a]'
 subprocess.run(cmd+['-filter_complex',vf+';'+af,'-map','[v]','-map','[a]','-t','30','-r','24','-c:v','libx264','-threads','4','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',str(D/f'{name}.mp4')],check=True)
render('opening',['-loop','1','-i',str(R/'verify/hook.png'),'-loop','1','-i',str(R/'verify/label.png'),'-i',str(R/'overlays/pain_v2/pain.mov'),'-i',str(R/'captions/opening.mov')],"[0:v]setpts=PTS-STARTPTS,fps=24[src];[src][2:v]overlay=0:0[base];[1:v]format=rgba,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st=3.7:d=0.3:alpha=1[hook];[base][hook]overlay=0:0:enable='lt(t,4)'[h];[3:v]setpts=PTS-STARTPTS+25/TB[pain];[h][pain]overlay=0:0:eof_action=repeat:enable='gte(t,25)'[g];[g][4:v]overlay=0:940:shortest=1[v]")
render('demo',['-i',str(R/'overlays/demo/replay24.mp4'),'-loop','1','-i',str(D/'result.png'),'-i',str(R/'captions/demo.mov')],"[1:v]fps=24,tpad=stop_mode=clone:stop_duration=6[base];[2:v]format=rgba,fade=t=in:st=24:d=0.3:alpha=1[result];[base][result]overlay=0:0:enable='gte(t,24)'[g];[g][3:v]overlay=0:940:shortest=1[v]")
render('evidence',['-i',str(R/'overlays/evidence_v2/evidence_chapter.mp4'),'-i',str(R/'captions/evidence.mov')],"[1:v]setpts=PTS-STARTPTS,fps=24[base];[base][2:v]overlay=0:940:shortest=1[v]")
c=D/'concat.txt';c.write_text(''.join("file '"+str(D/f'{n}.mp4')+"'\n"for n in ['opening','demo','evidence']))
tmp=D/'joined.mp4';subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(c),'-c','copy',str(tmp)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(tmp)]));offset=next(s['start_time']for s in probe['streams']if s['codec_type']=='video')
out=R.parents[2]/'deliverables/REFLEX_90s_RESEARCH.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-itsoffset',str(-float(offset)),'-i',str(tmp),'-i',str(tmp),'-map','0:v','-map','1:a','-c:v','copy','-af','atrim=duration=90','-c:a','aac','-b:a','192k','-t','90','-movflags','+faststart',str(out)],check=True)
print(out)

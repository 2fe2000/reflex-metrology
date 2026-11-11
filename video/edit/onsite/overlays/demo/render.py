#!/usr/bin/env python3
"""30s actual replay + aggregate-result overlay. No UI is generated.
First 24s: original frame pixels, crop only below y920 to remove partial
comparison section. Last 6s: exact final source frame under a result overlay.
"""
from pathlib import Path
import subprocess, json, shutil
from PIL import Image, ImageDraw, ImageFont
D=Path(__file__).resolve().parent
SRC=D.parents[2]/'v7/clips/live.mp4'
FF=shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
FP=shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
W,H,FPS=1920,1080,24
NAVY=(14,25,34); WHITE=(244,246,247); MUTED=(169,184,196); BLUE=(111,158,255)
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
def font(n,b=False): return ImageFont.truetype(BOLD if b else FONT,n)
def run(args): subprocess.run(args,check=True)
def ease(x): return 1-(1-max(0,min(1,x)))**3
enc=['-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-pix_fmt','yuv420p','-r',str(FPS),'-video_track_timescale','12288','-movflags','+faststart']
run([FF,'-hide_banner','-loglevel','error','-i',str(SRC),'-t','24','-vf','fps=24,crop=1920:920:0:0,pad=1920:1080:0:0:color=0x0e1922',*enc,'-y',str(D/'replay24.mp4')])
run([FF,'-hide_banner','-loglevel','error','-ss','23.966666','-i',str(SRC),'-frames:v','1','-y',str(D/'final-source-frame.png')])
base=Image.new('RGB',(W,H),NAVY); base.paste(Image.open(D/'final-source-frame.png').convert('RGB').crop((0,0,W,920)),(0,0))
def frame(t):
    im=base.convert('RGBA')
    # Ease the exact source frame into a legible dark result surface.
    shade=Image.new('RGBA',(W,H),(14,25,34,int(238*ease(t/.65))))
    shade.paste((14,25,34,255),(0,940,W,H)); im=Image.alpha_composite(im,shade)
    def tx(x,y,s,n,b=False,color=WHITE,start=0.4):
        a=ease((t-start)/.5)
        if not a:return
        lay=Image.new('RGBA',(W,H)); draw=ImageDraw.Draw(lay)
        draw.text((x,y+int(12*(1-a))),s,font=font(n,b),fill=(*color,int(255*a)))
        nonlocal im
        im=Image.alpha_composite(im,lay)
    tx(140,104,'AGGREGATE RESULT  /  FIVE SAMPLING OFFSETS',29,True,MUTED,.15)
    tx(135,184,'18.8% fewer',108,True,WHITE,.35)
    tx(140,313,'large prediction errors',83,True,WHITE,.65)
    tx(143,452,'Dataset 1 • 20% measured • delay 5 • mean over all 5 offsets',33,False,MUTED,1.05)
    tx(140,571,'15.50% → 12.58%',80,True,BLUE,1.45)
    tx(143,673,'large-error frequency',36,False,WHITE,1.65)
    tx(143,812,'Prediction metric, not factory yield',35,True,WHITE,2.05)
    return im.convert('RGB')
p=subprocess.Popen([FF,'-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','24','-i','-',*enc,'-y',str(D/'result6.mp4')],stdin=subprocess.PIPE)
for n in range(6*FPS):
    im=frame(n/FPS)
    if n in (0,24,72,143):im.save(D/f'overlay-preview-{n:03d}.png')
    p.stdin.write(im.tobytes())
p.stdin.close()
if p.wait()!=0: raise RuntimeError('overlay encode failed')
(D/'concat.txt').write_text("file 'replay24.mp4'\nfile 'result6.mp4'\n")
run([FF,'-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(D/'concat.txt'),'-c','copy','-movflags','+faststart','-y',str(D/'demo.mp4')])
probe=json.loads(subprocess.check_output([FP,'-v','error','-count_frames','-show_entries','stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames:format=duration','-of','json',str(D/'demo.mp4')]))
assert probe['format']['duration']=='30.000000',probe
assert probe['streams'][0]['nb_read_frames']=='720',probe
(D/'verification.json').write_text(json.dumps(probe,indent=2)+'\n')
for sec in (0,12,23.9,24.1,25,28,29.9):
    run([FF,'-hide_banner','-loglevel','error','-ss',str(sec),'-i',str(D/'demo.mp4'),'-frames:v','1','-y',str(D/f'encoded-{sec:04.1f}.png')])
print(json.dumps(probe,indent=2))

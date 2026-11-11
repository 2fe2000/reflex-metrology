#!/usr/bin/env python3
"""Five-second editorial alpha overlay. Source: SIA, 2026-02-06.
https://www.semiconductors.org/global-annual-semiconductor-sales-increase-25-6-to-791-7-billion-in-2025/
Compose at 25s; subtitles must be applied after this overlay.
"""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import subprocess,json,shutil
D=Path(__file__).resolve().parent
FF=shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
FP=shutil.which('ffprobe') or '/opt/homebrew/bin/ffprobe'
W,H,FPS,N=1920,1080,24,120
REG='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
SERIF='/System/Library/Fonts/Supplemental/Georgia.ttf'
def ft(path,size):return ImageFont.truetype(path,size)
base=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(base)
d.rectangle((72,230,1222,724),fill=(244,241,233,247))
ink=(20,40,56,255);muted=(74,89,98,255)
d.text((118,275),'Metrology lags. Production continues.',font=ft(REG,43),fill=ink)
d.text((112,352),'$791.7B',font=ft(SERIF,142),fill=ink)
d.text((120,542),'2025 global semiconductor sales',font=ft(REG,38),fill=ink)
d.text((120,653),'Industry context, not REFLEX TAM · SIA, Feb 2026',font=ft(REG,25),fill=muted)
base.save(D/'overlay.png')
p=subprocess.Popen([FF,'-hide_banner','-loglevel','error','-f','rawvideo','-pixel_format','rgba','-video_size','1920x1080','-framerate','24','-i','-','-an','-c:v','qtrle','-pix_fmt','argb','-threads','2','-y',str(D/'pain.mov')],stdin=subprocess.PIPE)
for i in range(N):
    t=i/FPS; q=min(1,t/.25); opacity=1-(1-q)**3
    fr=base.copy();fr.putalpha(base.getchannel('A').point(lambda a:round(a*opacity)))
    p.stdin.write(fr.tobytes())
p.stdin.close();assert p.wait()==0
probe=json.loads(subprocess.check_output([FP,'-v','error','-count_frames','-show_entries','stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames:format=duration','-of','json',str(D/'pain.mov')]))
assert probe['format']['duration']=='5.000000' and probe['streams'][0]['nb_read_frames']=='120'
(D/'verification.json').write_text(json.dumps(probe,indent=2)+'\n')
for time in ('0.125','2','4.958'):
 subprocess.run([FF,'-hide_banner','-loglevel','error','-ss',time,'-i',str(D/'pain.mov'),'-frames:v','1','-y',str(D/f'encoded-{time}.png')],check=True)
qa=Image.new('RGBA',(W,H),(28,41,49,255));qa.alpha_composite(Image.open(D/'encoded-2.png').convert('RGBA'));qa.convert('RGB').save(D/'qa.png')
print(json.dumps(probe))

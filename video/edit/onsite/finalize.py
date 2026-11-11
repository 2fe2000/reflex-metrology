from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json,math
r=Path(__file__).resolve().parents[3];o=r/'video/edit/onsite/verify';F='/Users/2fe/Library/Fonts/Pretendard-Regular.otf';B=F.replace('Regular','Bold')
def text(d,x,y,s,n=40,b=False,c='white'):d.text((x,y),s,font=ImageFont.truetype(B if b else F,n),fill=c)
def canvas():return Image.new('RGBA',(1920,1080))
im=canvas();d=ImageDraw.Draw(im);d.rounded_rectangle((60,110,1200,920),30,fill=(6,16,28,244));text(d,105,150,'THE COST OF LATE FEEDBACK',30,True,'#73B7FF');text(d,100,215,'METROLOGY LAGS.',76,True);text(d,100,310,'THE PROCESS KEEPS RUNNING.',56,True);text(d,105,410,'Undetected drift can put more wafers at risk.',34);text(d,100,495,'$791.7B',116,True,'#73B7FF');text(d,105,635,'2025 global semiconductor sales',43,True);text(d,105,717,'Predict now. Learn when the measurement arrives.',35);text(d,105,812,'Industry scale — not REFLEX addressable revenue.',27,c='#BBC9DB');text(d,105,859,'Source: SIA, February 6, 2026 · semiconductors.org',25,c='#BBC9DB');im.save(o/'punch_pain.png')
im=canvas();d=ImageDraw.Draw(im);d.rectangle((0,58,1920,920),fill=(9,21,33,250));text(d,135,102,'SAME MEASUREMENT BUDGET. FEWER BIG MISSES.',35,True,'#73B7FF');text(d,125,175,'18.8%',180,True);text(d,140,385,'FEWER LARGE PREDICTION ERRORS',66,True);text(d,140,510,'15.50% → 12.58%',88,True,'#73B7FF');text(d,140,625,'Large-error frequency vs GRAPE',38);text(d,140,720,'Dataset 1 · 20% measured · delay 5 · all five offsets',33,c='#BBC9DB');text(d,140,815,'Measured prediction result; factory yield impact not yet tested.',30,c='#BBC9DB');im.save(o/'punch_error.png')
im=canvas();d=ImageDraw.Draw(im);d.rectangle((70,111,1090,920),fill=(245,245,240,255));ink='#102131';muted='#526372';blue='#235ED8';orange='#B16A25'
text(d,110,145,'DEVICE DESIGN / SIMULATION',25,True,muted);text(d,103,190,'35.6× LOWER LOSS',67,True,ink);text(d,110,273,'97.2% lower target mismatch vs random',29,False,ink);text(d,110,323,'5 paired seeds · 32 queried designs · silicon diode',26,False,muted)
data=json.loads((r/'video/edit/onsite/overlays/evidence/curve_data.json').read_text());x0,x1,y0,y1=190,1005,440,746
for exponent in [0,-1,-2,-3,-4]:
 y=y1-(exponent+4)/4*(y1-y0);d.line((x0,y,x1,y),fill='#D6DAD9',width=1);text(d,110,y-13,['1','0.1','0.01','0.001','0.0001'][-exponent],20,False,muted)
for q in [8,16,24,32]:text(d,x0+(q-8)/24*(x1-x0)-12,y1+14,str(q),22,False,muted)
for method,color in [('random',orange),('expected_improvement',blue)]:
 pts=[(x0+(q-8)/24*(x1-x0),y1-(math.log10(v)+4)/4*(y1-y0))for q,v in data['curves'][method]];d.line(pts,fill=color,width=5);x,y=pts[-1];d.ellipse((x-6,y-6,x+6,y+6),fill=color)
text(d,110,379,'Mean target log-current MSE',25,True,ink);text(d,545,379,'Random',23,False,orange);text(d,735,379,'GP active search',23,False,blue);text(d,782,791,'Queried designs',23,False,muted);text(d,110,841,'Simulation — not measured chip performance',28,True,ink);text(d,110,882,'Standard GP optimization; mean loss at 32 queries',23,False,muted);im.save(o/'punch_search.png')
im=canvas();d=ImageDraw.Draw(im);d.rectangle((70,650,1550,920),fill=(245,245,240,255));text(d,110,676,'BUSINESS MODEL / PROPOSED',24,True,muted);text(d,110,722,'Paid equipment pilots → On-premise model licenses',41,True,ink);text(d,110,786,'R&D: propose process or device parameters → simulate → measure → learn',29,False,ink);text(d,110,849,'Start with delayed metrology. Expand into experiment and design optimization.',27,False,muted);im.save(o/'punch_business.png')
cmd=['ffmpeg','-y','-v','error','-i',str(r/'deliverables/REFLEX_90s_submission.mp4')]
for n in ['pain','error','search','business']:cmd+=['-loop','1','-i',str(o/f'punch_{n}.png')]
f="[0:v][1:v]overlay=0:0:enable='between(t,25.2,29.95)'[a];[a][2:v]overlay=0:0:enable='between(t,54.6,59.95)'[b];[b][3:v]overlay=0:0:enable='between(t,68.6,82.3)'[c];[c][4:v]overlay=0:0:enable='between(t,84.1,89.95)',setpts=PTS-STARTPTS[v]"
cmd+=['-filter_complex',f,'-map','[v]','-map','0:a','-t','90','-c:v','libx264','-threads','4','-preset','fast','-crf','18','-c:a','copy','-movflags','+faststart',str(r/'deliverables/REFLEX_90s_FINAL.mp4')]
subprocess.run(cmd,check=True)
for t in [27,57,77,87]:subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(r/'deliverables/REFLEX_90s_FINAL.mp4'),'-frames:v','1',str(o/f'punch_{t}.jpg')],check=True)
print('DONE')

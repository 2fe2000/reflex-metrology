"""REFLEX on-site evidence overlays, transparent 1080p24, 30 seconds.

Pillow + ffmpeg. Writes alpha qtrle MOV, representative RGBA PNGs, contact sheet.
Curve data frozen from results/inverse/summary.json in curve_data.json.
No synthetic performance data. Footage and captions are composed by main editor.
"""
from pathlib import Path
from functools import lru_cache
import json, math, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'curve_data.json').read_text())
W,H,FPS,SECONDS=1920,1080,24,30
WHITE=(246,249,255,255);MUTED=(187,201,219,255)
BLUE=(102,177,255,255);AMBER=(238,184,119,255)
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
@lru_cache(maxsize=80)
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def txt(d,xy,s,size=32,color=WHITE,bold=False):d.text(xy,s,font=font(size,bold),fill=color)
def ease(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)
def panel(d,box):
    d.rounded_rectangle(box,radius=22,fill=(10,21,35,224),outline=(145,172,202,70),width=1)
def fade(im,a):
    if a<1:im.putalpha(im.getchannel('A').point(lambda v:round(v*a)))
    return im
def draw_partial(d,points,p,color,width=4):
    n=(len(points)-1)*max(0,min(1,p));count=int(n)
    pts=points[:count+1]
    if count<len(points)-1:
        a,b=points[count],points[count+1];f=n-count
        pts.append((a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f))
    if len(pts)>1:d.line(pts,fill=color,width=width,joint='curve')
    if pts:
        x,y=pts[-1];d.ellipse((x-5,y-5,x+5,y+5),fill=color)
def opening(t):
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    panel(d,(70,666,1015,915))
    d.rectangle((98,700,103,860),fill=BLUE)
    txt(d,(127,698),'ACROSS 4 DELAYED SETTINGS',26,MUTED,True)
    txt(d,(125,745),'~1.0% mean RMSE improvement',45,WHITE,True)
    txt(d,(128,820),'Same measurement budget · exploratory reused streams',27,MUTED)
    return fade(im,ease(t/.6)*ease((7-t)/.6))
def evidence(t):
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    panel(d,(70,111,1090,920))
    txt(d,(108,147),'DEVICE DESIGN / SIMULATION',23,BLUE,True)
    txt(d,(105,196),'97.2% lower target mismatch',53,WHITE,True)
    txt(d,(109,271),'DEVSIM silicon diode · GP search vs random',29,MUTED)
    txt(d,(109,315),'5 seeds, 32 queries',29,MUTED)
    txt(d,(110,369),'Mean best target log-current MSE',26,WHITE,True)
    # Log scale makes all observed values visible; arithmetic mean across seeds.
    x0,x1,y0,y1=182,1006,434,752
    def point(q,loss):return (x0+(q-8)/24*(x1-x0),y1-(math.log10(loss)+4)/4*(y1-y0))
    for exponent in [0,-1,-2,-3,-4]:
        y=y1-(exponent+4)/4*(y1-y0)
        d.line((x0,y,x1,y),fill=(183,204,226,36),width=1)
        txt(d,(112,y-14),['1','0.1','0.01','0.001','1e−4'][-exponent],21,MUTED)
    for q in [8,16,24,32]:
        x=x0+(q-8)/24*(x1-x0);txt(d,(x-12,y1+12),str(q),22,MUTED)
    txt(d,(789,791),'Queried designs',23,MUTED)
    # Reveal observed query trajectory continuously without inventing intermediate samples.
    p=ease((t-1.3)/5)
    for method,color in [('random',AMBER),('expected_improvement',BLUE)]:
        points=[point(q,v) for q,v in DATA['curves'][method]]
        draw_partial(d,points,p,color,4)
    d.line((385,329,416,329),fill=AMBER,width=4);txt(d,(425,313),'Random',26,AMBER)
    d.line((606,329,637,329),fill=BLUE,width=4);txt(d,(646,313),'GP expected improvement',26,BLUE)
    txt(d,(111,841),'Simulation; not measured chip performance',29,WHITE,True)
    txt(d,(111,882),'Standard GP optimization · mean loss reduction at 32 queries',23,MUTED)
    return fade(im,ease(t/.6)*ease((15-t)/.6))
def vision(t):
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    panel(d,(70,682,1090,910))
    txt(d,(110,714),'RESEARCH DIRECTION',25,BLUE,True)
    for i,(text,x) in enumerate([('Predict',110),('Experiment',370),('Improve',762)]):
        a=ease((t-.15-i*.28)/.55)
        color=tuple(round(v*a) if k==3 else v for k,v in enumerate(WHITE))
        txt(d,(x,770+round(12*(1-a))),text,47,color,True)
        if i<2:txt(d,([294,686][i],768),'→',49,BLUE)
    return fade(im,ease(t/.6))
def frame(t):
    if 0<=t<7:return opening(t)
    if 8<=t<23:return evidence(t-8)
    if 24<=t<30:return vision(t-24)
    return Image.new('RGBA',(W,H))
def sheet(frames):
    out=Image.new('RGB',(1920,1120),(29,35,43));d=ImageDraw.Draw(out)
    for i,(time,im) in enumerate(frames):
        # Checkerboard indicates transparency; it is not baked into MOV or frame PNGs.
        bg=Image.new('RGBA',(W,H));bd=ImageDraw.Draw(bg)
        for y in range(0,H,60):
            for x in range(0,W,60):bd.rectangle((x,y,x+60,y+60),fill=(50,58,68,255) if (x//60+y//60)%2 else (64,73,84,255))
        bg.alpha_composite(im)
        out.paste(bg.convert('RGB').resize((960,540)),((i%2)*960,(i//2)*560))
        txt(d,((i%2)*960+14,(i//2)*560+515),f'{time}s · checkerboard = transparent',20,WHITE)
    return out
def main():
    frames=[(t,frame(t)) for t in [3,11,20,27]]
    for t,im in frames:im.save(HERE/f'frame_{t:02d}.png')
    sheet(frames).save(HERE/'contact_sheet.png')
    cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s','1920x1080','-r',str(FPS),'-i','-','-an','-c:v','qtrle','-pix_fmt','argb','-threads','3',str(HERE/'evidence_alpha.mov')]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(FPS*SECONDS):
            p.stdin.write(frame(n/FPS).tobytes())
            if n%120==0:print(f'{n}/720',flush=True)
    finally:p.stdin.close()
    if p.wait():raise SystemExit('ffmpeg failed')
    print('Done',flush=True)
if __name__=='__main__':main()

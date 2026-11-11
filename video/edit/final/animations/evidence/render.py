"""REFLEX final evidence / industrial vision, 32 seconds, silent.

Frozen values from results/customer/{summary.json,means.csv}, 2026-11-11.
Self-contained generator: Python 3 + Pillow + ffmpeg, local Pretendard fonts.
All industrial savings and cross-chamber capabilities are explicitly future targets.
"""
from pathlib import Path
from functools import lru_cache
import subprocess, math
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W,H,FPS,DURATION = 1920,1080,30,32
BG='#F4F1E9'; INK='#142838'; BLUE='#225DFF'; AMBER='#B66C2B'
MUTED='#5F6D76'; LINE='#D7DAD7'; PALE='#E4E9F0'
FONT='/Users/2fe/Library/Fonts/Pretendard-Regular.otf'
BOLD='/Users/2fe/Library/Fonts/Pretendard-Bold.otf'
MONO='/System/Library/Fonts/Menlo.ttc'
INVERSE={'target_curve': [[0.0, 2.855438426870067e-11], [0.05, 7.574400583881392e-08], [0.1, 2.6773042852799263e-07], [0.15000000000000002, 7.910506222301097e-07], [0.2, 2.2746449859078866e-06], [0.25, 6.717122771907452e-06], [0.30000000000000004, 2.145735031199349e-05], [0.35000000000000003, 7.919984092070147e-05], [0.4, 0.0003548859765537556], [0.45, 0.0019075609979109435], [0.5, 0.011583307850922528]], 'best_curve': [[0.0, 4.0832034092605507e-10], [0.05, 7.654519584497637e-08], [0.1, 2.685920667714007e-07], [0.15000000000000002, 7.972869872990555e-07], [0.2, 2.296386681434347e-06], [0.25, 6.8077816923118194e-06], [0.30000000000000004, 2.1910243651492657e-05], [0.35000000000000003, 8.181009435925268e-05], [0.4, 0.00037119423450167663], [0.45, 0.002013451365405065], [0.5, 0.012282217386932772]], 'length_um': 0.42552670836449935, 'reduction_pct': 97.19264841687364, 'wins': 5, 'mean_loss_random': 0.012410366859003747, 'mean_loss_ei': 0.00034840263048803113}
ROWS=[(1,5,12.051285563214975,3.534332066228252),
      (1,20,7.60809267489223,-0.12350820994371237),
      (2,5,0.5497323760608852,0.5248528957920939),
      (2,20,0.06941062507561657,0.20325034333246172)]
@lru_cache(maxsize=100)
def font(size,bold=False,mono=False):
    return ImageFont.truetype(MONO if mono else BOLD if bold else FONT,size,index=0)
def ease(v):
    v=max(0.,min(1.,v)); return 1-(1-v)**3
def txt(d,xy,s,size=40,color=INK,bold=False,mono=False):
    d.text(xy,s,font=font(size,bold,mono),fill=color)
def reveal(im,t,delay,draw,duration=.6):
    a=ease((t-delay)/duration)
    if a<=0:return
    layer=im.copy();draw(ImageDraw.Draw(layer),round((1-a)*18))
    im.paste(Image.blend(im,layer,a))
def base(label,step):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,16,989),fill=BLUE)
    d.rectangle((0,990,W,H),fill=INK)
    txt(d,(96,44),'REFLEX',30,bold=True)
    txt(d,(1375,48),label,23,MUTED,mono=True)
    d.line((96,104,1824,104),fill=LINE,width=2)
    for i in range(4):d.rectangle((96+i*48,942,128+i*48,947),fill=BLUE if i<=step else LINE)
    return im,d
def first(t):
    im,d=base('EVIDENCE / 01',0)
    txt(d,(96,147),'Fewer large prediction errors.',64,bold=True)
    txt(d,(99,242),'Dataset 1 · 5-sample delay · same 20% measurement requests',32,MUTED)
    reveal(im,t,.1,lambda d,o:txt(d,(84,324+o),'18.8%',168,BLUE,True))
    reveal(im,t,.45,lambda d,o:txt(d,(98,518+o),'relative reduction',47,INK,True))
    reveal(im,t,.8,lambda d,o:txt(d,(100,589+o),'−2.92 percentage points',34,MUTED))
    x0=950; maxw=640
    for j,(name,value,color,delay) in enumerate([
        ('GRAPE baseline',15.498154981549817,INK,.65),
        ('REFLEX',12.583025830258301,BLUE,1.25)]):
        y=337+j*175
        reveal(im,t,delay,lambda d,o,n=name,y=y:txt(d,(x0,y+o),n,31,INK,True))
        d=ImageDraw.Draw(im);bw=maxw*value/16*ease((t-delay)/1.3)
        d.rectangle((x0,y+63,x0+maxw,y+113),fill=LINE)
        if bw>0:d.rectangle((x0,y+63,x0+bw,y+113),fill=color)
        reveal(im,t,delay+.35,lambda d,o,v=value,y=y,c=color:txt(d,(1625,y+61+o),f'{v:.2f}%',43,c,True))
    reveal(im,t,1.9,lambda d,o:txt(d,(98,737+o),'Large error = prediction error above a development-data threshold.',31,INK))
    reveal(im,t,2.2,lambda d,o:txt(d,(98,790+o),'Conditional 95% interval: 5.42–30.88% relative reduction.',31,INK))
    txt(ImageDraw.Draw(im),(98,858),'Exploratory reused streams · CI ignores model-selection bias · not a defect-rate result',27,MUTED)
    return im
def comparison(t):
    im,d=base('COMPARISON / 02',1)
    txt(d,(96,149),'Full comparison.',65,bold=True)
    txt(d,(96,228),'Same measurement budget.',65,BLUE,True)
    txt(d,(100,334),'All 4 delayed conditions · mean of 5 measurement offsets',30,MUTED)
    txt(d,(122,410),'DATASET / DELAY',25,MUTED,mono=True)
    txt(d,(790,407),'P90 error reduction',31,INK,True)
    txt(d,(1390,407),'RMSE improvement',31,INK,True)
    for i,(dataset,delay,p90,rmse) in enumerate(ROWS):
        y=472+i*76
        def row(d,o,y=y,dataset=dataset,delay=delay,p90=p90,rmse=rmse,i=i):
            d.line((102,y-10+o,1817,y-10+o),fill=LINE,width=1)
            txt(d,(124,y+o),f'Dataset {dataset} / delay {delay}',32,INK,True)
            txt(d,(790,y+o),f'{p90:.2f}%',35,BLUE,True)
            txt(d,(1390,y+o),f'{rmse:.2f}%',35,AMBER if rmse<0 else INK,True)
            width=310*p90/13*ease((t-.7-i*.3)/1.)
            if width>0:d.rectangle((1005,y+15+o,1005+width,y+29+o),fill=BLUE)
        reveal(im,t,.4+i*.3,row)
    reveal(im,t,1.75,lambda d,o:txt(d,(99,808+o),'Mean RMSE improvement 1.03%; half-measurement target not met.',34,INK,True))
    txt(ImageDraw.Draw(im),(99,871),'Previously inspected data. No independent confirmation. Negative = regression.',27,MUTED)
    return im
def business(t):
    im,d=base('DEVICE R&D / 03',2)
    txt(d,(96,146),'From prediction to device design.',61,bold=True)
    txt(d,(99,239),'1D diode simulation · vs random search · 32 queries · 5 seeds',33,MUTED)
    reveal(im,t,.15,lambda d,o:txt(d,(86,321+o),f"{INVERSE['reduction_pct']:.1f}%",132,BLUE,True))
    reveal(im,t,.45,lambda d,o:txt(d,(99,477+o),'lower target mismatch',43,INK,True))
    reveal(im,t,.75,lambda d,o:txt(d,(100,550+o),'5 / 5 search wins · DEVSIM physics',29,MUTED))
    def structure(d,o):
        txt(d,(100,619+o),'BOUNDED CANDIDATE STRUCTURE',23,MUTED,mono=True)
        d.rectangle((102,671+o,360,735+o),fill=BLUE)
        d.rectangle((360,671+o,618,735+o),fill=INK)
        txt(d,(218,681+o),'P',36,BG,True);txt(d,(473,681+o),'N',36,BG,True)
        txt(d,(102,755+o),f"Length {INVERSE['length_um']:.3f} µm",29,INK,True)
    reveal(im,t,1.1,structure)
    d=ImageDraw.Draw(im)
    x0,x1,y0,y1=1050,1760,407,756
    txt(d,(982,326),'log₁₀ J',26,MUTED)
    txt(d,(1135,326),'Target',26,INK,True)
    d.line((1090,344,1121,344),fill=INK,width=3)
    txt(d,(1380,326),'Selected design',26,BLUE,True)
    d.ellipse((1348,336,1362,350),outline=BLUE,width=3)
    def point(v,j):return (x0+(v-.05)/.45*(x1-x0),y1-(math.log10(abs(j))+7.5)/6*(y1-y0))
    for q in [-7,-5,-3]:
        y=y1-(q+7.5)/6*(y1-y0)
        d.line((x0,y,x1,y),fill=LINE,width=1);txt(d,(991,y-14),str(q),24,MUTED)
    for v in [.05,.2,.35,.5]:
        x=x0+(v-.05)/.45*(x1-x0)
        txt(d,(x-23,y1+17),f'{v:g}',24,MUTED)
    d.line((x0,y0,x0,y1,x1,y1),fill=MUTED,width=2)
    txt(d,(1778,770),'V',26,MUTED)
    progress=ease((t-1.1)/2)
    target=[point(v,j) for v,j in INVERSE['target_curve'] if v>=.05]
    count=max(1,round(len(target)*progress))
    if count>1:d.line(target[:count],fill=INK,width=4)
    for v,j in INVERSE['best_curve']:
        if .05<=v<=.05+.45*progress:
            x,y=point(v,j);d.ellipse((x-6,y-6,x+6,y+6),fill=BG,outline=BLUE,width=3)
    txt(d,(100,826),'Target mismatch = mean squared error of log-current at 0.2, 0.4 and 0.5 V.',28,INK)
    txt(d,(100,875),'Standard GP optimization · not a chip-performance gain · simulation only',29,AMBER,True)
    return im
def vision(t):
    im,d=base('THE VISION / 04',3)
    reveal(im,t,0,lambda d,o:txt(d,(89,159+o),'REFLEX',145,INK,True))
    reveal(im,t,.2,lambda d,o:txt(d,(99,381+o),'Learn from every experiment.',67,BLUE,True))
    reveal(im,t,.45,lambda d,o:txt(d,(99,470+o),'Design better semiconductor devices.',67,INK,True))
    reveal(im,t,.9,lambda d,o:txt(d,(101,615+o),'Target specs → propose structures / recipes → physics simulation → measured feedback',32,MUTED))
    reveal(im,t,1.2,lambda d,o:txt(d,(101,721+o),'VISION · advanced-device design and physical validation next',32,AMBER,True))
    reveal(im,t,1.45,lambda d,o:txt(d,(101,851+o),'Seeking a fab or equipment pilot partner.',31,INK))
    return im
def frame(t):
    im=first(t) if t<10 else comparison(t-10) if t<18 else business(t-18) if t<27 else vision(t-27)
    for boundary,previous,previous_duration in [(10,first,10),(18,comparison,8),(27,business,9)]:
        if boundary<=t<boundary+.3:im=Image.blend(previous(previous_duration),im,ease((t-boundary)/.3))
    # Caption-safe area is fixed and remains completely blank.
    ImageDraw.Draw(im).rectangle((0,990,W,H),fill=INK)
    return im
def main():
    HERE.mkdir(parents=True,exist_ok=True)
    for t in [3,9,13,17,22,26,30,31]:frame(t).save(HERE/f'check_{t:02d}.png')
    cmd=['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-pix_fmt','yuv420p','-movflags','+faststart',str(HERE/'evidence.mp4')]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(FPS*DURATION):
            p.stdin.write(frame(n/FPS).tobytes())
            if n%180==0:print(f'{n}/{FPS*DURATION}',flush=True)
    finally:p.stdin.close()
    if p.wait()!=0:raise SystemExit('ffmpeg failed')
    print('Done',flush=True)
if __name__=='__main__':main()

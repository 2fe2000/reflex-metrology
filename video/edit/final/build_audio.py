"""Generate original narration with native TTS; exact per-utterance caption timing."""
import concurrent.futures,json,re,subprocess,textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parent
scenes=json.loads((ROOT/'narration.json').read_text());audio=ROOT/'audio';audio.mkdir(exist_ok=True)
def run(cmd):subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def duration(path):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True))
items=[]
for s in scenes:
 s['items']=[]
 for k,text in enumerate(re.split(r'(?<=[.!?])\s+',s['text'])):
  name=f"{s['name']}_{k}";item={'text':text,'name':name,'source':audio/f'{name}.aiff'};items.append(item);s['items'].append(item)
def speak(i):
 textfile=audio/f"{i['name']}.txt";textfile.write_text(i['text']);run(['say','-v','Samantha','-r','158','-f',str(textfile),'-o',str(i['source'])]);i['duration']=duration(i['source'])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(speak,items))
parts=[];captions=[];cursor=0.
for s in scenes:
 total=sum(i['duration'] for i in s['items']);available=s['duration']-.6-.15*(len(s['items'])-1);speed=max(1.,total/available);padding=(s['duration']-total/speed)/len(s['items']);local=0.
 for i in s['items']:
  dur=i['duration']/speed;segdur=dur+padding;dest=audio/f"{i['name']}.wav"
  filters=f'atempo={speed:.6f},afade=t=in:st=0:d=0.03,afade=t=out:st={max(0,dur-.03):.6f}:d=0.03,apad,atrim=duration={segdur:.6f}'
  run(['ffmpeg','-y','-i',str(i['source']),'-af',filters,'-ar','48000','-ac','1','-c:a','pcm_s16le',str(dest)])
  parts.append(dest);captions.append({'start':s['start']+local,'end':s['start']+local+dur,'text':i['text']});local+=segdur
 concat=audio/'concat.txt'
concat.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-af','apad,atrim=duration=90','-c:a','pcm_s16le',str(ROOT/'narration.wav')])
def ass_time(t):
 cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
header='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Pretendard,28,&H00FFFFFF,&H00FFFFFF,&H0017202B,&H0017202B,0,0,0,0,100,100,0,0,1,0,0,2,80,80,15,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'''
lines=[]
for c in captions:
 txt='\\N'.join(textwrap.wrap(c['text'],width=105));lines.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Default,,0,0,0,,{txt}\n")
(ROOT/'master.ass').write_text(header+''.join(lines));(ROOT/'caption_timing.json').write_text(json.dumps(captions,indent=2))
print('Narration seconds',duration(ROOT/'narration.wav'),'utterances',len(items),flush=True)

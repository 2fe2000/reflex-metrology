"""Cache verbatim Soniox tokens and merge subwords without losing word boundaries."""
import importlib.util,json,pathlib,re,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('video_use_asr','/Users/2fe/.agents/skills/video-use/helpers/transcribe.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def transcribe(path):
 path=pathlib.Path(path); dest=ROOT/'transcripts'/f'{path.stem}.raw.json'; dest.parent.mkdir(exist_ok=True)
 if dest.exists(): raw=json.loads(dest.read_text())
 else:
  key=a.load_api_key(); receipt=dest.with_suffix('.job.json')
  if receipt.exists(): tx=json.loads(receipt.read_text())['transcription_id']
  else:
   with tempfile.TemporaryDirectory(prefix='reflex-asr-') as td:
    wav=pathlib.Path(td)/'audio.wav';a.extract_audio(path,wav);fid=a.upload_file(wav,key)
   tx=a.create_job(fid,key,['en']);receipt.write_text(json.dumps({'transcription_id':tx,'source':str(path)}))
  a.poll_until_done(tx,key); raw=a.fetch_transcript(tx,key); dest.write_text(json.dumps(raw,indent=2))
 words=[];current=None
 for t in raw:
  text=t.get('text','')
  if not text or text.startswith('<') or t.get('start_ms') is None:continue
  start=t['start_ms']/1000;end=t.get('end_ms',t['start_ms'])/1000
  if text[0].isspace() and current:
   words.append(current);current=None
  clean=text.strip()
  if not clean:continue
  if current is None:current={'text':clean,'start':start,'end':end,'speaker':t.get('speaker')}
  else:current['text']+=clean;current['end']=max(current['end'],end)
 if current:words.append(current)
 out={'source':str(path),'text':' '.join(w['text'] for w in words),'words':words}
 dest.with_name(path.stem+'.words.json').write_text(json.dumps(out,indent=2))
 print(out['text']);print('WORDS',len(words),'END',words[-1]['end'] if words else 0)
 return out
if __name__=='__main__':
 for p in sys.argv[1:]:transcribe(p)

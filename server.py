"""Local-only live REFLEX demo. Public source data replay, actual NumPy inference."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import json,threading,uuid,argparse
import numpy as np
from portable_runtime import LiveStream
from delayed_runtime import DelayedStream
ROOT=Path(__file__).resolve().parent
sessions={};lock=threading.Lock()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send_json(self,value,status=200):
  data=json.dumps(value,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if self.path=='/api/delay/evidence':
   return self.send_json(json.loads((ROOT/'results/v7/summary.json').read_text()))
  if self.path=='/api/evidence':
   return self.send_json(json.loads((ROOT/'results/evidence.json').read_text()))
  path=ROOT/'web'/('index.html' if self.path=='/' else self.path.split('?',1)[0].lstrip('/'))
  if not path.resolve().is_relative_to((ROOT/'web').resolve()) or not path.is_file():return self.send_json({'error':'not found'},404)
  data=path.read_bytes();self.send_response(200);self.send_header('Content-Type','text/html' if path.suffix=='.html' else 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_POST(self):
  try:
   body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
   with lock:
    if self.path=='/api/reset':
     ds=int(body.get('dataset',1));policy=body.get('policy','burst')
     if body.get('version')==7:
      delay=int(body.get('delay',5));phase=int(body.get('phase',0))
      if ds not in [1,2] or delay not in [0,5,20] or phase not in range(5):raise ValueError('invalid delayed choice')
      a=json.loads((ROOT/f'models/reflex_delayed_{ds}.json').read_text());data=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False)
      sid=str(uuid.uuid4());sessions[sid]=DelayedStream(a,data['X'],data['y'],data['keys'],delay,phase)
      if len(sessions)>30:del sessions[next(iter(sessions))]
      return self.send_json({'session':sid,'dataset':ds,**sessions[sid].advance(0)})
     if ds not in [1,2] or policy not in ['burst','uniform','all','frozen']:raise ValueError('invalid choice')
     a=json.loads((ROOT/f'models/reflex_{ds}.json').read_text());data=np.load(ROOT/f'models/replay_{ds}.npz',allow_pickle=False)
     sid=str(uuid.uuid4());sessions[sid]=LiveStream(a,data['X'],data['y'],data['keys'],policy)
     if len(sessions)>30:del sessions[next(iter(sessions))]
     return self.send_json({'session':sid,'dataset':ds,'model_bytes':(ROOT/f'models/reflex_{ds}.json').stat().st_size,**sessions[sid].advance(0)})
    if self.path=='/api/step':
     sid=body['session'];n=int(body.get('n',1));n=max(1,min(n,5000));return self.send_json(sessions[sid].advance(n))
   self.send_json({'error':'not found'},404)
  except Exception as exc:self.send_json({'error':str(exc)},400)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
 print(f'REFLEX http://127.0.0.1:{a.port}',flush=True);ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()

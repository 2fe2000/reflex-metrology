"""Capture actual locally executed UI states for an accelerated 48s demo segment."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent;out=ROOT/'video/edit/clips';frames=out/'live_frames';frames.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,channel='chrome')
 page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8765');page.wait_for_load_state('networkidle')
 page.add_style_tag(content='main{max-width:1760px;padding-top:24px;padding-bottom:100px}h1{font-size:48px}.heading{margin-bottom:22px}canvas{height:280px}.metric{padding:13px 0}.number{font-size:38px}.state{margin-top:12px}.statusbar{display:none}.foot{margin-top:14px}.toolbar{margin-bottom:18px}.chartbox{padding:20px}')
 page.evaluate("document.querySelector('#runtime').textContent='LOCAL MODEL · ACCELERATED DATA REPLAY'")
 for i in range(120):
  goal=round((i+1)*542/120)
  page.evaluate('(n)=>step(n)',goal-round(i*542/120))
  page.screenshot(path=str(frames/f'{i:04d}.png'))
 state=page.evaluate('latest');(out/'captured_run.json').write_text(json.dumps(state))
 assert state['index']==542 and state['queries']==88
 assert abs(state['rmse']-.21866161633306014)<1e-6
 page.get_by_role('button',name='Evidence',exact=True).click()
 # Compact only presentation spacing; no data changes.
 page.add_style_tag(content='.callout{padding:18px}.callout b{font-size:38px}.callout p{line-height:1.5;margin-bottom:0}table{margin-top:18px}th,td{padding:10px 15px}.note{margin-top:15px;padding:12px 17px}.evidence-intro{gap:20px}')
 page.screenshot(path=str(out/'evidence_ui.png'))
 page.get_by_role('button',name='Method',exact=True).click();page.screenshot(path=str(out/'method_ui.png'))
 (out/'ui_capture_audit.json').write_text(json.dumps({'browser_errors':errors,'samples':state['index'],'queries':state['queries'],'rmse':state['rmse'],'frames':120,'playback_fps':5,'note':'Actual local inference captured as accelerated public-data replay.'},indent=2))
 assert not errors
 browser.close()
print('Captured live model + evidence + method UI',flush=True)

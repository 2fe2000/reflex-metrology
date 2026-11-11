"""Capture actual API-driven delayed inference for the revised 90-second edit."""
from pathlib import Path
import json,subprocess
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent;out=ROOT/'clips';frames=out/'live_frames';frames.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,channel='chrome');page=b.new_page(viewport={'width':1920,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/delay.html');page.wait_for_load_state('networkidle')
    page.add_style_tag(content='main{max-width:1840px;padding-top:25px}.intro{grid-template-columns:1.25fr 1fr}h1{font-size:44px;margin-bottom:10px}.intro p{margin:0}.controls{margin-top:20px;margin-bottom:15px;padding-top:15px}.metrics{margin-bottom:18px}.metric{padding-top:14px;padding-bottom:14px}.value{font-size:34px}.plot{padding:18px}canvas{height:250px}.loop{margin-top:15px;padding-bottom:14px}.loop p{margin-bottom:0}.evidence{margin-top:30px}footer{display:none}')
    page.locator('.kicker').first.evaluate("e=>e.textContent='LOCAL INFERENCE · ACCELERATED PUBLIC-DATA REPLAY'")
    for i in range(120):
        goal=round((i+1)*542/120);before=round(i*542/120)
        page.evaluate('(n)=>step(n)',goal-before);page.screenshot(path=str(frames/f'{i:04d}.png'))
    state=page.evaluate('latest');assert state['index']==542 and state['queries']==109 and state['arrived']==108
    (out/'captured_state.json').write_text(json.dumps({k:v for k,v in state.items() if k!='history'},indent=2))
    page.add_style_tag(content='.intro,.controls,.metrics{display:none}.plot{margin-top:30px}canvas{height:400px}.loop{margin-top:35px}.loop strong{font-size:34px}.loop h2{font-size:13px}.detail,.note{font-size:14px}.evidence{display:none}')
    page.evaluate('draw()')
    page.screenshot(path=str(out/'mechanism.png'))
    page.add_style_tag(content='.plot,.loop{display:none}.evidence{display:block;margin-top:50px}h2{font-size:46px}.evidence .note{font-size:18px}table{font-size:21px}th{font-size:14px}td,th{padding:20px 16px}.warning{font-size:19px;padding:25px;margin-top:35px;line-height:1.65}.evidence .kicker{font-size:14px}')
    page.screenshot(path=str(out/'evidence.png'))
    assert not errors;(out/'audit.json').write_text(json.dumps({'browser_errors':errors,'captured_samples':542,'requests':109,'arrived':108,'delay':5,'phase':0,'frames':120,'playback_fps':5,'note':'Real local inference captured as accelerated recorded-feature replay.'},indent=2));b.close()
commands=[['ffmpeg','-y','-v','error','-framerate','5','-i',str(frames/'%04d.png'),'-t','24','-r','30','-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(out/'live.mp4')]]
for name in ['mechanism','evidence']:
    commands.append(['ffmpeg','-y','-v','error','-loop','1','-framerate','30','-i',str(out/f'{name}.png'),'-t','12','-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(out/f'{name}.mp4')])
for cmd in commands:subprocess.run(cmd,check=True)
print('Captured and encoded 48 seconds of actual local demo.')

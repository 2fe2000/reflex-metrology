import html,json
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
ROOT=Path(__file__).resolve().parent
e=json.loads((ROOT/'results/evidence.json').read_text())
rows=''.join(f"<tr><td>{r['dataset']}</td><td>{html.escape(r['method'])}</td><td>{r['queries']} / {r['n']}</td><td>{r['rmse']:.4f}</td><td>{r['p90']:.4f}</td></tr>" for r in e['rows'])
hw=[]
for f in sorted((ROOT/'results').glob('hardware_*.json')):
 d=json.loads(f.read_text())
 for ds,v in d['models'].items():hw.append(f"<tr><td>{d['chip']}</td><td>{ds}</td><td>{v['predict_ms_p50']:.4f}</td><td>{v['predict_ms_p95']:.4f}</td><td>{v['rmse']:.6f}</td><td>{v['queries']}</td></tr>")
delay=pd.read_csv(ROOT/'results/delay_sensitivity.csv').to_html(index=False,float_format=lambda n:f'{n:.4f}',border=0)
report=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>REFLEX — 실제 실험 결과와 제출 자료</title>
<style>body{{font-family:Pretendard,'Apple SD Gothic Neo',sans-serif;color:#19242e;background:#f5f6f3;margin:0}}main{{max-width:1050px;margin:auto;padding:60px 40px}}.eyebrow{{font:12px Menlo,monospace;color:#2563eb;letter-spacing:2px}}h1{{font-size:48px;letter-spacing:-2px;margin:14px 0}}h2{{font-size:25px;margin-top:46px}}p,li{{line-height:1.85;font-size:15px}}.lead{{font-size:20px;line-height:1.7}}.callout{{padding:24px 28px;background:white;border-left:4px solid #2563eb}}table{{border-collapse:collapse;width:100%;background:white;font-size:13px}}td,th{{text-align:left;padding:11px 13px;border-bottom:1px solid #dce2e6}}th{{font-size:12px;color:#667681}}a{{color:#2563eb}}.links{{display:flex;gap:12px;flex-wrap:wrap;margin:25px 0}}.links a{{padding:12px 18px;background:#2563eb;color:white;text-decoration:none}}.small{{font-size:12px;color:#63737c}}code{{background:#e8edf2;padding:3px 6px}}.scroll{{overflow:auto}}@media print{{body{{background:white}}main{{padding:20px}}h2{{break-after:avoid}}tr{{break-inside:avoid}}}}@media(max-width:700px){{main{{padding:25px 18px}}h1{{font-size:35px}}}}</style>
<main><div class="eyebrow">REFLEX / RESEARCH EVIDENCE</div><h1>만들었다. 검증했고, 한계도 찾았다.</h1>
<p class="lead">실행 가능한 로컬 모델·브라우저 데모·90초 영상·편집 가능한 발표 자료를 완성했다. 다만 <b>산업 경쟁력과 독자적인 기술 우위는 아직 검증되지 않았다.</b></p>
<div class="links"><a href="REFLEX_90s.mp4">90초 영상</a><a href="REFLEX_pitch.pptx">편집 가능한 PPTX</a><a href="REFLEX_pitch.pdf">발표 PDF</a><a href="http://127.0.0.1:8765">실행 중인 로컬 데모</a></div>
<div class="callout"><b>심사위원 관점의 판정</b><p>문제를 실험으로 좁히는 접근과 실제 로컬 실행은 매력적이다. 하지만 현재 결과만으로 수상 가능한 독자 기술이나 CMP 사업성을 입증했다고 말할 수 없다. 공개 GRAPE 기반 모델을 사용하며, 신규성도 입증하지 않았다. 새로운 현장 데이터와 지연 피드백 대응이 다음 검증 조건이다.</p></div>
<h2>실제로 확인된 결과</h2><ul><li>CMP 초기 실험은 실패했다. 고정 모델 RMSE 12.986보다 추가 측정 8개를 쓴 초기 후보의 14.410이 나빴다.</li><li>별도 GRAPE 데이터 두 세트로 평가한 사전 고정 v2 기준도 통과하지 못했다.</li><li>후속 탐색에서 측정 결과가 예상과 다를 때 측정을 집중하는 스케줄을 시험했다. 데이터셋 1에서 같은 88회 측정 대비 RMSE가 23.4% 낮았다.</li><li>데이터셋 2 개선은 1.0%이고 95% 블록 부트스트랩 구간이 0을 포함한다. 우위가 확실하지 않다.</li><li>측정 결과를 5개 샘플 뒤에 제공하자 데이터셋 1의 이점이 사라졌다.</li></ul>
<p class="small">후속 결과는 이전 평가 결과를 확인한 뒤의 탐색 실험이다. 95% 구간은 모델 선택 편향을 제거하지 않으며, 새로운 독립 검증으로 해석하면 안 된다. 목표값은 저자 제공 스케일이며 물리 단위가 아니다.</p>
<div class="scroll"><table><thead><tr><th>데이터</th><th>방법</th><th>측정 수</th><th>RMSE</th><th>P90 절대 오차</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>현장 적용을 가르는 조건: 지연 피드백</h2><p>데이터셋 1, 즉시 피드백: 88회 측정으로 0.219 대 0.286. 5개 샘플 지연: 145회 측정으로 0.336 대 0.320. 지연 시 스케줄이 더 자주 측정하면서도 오차가 커졌다. 이 때문에 지금의 23.4%를 실제 공장 절감 효과로 바꿔 말할 수 없다.</p><div class="scroll">{delay}</div>
<h2>직접 실행한 컴퓨팅 자원</h2><div class="scroll"><table><thead><tr><th>장치</th><th>데이터</th><th>p50 ms</th><th>p95 ms</th><th>전체 RMSE</th><th>측정 수</th></tr></thead><tbody>{''.join(hw)}</tbody></table></div>
<p>모델 아티팩트는 3,510바이트와 31,025바이트다. 위 지연시간은 준비된 특징 벡터의 정규화와 단일 추론을 200회 워밍업 후 2,000회 측정한 값이다. 센서 원본 처리·계측 장비·통신 시간은 포함하지 않는다. 실시간 성능 보증이 아니다. M4의 다른 NumPy 버전에서는 부동소수점 비트 차이가 있으나 표에 표시한 RMSE와 요청 수는 일치했다.</p>
<p>DGX는 저장된 호스트 이름 해석 및 로그인 권한 문제로 사용하지 못했다. GMI 키·크레딧 잔액도 인증이 완료되지 않아 확인되지 않았다. 유료 클라우드 사용이나 대규모 GPU 학습을 했다고 주장하지 않는다. 현재 병목은 연산량보다 모델·평가 설계다.</p>
<h2>데모가 실제로 하는 일</h2><p>브라우저에서 데이터를 진행하면 Python 서버가 매 샘플을 실제로 추론한다. 예측 후 스케줄이 측정을 요청한 경우에만 정답으로 모델 상태를 갱신한다. 화면의 전체 정답 곡선은 평가를 위한 사후 감사 정보다. 요청 정책에는 측정 전 정답이 들어가지 않는다. 원자료는 실제 장비 연결이 아닌 공개 기록의 재생이다.</p>
<p>검증: 미측정 정답을 임의로 바꿔도 예측·요청이 유지되는지, 자기 정답을 보기 전에 예측하는지, NumPy 이식 결과가 원 구현과 일치하는지 테스트했다. 4가지 정책의 전체 API 실행, 모바일 가로 넘침, 브라우저 오류를 확인했다. 발표 자료 8장을 이미지로 검토하고 마지막 장의 출처 잘림을 수정했다. 영상은 90.000초, H.264 1920×1080 30fps + AAC이며 전환 주변과 주요 프레임을 시각 확인했다. 음성은 원본 영어 대본에서 생성한 합성 내레이션이다.</p>
<h2>사업과 해자: 검증해야 할 가설</h2><p>첫 고객 후보는 CMP 공정개발팀·소모품 업체의 응용개발팀이다. 제안 가격은 유상 검증 500만~1,000만원, 통합 2,000만~5,000만원이며 시장에서 확인된 가격이 아니다. 현재 고객·매출·측정 비용 절감·생산량 개선은 검증하지 않았다.</p><p>잠재적 자산은 재사용 권한이 있는 공정 변경 전후 데이터, 반복 설치 가능한 어댑터, 검증된 실패 조건이다. 현재 구현은 공개 모델과 단순 스케줄을 결합한 수준이므로 기술 해자가 확보됐다고 할 수 없다. 두 번째·세 번째 고객에서 초기 측정 수와 통합 공수가 줄어드는지 확인해야 한다.</p>
<h2>재현과 출처</h2><p><a href="../README.txt">실행·재현 안내</a> · <a href="../protocol.json">CMP 사전 프로토콜</a> · <a href="../protocol_v2.json">스트리밍 사전 프로토콜</a> · <a href="../results/evidence.json">전체 지표 JSON</a> · <a href="../results/burst_bootstrap.json">불확실성 계산</a> · <a href="../results/delay_sensitivity.csv">지연 실험 CSV</a></p>
<p><a href="https://github.com/cheonwoolee/GRAPE">GRAPE 공식 코드</a> / <a href="https://arxiv.org/abs/2611.00806">논문</a>, 고정 커밋 <code>cce2d27a092abd9e397d7739e4beb6dfe0ae145e</code>. 본 비교는 공개 특징 열 순서를 일관되게 사용했다. 원 저장소 평가 코드의 unseen 열 처리와 다르므로 논문 수치 재현이라고 주장하지 않는다. 원 특징의 의미·내보내기 정렬은 독립 검증되지 않았다.</p>
<p><a href="https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/">PHM 원 설명</a> / <a href="https://github.com/akangel0307/PHM-Data-Challenge">사용한 공개 미러</a>. 원본 다운로드 링크 접근 실패 후 미러를 사용했다. 파일 해시는 보존했지만 원 제공자의 체크섬과 동일함을 검증한 것은 아니다. 실제 정비 이벤트와 불량 규격이 없어 제조 합격 여부를 평가할 수 없다.</p>
<p class="small">생성: {datetime.now(timezone.utc).isoformat()} · 해커톤 등록·제출·공개 배포 완료를 의미하지 않는다. 프로토콜 생성시각의 임시 표기는 실제 파일 생성시각으로 정정했으며 평가 조건은 변경하지 않았다.</p></main></html>'''
(ROOT/'deliverables/REFLEX_report.html').write_text(report)
print('Report generated')

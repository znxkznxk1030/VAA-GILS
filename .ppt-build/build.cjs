const pptxgen=require('pptxgenjs');
const p=new pptxgen();p.layout='LAYOUT_WIDE';p.author='연구 수정 대응';p.subject='교수님 면담용 수정 후 재심 대응 현황';p.title='수정 후 재심 대응 현황';p.lang='ko-KR';
const C={navy:'355C7D',teal:'4E8D8C',gray:'4D4D4D',light:'D9DEE3',white:'FFFFFF'};
p.imageSizingContain=(path,x,y,w,h)=>{const b=require('fs').readFileSync(path);const ratio=b.readUInt32BE(16)/b.readUInt32BE(20);let iw=w,ih=w/ratio;if(ih>h){ih=h;iw=h*ratio;}return {x:x+(w-iw)/2,y:y+(h-ih)/2,w:iw,h:ih};};
p.theme={headFontFace:'맑은 고딕',bodyFontFace:'맑은 고딕',lang:'ko-KR'};
const root=process.cwd(); const drafts='docs/revision_drafts/';
function txt(s,t,x,y,w,h,size=20,color=C.gray,bold=false){s.addText(t,{x,y,w,h,fontFace:'맑은 고딕',fontSize:size,color,bold,margin:0,breakLine:false,paraSpaceAfterPt:10,fit:'shrink'});}
const reviewIds=[
'R1-1~R1-18 / R2-1~R2-14',
'R1-1~R1-18 / R2-1~R2-14',
'R1-1 / R1-18 / R2-11 / R2-14',
'R1-1 / R1-18 / R2-11 / R2-14',
'R2-1 / R2-2',
'R1-8 / R2-2 / R2-14',
'R2-3 / R1-8 / R2-14',
'R2-9',
'R1-11 / R1-12 / R2-9',
'R1-10 / R1-11 / R2-9',
'R1-15',
'R1-16',
'R1-13 / R2-11',
'R1-2~R1-7 / R1-9 / R1-14 / R1-17 / R2-4~R2-8 / R2-10~R2-14',
'R1-1 / R1-13 / R1-15 / R1-18 / R2-3 / R2-11 / R2-14'];
function slide(title,source='',tag='보고'){const s=p.addSlide();s.background={color:C.white};txt(s,tag,0.55,.3,11,.3,12,C.teal,true);txt(s,title,.55,.82,12.2,.65,28,C.navy,true);txt(s,'관련 의견  '+reviewIds[p._slides.length-1],.57,1.51,12.1,.24,12,C.teal);txt(s,source,.55,7.08,11.6,.22,9,'777777');txt(s,String(p._slides.length).padStart(2,'0'),12.25,7.05,.5,.25,10,C.gray);s.addNotes('근거: '+source+'\n작성 기준: 2026-11-16. 제공된 현황표와 수정 초안. 수치 재계산 없이 인용.');return s;}
function table(s,rows,widths,y=2.05,h=.58){s.addTable(rows,{x:.55,y,w:12.2,colW:widths,rowH:h,fontSize:17,fontFace:'맑은 고딕',color:C.gray,margin:.12,border:{type:'solid',color:'D9DEE3',pt:.6},fill:'FFFFFF',bold:false,autoPage:false,});}
function head(row){return row.map(text=>({text,options:{bold:true,fill:C.navy,color:'FFFFFF'}}));}
function lines(s,arr,y=2.2,size=23){arr.forEach((a,i)=>txt(s,a,.7,y+i*.92,11.9,.75,size));}
function decision(title,problem,rows,recommend,source){let s=slide(title,source,'교수님 결정');txt(s,problem,.6,1.8,12.1,.65,20);table(s,[head(['선택지','내용','판단 기준']),...rows],[1.4,6.3,4.5],2.65,.72);txt(s,recommend,.65,5.8,12,.8,22,C.teal,true);return s;}
let s=slide('수정 후 재심 대응 현황','','교수님 면담 자료');txt(s,'도착 시각과 연성 납기를 고려한\n입출고 병행 트럭 크로스도킹 스케줄링',.7,2.2,11.8,1.55,32,C.navy,true);txt(s,'병목 유도 반복 지역탐색',.7,4,11.8,.6,25,C.gray);txt(s,'2026. 11. 16.\n32개 심사 의견 대응 및 결정 안건 4건',.7,5.2,11.8,.9,21,C.teal);
s=slide('재심 진행사항','제공된 심사 의견 현황표 기준');table(s,[head(['분류','건수','진행 중','미착수']),['정정','5','4','1'],['그림·의사코드','4','4','0'],['가정·정의','5','4','1'],['추가 실험','2','1','1'],['수리모형','6','0','6'],['표현','5','0','5'],['구성','5','0','5']],[4.5,2.3,2.7,2.7],1.95,.43);txt(s,'검토 안건: ① CP-SAT 정정  ② 이송시간 차이  ③ ablation 범위  ④ 독립 실험 범위',.6,6.05,12,.7,20,C.teal,true);s.addNotes('R1 18건, R2 14건. 진행 중 13건, 미착수 19건. 상태는 제공 표 기준이며 R1-13 초안에는 실행 중으로 기록됨. 실험 완료와 본문 반영 완료를 구분.');
s=slide('CP-SAT 기록 오류 및 재실행 결과','R1-1_R1-18_R2-11_R2-14_cpsat_m_correction.md');table(s,[head(['범위','재실행 결과','해석']),['재실행 사유','기존 실험 결과의 부정확성 확인','결과 재확인을 위한 재실행'],['S: 각 20개 평가','최적성 증명: none 20/20개\nmedium 1/20개, tight 0/20개','300초 제한\n미증명 ≠ 실행 가능해 없음'],['M: 6건','모두 실행 가능해 반환','최적성은 모두 미증명'],['L: 6건','모두 실행 가능해 미반환','전처리에서 종료, 분기 0회'],['재실행 설정','12건, 순차 실행, 8스레드','600초 제한, 로그로 유효성 확인']],[2,4.5,5.7],2.1,.65);txt(s,'전체 인스턴스의 최적성 증명: S-none만 해당\n정정 대상: M 시간 제약 조건의 실행 가능해 미반환 서술',.65,6,12,.8,20,C.teal,true);
decision('결정 1. CP-SAT 정정 및 초록 수치 변경','M-none 재실행 기준해 통일에 따른 초록 격차 범위 변경',[['정정안','0.10~0.23%를 0.11~0.23%로 변경','S 세 조건과 M-none에 한정'],['범위','“fails”는 L에서 600초 내 실행 가능해 미반환','M 시간 제약 조건은 제외'],['공개 방식','Table 4·5.1절·7장과 초록을 함께 정정','답변서에 저자 자체 정정 명시']],'검토안: 정정 반영 / 최적해 대비 0.23% 및 Δbo 유지','R1-1_R1-18_R2-11_R2-14_cpsat_m_correction.md');
s=slide('문제 구조도','fig_problem_structure.png / R2-1, R2-2','그림 확인');s.addImage({path:root+'/paper/figures/fig_problem_structure.png',...p.imageSizingContain(root+'/paper/figures/fig_problem_structure.png',.6,1.9,12.1,4.65)});txt(s,'확인 사항: 유지 화물·부분 하역·추가 적재 흐름',.65,6.6,12,.35,17,C.teal);
s=slide('주요 운영 가정','R1-8_R2-2_operating_assumptions.md');table(s,[head(['항목','명시할 가정','적용 범위']),['병행 트럭 배정','계획기간 전체에서 도어당 최대 1대','물리적 동시 점유 제약과 구분'],['차량 용량','목적지 전체 물량을 한 차량이 운송 가능','차량 용량 제약·분할 운송 미고려'],['차량 역할','입고 후 일부 화물 유지, 하역·추가 적재','문제 구조도와 타임라인 연결'],['한계','복수 병행 트럭의 도어 순차 처리 미고려','일반 운영으로 확장할 과제']],[2.5,5.5,4.2],2.1,.8);txt(s,'원 모델에서 계승한 가정의 원문 근거 제시',.65,6.15,12,.6,20,C.teal);
decision('결정 2. 이송시간 가정 및 원 모델과의 차이','원 모델: 단위 이동시간×물량 / 본 연구: 도어 쌍별 배치 이송시간',[['안 1','차이를 밝히고 모형 가정·한계로 설명','새 실험 없음, 선택 이유 확인 필요'],['안 2','물량 비례 이송시간의 민감도 실험 추가','평가기·CP-SAT 변경 및 추가 실험'],['공통','“원 모델과 같다”와 “재구현”의 범위 정정','계산식과 수치 예시를 함께 제시']],'검토안: 안 1 우선 / 배치 이송 가정의 선택 근거 확인','R2-3_interdoor_transfer_time.md / fig_transfer_example');
s=slide('VAA 후회도 수식 및 예시','R2-9_vaa_regret.md');txt(s,'식 (17)  cᵢd = (Hᵢ − hᵢd) + Lᵢd\n식 (18)  후회도 = 두 번째 최소 비용 − 최소 비용\n식 (19)  최대 후회도의 행·열에서 최소 비용 짝 선택',.65,1.95,12,1.5,23,C.navy);table(s,[head(['회차','최대 후회도','확정']),['1','목적지 d₂: 11','i₂가 d₂ 유지'],['2','목적지 d₁: 10','i₁이 d₁ 유지'],['3','트럭 i₃: 1','i₃이 d₄ 유지, d₃은 출고트럭']],[2,4,6.2],3.8,.55);txt(s,'비용식: 원 모델 / 후회도: 기본 Vogel 근사법에 따른 구현\nKorukoğlu & Ballı (2011) 참고문헌 추가',.65,6,12,.7,18,C.teal);
s=slide('의사코드 및 병목 정의','R1-11_R2-9_algorithm1_pseudocode.md / R1-12_bottleneck_definitions.md');lines(s,['최선해보다 좋은 후보에만 Descent를 적용한 뒤 최선해 갱신','현재 해보다 엄격히 좋은 후보만 수용하는 탐욕적 규칙','병목 도어: 최종 작업완료 시각이 최대인 도어','병목 트럭: 완료 시각 최대 / 최대 지연 트럭: 납기지연 최대'],2.05,22);txt(s,'“30회 연속 개선 없음”: 최선해 미갱신 기준\n정체 카운터: 최선해 갱신 또는 restart 후 0으로 초기화',.65,6,12,.75,19,C.teal);
s=slide('알고리즘 흐름도','fig_algorithm_flow.png / R1-10, R1-11, R2-9','그림 확인');s.addImage({path:root+'/paper/figures/fig_algorithm_flow.png',...p.imageSizingContain(root+'/paper/figures/fig_algorithm_flow.png',.6,1.8,8.3,5.05)});txt(s,'그림 확인\n\n11개 연산자 균등 선택\n\ng1~g4 대상·이동 구분\n\n지각 트럭 부재 시 대체\n\n의사코드 행 번호 삭제',9.2,2.05,3.5,4.7,20,C.gray);s.addNotes('원본 그림 전체 삽입. 세부 검토는 확대 또는 원본 drawio/PDF 사용.');
decision('결정 3. 통제 비교의 대상 및 서술 범위','5.2절: Table 6·7 / 5.3절: 선택 정책 비교(Table 8)',[['안 A','5.2절을 “두 가지 ablation”으로 정정','절 내부의 두 분석만 설명'],['안 B','“세 가지 통제 비교”로 유지','연산자 집합·구성요소·선택 정책 명시'],['표 참조','Table 6 / Table 7 / Table 8을 각각 연결','새 표 추가 시 번호 재정렬']],'검토안: 안 B / 도입 문장에서 5.2절·5.3절의 역할 구분','R1-15_ablation_targets.md');
s=slide('연산자별 개별 ablation 결과','R1-16_individual_operator_ablation.md / 시간 제약 조건 30쌍','해석 확인');table(s,[head(['연산자','단독 추가 개선(%)','Holm p','전체 집합 내 추가 개선(%)','Holm p']),['g1','+0.038','0.0062','+0.035','0.0015'],['g2','+0.064','0.0013','+0.051','0.0060'],['g3','−0.002','0.2694','+0.015','0.2694'],['g4','+0.049','0.0412','+0.048','0.2694']],[1.3,3,1.7,4,2.2],2.1,.62);txt(s,'g1·g2: 각각 유의 / g4: 단독 추가에서 유의 / g3: 개별 효과 미확인\n최종 엔진 full 유지 / 시험 집합 결과에 따른 구성 재선택 제외',.65,5.65,12,.9,21,C.teal);s.addNotes('양수는 연산자가 있는 집합이 좋음. 단독: generic 대비. 전체 집합 내 추가: full−g 대비 full. 시간 제약에서도 납기지연이 없으면 g3/g4는 g1/g2로 대체됨. 집합 크기에 따라 선택 확률도 달라짐.');
decision('결정 4. 도착 분산·납기 여유 독립 실험','초안: 3×3 실행 중 / 요청 계획: 4×4 / 설계 범위 확인 필요',[['현재 초안','ρ: 0.10, 0.25, 0.50 / δ: 1.00, 0.60, 0.35','같은 인스턴스에서 두 요인만 변경'],['확장안','각 요인의 “꺼짐” 수준을 더한 4×4','수준 정의 및 추가 실행 범위 확인'],['보고 범위','규모별 20개, 5회 반복 / 결과는 미확인','본문 요약표와 상세 부록 분량 결정']],'검토안: 설계 확정 후 결과 확인 / 본문 핵심 표·부록 분량 구분','R1-13_tw_factorial.md / 결과 수치 미기재');
s=slide('잔여 수정사항 및 우선순위','제공된 심사 의견 현황표 / R1-14·R1-17은 진행 중','우선순위 확인');table(s,[head(['작업 묶음','관련 ID','처리 방향']),['모형·지표 설명','R1-9, R2-6~8, R2-12~13','제약 의미·인덱스·λ·Δbo·Gain 명시'],['방법론 구성','R2-10','비교 방법과 parameter 설정을 실험 장으로 이동'],['논의·결론','R2-11, R2-14','개선의 의미·조건별 효과·한계 보완'],['표현·가독성','R1-2~7, R2-4~5','용어·인용·소제목·표 약어 정리'],['정정·그림 교체','R1-14, R1-17','인스턴스당 값 하나 / Figure 2·3 최신화']],[2.5,4,5.7],2.05,.65);txt(s,'추가 실험 완료 및 본문·답변서 반영 상태 구분',.65,6.3,12,.5,20,C.teal);
s=slide('결정사항 정리 및 향후 일정','일정 날짜는 면담에서 협의','결정 및 일정');table(s,[head(['결정','교수님께 확인할 사항','다음 작업']),['1','CP-SAT 자체 정정과 초록 수치 변경','초록·Table 4·5.1절·7장 동시 반영'],['2','배치 이송 차이의 대응 방식과 근거','가정 설명 또는 민감도 실험'],['3','ablation 안 A / 안 B','절 도입과 표 참조 정리'],['4','독립 실험 범위와 본문 분량','결과 확인 후 표·해석 확정']],[1.1,5.5,5.6],2.05,.7);txt(s,'남은 순서: 결정 반영 → 원고 수정 → 답변서 대조 → 제출본 검수\n수정 마감일·교수님 검토일·제출일은 면담에서 확정',.65,5.9,12,.9,20,C.teal);
p.writeFile({fileName:root+'/outputs/presentations/revision_review_2026-11-16_v4.pptx'});

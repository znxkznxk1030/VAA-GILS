# 지도교수 피드백 반영 논문 수정계획서

## 1. 수정 목적

본 계획서는 지도교수 검토 의견을 바탕으로 한글 논문의 핵심 기여와 문제 정의를
단순하고 명확하게 정리하고, 실험 결과 및 CP-SAT 검증 범위를 정확하게 전달하기
위한 수정 작업을 정의한다.

이번 수정에서는 새로운 알고리즘이나 실험을 추가하기보다 현재까지 개발한 문제,
VAA-GILS 및 검증 결과를 일관된 논리로 제시하는 데 중점을 둔다.

## 2. 논문의 핵심 구조

논문의 핵심 contribution은 다음 세 가지로 통일한다.

1. 기존 compound-truck cross-docking 문제에 release time과 soft due date를
   도입한 문제 확장
2. 병목 정보를 활용하는 bottleneck-guided GILS 휴리스틱 개발
3. CP-SAT 및 비교실험을 이용한 제안 방법의 성능 검증

Q-learning, transfer DQN 및 learned selector 분석은 주요 contribution에서 제외하고,
uniform selection 대비 추가 효과를 검토하는 보조적인 ablation study로 제시한다.

## 3. 세부 수정 계획

### 3.1 핵심 contribution 단순화

#### 수정 대상

- 제목
- 초록
- 서론의 연구 기여 문단
- 논의 및 결론

#### 수정 내용

- MILP, lower bound, Q-learning 및 DQN을 각각 독립적인 핵심 기여처럼 나열하지 않는다.
- 초록과 서론의 contribution을 위의 세 가지 구조로 통일한다.
- RL selector 결과는 제안 방법의 핵심이 아니라 보조 분석임을 명시한다.
- VAA-GILS의 핵심 구성요소를 best-improvement descent, bottleneck-guided operator,
  kick restart로 정리한다.
- 새로운 아이디어를 추가하기보다 기존 방법의 정의와 실험 근거를 명확히 제시한다.

#### 완료 기준

- 초록, 서론 및 결론에서 동일한 세 가지 contribution이 확인된다.
- RL 또는 DQN이 제목이나 핵심 contribution 목록에 포함되지 않는다.
- 논문의 주된 이야기를 문제 확장, GILS 및 CP-SAT 검증의 세 문장으로 설명할 수 있다.

### 3.2 release time, soft due date 및 time window 용어 정리

#### 문제점

일반적으로 time window는 earliest/latest service time으로 구성된 구간을 의미한다.
현재 모형이 실제로 사용하는 요소는 release time과 위반 시 tardiness 비용이 발생하는
soft due date이므로, 이를 전형적인 time-window problem과 구분해야 한다.

#### 용어 원칙

- 문제 명칭: `release times and soft due dates`
- $r_q$: 트럭 $q$가 도어 작업을 시작할 수 있는 가장 이른 시각인 release time
- $\bar d_q$: 위반할 수 있지만 지연 비용이 발생하는 soft due date
- $T_q=\max\{0,C_q-\bar d_q\}$: 트럭 $q$의 tardiness
- `time window`는 관련 연구의 기존 모형을 설명할 때만 사용한다.
- 실험의 none/medium/tight는 `시간 제약 수준` 또는
  `release-time/due-date scenario`로 표현한다.

#### 수정 대상

- 제목
- 초록
- 서론
- 관련 연구
- 문제 정의
- 실험 설계와 결과의 표·그림
- 결론

#### 완료 기준

- 제목, 초록, 서론 및 문제 정의에서 동일한 문제 명칭을 사용한다.
- 현재 연구의 문제를 단순히 `time-window problem`이라고 부르는 문장이 없다.
- $r_q$, $r_i$, $r_f$, $\bar d_q$, $T_q$가 처음 사용되기 전에 정의된다.
- soft due date가 hard constraint가 아니라 목적함수의 tardiness 기준임이 설명된다.

### 3.3 실험 결과 재구성

결과 절은 다음 세 질문에 순서대로 답하도록 구성한다.

1. VAA-GILS가 기존 방법보다 얼마나 좋은 해를 얼마나 빠르게 찾는가?
2. CP-SAT으로 최적해 또는 incumbent를 얻은 문제에서 VAA-GILS의 gap은 얼마인가?
3. VAA-GILS의 성능 향상에 실제로 기여하는 component는 무엇인가?

#### 권장 결과 절 순서

1. 해 품질 및 실행시간 비교
2. CP-SAT 최적해·incumbent 대비 gap
3. GILS component ablation
4. Learned selector 보조 분석
5. Tardiness-weight sensitivity

#### 핵심 수치

- VAA 대비 VAA-GILS 평균 개선율
- SA-RL5 대비 VAA-GILS 평균 개선율
- 1,000 iterations의 S/M/L 평균 실행시간
- 최적성이 증명된 S-none 결과
- CP-SAT incumbent가 존재하는 조건의 0.1--0.6% 비교 결과
- Descent, guided operator 및 restart의 제거 효과

#### RL 분석 축소

- Uniform, tabular Q-learning 및 transfer DQN 비교는 보조 결과로 배치한다.
- 본문에서는 핵심 결론과 통계 검정만 제시한다.
- DQN 구조, 학습 절차 및 budget별 상세 결과는 부록 이동을 검토한다.
- Learned selector가 uniform selection보다 뚜렷한 이득을 주지 않았다는 범위에서만
  해석한다.

#### 완료 기준

- 첫 번째 결과 표에서 해 품질과 실행시간의 핵심 차이를 파악할 수 있다.
- CP-SAT 비교 대상과 표본 수가 표 또는 caption에 명시된다.
- Ablation 결과의 중심이 descent, guided operator 및 restart로 정리된다.
- RL 관련 내용이 전체 결과 절의 중심처럼 보이지 않는다.

### 3.4 CP-SAT 결과 및 최적성 표현 정비

#### 표현 기준

| CP-SAT 결과 | 허용 표현 | 금지 또는 주의 표현 |
|---|---|---|
| 최적성 증명 | proven optimal, 증명된 최적해 | 제한 없음 |
| 제한시간 내 실행 가능해 획득 | CP-SAT incumbent, CP-SAT 기준해 | optimal solution |
| 실행 가능해 미발견 | CP-SAT 기준 없음 | near-optimal |
| 대형 문제의 휴리스틱 비교 | best solution observed among the compared methods | near-optimal, 근거 없는 best-known |

#### 수정 대상

- 초록
- 결과 표와 caption
- 그림 caption
- 결과 해석
- 논의
- 결론

#### 추가 점검

- `optimal`, `optimization`, `near-optimal`, `best-known`, `exact`, `incumbent`를
  전역 검색하여 문맥을 확인한다.
- `best-known solution`은 공개된 외부 기준까지 확인한 경우에만 사용한다.
- 현재 비교실험 안에서만 가장 좋은 경우에는
  `비교한 방법 가운데 관측된 최선해`라고 쓴다.
- CP-SAT이 최적성을 증명한 인스턴스 수와 incumbent만 반환한 인스턴스 수를 구분한다.

#### 완료 기준

- 최적성이 증명되지 않은 결과에 `optimal` 또는 `near-optimal`을 사용하지 않는다.
- Abstract, 표, Results 및 Conclusion의 CP-SAT 표현이 서로 일치한다.
- 모든 gap의 기준과 표본 범위를 독자가 확인할 수 있다.

### 3.5 Writing 및 용어 통일

#### 물류 운영 용어

다음 용어는 한글을 기본으로 사용한다.

- 입고 트럭, 출고 트럭
- 부분 하역
- 적재 및 하역
- 도어 배정
- 도어 간 이송
- 처리시간
- 완료 시각
- 트럭 작업 순서
- 출차

#### 알고리즘 및 실험 용어

고유한 알고리즘 용어는 첫 등장 시 한글 설명과 영문을 병기하거나 영문을 유지한다.

- best-improvement descent
- bottleneck-guided operator
- kick restart
- uniform selection
- learned selector
- ablation study
- CP-SAT incumbent
- train, tuning, test seed

한 용어에 대해 한글과 영어 표현을 번갈아 사용하지 않고, 첫 정의 이후 하나의 표현을
일관되게 사용한다.

#### 문체 정리

- 연구노트식 표현과 구어체를 학술 문체로 수정한다.
- `best`, `engine`, `pool`, `component`, `negative result`처럼 문장에 직접 삽입된
  영어 표현은 필요한 경우를 제외하고 자연스러운 한국어로 바꾼다.
- 한 문장에 여러 주장과 수치를 과도하게 넣지 않는다.
- 결과 설명은 관찰, 근거 수치, 해석 순으로 작성한다.

#### 완료 기준

- 주요 용어 목록과 본문의 실제 표기가 일치한다.
- 동일 개념에 두 개 이상의 번역이 혼용되지 않는다.
- 초록과 결론에 연구노트식 표현이 남아 있지 않는다.

### 3.6 표, 그림, 수식 및 참고문헌 형식 정리

#### 표와 그림

- Caption만 읽어도 비교 대상, 지표 및 표본 범위를 알 수 있게 한다.
- `best observed`, `CP-SAT incumbent`, `proven optimal`의 의미를 필요한 표에서 설명한다.
- 표와 그림의 글꼴, 소수점 자릿수, 기호 및 단위를 통일한다.
- 본문에서 모든 표와 그림을 순서대로 참조한다.

#### 수식과 notation

- 모든 집합, 매개변수, 결정변수를 처음 사용하기 전에 정의한다.
- $r_i$, $r_f$ 및 $r_q$의 관계를 명시한다.
- CP-SAT의 시간 정수화는 다음과 같이 정확하게 기술한다.

  > 모든 시간값을 가장 가까운 0.01 단위로 반올림한 뒤 100배하여 정수로 변환한다.

- MILP의 big-$M$ 제약과 CP-SAT enforcement-literal 제약의 대응을 간결하게 설명한다.

#### 참고문헌 및 제출 형식

- 대한산업공학회지 참고문헌 형식으로 통일한다.
- 본문의 모든 인용이 참고문헌에 있고, 참고문헌의 모든 항목이 본문에서 인용되는지 확인한다.
- 저자명, 소속, 교신저자 이메일, acknowledgements, funding 및 data availability의
  placeholder를 확인한다.
- 익명 심사용 원고에서는 저자명과 소속을 제거한다.
- 생성형 AI 사용 명시의 위치와 문구를 투고 지침에 맞춘다.

## 4. 수정 작업 순서

### 1단계: 논리 구조 수정

- 제목 및 문제 명칭 확정
- Contribution 세 가지로 축소
- 서론과 결론의 story 통일
- RL 분석의 위치와 비중 축소

### 2단계: 문제 정의와 notation 수정

- Release time 및 soft due date 정의 명확화
- Time-window 표현 전수 점검
- 모든 기호의 최초 정의 확인
- MILP와 CP-SAT 설명 보완

### 3단계: 결과 절 재구성

- 해 품질과 실행시간을 우선 제시
- CP-SAT 상태별 결과 구분
- 핵심 component ablation 강조
- RL 및 DQN 세부 내용 축소 또는 부록 이동

### 4단계: Writing 및 형식 교정

- 한글·영문 용어 통일
- 연구노트식 문장 교정
- 표·그림 caption 정리
- 참고문헌 및 대한산업공학회지 형식 적용

### 5단계: 최종 검증

- 수치와 원 실험 결과 대조
- CP-SAT 상태와 주장 범위 대조
- 인용 및 교차참조 확인
- Placeholder 제거
- 익명 원고와 title page 분리 확인
- XeLaTeX 2회 컴파일
- PDF 전체 페이지 육안 점검

## 5. 최종 점검 체크리스트

- [ ] Contribution이 세 가지로 정리되어 있다.
- [ ] RL selector는 보조적인 ablation 결과로 제시된다.
- [ ] 현재 문제를 일반적인 time-window problem으로 잘못 부르지 않는다.
- [ ] Release time과 soft due date가 명확하게 정의되어 있다.
- [ ] $r_i$, $r_f$, $r_q$, $\bar d_q$, $T_q$가 최초 사용 전에 정의되어 있다.
- [ ] CP-SAT optimal과 incumbent가 명확히 구분되어 있다.
- [ ] 대형 문제에 near-optimal이라는 표현을 사용하지 않는다.
- [ ] Best-known의 사용 근거가 없으면 `비교 방법 가운데 관측된 최선해`로 쓴다.
- [ ] 결과 절이 품질·시간, CP-SAT gap, 핵심 component 순서로 구성되어 있다.
- [ ] Descent, guided operator 및 restart의 기여가 명확하게 보인다.
- [ ] Q-learning 및 DQN이 논문의 중심처럼 보이지 않는다.
- [ ] 한글 물류 용어와 영문 알고리즘 용어의 사용이 일관된다.
- [ ] 표와 그림의 caption에 지표 및 표본 범위가 명시되어 있다.
- [ ] 수식 notation과 본문 설명이 일치한다.
- [ ] 참고문헌이 대한산업공학회지 형식에 맞는다.
- [ ] 교신저자 이메일 등 placeholder를 모두 확인했다.
- [ ] 익명 심사용 원고에 저자 정보가 없다.
- [ ] 생성형 AI 사용 명시가 올바른 위치에 있다.
- [ ] 최종 PDF에 컴파일 오류, 잘린 표·그림 또는 깨진 수식이 없다.

## 6. 수정 후 지도교수 전달 자료

수정본을 전달할 때 다음 세 파일을 준비한다.

1. 수정된 한글 논문 PDF
2. 주요 수정사항을 1페이지 이내로 정리한 change summary
3. 필요한 경우 수정 위치를 표시한 비교본 또는 tracked-changes 문서

수정본 전달 메일에서는 계획을 장황하게 반복하기보다, 피드백을 반영한 핵심 변경사항과
추가 확인이 필요한 부분만 간단히 설명한다.

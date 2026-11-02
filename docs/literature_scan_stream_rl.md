# 문헌 조사: 연속 도착 크로스도크 디스패칭과 학습 기반 방법 (research/rl)

조사일 2026-10-12 (3.4·3.5절은 2026-11-02 추가). 웹 검색(제목·초록·검색 요약 수준)으로 찾은 결과이며, **원문의 모델 절까지 확인한 문헌은 없다**.
"확인 수준" 열을 반드시 같이 볼 것. 논문에 인용하기 전에 원문 대조가 필요하다
(JKIIE 때 Nowak & Puladi 2025가 제목만 보고 판단했다가 모델 절에서 뒤집힌 전례가 있음).

확인 수준: A = 출판 정보와 초록 확인, B = 검색 요약에서만 확인, C = 존재 자체가 불확실(서지 미확인)

## 1. 크로스도크 문헌

### 1.1 학습을 쓰는 크로스도크 연구 (모두 오프라인 최적화 안의 보조 요소)

| 문헌 | 문제 | 학습의 역할 | 본 연구와 차이 | 확인 |
|---|---|---|---|---|
| Shahmardan & Sajadieh (2020), C&IE | 병행 트럭(부분 하역) 다중 도어, makespan | RL이 SA의 이웃 구조 선택 | 정적·오프라인. 본 연구의 기반 논문 | A |
| Li, Hao & Wu (2024), EJOR | 크로스도크 도어 배정 | Q-learning 기반 strategic oscillation | 정적 배정 문제, 트럭 흐름 없음 | A |
| Q-learning ALNS, 혼합 모드 도어 (arXiv 2412.09090, 2024) | 도어 모드·트럭 배정·일정, 지연+makespan+이동거리 | Q-learning이 ALNS 연산자 선택 | 정적·오프라인 | A |
| Neural branch-and-price (C&OR, 2024) | 도어 일정·트럭 순서 | 심층망이 pricing 문제 보조 | 정확해법 안의 학습 | A |

정리: 크로스도크에서 학습은 **정적 문제를 푸는 탐색기의 연산자 선택이나 정확해법 보조**로만 쓰였다.
트럭이 실시간으로 들어오는 상황에서 **결정 정책 자체를 학습한 연구는 찾지 못했다**.

### 1.2 동적·온라인 크로스도크 (학습 없음)

| 문헌 | 내용 | 확인 |
|---|---|---|
| Larbi et al. (2011), C&OR, "Scheduling cross docking operations under full, partial and no information on inbound arrivals" | 도착 정보 수준별 일정. 정보가 없으면 우선순위 규칙으로 온라인 일정 | A |
| Konur & Golias (2013), C&IE / TR-E | 도착 시간창만 아는 입고 트럭 일정, 비관·낙관 전략, 이층 최적화 + GA | A |
| Gallo et al. (2022), EURO J. Transportation and Logistics | 시나리오 트리 확률적 GA, 실제 271대 사례 | B |
| Torbali & Alpan (2023), Supply Chain Analytics 3:100028 | 입고·출고 도어 각 1개의 실시간 다중 에이전트 트럭 일정(규칙 기반 에이전트, RL 아님). 박사논문에서 다중 도어(2–20) 확장 | A |
| Inbound truck scheduling for workload balancing (Mathematics, MDPI, 2025) | 도어가 비면 실시간 재일정 | B |
| Dynamic vs. static optimization of crossdocking operations (Optimization Online, 2014) | 트레일러 도착마다 도어 배정 재검토, 정적 대 동적 비교 | B |
| Rolling horizon bi-objective dynamic truck dispatching with cross-dock door assignment (ResearchGate, 2026) | 롤링 호라이즌으로 새 요청마다 휴리스틱 재계획, 실무 탐욕 규칙보다 좋음 | **C** (서지 확인 실패) |

정리: 동적 크로스도크는 **우선순위 규칙, 롤링 호라이즌 재최적화, 규칙 기반 다중 에이전트**로 다뤄져 왔다.
병행 트럭(부분 하역 → 운송 트럭 전환)과 끝없는 연속 도착을 결합한 연구는 찾지 못했다.

## 2. 유사 문제에서의 학습 기반 디스패칭

| 문헌 | 문제 | 방법 | 본 연구에 주는 시사점 | 확인 |
|---|---|---|---|---|
| Zhang et al. (2020), NeurIPS, "Learning to Dispatch for JSSP" | 작업장 일정 | GNN(분리 그래프) + PPO로 우선순위 규칙 학습, 더 큰 인스턴스로 일반화 | 제안 2(그래프 정책망) 근거. 규모 일반화가 핵심 기여였음 | A |
| Hybrid intelligence for dynamic JSSP (arXiv 2201.00548, 2022) | 동적 작업장 | 어텐션 그래프 표현 + D3QN이 디스패칭 규칙 선택 | 규칙 선택형 DRL의 비교 대상 | A |
| Container port truck dispatching, Real2Sim DRL (EJOR 315(1), 2024) | 항만 트럭 디스패칭 | 실제 데이터 기반 시뮬레이터 + DRL | 크로스도크와 가장 가까운 운영 디스패칭 DRL | A |
| 항만 MARL: 야드 크레인 재배치(2025), IGV 작업·충전(C&OR 2025), 안벽 크레인 MAPPO + 메타휴리스틱(2025) | 컨테이너 터미널 | 다중 에이전트 DRL | 물류 터미널 MARL의 선례. 크로스도크 적용은 없음 | B |
| Liu et al. (Amazon, arXiv 2503.09755, 2025), DRMARL | 로봇 분류센터의 목적지-슈트 배정 | 분포 강건 MARL + 상황 밴딧으로 최악 분포 추정 | **가장 가까운 MARL 선례**(목적지 단위 에이전트, 유입률 변동). 재순환 평균 80% 감소(시뮬레이션) | A |
| Tote 처리 로봇 주문 처리 (arXiv 2605.08758, 2026) | 창고 | 주문·토트·로봇 3종 에이전트 MAPPO | 이질적 에이전트 분해 예시 | B |
| RWARE에서 QMIX 대 IPPO 비교 (2025) | 창고 로봇 | 가치 분해가 독립 학습보다 크게 좋지만 튜닝 부담, 소규모에서만 유망 | MARL 확장성 위험의 근거 | B |

## 3. 방법론 문헌 (제안한 RL 방향의 이론적 배경)

### 3.1 Rollout, 근사 정책 반복, 증류 (현재 RL-API의 계보)

| 문헌 | 내용 | 확인 |
|---|---|---|
| Bertsekas, *Rollout, Policy Iteration, and Distributed RL* (Athena, 2020) | rollout = 기본 정책에서 한 번의 정책 개선, 근사 정책 반복 = rollout의 반복 | A |
| Bhattacharya, Bertsekas et al. (arXiv 2011.04222, 2020), Multiagent rollout and policy iteration for POMDP | 에이전트 하나씩 순차 rollout(계산량이 에이전트 수에 선형), rollout 결정을 신경망에 학습시켜 다음 반복의 기본 정책으로 사용 | A |
| Goodson, Ohlmann & Thomas (2013), Operations Research 61(1) | 확률적 수요 VRP의 rollout 정책. 롤링 호라이즌과 고정 경로 정책보다 좋음 | A |
| Goodson, Thomas & Ohlmann (2016), Transportation Science 50(2) | 재보충 기반 rollout | A |
| Offline–online ADP for dynamic VRP with stochastic requests (Transportation Science, 2017 이후) | 오프라인 가치함수 근사 + 온라인 rollout 결합, VFA 기반 rollout의 정책 개선 보장 | A (저자 목록 미확인) |
| Rusu et al. (2016), ICLR, Policy distillation | 교사 정책을 학생 망으로 증류 | A |

시사점: 본 연구의 "Rollout → DAgger 증류"는 Bertsekas 계열 근사 정책 반복의 한 단계이고, 2020년 multiagent rollout 논문이 거의 같은
구조(rollout 결정 → 신경망 → 다음 반복의 기본 정책)를 쓴다. 따라서 **방법 자체의 새로움은 약하고**, 새로움은 이 계열을 연속 도착
병행 트럭 크로스도크에 처음 적용한 점과 정적 최적화(VAA-GILS·CP-SAT 사이클 최적해)의 한계를 정량화한 점에 둬야 한다.
Offline–online ADP는 제안 1(가치망으로 rollout 대체)의 직접 선례다.

### 3.2 MCTS·AlphaZero 계열 일정 문제 (제안 1)

| 문헌 | 내용 | 확인 |
|---|---|---|
| Runarsson et al. (arXiv 1210.0374, 2012), Pilot, rollout and MCTS for JSSP | rollout·MCTS를 작업장 일정에 적용 | A |
| Rinciog et al. (2020), CPSL, Sheet-metal production scheduling using AlphaGo Zero | AlphaGo Zero를 생산 일정에 적용 | B |
| Kemmerling, Abdelrazeq & Schmitt (2024), ICAART, Neural MCTS for JSSP | 탐색의 평가 단계가 가장 중요, 학습 가치로 노드 초기화 + rollout 평가 조합이 최선 | A |
| Czech et al. (2021), ICAPS, Monte-Carlo graph search for AlphaZero | 하위 트리 정보 공유 | A |

시사점: AlphaZero식 방법은 정적 일정 문제에는 선례가 있으나, **연속 도착 물류 디스패칭에 적용한 사례는 찾지 못했다**.
Kemmerling et al.의 "학습 가치 + rollout 평가 혼합" 결과는 본 연구의 Rollout을 가치망과 섞는 설계를 지지한다.

### 3.3 MARL 기여도 분배

| 문헌 | 내용 | 확인 |
|---|---|---|
| Foerster et al. (2018), AAAI, COMA | 한 에이전트의 행동만 바꾼 반사실 기준선 | A |
| MAPPO 계열 | 중앙 가치망(전역 입력) + 분산 정책. IPPO는 비정상성 문제 | A |
| Transformer 기반 MARL 반사실 기준선 (arXiv 2511.13103, 2025) | 기존 반사실 기법은 에이전트 수에 확장성이 나쁘고 MAPPO 상태가치 critic과 맞지 않아 새 기준선 제안 | B |

시사점: COMA는 반사실 기준선을 **학습된 Q로 근사**한다. 본 시뮬레이터는 상태 복제(fork)로 반사실을 **직접 시뮬레이션**할 수 있어
근사가 필요 없다. 이 점은 MARL 제안의 방법론 차별점이 될 수 있다(유사 선례는 이번 검색에서 찾지 못함).

### 3.4 추가 조사 (2026-11-02): Rollout 증류, 미래 표본 rollout, 사후 모방

현재 최선 방법(Rollout, RL-API)과 구조가 비슷한 연구. 같은 확인 수준 기준(A/B/C)을 쓴다. 3.1에 이미 있는 문헌은 뺐다.

| 문헌 | 내용 | 본 연구와의 관계 | 확인 |
|---|---|---|---|
| Mukunda, Somani & Malaiya (SSRN 7076169, 2026), Sample-efficient adaptive heuristic selection via offline rollout distillation for dynamic warehouse order dispatching | 시뮬레이션한 교대의 결정 상태마다 후보 규칙을 짧은 구간 rollout으로 평가하고, 비용 벡터로 gradient boosting 순위 모형을 학습. 납기·신선도 제약 창고 주문 디스패칭 | **RL-API와 가장 가까운 구조**(rollout 평가 → 빠른 정책 증류). 차이: 규칙 선택기 대 (트럭, 도어, 목적지) 직접 선택, 오프라인 1회 대 DAgger 반복. 투고 시 필수 인용·비교 | B |
| Ulmer, Goodson, Mattfeld & Hennig (2019), Transportation Science 53(1), 185–202, Offline–online ADP for dynamic VRP with stochastic requests | 오프라인 가치함수 근사 + 온라인 rollout. 실시간 계산량을 줄이면서 예측(공간·시간 예상)을 반영 | 3.1의 "Offline–online ADP" 서지 확정. 로드맵 제안 1(가치망 절단 rollout)의 직접 선례 | A |
| Ulmer, Mattfeld et al., A rollout algorithm for vehicle routing with stochastic customer requests (Springer, Operations Research Proceedings 장) | 미래 요청 표본 + cheapest insertion 기본 정책으로 남은 비용 추정 | 본 연구 Rollout과 같은 구조(FCFS-VAA = 기본 정책, `fork` = 미래 표본) | B |
| The dynamic dispatch waves problem for same-day delivery (ResearchGate 308962698; 학술지·저자 확인 필요) | 동적 rollout 정책의 기대 비용이 최적 사전(a priori) 계획 이하임을 증명 | 사이클 계획 대 상태 기반 정책 결과(stream_rl_research.md 5.4)의 이론적 근거 후보 | B |
| A rollout algorithm framework for heuristic solutions to finite-horizon stochastic dynamic programs (EJOR, S0377221716307925; 저자 확인 필요) | 유한 구간 확률 DP의 rollout 일반 틀, 확률적 배낭 문제 예시 | 방법론 절의 정의 출처 | B |
| Dynamic dispatching and routing with random demand (arXiv 2107.13058) | 순차적 불확실 주문의 배차를 ADP rollout으로 | 같은 계열 | B |
| Baty et al. (arXiv 2304.00789, 2023), Combinatorial optimization enriched ML for dynamic VRPTW (EURO Meets NeurIPS 2022 동적 트랙 1위, Kléopatra 팀) | 신경망 + prize-collecting VRPTW 최적화 층, 미래를 아는 해를 모방하는 구조적 학습 | **대조 사례.** 같은 계열(사후 교사·COAML, 5.7–5.8)이 본 문제에서는 실패. 사후 편향이 큰 묶음 적재 타이밍 문제에서 사후 모방이 통하지 않는 조건을 논의할 근거 | B |
| EURO Meets NeurIPS 2022 2위 OptiML (Wouda et al., GitHub N-Wouda/Euro-NeurIPS-2022) | 미래 요청 시뮬레이션 + 배송 연기 | Rollout에 가까운 접근. 1위 팀 발표에 따르면 상위 5개 방법 차이 약 4% → 방법을 바꿔도 Rollout 수준에서 정체한 본 결과와 비슷한 양상 | B |
| Semiconductor fab scheduling with self-supervised and RL (arXiv 2302.07162, WSC 2023) | 로트 수에 불변인 self-attention 전역 디스패처 | 규모 일반화(L 평가) 설계 참고 | B |
| RL based dispatching solutions in semiconductor manufacturing: a literature review on validation and deployment (2025, T&F 10.1080/21693277.2025.2582472) | 모방학습은 초기 정책 확보에 그친다는 정리, 기본 규칙보다 국소적으로 좋을 때만 켜는 배포 사례 | RL-API가 교사 이득의 2/3만 얻는 한계와 같은 지적 | B |

시사점: rollout → 빠른 정책 증류는 창고 디스패칭(2026)에 거의 같은 구조의 선례가 있다. 방법의 새로움은 더 약해졌고,
기여는 문제 설정, 정적 최적화 한계 정량화, 정보 가치·최적화 격차 분해와 사후 학습이 실패하는 조건에 둬야 한다.

### 3.5 추가 조사 (2026-11-02): 예측 정보, 출발 시점(합적), MARL 배차

"비정상 목적지별 수요 + 예측 정보 + 출발 시점 결정" 실험 설계의 배경.

| 문헌 | 내용 | 본 연구와의 관계 | 확인 |
|---|---|---|---|
| A machine learning approach to shipment consolidation (ResearchGate 325925137; 학술지·저자 확인 필요) | 시간·수량 혼합(TQ) 합적 정책의 최적 매개변수와 DRL·모방학습 비교 | 출발 시점 행동을 넣을 때 TQ 규칙 비교 대상 | B |
| Learning algorithms for regenerative stopping problems with applications to shipping consolidation (arXiv 2105.02318) | 합적을 재생 정지 문제(연속 시간 MDP)로, 신경망 정책이 출발 시점 결정 | 출발 시점 결정의 학습 선례 | B |
| Optimal outbound shipment policy for an inventory system with advance demand information (EJOR, 2025, S0377221725000451) | 사전 수요 정보 아래 출고 정책의 구조, 3단계 임계 휴리스틱, 사후 결정 상태 가치 DRL | 예측(사전 정보) + 출발 시점의 결합 선례 | B |
| Real-time integrated dispatching and idle fleet steering with DRL for a meal delivery platform (arXiv 2501.05808, 2025) | 단기 수요 예측을 RL 배차·유휴 차량 이동의 입력으로 쓰는 predict-then-optimize | 예측 특징을 RL 정책에 넣는 설계 참고 | B |
| A smart predict-then-optimize framework for vehicle rebalancing (ResearchGate 401296666) | 예측 모형을 결정 손실로 학습 | COAML 중단 판단(5.8)과 같은 문제의식 | B |
| 택배 허브 운영 일정용 도착 예측 (arXiv 2602.03135, 2026) | 허브 도착 예측과 자원 배정, 운영 일정용 예측 연구가 적다고 언급 | 허브 예측 정보의 현실성 근거 | B |
| DeepFreight (arXiv 2103.03450) | 트럭 배차(QMIX) + 화물 매칭(MIP) 분해 | MARL + 최적화 결합 선례 | B |
| Ride-hailing MARL: mean-field MARL (arXiv 1901.11454), CoRide (arXiv 1905.11353), 분포 매칭 MARL (arXiv 1910.02591) | 파라미터 공유, 수요-공급 분포를 반영한 장기 가치 | 목적지 에이전트 설계 참고 | B |
| Triple-BERT: Do we really need MARL for order dispatch on ride-sharing platforms? (ICLR 2026) | 배차는 본질적으로 중앙집중 문제, 단일 에이전트 방법이 더 낫다는 주장 | **MARL 반론.** 로드맵의 "왜 MARL인가" 위험의 근거 | B |
| Truck scheduling model in the cross-docking terminal by using multi-agent system and SRT (IJACSA 12(7), 2021) | 입고·출고 스케줄러·자재 처리 3종 규칙 기반 에이전트 | 크로스도크 다중 에이전트(학습 없음) 추가 사례 | B |

시사점: 크로스도크·허브에서 목적지별 수요 예측을 RL 디스패처 입력으로 쓰고 출발 시점까지 결정한 연구는 찾지 못했다.
MARL은 같은 정보를 보는 중앙 정책보다 나아야 의미가 있다(Triple-BERT 반론).

## 4. 공백(gap)과 본 연구의 위치

검색 범위 안에서 확인한 공백

1. **연속 도착 크로스도크의 학습 기반 디스패칭 정책**: 크로스도크 학습 연구는 모두 정적 문제의 탐색 보조였다(1.1).
2. **병행 트럭 + 연속 도착**: 동적 크로스도크 연구는 고정 역할 트럭을 전제한다(1.2).
3. **크로스도크 MARL**: 규칙 기반 다중 에이전트(Torbali & Alpan 2023)만 있고, 다중 에이전트 강화학습은 항만·분류센터에만 있다(2).
4. **정적 최적화 방법을 연속 흐름에 적용했을 때의 한계 정량화**: 롤링 호라이즌 연구는 탐욕 규칙과만 비교하고, 사이클별 최적해와
   상태 기반 정책을 비교한 연구는 찾지 못했다.

주의할 점

- 방법론(rollout + 증류)은 Bertsekas 계열에서 확립된 것이므로 "새 RL 알고리즘"으로 주장하면 안 된다.
- 가장 가까운 비교 대상: 롤링 호라이즌 재최적화(1.2), Real2Sim 항만 디스패칭 DRL, Amazon DRMARL. 외국 학술지 투고 시
  롤링 호라이즌 기준선이 필요하다는 기존 다음 단계(stream_rl_research.md 6절 5번)를 다시 확인했다.
- 확인 수준 C인 2026 롤링 호라이즌 논문은 서지부터 확인해야 한다. 존재하면 가장 직접적인 경쟁 연구이다.

## 5. 원문 대조 우선순위

1. Rolling horizon bi-objective dynamic truck dispatching with cross-dock door assignment (2026): 서지, 도착 과정, 트럭 유형
2. Torbali & Alpan (2023)과 박사논문: 다중 도어 실시간 모형, 비교 규칙
3. Container port truck dispatching Real2Sim DRL (EJOR 2024): 상태·행동 설계, 기준선
4. Liu et al. DRMARL (2025): 에이전트 정의, 보상, 확장성
5. Bhattacharya et al. multiagent rollout (2020): 본 연구 RL-API와의 차이
6. Offline–online ADP (Ulmer et al. 2019, Transportation Science): 가치함수 근사 형태 (서지는 3.4에서 확정)
7. (2026-11-02 추가) Mukunda et al. 2026 (SSRN): 증류 방식, 비교 대상, 규모. RL-API와의 차이를 정리할 1순위
8. (2026-11-02 추가) Baty et al. 2023 (EURO-NeurIPS 1위): 사후 모방이 통한 조건과 본 문제와의 차이
9. (2026-11-02 추가) Dynamic dispatch waves: rollout ≥ a priori 증명의 가정

## 출처

- https://www.sciencedirect.com/science/article/abs/pii/S0360835219306035
- https://www.sciencedirect.com/science/article/abs/pii/S0377221723005520
- https://arxiv.org/html/2412.09090v1
- https://www.sciencedirect.com/science/article/abs/pii/S0305054824000765
- https://www.sciencedirect.com/science/article/abs/pii/S0305054810002182
- https://ktisis.cut.ac.cy/entities/publication/f2fde6be-ed86-4baf-b2f3-e96c24cba690
- https://scholarsmine.mst.edu/engman_syseng_facwork/1525
- https://doaj.org/article/1e976e2204cc4169908e84f2b9e8783b
- https://hal-hprints.archives-ouvertes.fr/G-SCOP_DOME2S/hal-04350024v1
- https://www.mdpi.com/2227-7390/13/15/2533
- https://optimization-online.org/2014/05/4346/
- https://www.researchgate.net/publication/399944905_A_rolling_horizon_based_bi-objective_optimization_approach_for_dynamic_truck_dispatching_with_cross-dock_door_assignment
- https://arxiv.org/pdf/2010.12367
- https://arxiv.org/pdf/2201.00548
- https://ideas.repec.org/a/eee/ejores/v315y2024i1p161-175.html
- https://www.sciencedirect.com/science/article/abs/pii/S1474034625011644
- https://www.sciencedirect.com/science/article/abs/pii/S0305054825002175
- https://www.sciencedirect.com/science/article/abs/pii/S0952197625000211
- https://arxiv.org/abs/2503.09755
- https://arxiv.org/pdf/2605.08758
- https://www.themoonlight.io/es/review/marl-warehouse-robots
- https://web.mit.edu/dimitrib/www/Rollout_Complete%20Book.pdf
- https://arxiv.org/pdf/2011.04222
- https://ideas.repec.org/a/inm/oropre/v61y2013i1p138-154.html
- https://ideas.repec.org/a/inm/ortrsc/v50y2016i2p591-607.html
- https://pubsonline.informs.org/doi/fpi/10.1287/trsc.2017.0767
- https://arxiv.org/pdf/1511.06295
- https://arxiv.org/pdf/1210.0374
- https://publikationen.bibliothek.kit.edu/1000120053
- https://www.scitepress.org/publishedPapers/2024/123117/pdf/index.html
- https://ojs.aaai.org/index.php/ICAPS/article/view/15952
- https://arxiv.org/html/1705.08926v3
- https://arxiv.org/pdf/2511.13103

- (2026-11-02 추가)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7076169
- https://pubsonline.informs.org/doi/fpi/10.1287/trsc.2017.0767
- https://link.springer.com/chapter/10.1007/978-3-319-20863-3_16
- https://www.researchgate.net/publication/308962698_The_Dynamic_Dispatch_Waves_Problem_for_Same-Day_Delivery
- https://www.sciencedirect.com/science/article/abs/pii/S0377221716307925
- https://arxiv.org/pdf/2107.13058
- https://ar5iv.labs.arxiv.org/html/2304.00789
- https://github.com/N-Wouda/Euro-NeurIPS-2022
- https://batyleo.github.io/assets/pdf/roadef2023_pres.pdf
- https://arxiv.org/pdf/2302.07162
- https://www.tandfonline.com/doi/full/10.1080/21693277.2025.2582472
- https://www.researchgate.net/publication/325925137_A_Machine_Learning_Approach_to_Shipment_Consolidation
- https://arxiv.org/html/2105.02318
- https://www.sciencedirect.com/science/article/pii/S0377221725000451
- https://arxiv.org/html/2501.05808v1
- https://www.researchgate.net/publication/401296666_A_smart_predict-then-optimize_framework_for_vehicle_rebalancing_problem
- https://arxiv.org/pdf/2602.03135
- https://arxiv.org/pdf/2103.03450
- https://arxiv.org/pdf/1901.11454
- https://arxiv.org/pdf/1905.11353.pdf
- https://arxiv.org/pdf/1910.02591.pdf
- https://iclr.cc/virtual/2026/oral/10007021
- https://thesai.org/Publications/ViewPaper?Volume=12&Issue=7&Code=IJACSA&SerialNo=15

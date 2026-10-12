# 문헌 조사: 연속 도착 크로스도크 디스패칭과 학습 기반 방법 (research/rl)

조사일 2026-10-12. 웹 검색(제목·초록·검색 요약 수준)으로 찾은 결과이며, **원문의 모델 절까지 확인한 문헌은 없다**.
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
6. Offline–online ADP (Transportation Science): 저자, 가치함수 근사 형태

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

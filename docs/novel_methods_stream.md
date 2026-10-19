# 연속 도착 크로스도크: 더 참신한 방법 조사 (2026-10-19)

확인 수준: 웹 검색 결과(제목·초록·요약) 수준이다. 원문은 아직 확인하지 않았다. 원문이 필요한 논문은 7절에 정리했다.

## 0. 출발점 (이 브랜치의 실험 사실)

- Rollout 계산을 4배로 늘려도(Rollout-32: 표본 32, 구간 2 SLA) 기존 Rollout과 차이가 없다(S −0.3%, M +2.1%, 중간 결과).
  FCFS를 기본 정책으로 한 번 개선하는 방식은 한계에 도달했다.
- 작은 유한 인스턴스(트럭 6–8대)에서 사후 최적(CP-SAT)이 FCFS·Rollout보다 15–25% 좋다. 몇 개 인스턴스의 예비 결과이고 본 실험은 대기 중이다.
- 학습 정책의 이득은 주로 보류(HOLD) 같은 비선형 판단에서 나온다.
  튜닝한 규칙과 선형 정책은 보류를 쓰지 않는다.
- PPO는 보상 잡음 때문에 실패했다.
- 롤링 호라이즌은 남은 화물이 미래 운송 트럭을 얼마나 기다린다고 볼지(종료 지연)에 결과가 크게 좌우된다.
- 구조적 특징: 도착 과정은 정책과 무관한 외생 변수다.
  시뮬레이터는 같은 미래를 고정해 반사실을 계산할 수 있다(fork + 공통 난수, oracle fork).
  미래를 모두 아는 사후 최적 모형(hindsight.py)도 이미 있다.

마지막 특징 때문에 아래 1·2·3번 계열은 이 문제에 특히 잘 맞는다.

## 1. 사후 학습 (Hindsight Learning, Exo-MDP)

- 문헌: Sinclair, Frujeri, Cheng, Swaminathan, "Hindsight Learning for MDPs with Exogenous Inputs", ICML 2022.
  - 불확실성이 외생 입력(수요·도착)뿐인 문제를 Exo-MDP로 정의한다.
  - 관측된 외생 경로로 과거 결정을 다시 풀어 얻은 사후 최적 행동을 학습 신호로 쓴다.
  - 사후 최적과 진짜 최적의 차이("hindsight bias")가 자원 배분 문제에서는 작다고 보인다.
  - 실제 클라우드 VM 배치 데이터에서 현행 휴리스틱을 꾸준히 이긴 유일한 방법이었다고 보고한다.
- 적용: 상태마다 같은 실제 미래로 각 행동의 사후 비용을 계산한다.
  계산은 oracle fork 또는 사건 정렬 CP-SAT로 한다.
  그 비용으로 정책을 학습한다(분류, 또는 비용 민감 회귀).
  현재 DAgger 교사(Rollout)를 사후 교사로 바꾸는 셈이다.
- 위험: 사후 교사는 미래를 알기 때문에 온라인에서 쓸 수 없는 보류를 가르칠 수 있다.
  - 사건 정렬 모형으로 행동 공간을 맞춘다.
  - 표본 미래 여러 개의 사후 비용을 평균한다. 이는 Bent & Van Hentenryck 계열 온라인 예측 알고리즘의 consensus/regret과 같은 구조이며, 검색으로는 원문을 찾지 못했다.
  - hindsight bias를 측정해 보고한다. 측정에는 oracle 결과와 사후 최적 실험을 쓴다.
- 참신성: 크로스도크와 병행 트럭 문제에 사후 학습을 쓴 사례는 찾지 못했다.
  또 시뮬레이터와 정확히 일치하는 CP-SAT 사후 교사를 붙이는 점이 다른 연구와 구분된다.

## 2. 최적화 결합 학습 정책 (COAML, structured learning)

- 문헌:
  - Baty, Jungel, Klein, Parmentier, Schiffer, "Combinatorial Optimization-Enriched Machine Learning to Solve the Dynamic Vehicle Routing Problem with Time Windows", Transportation Science.
    EURO–NeurIPS 2022 동적 VRP 대회 1위 방법이다.
    신경망이 결정론적 최적화 문제의 매개변수를 예측하고, 고전 풀이기가 그 문제를 푼다.
    미래를 아는 해(anticipative solution)를 모방해 학습했다고 알고 있지만 검색으로는 확인하지 못했다(원문 확인 필요).
  - Schiffer, Hoppe, Su, Bouvier, Parmentier, "Combinatorial Optimization Augmented Machine Learning" (arXiv 2601.10583, 2026). 다단계 확률 최적화에서 이를 모방 학습으로 정리한 서베이다.
- 적용: 롤링 CP-SAT(rolling.py)의 매개변수를 신경망이 상태에 따라 예측한다.
  - 예측 대상: 종료 지연(현재는 상수 하나), 목적지별 미래 운송 트럭 도착 기대, 묶음별 가치.
  - 학습: 사후 최적 일정과의 Fenchel–Young 손실, 또는 1번의 사후 비용.
- 근거: 롤링 호라이즌이 종료 지연 하나에 크게 흔들린다는 관찰이 이 결합의 필요성을 직접 보여준다.
  CP-SAT의 실행 가능성과 학습한 미래 판단을 함께 가져간다.
- 참신성: 크로스도크에서 최적화 계층이 들어간 학습 정책은 찾지 못했다. 이 문제에서 가장 차별화되는 후보다.

## 3. 외생 구조를 쓰는 낮은 분산 정책 경사 (PPO 실패 원인 대응)

- 문헌:
  - Dai & Gluzman, "Queueing Network Controls via Deep Reinforcement Learning" (arXiv 2008.01644).
    장기 평균 비용 PPO에 할인 상대가치, 재생 시뮬레이션, AMP 제어변량을 쓴다.
    분산 감소에 가장 큰 효과는 할인율이었다.
  - Sinclair et al. 2022의 "hindsight control variates".
  - 외생 경로를 관측하는 시뮬레이터에서 같은 시나리오로 반사실 평가를 하는 최근 연구들(arXiv 2605.14297, 2601.20694).
- 적용: RL-API를 초기값으로 미세조정한다.
  상태를 복제해 공통 난수로 행동 간 이점을 직접 시뮬레이션한다.
  이것을 장기 평균 비용 actor-critic의 기준선으로 쓴다(로드맵의 제안 2를 구체화).
- 판정: 미세조정 결과가 교사(Rollout)를 넘으면 순수 RL의 기여가 된다. 넘지 못하면 PPO 실패 원인을 확정하는 근거가 된다.

## 4. 탐색 기반 정책 반복 (Gumbel AlphaZero 계열)

- 문헌: Pirnay, Göttl, Burger, Grimm, "Policy-Based Self-Competition for Planning Problems", ICLR 2023.
  Gumbel AlphaZero에 과거 정책과의 자기 경쟁을 더했다.
  외판원 문제(TSP)와 job-shop에서 탐색 예산 절반으로 단일 플레이어 변형들보다 좋았다고 보고하며, 코드가 공개돼 있다.
- 적용: 정책-가치망에 짧은 MCTS를 붙이고 반복 증류한다.
  Rollout-32가 한계에 도달했으므로, 기본 정책 자체를 개선하는 반복이 필요하다는 근거가 생겼다.
- 비용: 가장 크다. 1·2번이 사후 최적과의 격차를 줄이지 못할 때의 다음 단계로 둔다.

## 5. LLM 기반 휴리스틱 진화 (해석 가능한 규칙, 강한 최신 비교 대상)

- 문헌:
  - EoH와 FunSearch: 자연어 아이디어와 코드를 함께 진화시킨다.
  - SeEvo(arXiv 2410.22657): 동적 job-shop에서 GP, GEP, DRL, 10여 개 규칙보다 좋다고 보고한다.
  - DSevolve(arXiv 2603.27628, 2026): 규칙 포트폴리오를 오프라인으로 진화시키고, 온라인에서 시뮬레이션으로 하나를 고른다. 실제 산업 데이터 기반 동적 FJSP 500개로 평가했다.
  - LLM-guided heuristic design from simulation traces(arXiv 2608.09343): 시뮬레이션 기록을 근거로 휴리스틱을 설계한다.
- 적용: 시뮬레이터를 평가기로 두고 보류 판단까지 포함한 디스패칭 코드를 LLM으로 진화시킨다.
  - 비교 대상으로서: 튜닝한 선형 규칙보다 훨씬 강한 "사람이 읽을 수 있는 규칙"이다. 심사자가 요구할 최신 비교 대상이기도 하다.
  - 기여로서: 진화된 규칙이 RL-API에 가까우면 해석 가능성 측면의 기여가 된다.
- 위험: LLM 호출 비용과 재현성. 모델과 버전을 고정하고, 진화된 코드를 공개해야 한다.

## 6. 보조 문헌 (포지셔닝용)

- "Dispatch or Hold?", Transportation Science (DOI 10.1287/trsc.2025.0149).
  음식 배달에서 지금 보낼지 묶기 위해 보류할지를 PPO로 정한다.
  보류는 도착 밀도가 낮을 때 가장 유용하다고 보고한다. 보류 결정의 동기로 인용할 수 있다.
- Xu, Mei, Wang, Ji, Zhang, "GP with delayed routing", Evolutionary Computation 2021. 결정을 미뤄 최신 정보로 판단하는 템플릿이다.
- Chen et al., IEEE TEVC 2025. 항만 트럭 동적 배차에 DRL이 보조하는 GP 앙상블 하이퍼휴리스틱을 쓴다. 가장 가까운 물류 트럭 사례다.
- 이종 그래프 트랜스포머 정책: HGT-Scheduler(arXiv 2603.06777), HetGPO(Georgia Tech, 동적 도착).
  규모 일반화(E3)용 정책망 몸통 후보다.

## 7. 권장 조합과 순서

| 순위 | 방법 | 겨냥 | 판정 (tuning 풀) |
|---|---|---|---|
| 1 | **사후 학습 (1)**: 사건 정렬 사후 교사 + 표본 미래 평균 | 교사 한계, 사후 최적과의 격차 | RL-API보다 3% 이상 좋으면 채택. hindsight bias 측정 |
| 2 | **COAML 롤링 정책 (2)**: 신경망이 CP-SAT 매개변수 예측 | 롤링 호라이즌의 종료 지연 민감도, 실행 가능성 | 튜닝한 롤링 호라이즌·Rollout보다 좋으면 핵심 기여 |
| 3 | **LLM 진화 규칙 (5)** | 강한 해석 가능 비교 대상 | 튜닝한 규칙보다 좋고 RL-API와의 차이를 보고 |
| 4 | 공통 난수 이점 미세조정 (3) | PPO 실패 원인 | 교사를 넘는지 |
| 5 | Gumbel AlphaZero 반복 (4) | 1·2가 실패할 때 | 2세대가 Rollout보다 3% 이상 좋은지 |

논문 서사 후보: "외생 도착 구조 + 시뮬레이터와 정확히 일치하는 사후 최적 모형 → 사후 교사로 학습한 정책(1)과 최적화 계층 정책(2)".
현재 기여 3+1(scie_plan_stream.md) 가운데 방법 기여 (a)를 이것으로 바꾸거나 보강한다.

먼저 대기 중인 사후 최적 실험 결과로 정보 가치와 사후 격차를 확인해야 한다.
격차가 작으면 1·2번의 여지도 작으므로 3번(해석 가능성) 중심으로 간다.

## 8. 원문 확인이 필요한 논문 (PDF 요청 목록)

| # | 논문 | 확인할 것 |
|---|---|---|
| N01 | Sinclair et al., Hindsight Learning for MDPs with Exogenous Inputs, ICML 2022 (arXiv 2207.06272, 공개) | 알고리즘, hindsight bias 정의, 제어변량 |
| N02 | Baty et al., Transportation Science (DOI 10.1287/trsc.2023.0107; arXiv 2304.00789) | 학습 목표가 anticipative 해 모방인지, Fenchel–Young 손실 |
| N03 | Schiffer et al., Combinatorial Optimization Augmented Machine Learning (arXiv 2601.10583, 공개) | 동적 문제 분류, 모방 학습의 분포 이동 대책 |
| N04 | Dispatch or Hold?, Transportation Science (DOI 10.1287/trsc.2025.0149) | 보류 결정 설계, 비교 대상 |
| N05 | Pirnay et al., Policy-Based Self-Competition, ICLR 2023 (공개) | GAZ 설정, 계산 예산 |
| N06 | DSevolve (arXiv 2603.27628), SeEvo (arXiv 2410.22657) | LLM 진화 절차, 비용, 재현성 |
| N07 | Dai & Gluzman (arXiv 2008.01644, 공개) | 장기 평균 비용 PPO 구현 세부 |
| N08 | Bent & Van Hentenryck, 온라인 확률 조합 최적화(예측 알고리즘, consensus/regret) 원 논문 | 검색으로 서지를 찾지 못함. 서지 확인 필요 |
| N09 | Chen et al., IEEE TEVC 2025 (항만 트럭 DRL+GP) | 가장 가까운 물류 사례의 설정 |

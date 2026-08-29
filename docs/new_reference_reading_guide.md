# 신규 참고문헌 정독 가이드

이 문서는 `paper/apiems2026_draft.md`에 새로 추가한 참고문헌 [15]–[24]를
어떤 순서로 읽고, 각 논문에서 무엇을 확인해야 하는지 정리한 것이다. 목적은
문헌을 단순 요약하는 것이 아니라 다음 두 주장을 안전하게 뒷받침하는 데 있다.

1. 시간창, ready time, due date와 tardiness 자체는 기존 cross-dock 연구에 이미
   존재한다.
2. 본 연구의 차별점은 이 요소들을 **partial-unloading compound-truck** 모델에
   결합했다는 데 있다.

아래의 ‘현재 파악된 내용’은 출판사 서지정보와 초록을 기준으로 한 요약이다.
수식, 세부 가정, 실험설계에 관한 판단은 반드시 원문을 확인한 뒤 논문에 써야
한다.

## 1. 권장 읽기 순서

### 1순위: 신규성 경계를 직접 결정하는 논문

1. Assadi and Bagheri (2016) [16]
2. Van Belle et al. (2013) [15]
3. Bodnar et al. (2017) [17]
4. Molavi et al. (2018) [18]

이 네 편은 conventional inbound/outbound truck 문제에서 ready time, time
window, earliness/tardiness 또는 due date가 이미 사용되었음을 보여준다. 본
논문의 신규성 문구를 확정하기 전에 가장 먼저 읽어야 한다.

### 2순위: 도착정보와 불확실성의 범위를 구분하는 논문

5. Konur and Golias (2013), arrival-time uncertainty [19]
6. Konur and Golias (2013), cost-stable scheduling [20]
7. Ladier and Alpan (2016) [21]
8. Larbi et al. (2011) [22]
9. Xi et al. (2020) [23]

이 논문들은 known release time과 uncertain/unknown arrival의 차이를 설명할 때
필요하다. 현재 연구는 모든 release time을 계획 시점에 알고 있는 deterministic
offline problem이므로, 이들을 동일한 문제로 서술하면 안 된다.

### 3순위: 도어 배정 구조와 해법을 비교하는 논문

10. Rijal et al. (2019) [24]

이 논문은 integrated door assignment, mixed-service doors, ALNS와 tardiness를
함께 다루므로 문제 구조와 탐색법을 비교하기에 좋다. 다만 유연성이 truck이
아니라 dock-door에 있다는 차이가 핵심이다.

## 2. 논문별 확인 항목

### [15] Van Belle et al. (2013)

**현재 파악된 내용**

- 여러 dock에서 inbound/outbound truck을 스케줄링한다.
- truck time window와 tardiness를 고려한다.
- tabu search를 제안한다.

**원문에서 반드시 읽을 부분**

- Problem description: time window가 arrival 가능구간인지, service 가능구간인지,
  departure deadline인지 확인한다.
- Mathematical model/objective: tardiness가 어느 truck에 부과되는지와 makespan이
  목적함수에 포함되는지 확인한다.
- Door assumptions: inbound/outbound 전용 door인지, mixed-service door인지
  확인한다.
- Tabu-search neighborhood: door assignment와 truck sequence를 각각 어떻게
  변경하는지 확인한다.
- Computational study: 비교 기준, instance 규모, time-window 생성법을 기록한다.

**본 논문과 연결할 내용**

- 인용 용도: “multi-door cross-docking에서 time windows와 tardiness가 이미
  연구되었다.”
- 차이: truck은 inbound 또는 outbound 역할로 고정되며, retained destination과
  partial unloading을 갖는 compound truck은 없다.

**주의할 표현**

- 원문 확인 전에는 time window를 곧바로 본 연구의 release time과 동일하다고
  쓰지 않는다.

### [16] Assadi and Bagheri (2016)

**현재 파악된 내용**

- inbound와 outbound truck의 ready time을 명시적으로 고려한다.
- door 사이의 서로 다른 transshipment time을 사용한다.
- outbound truck의 총 earliness와 tardiness를 최소화한다.
- MILP, differential evolution, population-based simulated annealing을 제안한다.

**원문에서 반드시 읽을 부분**

- Notation과 MILP: inbound/outbound ready-time 제약을 정확히 옮겨 적는다.
- Objective: earliness와 tardiness의 정의, 가중치, due date 또는 desired departure
  time의 의미를 확인한다.
- Timing semantics: ready time이 door 진입 가능시각인지, 화물 이용 가능시각인지
  확인한다.
- Flow assumptions: product interchangeability, 임시저장 허용 여부, inbound에서
  outbound로의 선행관계를 확인한다.
- Experiments: instance 생성법과 목적함수 단위를 기록한다.

**본 논문과 연결할 내용**

- 신규성 경계를 정하는 가장 중요한 문헌이다.
- “release/ready time과 tardiness를 cross-docking에 처음 도입한다”는 주장을
  사용할 수 없다는 직접 근거다.
- 본 연구는 compound truck이 일부 화물을 보유한 채 outbound carrier가 된다는
  점과 makespan과 total tardiness를 함께 최소화한다는 점에서 구분한다.

**원문을 읽고 답해야 할 질문**

> Assadi의 ready time과 우리 모델의 $r_q$는 수학적으로 같은 역할을 하는가?

같다면 Related Work에서 이를 명시적으로 인정해야 한다. 다르다면 차이를 한
문장으로 정확히 설명해야 한다.

### [17] Bodnar et al. (2017)

**현재 파악된 내용**

- mixed-service-mode dock door를 갖는 multi-door 문제를 다룬다.
- time windows와 outbound tardiness를 고려한다.
- truck scheduling과 flexible door 사용의 효과를 분석한다.

**원문에서 반드시 읽을 부분**

- Mixed-service mode의 정확한 정의와 door mode 변경 가능 여부
- Truck time-window 제약과 tardiness 계산식
- Temporary storage와 door-to-door transfer 가정
- Exact formulation과 제안 알고리즘의 의사결정변수
- 유연한 door가 성능에 미치는 실험 결과

**본 논문과 연결할 내용**

- 공통점: multiple doors, temporal constraints, tardiness
- 차이: Bodnar의 유연성은 **door level**, 본 연구의 유연성은 **truck level**
- compound truck은 unload와 load 역할을 연속해서 수행하지만, mixed-service
  door는 서로 다른 pure truck을 양방향으로 처리한다.

### [18] Molavi et al. (2018)

**현재 파악된 내용**

- outbound truck의 due date를 hard constraint로 사용한다.
- 지연된 shipment의 penalty와 delivery cost를 최소화한다.
- shipment sorting과 FIFO loading을 고려한다.
- hybrid GA–reduced VNS를 제안한다.

**원문에서 반드시 읽을 부분**

- Hard due date 위반 시 truck이 늦게 출발하는지, 미적재 shipment가 별도의
  운송수단으로 처리되는지 확인한다.
- Truck entry time이 실제로 개별 truck별로 다른지, 있다면 어느 식에 들어가는지
  확인한다.
- Due-date adjustment window의 의미와 의사결정 여부를 확인한다.
- Shipment sorting, FIFO, temporary storage 가정을 확인한다.
- 목적함수가 truck tardiness인지 delayed-shipment cost인지 구분한다.

**본 논문과 연결할 내용**

- due date가 기존 문헌에 존재한다는 근거로 사용할 수 있다.
- 본 연구의 soft tardiness는 carrier completion time을 기준으로 연속적인 벌점을
  부과한다. Molavi의 hard due date 및 delayed-shipment 처리와 동일하다고 쓰면
  안 된다.

### [19] Konur and Golias (2013): bounded arrival windows

**현재 파악된 내용**

- inbound truck의 실제 arrival time을 알 수 없고 lower/upper bound만 안다.
- deterministic, optimistic, pessimistic, hybrid 접근을 비교한다.
- truck-to-door assignment를 위한 GA를 사용한다.

**원문에서 반드시 읽을 부분**

- Arrival interval의 정보 구조와 실제 arrival realization의 처리
- deterministic/optimistic/pessimistic formulation의 차이
- 목적함수인 service cost의 정확한 구성
- inbound door만 다루는지, outbound flow와 연결되는지 확인
- 모델이 static, rolling-horizon 또는 bilevel인지 확인

**본 논문과 연결할 내용**

- arrival-time window가 문헌에 이미 있다는 사실을 인정한다.
- 본 연구의 $r_q$는 알려진 단일 release time이고, [19]는 실제 도착시각이 불확실한
  interval 정보라는 차이를 강조한다.

### [20] Konur and Golias (2013): cost-stable scheduling

**현재 파악된 내용**

- unknown truck arrival 아래에서 평균 service cost와 cost variation을 함께
  고려한다.
- bi-objective, bilevel model과 genetic-algorithm 기반 해법을 사용한다.

**원문에서 반드시 읽을 부분**

- cost stability의 수학적 정의
- unknown arrival을 표현하는 scenario 또는 uncertainty structure
- 두 목적 사이의 trade-off와 Pareto solution 생성법
- FCFS와의 비교 방식

**본 논문과 연결할 내용**

- deterministic schedule 품질보다 실행 시 안정성을 연구한 문헌으로 분류한다.
- 현재 연구의 직접 비교군이라기보다, unrevealed arrival을 다루는 후속연구의
  출발점으로 사용한다.

### [21] Ladier and Alpan (2016)

**현재 파악된 내용**

- time-window truck schedule의 robustness를 다룬다.
- minimax, expected regret, resource/time redundancy 등의 방법을 비교한다.
- storage를 줄이고 운송업체의 time-window 만족도를 높이는 문제를 다룬다.

**원문에서 반드시 읽을 부분**

- 불확실한 변수가 arrival time인지 processing time인지 둘 다인지 확인한다.
- Robustness와 regret의 정의 및 nominal objective와의 관계
- Truck presence time window의 정의
- Door redundancy가 storage와 robustness에 미치는 trade-off

**본 논문과 연결할 내용**

- time-window literature와 robust scheduling literature를 연결하는 근거다.
- VAA의 regret과 이 논문의 robust expected regret은 서로 다른 개념이므로 혼동하지
  않는다. 전자는 배정 후보 간 비용 차이고, 후자는 불확실성 시나리오의 성능
  손실이다.

### [22] Larbi et al. (2011)

**현재 파악된 내용**

- inbound arrival 순서와 truck contents에 대해 full, partial, no information을
  구분한다.
- single receiving/single shipping door를 중심으로 한다.
- full-information case에는 graph-based exact method, 나머지에는 heuristic을
  사용한다.

**원문에서 반드시 읽을 부분**

- 각 information level에서 정확히 무엇을 알고 무엇을 모르는지
- Arrival time 자체와 arrival sequence 정보의 차이
- FIFO 또는 다른 운영정책의 사용 여부
- 목적함수와 value-of-information 계산법
- multi-door 확장에 붙는 제한조건

**본 논문과 연결할 내용**

- 현재 연구는 full-information offline setting에 속한다고 설명할 수 있다.
- Discussion에서 online/dynamic arrival 및 정보가 순차적으로 공개되는 문제를
  future work로 제안할 때 인용한다.

### [23] Xi et al. (2020)

**현재 파악된 내용**

- truck arrival time과 operation time의 불확실성을 함께 다룬다.
- schedule overlap을 conflict로 정의한 two-stage robust model을 제안한다.
- column-and-constraint generation을 사용한다.
- probability distribution 없이 uncertainty set을 사용한다.

**원문에서 반드시 읽을 부분**

- Conflict의 수학적 정의와 baseline schedule의 실행 방식
- First-stage와 second-stage decision의 구분
- Arrival/operation uncertainty set의 생성 방법
- K-means 기반 multiple uncertainty sets의 역할
- Exact algorithm의 최적성 보장과 계산 가능 규모

**본 논문과 연결할 내용**

- 최근 arrival-uncertainty 연구까지 검토했다는 근거다.
- 현재 CP-SAT/MILP는 deterministic known-release model이며, [23]과 같은 robust
  counterpart를 포함하지 않는다고 명확히 한다.

### [24] Rijal et al. (2019)

**현재 파악된 내용**

- unit-load cross-dock에서 truck scheduling과 dock-door assignment를 통합한다.
- inbound, outbound, flexible door가 공존하는 mixed-service-mode 구조다.
- temporary storage, travel distance와 outbound tardiness를 고려한다.
- integrated ALNS와 sequential approach를 비교한다.

**원문에서 반드시 읽을 부분**

- Integrated model의 목적함수와 각 항의 가중치
- Flexible door의 mode 결정 및 sequence 제약
- Temporary storage와 internal travel distance 계산법
- ALNS의 destroy/repair operator와 adaptive weight 갱신법
- Sequential schedule-then-assign 대비 integrated approach의 이득

**본 논문과 연결할 내용**

- 우리 문제도 carrier/door assignment와 sequencing을 함께 결정한다는 구조적
  공통점이 있다.
- 다만 [24]의 truck은 unit-load pure inbound/outbound이고 본 연구처럼 destination
  하나를 retain한 compound carrier가 아니다.
- ALNS의 adaptive operator selection은 VAA-GILS의 uniform/tabular-Q/DQN 비교를
  설명할 때 보조 문헌으로 사용할 수 있다.

## 3. 횡단 비교표

원문을 읽으면서 물음표를 실제 값으로 교체한다.

| Ref. | 도착정보 | 시간 제약 | 목적함수 핵심 | 유연성 위치 | Compound/partial unload | 해법 |
|---|---|---|---|---|---|---|
| [15] | 원문 확인 | Time windows | Tardiness 포함 | Door/sequence | 없음 | Tabu search |
| [16] | Known ready times | Ready times, due/target time | Earliness + tardiness | Door/sequence | 없음 | MILP, DE, PBSA |
| [17] | 원문 확인 | Time windows | Outbound tardiness 포함 | Mixed-service door | 없음 | 원문 확인 |
| [18] | 원문 확인 | Hard due dates | Delayed-shipment penalty/cost | Sorting/sequence | 없음 | MILP, HGARVNS |
| [19] | Bounded uncertain arrival | Arrival interval | Service cost | Door assignment | 없음 | Bilevel models, GA |
| [20] | Unknown arrival | 불확실 도착 | Mean cost + stability | Door sequence | 없음 | Bi-objective bilevel, GA |
| [21] | Uncertain | Time windows | Storage/satisfaction/robustness | Door redundancy | 없음 | Robust models |
| [22] | Full/partial/no information | Arrival sequence 정보 | Transshipment schedule cost | Information policy | 없음 | Exact graph method, heuristics |
| [23] | Uncertain arrival/operation | Scenario-dependent | Cost + conflicts | Mixed-mode docks | 없음 | Two-stage RO, C&CG |
| [24] | 원문 확인 | Departure times | Storage/travel/tardiness | Mixed-service door | 없음 | MIP, ALNS |
| 본 연구 | Known release times | Soft due dates | Makespan + total tardiness | Compound truck | 있음 | MILP, CP-SAT, VAA-GILS |

## 4. 정독하면서 작성할 공통 메모 양식

각 논문을 읽은 뒤 아래 양식을 채우면 Related Work와 reviewer response를 바로
작성할 수 있다.

```text
논문 번호/제목:
문제 단위와 truck 종류:
도착정보가 계획 시점에 알려지는가:
release/ready/arrival window의 정확한 정의:
due date/time window가 hard인가 soft인가:
tardiness 대상과 계산식:
목적함수 전체:
door service mode:
temporary storage 허용 여부:
truck-door assignment와 sequencing의 통합 여부:
compound truck 또는 partial unloading 존재 여부:
해법과 neighborhood/operator:
instance 규모와 데이터 생성법:
본 논문과 겹치는 점:
본 논문과 구조적으로 다른 점:
Related Work에 사용할 한 문장:
Discussion/future work에 사용할 한 문장:
확인한 원문 페이지와 식 번호:
```

## 5. 원고에 사용할 수 있는 안전한 결론

현재 단계에서 다음 표현은 사용할 수 있다.

> Release times, time windows, and due-date-related objectives have been
> studied for conventional inbound/outbound truck scheduling [15–24]. Our
> contribution is to integrate known release times and soft due dates into the
> partial-unloading compound-truck setting.

다음 표현은 사용하지 않는다.

> This is the first cross-docking model with release times and due dates.

또한 [19]–[23]은 deterministic known-release 연구의 직접 선행모델로 한데 묶기보다
**arrival uncertainty/incomplete information**이라는 별도 문헌 흐름으로 설명하는
것이 정확하다.

## 6. 정독 완료 기준

각 논문에 대해 다음 조건을 모두 만족하면 읽기를 완료한 것으로 본다.

- 초록뿐 아니라 problem definition과 formulation을 읽었다.
- arrival/ready/release/time-window 용어의 수학적 의미를 확인했다.
- 목적함수와 tardiness 정의를 식 번호와 함께 기록했다.
- pure truck과 compound truck의 차이를 확인했다.
- 실험 instance의 규모와 생성방식을 기록했다.
- 원고에 넣을 수 있는 비교문장 한 개와 과장 위험이 있는 문장 한 개를 작성했다.


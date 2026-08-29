# 학회 선행 등록 논문 읽기 목록

논문 투고 전에 확인할 학회 선행 발표·수상 논문을 정리한 문서다. 아래 내용은
사용자가 제공한 정보를 기준으로 작성했으며, 최종 원고에서 인용하거나 학회 동향을
설명하기 전에는 proceedings에서 발표연도, 학회명, 세션, 페이지, DOI와 저자
소속을 확인해야 한다.

## 1. 협조적 물류계획과 핵심 물류 최적화

### Integrated Optimization of Coordinated Logistics Planning and Incentive Mechanism

- 저자: Qian Huang, Yao Hu, Shunichi Ohmori
- 소속: Waseda University 등으로 전달받음
- 학회 정보: Excellent Paper Award 수상작으로 전달받음
- 주요 내용:
  - 여러 이해관계자가 참여하는 물류 네트워크를 다룬다.
  - 협조적 물류계획과 참여를 유도하는 incentive mechanism을 하나의 수학적
    최적화 틀에서 다룬다.
  - synchro-modality와 참여자 간 이익배분·상생 물류 최적화 관점에서 참고할 수
    있다.
- 읽을 때 확인할 사항:
  - 중앙집중형 또는 분산형 의사결정 구조
  - 참여 이해관계자와 각 참여자의 목적함수
  - Incentive compatibility 및 individual rationality 보장 여부
  - 물류계획과 인센티브를 순차적으로 결정하는지, 동시에 최적화하는지
  - 비용절감액 또는 coalition value의 배분 방식
  - Exact model, decomposition, heuristic 등 사용된 해법
  - Excellent Paper Award의 정확한 수상 학회와 연도
- 현재 VAA-GILS 논문과의 관계:
  - 직접적인 cross-dock truck scheduling 선행연구라기보다 복합 물류 시스템의
    통합 최적화 사례다.
  - 논문의 문제 범위를 여러 운영주체 또는 협조적 운송으로 확장할 때 참고할 수
    있다.

### A Profit-Oriented Multi-Period 3D Bin Packing Model with Delivery Penalty

- 저자: Di Jingjie, Takashi Irohara
- 소속: Sophia University로 전달받음
- 주요 내용:
  - 3D bin packing을 multi-period 계획문제로 확장한다.
  - 공간 활용률만 최소화·최대화하는 대신 수익과 delivery penalty를 함께 고려한다.
  - 창고 적재와 운송 납기를 결합한 실무 지향적 목적함수를 사용한다.
- 읽을 때 확인할 사항:
  - Item, bin, vehicle 및 planning period의 관계
  - 3차원 배치의 회전 허용 여부와 안정성·적재순서 제약
  - Delivery penalty가 tardiness, missed delivery 또는 backlog 중 무엇인지
  - Profit의 수익·운송비·보관비·지연비 구성
  - 기간 사이 미배정 화물의 이월 방식
  - MILP의 의사결정변수와 non-overlap formulation
  - 계산 가능한 instance 규모와 제안 휴리스틱
- 현재 VAA-GILS 논문과의 관계:
  - delivery penalty를 운영계획 목적함수에 포함한다는 점에서 soft due-date
    모델링과 연결된다.
  - 다만 3D 공간배치 문제이므로 cross-dock scheduling의 직접 선행연구로
    분류하지 않는다.

## 2. 스마트 물류 및 로봇 AGV/AMR 최적화

### Mathematical Models of DRCHFS Problems to Minimize the Total Misplaced Value or the Makespan

- 저자: Muhammad Akbar, Takashi Irohara 등
- 주요 내용:
  - 분산 환경의 hybrid flow-shop scheduling 문제를 다룬다.
  - Total misplaced value 또는 makespan을 최소화하는 수리모형을 제시한다.
  - 제조공정과 물류 이동이 결합된 일정계획 문제로 파악된다.
- 읽을 때 확인할 사항:
  - DRCHFS 약어의 원문상 정확한 명칭
  - Distributed site, stage, machine과 job의 구조
  - Misplaced value의 수학적 정의와 물류적 의미
  - Makespan 모델과 misplaced-value 모델이 별도 모델인지 다목적 모델인지
  - Routing, recirculation 또는 material handling 제약의 존재 여부
  - Integer-programming formulation의 선행관계 및 machine-capacity 제약
  - Exact solver가 증명한 instance 규모와 계산시간
- 현재 VAA-GILS 논문과의 관계:
  - makespan 최소화 MILP와 복합적인 자원 선행관계 모델링을 비교하는 데 유용하다.
  - Cross-dock 문제와 직접 연결하려면 DRCHFS의 물류 이동 및 자원공유 구조를
    원문에서 먼저 확인해야 한다.

### Optimization of Replenishment and Picking Processes in Robotic Mobile Fulfillment Systems with Multiple Picking Stations

- 저자: Takashi Irohara, Shinnosuke Kawahara
- 주요 내용:
  - Robot 또는 AMR이 저장 선반을 이동시키는 robotic mobile fulfillment system을
    다룬다.
  - Replenishment와 picking을 여러 picking station 환경에서 함께 최적화한다.
  - Station 간 작업분배와 병목 완화를 주요 문제로 다룬다.
- 읽을 때 확인할 사항:
  - Replenishment와 picking 의사결정의 결합 방식
  - Pod, robot, station, order 및 item의 관계
  - Robot 이동시간과 충돌·혼잡을 명시적으로 고려하는지
  - Picking station의 capacity 및 작업자 제약
  - 목적함수가 throughput, makespan, waiting time 또는 travel distance 중
    무엇인지
  - 통합 최적화와 순차 최적화의 비교 여부
  - 실제 데이터 또는 simulation을 사용했는지
- 현재 VAA-GILS 논문과의 관계:
  - 여러 station 중 critical station을 찾아 병목을 완화한다면 VAA-GILS의
    critical-door guided operator와 개념적으로 비교할 수 있다.
  - 직접 인용할 때는 동일한 scheduling problem이 아니라 병목 기반 복합 물류
    최적화의 사례로 한정한다.

## 3. 공급망 및 리스크 관리 최적화

### Multi-Objective Modeling for Resilient and Risk-Aware Design of Perishable Logistics Considering Uncertainty

- 저자: Jianming Lei, Kwangyeol Ryu 등
- 소속: 부산대학교 등으로 전달받음
- 주요 내용:
  - 신선식품이나 의약품과 같은 부패성 화물의 물류 네트워크를 설계한다.
  - 불확실성과 공급망 위험을 고려하는 multi-objective model을 사용한다.
  - 비용·위험·회복탄력성 사이의 균형을 통해 경로와 시설 결정을 지원한다.
- 읽을 때 확인할 사항:
  - Strategic facility design과 operational routing의 통합 여부
  - 수요, 운송시간, 품질저하 또는 disruption 중 불확실한 변수
  - Scenario, stochastic, robust 또는 fuzzy formulation 중 채택한 방식
  - Resilience와 risk의 정량화 방법
  - Perishability 또는 freshness decay 식
  - Pareto solution 생성법과 의사결정자 선호 반영 방식
  - Case study의 실제성 및 sensitivity analysis
- 현재 VAA-GILS 논문과의 관계:
  - 현재 연구의 known release-time 가정을 uncertain arrival/operation-time 문제로
    확장할 때 참고할 수 있다.
  - 현재 논문의 직접 선행연구가 아니라 uncertainty와 resilience를 다루는 확장
    방향의 문헌이다.

## 4. 우선 읽기 순서

현재 VAA-GILS 원고와의 관련성을 기준으로 다음 순서를 권장한다.

1. **Optimization of Replenishment and Picking Processes in RMFS**
   - 다중 station 병목과 통합 scheduling 관점 확인
2. **A Profit-Oriented Multi-Period 3D Bin Packing Model**
   - delivery penalty와 다기간 목적함수 설계 확인
3. **Mathematical Models of DRCHFS Problems**
   - makespan MILP와 복합 선행관계 확인
4. **Integrated Optimization of Coordinated Logistics Planning and Incentive
   Mechanism**
   - 학회 수상작의 문제정의·기여 제시 방식 확인
5. **Multi-Objective Modeling for Resilient and Risk-Aware Design**
   - uncertainty와 후속연구 방향 확인

## 5. 학회 투고 관점에서 볼 항목

논문 내용뿐 아니라 같은 학회에서 어떤 연구가 높게 평가되었는지를 파악하기 위해
다음 항목도 기록한다.

```text
논문 제목:
학회명과 개최연도:
세션명:
수상 여부와 상의 정확한 명칭:
페이지 또는 paper ID:
저자와 소속:
연구문제 한 문장:
현실적 동기와 적용산업:
수리모형의 핵심 의사결정:
목적함수:
핵심 제약:
해법:
비교군:
계산실험 규모:
통계검정 여부:
논문이 강조한 기여:
발표자료에서 강조할 만한 그림/표:
우리 원고에 적용할 작성 방식:
직접 인용 가능 여부:
확인이 필요한 서지정보:
```

## 6. 서지정보 확인 상태

| 논문 | 제목 | 저자 | 학회·연도 | 수상 | 원문/Proceedings |
|---|---|---|---|---|---|
| Coordinated logistics/incentive | 제공됨 | 일부 제공됨 | 확인 필요 | Excellent Paper Award 확인 필요 | 확인 필요 |
| Multi-period 3D bin packing | 제공됨 | 제공됨 | 확인 필요 | 확인 필요 | 확인 필요 |
| DRCHFS mathematical models | 제공됨 | 일부 제공됨 | 확인 필요 | 확인 필요 | 확인 필요 |
| RMFS replenishment/picking | 제공됨 | 제공됨 | 확인 필요 | 확인 필요 | 확인 필요 |
| Perishable resilient logistics | 제공됨 | 일부 제공됨 | 확인 필요 | 확인 필요 | 확인 필요 |

서지정보가 확인되기 전에는 이 문서의 내용을 `paper/apiems2026_draft.md`의 정식
References에 추가하지 않는다.

# VAA-GILS: 도착 시각과 연성 납기를 고려한 병행 트럭 크로스도킹 스케줄링

> **Compound-Truck Cross-Docking Scheduling with Release Times and Soft Due Dates:
> A Bottleneck-Guided Iterated Local Search**
>
> 대한산업공학회지(JKIIE) 투고 원고: [paper/jkiie_submit_body.tex](paper/jkiie_submit_body.tex)
> (PDF: [paper/jkiie_submit_body.pdf](paper/jkiie_submit_body.pdf))

> 구 저장소명 `CPG-RL-ALNS`는 초기 연구 방향의 이름입니다. 최종 제안 방법은
> 결정론적 구조의 **VAA-GILS**이며, 강화학습 기반 연산자 선택은 ablation으로만 다룹니다.

부분 하역(partial unloading) 병행 트럭(compound truck)이 있는 multi-door 크로스도킹
스케줄링 문제에 **트럭별 도착 시각(release time)** 과 **연성 납기(soft due date)** 를
결합한 모형, 이를 위한 MILP/CP-SAT 정식화, 그리고 제안 휴리스틱 VAA-GILS의 구현과
실험 코드입니다.

## 연구 요약

병행 트럭은 여러 목적지 화물을 싣고 도착해 한 목적지 화물만 남기고 부분 하역한 뒤,
그 목적지로 오는 이송 화물을 모두 받고 나서 출고 운송 트럭으로 출발합니다. 이 구조에서
한 트럭의 늦은 도착은 공유 목적지를 따라 다른 운송 트럭의 납기지연으로 전파됩니다.
기존 연구는 (i) 역할이 고정된 입고/출고 트럭에 시간 제약을 두거나, (ii) 부분 하역 병행
트럭을 다루되 모든 트럭이 시각 0에 가용하고 makespan만 최소화했습니다
(Shahmardan and Sajadieh, 2020). 본 연구는 두 계열을 결합합니다.

**기여**

1. **문제 정식화** — 부분 하역 병행 트럭 + 트럭별 도착 시각 + 연성 납기. 목적식은
   `J = C_max + λ · Σ T_q` (λ = 1). 독립 스케줄 평가기와 일치하는 big-M MILP와 CP-SAT 모형을 제시합니다.
2. **해법** — 원 모델(SA-RL5)의 VAA 구성 휴리스틱과 기본 이웃 7종 위에 병목 유도 연산자 4종,
   최선개선 하강 탐색, 섭동 재시작, greedy 수락을 결합한 **VAA-GILS**. 같은 반복 횟수뿐 아니라
   같은 실행 시간에서도 SA-RL5 계열보다 좋은 해를 찾습니다.
3. **검증** — S-none 20개 인스턴스 전부에서 CP-SAT로 최적성을 증명해 최적해 대비 격차를 제시하고,
   최적해 / 기준해(CP-SAT incumbent) / 관측 최선해를 구분해 보고합니다. 학습 기반 연산자 선택은
   같은 엔진·같은 반복 횟수의 균등 선택과 통제 비교합니다.

## 주요 결과

시험 집합, 조건당 20개 인스턴스 × 5회 반복, 반복 1,000회 기준입니다.

| 항목 | 결과 |
|---|---|
| CP-SAT 기준해 대비 | GILS-uniform 평균 격차 0.10–0.23% (S 전 조건, M-none) |
| 증명된 최적해 대비 (S-none, 20개) | 평균 0.23% |
| VAA 대비 | 평균 2.66% 우수 (n=180, p<0.0001) |
| Paper-SA-RL5 대비 (none) | 평균 1.44% 우수 (n=60, p<0.0001) |
| Extended SA-RL5 대비 (medium/tight) | 평균 0.93% 우수 (n=120, p<0.0001) |
| 동일 실행 시간 비교 | SA-RL5 대비 평균 1.30% 우수, 180개 인스턴스 중 SA-RL5 승리 0 |
| GILS 실행 시간 | S 0.09초, M 0.49초, L 2.43초 |
| CP-SAT 실행 시간 | S-none 40초, S-medium 245초, S-tight 250초, M-none 606초. M 시간 제약 조건과 L 전체는 600초 안에 실행 가능해 없음 |

**Table 4. 해 품질** (`Δbo`: 관측 최선해 대비 평균 격차)

| 조건 | 방법 | 평균 목적값 ± s.d. | Δbo (%) | vs CP-SAT (%) | 시간 (s) |
|---|---|---|---:|---:|---:|
| S-none | VAA | 1497.5 ± 400.3 | 6.61 | +6.61 | 0.00 |
| | Paper-SA-RL5 | 1423.8 ± 383.8 | 1.07 | +1.07 | 0.16 |
| | GILS-uniform | 1412.4 ± 382.0 | 0.23 | +0.23 | 0.09 |
| S-medium | VAA | 5447.5 ± 1468.9 | 3.90 | +3.90 | 0.00 |
| | Extended-SA-RL5 | 5302.0 ± 1431.8 | 0.97 | +0.97 | 0.17 |
| | GILS-uniform | 5259.4 ± 1412.1 | 0.17 | +0.17 | 0.09 |
| S-tight | VAA | 9276.8 ± 2387.6 | 2.91 | +2.91 | 0.00 |
| | Extended-SA-RL5 | 9056.3 ± 2214.9 | 0.61 | +0.61 | 0.16 |
| | GILS-uniform | 9011.9 ± 2206.5 | 0.11 | +0.11 | 0.09 |
| M-none | VAA | 3030.9 ± 903.6 | 3.72 | +4.80 | 0.00 |
| | Paper-SA-RL5 | 2979.2 ± 860.9 | 1.98 | +1.55 | 0.60 |
| | GILS-uniform | 2929.5 ± 844.2 | 0.28 | +0.10 | 0.47 |
| M-medium | VAA | 23025.5 ± 4075.4 | 2.58 | — | 0.00 |
| | Extended-SA-RL5 | 22821.9 ± 3985.3 | 1.65 | — | 0.54 |
| | GILS-uniform | 22513.0 ± 3960.7 | 0.25 | — | 0.50 |
| M-tight | VAA | 38903.7 ± 11283.5 | 1.26 | — | 0.01 |
| | Extended-SA-RL5 | 38811.1 ± 11075.1 | 0.99 | — | 0.52 |
| | GILS-uniform | 38501.1 ± 11067.3 | 0.13 | — | 0.52 |
| L-none | VAA | 5492.3 ± 1482.2 | 2.17 | — | 0.02 |
| | Paper-SA-RL5 | 5480.3 ± 1450.5 | 1.94 | — | 1.95 |
| | GILS-uniform | 5383.9 ± 1423.8 | 0.15 | — | 2.37 |
| L-medium | VAA | 55611.1 ± 18087.3 | 1.57 | — | 0.02 |
| | Extended-SA-RL5 | 55544.0 ± 17684.8 | 1.46 | — | 1.49 |
| | GILS-uniform | 54825.9 ± 17531.9 | 0.11 | — | 2.47 |
| L-tight | VAA | 119671.9 ± 32475.3 | 0.78 | — | 0.02 |
| | Extended-SA-RL5 | 119634.3 ± 31842.5 | 0.74 | — | 1.57 |
| | GILS-uniform | 118863.6 ± 31785.2 | 0.06 | — | 2.45 |

`vs CP-SAT`는 CP-SAT가 기준해를 반환한 부분집합(S 조건당 20개, M-none 2개)에서만 계산합니다.

**Ablation** (조건당 5개 인스턴스 × 5회, 9개 조건, 양측 Wilcoxon)

| 변경 | 효과 (%p) | p |
|---|---:|---|
| 연산자: 기본 7종 → +g1, g2 | +0.150 개선 | <0.0001 |
| 연산자: +g1, g2 → +g3, g4 | +0.034 개선 | 0.013 |
| 섭동 재시작 제거 | +0.375 악화 | <0.0001 |
| 하강 탐색 제거 | +0.064 악화 | 0.0016 |
| VAA 대신 무작위 초기해 | +0.057 악화 | 0.0495 |
| SA 수락 + reheating 추가 | +0.036 악화 | 0.0043 |

**선택 정책** (조건당 20개, 1,000회): tabular Q-learning은 균등 선택보다 0.040%p,
transfer DQN은 0.093%p 나쁘며 둘 다 유의합니다(p<0.0001). 성능은 섭동 재시작, 유도 연산자,
하강 탐색이라는 결정론적 구조에서 나오고, 학습 기반 선택과 확률적 수락은 이득이 없습니다.

## 문제 정의

| 기호 | 의미 |
|---|---|
| `I`, `F`, `D`, `M` | 병행 트럭, 출고트럭, 목적지(`|D|=|I|+|F|`), 도어 |
| `r_q` | 트럭 `q`의 도착 시각 — 이전에는 도어 작업 불가 |
| `d̄_q` | 트럭 `q`의 연성 납기 — 위반 시 `T_q = max(0, C_q − d̄_q)` |
| `λ` | 납기지연 벌점 계수 (기본 1, 조정 집합에서 민감도 분석) |

결정 사항은 (1) 병행 트럭이 유지할 목적지와 도어(도어당 최대 1대), (2) 출고트럭의 목적지와
도어, (3) 같은 도어 출고트럭의 작업 순서입니다. `r_q = 0`, `d̄_q = ∞`이면 원 모델(makespan
최소화)로 환원됩니다. 정식화와 코드 대응은 [docs/problem_definition.md](docs/problem_definition.md)에 있습니다.

## VAA-GILS

엔진은 [crossdock_solver/baselines/vaa_qrl.py](crossdock_solver/baselines/vaa_qrl.py)에
있습니다(초기 이름 `VAA-QRL`이 파일명에 남아 있음).

| 구성요소 | 내용 |
|---|---|
| 초기해 | 원 모델의 VAA: Vogel식 regret으로 유지 목적지 배정, 도착 시각 반영 도어 삽입 |
| 하강 탐색 | 출고트럭 재배치, 병행 트럭 도어 교환/빈 도어 이동, 목적지 교환의 best-improvement. 초기해·새 최선해·최종해에 적용 |
| 반복 탐색 | 1,000회. 선택 정책(기본: 균등 무작위)이 연산자 하나를 골라 후보 생성, greedy 수락 |
| 섭동 재시작 | 30회 무개선 시 최선해 복사본에 기본 이웃 kick 3회 |
| 기본 이웃 7종 | k1 목적지 교환, k2/k3 도어 교환, k4 출고트럭 삽입, k6/k7 룰렛 삽입, k8 룰렛 목적지 배정 |
| 유도 연산자 4종 | g1 병목 도어의 마지막 출고트럭 재배치, g2 병목 트럭 목적지 교환, g3/g4 최대 납기지연 트럭 기준 동일 이동 |
| 고속 평가기 | [crossdock_solver/core/fast_evaluator.py](crossdock_solver/core/fast_evaluator.py) — 해 하나당 S 약 25–28μs, L 약 95–148μs |

SA-RL5(원 모델)와의 차이: 순수 SA → 반복 지역탐색, 연산자 7 → 11종, Q-learning 선택 → 균등 선택,
하강 탐색·섭동 재시작 추가, Metropolis 수락 → greedy 수락, makespan → makespan + λ·tardiness.

## 실험 설계

| 항목 | 설정 |
|---|---|
| 규모 `(|I|,|F|,|D|,|M|)` | S (6,3,9,6), M (12,6,18,12), L (20,10,30,20) |
| 시간 제약 `(ρ, δ)` | none; medium (0.25, 0.60); tight (0.50, 0.35). `r_q ~ U[0, ρH]`, `d̄_q = r_q + δH` |
| 기타 생성 | `|K|=3`, `f_idk ~ U[0,20]`, `t_k ~ U[1,4]`, `DE/DL ~ U[1,5]`, 도어 좌표 `[0,100]²`, 이송시간 = 거리/10 |
| 시드 | 학습 / 조정 / 시험 집합 서로소. λ와 수락 규칙은 조정 집합에서만 결정 |
| 주 비교 | 조건당 시험 인스턴스 20개 × 5회 |
| CP-SAT | 8 스레드, S 300초(20개), M/L 600초(2개) |
| 통계 | 인스턴스별 반복 평균에 양측 Wilcoxon signed-rank |
| 환경 | Apple M2 (8코어), 16GB, Python 3.12, OR-Tools 9.15 |

## 방법 이름 (코드 ↔ 논문)

| 코드 (`experiments/methods.py`) | 논문 |
|---|---|
| `VAA` | VAA |
| `Paper-SA-RL5-1000` | Paper-SA-RL5 (none 조건) |
| `Extended-SA-RL5-1000` | Extended SA-RL5 (medium/tight 조건) |
| `*-SA-RL5-timematch` | 동일 실행 시간 비교 (Table 5) |
| `v2-GILS-uniform-1000` | **GILS-uniform (제안 방법 기본값)** |
| `v2-GILS-1000`, `v2-GILS-dqn-1000` | GILS-tabular, GILS-DQN (ablation) |
| `v2-GILS-{generic,critical,full}-1000` | 연산자 집합 ablation (Table 6) |
| `v2-GILS-ablate-{none,init,descent,restart,addsa}-1000` | 엔진 구성요소 ablation (Table 7) |
| `CPSAT-300`, `CPSAT-600` | CP-SAT |

`v2-` 접두사는 최종 greedy 수락 엔진을 뜻합니다. 접두사가 없는 `GILS-*` 기록은 이전 SA 엔진 결과이며 요약에서 제외됩니다.

## 실행

```bash
python -m pytest -q                 # 테스트
python examples/run_mvp.py          # 최소 예제
```

논문 표/그림 재현:

| 논문 | 실행 | 요약 |
|---|---|---|
| Table 4, 8 (해 품질, 선택 정책) | `python experiments/k1_run.py search` / `budget` / `cpsat` / `cpsat_s20` | `python experiments/k1_summary.py`, `python experiments/k1_stats.py` |
| Table 5 (동일 실행 시간) | `python experiments/budget_fairness.py` | `python experiments/budget_fairness.py summary` |
| Table 6, Figure 2 (연산자 집합) | `python experiments/b1_run.py` | `python experiments/b1_summary.py` |
| Table 7 (엔진 구성요소) | `python experiments/b2_run.py` | `python experiments/b2_summary.py` |
| 수락 규칙 조정 (3장) | `python experiments/acceptance_tuning.py` | — |
| Figure 3 (λ 민감도) | `python experiments/lambda_sensitivity.py` | `python experiments/lambda_summary.py` |
| 그림 생성 | `python experiments/make_figures.py` | `paper/figures/` |

결과는 `outputs/*.jsonl`에 append되며, runner는 이미 기록된 job을 건너뜁니다. `cpsat` 배치는 수 시간이 걸리고,
`budget_fairness.py`는 벽시계 시간을 예산으로 쓰므로 다른 실험과 병행하지 마세요.

## 코드 구조

| 경로 | 내용 |
|---|---|
| `crossdock_solver/data/` | 인스턴스 dataclass, 벤치마크 생성기 |
| `crossdock_solver/core/` | feasibility, 기준 evaluator, FastEvaluator |
| `crossdock_solver/baselines/vaa.py` | VAA 구성 휴리스틱 |
| `crossdock_solver/baselines/vaa_qrl.py` | VAA-GILS 엔진, 유도 연산자 |
| `crossdock_solver/baselines/paper_sa_rl.py` | Paper/Extended SA-RL5 |
| `crossdock_solver/rl/` | tabular / DQN 선택 정책, 규모 불변 특징 |
| `crossdock_solver/exact/` | MILP(PuLP/CBC), CP-SAT, 조합적 하한 |
| `experiments/` | seed 프로토콜, method registry, 실험·요약 스크립트 |
| `paper/` | JKIIE 투고 원고(`jkiie_submit_*`), 그림, 이전 APIEMS/CAIE 원고 |
| `docs/` | 문제 정의, 벤치마크 설계, 문헌 조사, 투고 체크리스트 |

## 문서

- [paper/jkiie_submit_body.tex](paper/jkiie_submit_body.tex): 최종 투고 원고 (본문)
- [docs/problem_definition.md](docs/problem_definition.md): 문제 정식화와 코드 대응
- [docs/model_and_solution_guide.md](docs/model_and_solution_guide.md): 모형과 해법 해설
- [docs/benchmark_design.md](docs/benchmark_design.md): 벤치마크 설계 근거
- [docs/literature_scan_tw.md](docs/literature_scan_tw.md): 시간 제약 변형 문헌 조사
- [docs/jkiie_submission_checklist.md](docs/jkiie_submission_checklist.md): 투고 체크리스트
- [docs/archive/](docs/archive/): 이전 연구 계획과 APIEMS 초안

## 환경 메모

고정된 requirements 파일은 없습니다. NumPy, pytest, PuLP, OR-Tools, PyTorch를 사용합니다.
CP-SAT import 시 pandas/pyarrow와 NumPy ABI가 충돌하는 환경을 위해
[crossdock_solver/exact/cpsat.py](crossdock_solver/exact/cpsat.py)에 최소 stub 우회가 들어 있습니다.
같은 이유로 그림은 matplotlib 없이 SVG를 직접 생성합니다.

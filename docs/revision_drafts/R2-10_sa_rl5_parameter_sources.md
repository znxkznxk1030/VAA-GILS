# R2-10 후속: Table 3의 SA-RL5 파라미터 출처 확인

- 작성일: 2026-11-23
- 확인한 문헌: Shahmardan, A. and Sajadieh, M. S.(2020), Truck Scheduling in a Multi-Door Cross-Docking Center with Partial Unloading – Reinforcement Learning-Based Simulated Annealing Approaches, *Computers & Industrial Engineering*, 139, 106134 (로컬 파일 `~/Desktop/05. 물류 ai/문헌/013-Shahmardan & Sajadieh (2020).pdf`, 18쪽)
- 관련 항목: R2-10(비교 방법 설명과 파라미터를 4.3절로 이동). 반영 후 Table 3에 값을 적었으나, 원 논문 값인지 본 연구가 정한 값인지 구분하지 못한 상태였다.
- 대조한 구현: `crossdock_solver/baselines/paper_sa_rl.py`(`PaperSARLConfig`)

## 결론

원 논문이 숫자로 밝힌 SA-RL5 설정은 **상태 경계 (ν₁, ν₂, ν₃, ν₄) = (5, 10, 15, 20)** 하나뿐이다.

- 학습률, 할인율, 선택 확률, 초기 온도, 냉각 계수는 원 논문에 값이 없다.
- 따라서 Table 3의 이 값들은 **본 연구가 정한 값**으로 밝혀야 한다.
- 보상, 선택 방식, Q값 초기값, 초기해, 냉각 방식은 원 논문의 구조와 같다.

## 항목별 대조

| 항목 | 원 논문 | 우리 구현 (Table 3) | 판단 |
|---|---|---|---|
| 상태 경계 (ν₁–ν₄) | (5, 10, 15, 20) — 12쪽, SA-RL5 정의 | (5, 10, 15, 20) | 원 논문 값과 같음 |
| 상태 정의 | 현재 해가 개선되지 않은 횟수 NI로 5개 상태 — 11쪽 | 같음 | 같음 |
| 보상 | 새 해의 목적값이 현재 해와 같거나 좋으면 1, 아니면 0 — 10쪽 | 1/0 | 같음 |
| 선택 방식 | rand ≤ ε이면 무작위, ε < rand ≤ ε + Pr_rol이면 Q값 기반 룰렛, 그 밖에는 탐욕 선택 — 11쪽 | 같은 구조 | 같음 |
| Q값 초기값 | 0 — Figure 7 설정, 14–15쪽 | 0 | 같음 |
| Q-learning 갱신식 | Q(s,a) ← Q(s,a) + α[r + γ·max Q(s′,b) − Q(s,a)] — 11쪽 | 같은 식 | 같음 |
| 초기해 | 휴리스틱의 최종해 — 9쪽 | VAA 해 | 같음 |
| 냉각 방식 | T_new = α·T_old — 9쪽 | 기하 냉각 | 형태는 같음 |
| ε (무작위 선택 확률) | 최종값 없음. 5.1절 민감도 분석에서 ε = 0, 0.1, 0.2, 0.3, 1.0을 비교했고, Figure 7은 ε = 0.3으로 그림 | 0.10 | 원 논문에 값 없음 |
| Pr_rol (룰렛 선택 확률) | 기호만 있음 | 0.20 | 원 논문에 값 없음 |
| 학습률 α | 식에 기호만 있음 | 0.3 | 원 논문에 값 없음 |
| 할인율 γ | "γ ∈ (0, 1)"만 있음 | 0.9 | 원 논문에 값 없음 |
| 초기 온도 | 없음 | max{1, 0.05·J(s₀)} | 원 논문에 값 없음 |
| 냉각 계수 | 없음 (학습률과 같은 기호 α로 표기) | 0.995 | 원 논문에 값 없음 |
| 종료 조건 | CPU 시간 ((1+D)/2 × M × 0.7)초 — 9쪽 | 반복 1,000회 | 다름. 4.3절에 이미 밝혔고 같은 시간 비교(Table 5)로 보완함 |

## 심사에서 질문받을 수 있는 점

1. **ε 값**: 원 논문의 민감도 그림은 ε = 0.3을 쓰고 우리는 0.10을 쓴다.
   - 원 논문이 최종값을 밝히지 않았으므로 "원 논문에 제시되지 않아 본 연구가 정했다"는 서술은 사실과 맞다.
   - 0.10을 고른 근거 기록은 저장소에서 찾지 못했다.
2. **SA-RL5와 SA-RL6**: 원 논문은 대형 문제에 상태 경계 (10, 20, 50, 100)의 SA-RL6을 권한다(13쪽). 본 연구는 SA-RL5와 비교한다.
   - 원 논문의 대형 실험(Table 4)에서 두 방법의 평균 목적값은 5,070.83(SA-RL5)과 5,070.22(SA-RL6)로 차이가 약 0.01%다.
   - 질문을 받으면 이 수치로 답할 수 있다.

## 원고 수정 (2026-11-23 반영)

**Table 3 캡션 끝 (영문)**
> For SA-RL5, the state thresholds, reward, and selection scheme follow Shahmardan and Sajadieh (2020); the original paper does not report the learning rate, discount factor, selection probabilities, initial temperature, or cooling rate, so these values are set in this study.

**4.3절 파라미터 문단 끝 (국문)**
> SA-RL5의 상태 경계, 보상, 연산자 선택 방식은 원 논문을 따랐으며, 원 논문에 값이 제시되지 않은 학습률, 할인율, 선택 확률, 초기 온도와 냉각률은 본 연구가 정하였다.

## 답변서에 쓸 수 있는 문장 (R2-10 보충)

> Table 3에 정리한 SA-RL5의 설정 가운데 상태 경계, 보상, 연산자 선택 방식은 원 논문(Shahmardan and Sajadieh, 2020)을 따랐습니다. 원 논문에 값이 제시되지 않은 학습률, 할인율, 선택 확률, 초기 온도와 냉각률은 본 연구가 정하였음을 표와 본문에 밝혔습니다.

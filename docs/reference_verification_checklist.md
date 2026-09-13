# 문헌 검증 체크리스트 (jkiie_korean.tex)

**상태: 참고문헌 17편 전부 원문 대조 검증 완료 (2026-09-07).**
저자가 제공한 PDF 전문을 기준으로 각 문헌에 대한 원고의 **내용 주장**을 대조했다.
결과는 내용 주장 **불일치 1건**(Shahmardan & Sajadieh의 보상 정의)과
**서지 제목 잘림 3건**이며, 모두 원고에 반영 완료했다.

- 검증 가능했던 것: 서지정보(제목·저자·저널·권·호·쪽·연도·DOI), 인용↔참고문헌 정합성,
  형식 준수 → 이미 확인 완료(미인용 0건, 형식 JKIIE 준수)
- 원문 대조로 검증한 것: 아래 표의 "우리 주장" 열 **전부**

검증 자료: 저자 제공 PDF 17편 전문(`~/Desktop/05. 물류 ai/`).
주의 — 파일명 오기 2건: `014-Van Belle et al. (2013).pdf`는 실제로 **Van Belle et al.
(2012)** Omega 40, `017-Mnih et al. (2015).pdf`는 실제로 **Xi et al. (2020)** TR-E 144다.

---

## 🔴 1순위 — 논문의 핵심 논거가 걸린 것 (3편)

> 진행: 1·2·3번 **전부 검증 완료**

### 1. Shahmardan & Sajadieh (2020), C&IE 139, 106134 — **원 모델** ✅ **검증 완료 (2026-09-07)**
검증 자료: 출판본 PDF 원문(18쪽) 전문 대조. 서지정보 일치 확인
(A. Shahmardan, M.S. Sajadieh, *Computers & Industrial Engineering* 139 (2020) 106134,
Amirkabir University of Technology).

| # | 우리 주장 | 판정 | 원문 근거 |
|---|---|---|---|
| 1.1 | "Joo와 Kim이 도입하고 **Shahmardan과 Sajadieh가 발전**시킨" | ✅ 정확 | §1: Joo & Kim (2013)은 **exclusive mode** 하에서 inbound-only/outbound-only/**compound truck** 3분류를 도입. 본 논문은 "a truck scheduling model … with a **mixed mode of service**"에 **partial unloading**을 추가. Table 1의 "This Paper" 행에 Partial Unloading·Mixed Service ✓ |
| 1.2 | "**VAA 구성 휴리스틱과 generic 이웃 7종**은 이 모델에서 가져왔다" | ✅ 정확 (서술 1건 보정) | §3.1 Step 2: "Use **Vogel's approximation algorithm** to allocate each compound truck to one destination"; Step 4–5: $TEE_f$ 오름차순 정렬 후 최소 $TEE_f$ 출고 트럭을 최대 $T_d$ 목적지에 배정; Step 11: 잔여 출고 트럭을 **$FT_m$이 가장 작은(가장 이른) 도어**에 배정. ⚠️ 단 **Step 8**(최초 처리 트럭 목록 $FAT$)은 **$T_m$ = 도어 간 이송시간 합이 최소인 중앙 도어**를 쓴다 → 원고가 "가장 이른 도어"만 언급해 누락 → **§4 문장 보정 완료** |
| 1.3 | **k1–k8 중 k5 미정의 → 실제 7종** | ✅ 정확 | §3.2 목록이 $k=4$ → $k=6$으로 건너뜀. PDF 전문 텍스트에서 `k = 5` **0건**. |
| 1.4 | k1 목적지 교환 / k2 컴파운드 도어 교환 / k3 출고 도어 교환 / k4 출고 도어 삽입 | ✅ 정확 | §3.2 축자 일치: "Swap of destinations, $k=1$"(두 트럭, 컴파운드·출고 무관) / "Swap of dock door for compound (outbound) trucks, $k=2$ ($k=3$)" / "Insertion of outbound trucks, $k=4$: An outbound truck is chosen and assigned to another door" |
| 1.5 | **k6·k7·k8이 룰렛 선택 기반**(하역시간·적재시간·목적지 기준) | ✅ 정확 | §3.2: $k=6$은 하역시간 $UT_i$ 기준 룰렛, $k=7$은 적재시간 $T_d$ 기준 룰렛, $k=8$은 $\max_{d}T_{id}$ 기준 룰렛. (부기: $k=6,7$은 **도어 선택도** $T_m$ 기준 룰렛) |
| 1.6 | "SA-RL5는 **RL이 단일 이동을 고르고 SA accept/reject로 한 단계가 끝나는 순수 SA**" | ✅ 정확 | §4의 알고리즘 정의 9종이 모두 SA 변형("Simple simulated annealing …", "Simulated annealing with the learning approach …"). PDF 전문에서 `descent`·`local search`·`restart`·`reheat`는 **참고문헌 제목에만** 등장(Morais et al. 2014, Tarantilis 2013), **본문 방법 서술에는 0건**. 냉각은 $T_{new}=\alpha T_{old}$ 단일, 종료는 CPU 시간 $\frac{|I|+|D|}{2}\times|M|\times0.7$초. → **표 1의 "개선 이동 이후: 없음", "정체 처리: 없음" 주장 성립** |
| 1.7 | SA-RL5 selector = 무개선 5-상태 tabular Q-learning, ε-greedy + 룰렛, 셰이핑 보상 | ⚠️ **보상만 불일치 → 수정 완료** | 상태·선택은 일치: $NI$(무개선 횟수)로 $S\in\{1..5\}$, SA-RL5는 $(v_1..v_4)=(5,10,15,20)$; 선택은 `rand≤ε`→랜덤, `ε<rand≤ε+P_rol`→$Q$ 기반 룰렛, 그 외 greedy. **그러나 보상은 이진**: "the reward is defined as **1 if the objective value of new solution is equal or better** than that of current solution, **otherwise 0**". 우리 2/1/0 셰이핑은 **본 연구의 변형** → 영문·국문 원고에 "원 모델은 이진 보상, 본 연구는 셰이핑(신호 강화이므로 비교 대상을 불리하게 하지 않음)"으로 명시 |
| 1.8 | "타이밍은 **evaluator 규칙**을 따른다" | ✅ 정확(등가 재매개화) | 식 (3): 컴파운드 트럭은 **미배정 목적지** 하역 완료 후 적재 시작 → 우리 $r_i+DE_i+\sum_{d'\ne d}h_{id'}$와 일치($r_i\equiv0$이 원 모델). 식 (28)–(31): 원 모델 $d_f$(적재 시작) $=$ 우리 $S_f+DE_f$, 완료 $FT_f=d_f+L_d+DL_f$ → 우리 $S_f+DE_f+L_d+DL_f$와 동일. 전환시간 "$DE_j+DL_i$ if truck $j$ is the immediate successor to truck $i$" 일치. 식 (13)(14)(15)(16)이 도어당 컴파운드 1대·트럭당 도어 1개·목적지당 트럭 1대와 일치 |
| 1.9 | "부분 하역은 makespan을 크게 줄인다" (영문본 "최대 56%") | ✅ 정확 | §5 결론 축자: 부분 하역이 "improve the objective function **up to 56%**". Table 7(DBPR 민감도) 최대 개선 **55.0–55.9%**(수요밀도 0.87). Table 6(부분 vs 전량 하역)은 최대 50.16%. → **"최대 56%" 유지 가능** |

**원고 반영 완료**
1. §4 초기해 구성: 도어 배정 2단계(중앙 도어 우선 → 최조기 종료 도어 삽입) 명시 —
   `jkiie_korean.tex`, `jkiie_submit_body.tex`
2. §4 선택 정책: tabular Q의 보상이 원 모델의 이진 보상과 다름을 명시 —
   `jkiie_korean.tex`, `jkiie_submit_body.tex`, `caie_submission.tex/.md`,
   `apiems2026_draft.md`, `thesis_ko.md`

**부수 확인 사항**
- 원 모델 알고리즘 9종: H, SA, SA-NS, SA-RL1(Incremental), SA-RL2(Non-Stationary),
  SA-RL3(UCB Type 1), SA-RL4(UCB Type 2), SA-RL5·SA-RL6(Q-learning, 상태 경계만 다름).
  **SA-RL5를 base로 고른 것은 타당** — 원 논문은 대형 문제에 SA-RL6 $(10,20,50,100)$을
  권하나 두 변형의 평균 차이는 미미(Table 4: 5070.83 vs 5070.22).
- 원 모델은 **makespan 단일 목적**(Table 1 objective 열 = M) → 우리 표 1의 "목적함수" 행 정확.
- SA 초기해는 **휴리스틱 H의 최종해**(랜덤 아님) → 우리 VAA 초기해 계승과 일치.
- 인스턴스 생성은 Van Belle et al. (2013) 관행을 따르며 도어 간 이송 1s,
  $DE_i,DL_i\sim U(3,10)$, $t_k\sim U(0,20)$, $f_{idk}\sim U(0,20)$.

### 2. Li et al. (2026), EJOR 333(1), 117–137 — **최근접 경쟁자** ✅ **검증 완료 (2026-09)**
검증 자료: arXiv:2412.09090v1 (2024-12-12) 프리프린트 PDF 원문 대조.

| # | 우리 주장 | 판정 | 원문 근거 |
|---|---|---|---|
| 2.1 | mixed service mode dock + time window를 **Q-learning 기반 ALNS**로 | ✅ 정확 | 제목·초록 "Q-ALNS"; §3.1 "time windows $(r_i,d_i)$" |
| 2.2 | 유연성이 **도어 수준**, 트럭은 순수 inbound/outbound | ✅ 정확 | §3.1 "Inbound trucks can be assigned to either the unloading-only or mixed-mode docks…"; 도어 모드가 결정변수 $\lambda_k,\rho_k,\mu_k$ |
| 2.3 | 환적이 **AGV를 통해 저장 구역** 경유 | ✅ 정확 | §3.1 "unload pallets, which are then handled in the corresponding storage area by Automated Guided Vehicles (AGVs)" |

**추가로 확인된 사실 (원고에 반영 완료)**
1. **시간 구조가 본 연구와 유사**: $r_i$는 앞당길 수 없는 하한, $d_i$는 연장 가능한 상한이며
   $f_1=\min\sum\delta_i,\ \delta_i=\max\{0,e_i-d_i\}$ (= tardiness), $f_2$ = makespan.
   → "release time·soft due date 도입" 자체는 novelty가 아님. **partial-unloading carrier
   변환과의 상호작용**이라는 현재 프레이밍이 옳음이 확인됨.
2. **크로스도킹이 아니라 배송센터(DC)**: Table 1에서 자신을 DC로 분류(타 연구는 C=cross-docking).
   대상은 unmanned distribution center, 저장 버퍼 경유. → 차별화 근거로 §2에 반영.
3. **다목적(Pareto)**: $f_1$ tardiness, $f_2$ makespan, $f_3$ AGV 이동거리. 본 연구는 단일 가중합.
4. **그들은 Q-learning이 성능을 높인다고 보고** ("consistently outperforming benchmark
   algorithms"). → 본 연구의 negative result와 대비되며, §7의 "엔진 구조에 따라 결과가
   갈린다"는 논거를 뒷받침.

**⚠️ 남은 확인 1건**: 받은 PDF는 **arXiv 프리프린트**(2024-12)이다. 참고문헌의 출판 서지정보
(**EJOR 333(1), 117–137, 2026**, DOI 10.1016/j.ejor.2025.12.036)는 **출판본으로 재확인 필요**.
저자명·제목은 일치 확인함(제목은 전체 제목으로 교정 완료).

### 3. Molavi et al. (2018), C&IE 117, 29–40 ✅ **검증 완료 (2026-09-07)**
| # | 우리 주장 | 판정 | 원문 근거 |
|---|---|---|---|
| 3.1 | "**hard** due date를 부과" | ✅ 정확 | 초록: "a truck scheduling problem is investigated at a two-touch cross-docking center with **due dates for outbound trucks as a hard constraint**". 제목 "with **fixed due dates**", 키워드 "Fixed due date". 목적은 지연 화물의 penalty·delivery cost 최소화 |

> 참고: 수치실험 논의에서 "due date를 time-window 사이에서 조정하거나 연기할 수 있다"고
> 언급하나, **모형 자체는 hard constraint**이므로 soft vs hard 대비 논거는 그대로 성립한다.

---

## 🟠 2순위 — 선행연구 커버리지 주장 (6편) ✅ **전부 검증 완료 (2026-09-07)**

| 문헌 | 우리 주장 | 판정 | 원문 근거 |
|---|---|---|---|
| **Van Belle et al. (2013)** C&IE 66(4), 818–826 | "**다중 도어·time window·tardiness**"를 tabu search로 | ✅ 정확 | 제목 "A **tabu search** approach to the truck scheduling problem with **multiple docks and time windows**"; 초록 "objective is to minimize the total travel time and the **total tardiness**" |
| **Assadi & Bagheri (2016)** C&IE 96, 149–161 | "**ready time**과 outbound **earliness/tardiness**" | ✅ 정확 | 초록 "**ready times for both inbound and outbound trucks** … The objective is to minimize **total earliness and tardiness for outbound trucks**"; 키워드 "Ready times" |
| **Bodnar et al. (2017)** Transp. Sci. 51(1), 112–131 | "time window와 **mixed-service door**" | ✅ 정확 | 제목 "…with **Mixed Service Mode Dock Doors**"; 초록 "schedule inbound and outbound trucks **subject to time windows** at a multidoor cross-dock. Dock doors can either be dedicated … or be capable of handling both truck types". 목적함수에 **tardiness cost** 포함, ALNS로 해결 |
| **Rijal et al. (2019)** EJOR 278(3), 752–771 | "truck scheduling과 **door assignment의 통합**" (영문본은 "**tardiness 포함**"까지 주장) | ✅ 정확 (둘 다) | 제목 "**Integrated scheduling and assignment** of trucks…"; §3에서 문제를 $[EM\,|\,r_i,d_i,p_i,t_p{=}0\,|\,\sum T_i+S_p+DC]$로 표기하고 "the **minimization of the total tardiness**, temporary storage, and total direct transfer distance costs"라 명시 |
| **Boysen & Fliedner (2010)** Omega 38, 413–422 | "도크 스케줄링 문제를 **분류**하였다" | ✅ 정확 | 제목 "Cross dock scheduling: **Classification**, literature review and research agenda"; 초록 "this paper introduces a **classification** of deterministic truck scheduling" |
| **Van Belle et al. (2012)** Omega 40(6), 827–846 | "분야를 **조망**하였다" | ✅ 정확 | 제목 "Cross-docking: **State of the art**"; Review 논문, "presents an extensive **review** of the existing literature" |

> ⚠️ **Rijal (2019)은 $r_i$(도착)·$d_i$(출발)·tardiness·mixed-mode door를 모두 갖는다.**
> 따라서 "release time·soft due date 도입"이나 "door 유연성"은 본 연구의 novelty가
> **아니다.** Li et al. (2026)에서 얻은 결론과 동일하며, 현재 §2·§3.3의 프레이밍
> (**트럭 수준 partial-unloading 전환과의 상호작용**이 novelty)이 옳음을 재확인한다.

---

## 🟡 3순위 — 불확실성 스트림 (5편) ✅ **전부 검증 완료 (2026-09-07)**

| 문헌 | 우리 주장 | 판정 | 원문 근거 |
|---|---|---|---|
| **Konur & Golias (2013a)** C&IE 65(4), 663–672 | "**bounded arrival window**" | ✅ 정확, **a/b 뒤바뀜 없음** | 제목 "Analysis of different approaches to cross-dock truck scheduling with **truck arrival time uncertainty**"; 초록 "the cross-dock operator only acknowledges the **arrival time window** of each truck, i.e., the **lower and upper bounds**". deterministic/pessimistic/optimistic 3접근을 bi-level GA로 비교 |
| **Konur & Golias (2013b)** TR-E 49(1), 71–91 | "unknown arrival 하의 **cost-stable** schedule" | ✅ 정확 | 제목 "**Cost-stable** truck scheduling at a cross-dock facility with **unknown truck arrivals**"; 초록 "A **cost-stable** scheduling strategy is defined as a schedule with low variation levels" |
| **Larbi et al. (2011)** C&OR 38(6), 889–900 | "도착 정보의 **full/partial/absent**를 구분", 정보 가치 정량화 | ✅ 정확 | 제목 "Scheduling cross docking operations under **full, partial and no information** on inbound arrivals"; 초록 "helps evaluating the **value of information**"; 키워드 "Value of information". ⚠️ 단 대상은 **single receiving·single shipping door** → 원고가 다중 도어로 오인될 서술을 하지 않는지만 유지 확인 |
| **Ladier & Alpan (2016)** C&IE 99, 16–28 | "time window 하의 **robust schedule**" | ✅ 정확 | 제목 "**Robust** cross-dock scheduling **with time windows**"; minimax·expected regret·resource/time redundancy 9개 robust 모형 비교 |
| **Xi et al. (2020)** TR-E 144, 102123 | "**two-stage** conflict robust optimization" | ✅ 정확 | 제목 "**Two-stage** conflict robust optimization models…"; 초록 "We introduce a concept named **conflict** and present a **two-stage** optimization model"; 키워드 "Two-stage robust model". 도착·작업시간 불확실성, column-and-constraint generation |

---

## ⚪ 4순위 — 방법 원전 (2편) ✅ **검증 완료**

| 문헌 | 판정 | 근거 |
|---|---|---|
| **Watkins & Dayan (1992)** Machine Learning 8, 279–292 | ✅ 정확 | PDF 헤더 "Machine Learning, 8, 279-292 (1992)", Technical Note "**Q-Learning**", Watkins & Dayan |
| **Mnih et al. (2015)** Nature 518, 529–533 | ✅ 정확 | "Human-level control through deep reinforcement learning", doi:10.1038/nature14236 |

---

## 서지정보 오류 및 수정 (2026-09-07)

원문 대조 중 **제목 잘림 3건**을 발견해 수정했다.

| 문헌 | 수정 전 | 수정 후 |
|---|---|---|
| Assadi & Bagheri (2016) | "…simulated annealing for truck scheduling" | "…simulated annealing for truck scheduling **problem in multiple door cross-docking systems**" |
| Rijal et al. (2019) | "Integrated scheduling and assignment of trucks at unit-load cross-dock terminals" | "…cross-dock terminals **with mixed service mode dock doors**" |
| Xi et al. (2020) | "…for cross-dock truck scheduling under uncertainty" | "…for cross-dock truck scheduling **problem** under uncertainty" |

적용 파일: `jkiie_korean.tex`, `apiems2026_8page.tex`, `apiems2026_korean.tex`
(`caie_submission.tex/.md`, `apiems2026_draft.md`, `jkiie_submit_body.tex`는 이미 정확)

**나머지 서지정보는 전부 원문과 일치** — 저널명·권·호·쪽·연도·저자 표기 이상 없음.

---

## 남은 확인 1건

- **Li et al. (2026) 출판 서지정보**: 대조에 쓴 PDF는 arXiv:2412.09090v1 **프리프린트**(2024-12)다.
  참고문헌의 **EJOR 333(1), 117–137, 2026**(DOI 10.1016/j.ejor.2025.12.036)은 출판본으로
  재확인이 필요하다. 저자·제목은 일치 확인 완료.

---

## 검증 후 할 일

핵심 3건 — **1.3(k5 미정의)**, **1.6(원 모델에 descent 없음)**, **2.2(도어 수준
유연성)** — 은 표 1과 novelty 주장의 뼈대였고, **모두 원문에서 확인되었다.**
따라서 논문의 구조적 주장은 유지된다.

원고에 반영한 수정은 다음 3건뿐이다.

1. **보상 정의 정정** — 원 모델 SA-RL5는 이진 보상(1/0), 본 연구는 셰이핑 보상(2/1/0).
   이를 "본 연구의 변형"으로 명시 (§4·부록, 영문 4개 파일 + 국문 2개 파일)
2. **VAA 초기해 서술 보정** — 도어 배정이 2단계(중앙 도어 우선 → 최조기 종료 도어 삽입)
   임을 명시 (§4)
3. **서지 제목 잘림 3건 복원** — Assadi, Rijal, Xi

향후 유사 검증 시에도 이 문서의 표 형식(우리 주장 / 판정 / 원문 근거)을 유지할 것.

---

## 🆕 2026-09-13 추가 8편 (심사 지적: 참고문헌 부족) — **7편 원문 대조 완료, 1편 원문 미확보**

`jkiie_submit_body.tex`·`.docx`에만 반영(총 17편 → 25편). 검증 자료: 저자 제공 PDF 7편
(`~/Desktop/05. 물류 ai/018`–`025`, 021 없음). 결과는 **내용 주장 불일치 2건**(Nowak & Puladi의 병행 트럭
누락, Pan이 "가장 가깝다"는 서술)과 **서술 보강 1건**(Theophilus의 도착·지연 출발 비용)이며, 모두 원고에
반영 완료했다.

| 문헌 | 우리 주장 | 판정 | 원문 근거 |
|---|---|---|---|
| **Karimi-Mamaghan, Mohammadi, Pasdeloup & Meyer (2023)** EJOR 304(3), 1296–1330 (`018`) | "iterated greedy에 Q-learning 연산자 선택을 통합", 학습 제어가 개선을 보고 | ✅ 정확 | p.1296 헤더 "EJOR 304 (2023) 1296–1330". 초록 "incorporates Q-learning to select appropriate perturbation operators during the search process … against non-learning versions of the iterated greedy algorithm and seven state-of-the-art algorithms … show the better performance". ⚠️ 부기: 선택 대상은 **perturbation 연산자**. 서론 p.1297은 Turkeš et al. (2021)을 인용해 "the added-value of simple methods of AOS is not significant"라 적는다 → 본 연구 §7 negative result와 정합하는 추가 인용 후보 |
| **Li, Hao & Wu (2024)** EJOR 312(2), 473–492 (`020`) | "cross-dock door assignment에 강화학습 기반 strategic oscillation을 적용", 개선 보고 | ✅ 정확 | p.473 헤더 "EJOR 312 (2024) 473–492". 초록 "a reinforcement learning based heuristic approach … relies on a Q-learning reinforced procedure to guide the search toward promising areas, and a strategic oscillation method … improved the best solutions (new upper bounds) for 43 of the 99 tested instances". 대상은 트럭 스케줄링이 아닌 **door assignment(CDAP)**이며 원고도 그렇게 씀 |
| **Theophilus et al. (2021)** C&IE 156, 107240 (`025`) | (수정 전) "신선 화물의 부패를 고려한 cold-chain 트럭 스케줄링" | ⚠️ **보강 → 수정 완료** | 제목·초록은 "perishable products"(신선 화물로 한정 아님). p.5 Table 1: 도착 시각 $\tau^{at}_t$, 예정 출발 시각 $\tau^{sd}_t$, 지연 출발 시간 $\tau^{dt}_t$와 단위 비용 $c^{dt}_t$; p.7 §3.3 "Whenever the service completion of a truck extends beyond the deadline, a unit delayed departure cost … is incurred". p.5 §3.1 "$T^{in}\cup T^{out}=T$, $T^{in}\cap T^{out}=\emptyset$", p.6 segregated door mode → **입고·출고트럭 구분**. 원고를 "부패성 제품의 품질 저하, 트럭 도착 시각, 예정 출발 시각을 넘긴 지연 출발 비용을 함께 고려하지만 입고트럭과 출고트럭은 서로 구분된다"로 수정 |
| **Nowak & Puladi (2025)** C&IE 209, 111423 (`022`) | (수정 전) "선점과 혼합 서비스 도어를 함께 허용하는 트럭 스케줄링의 메타휴리스틱"으로만 서술 | 🔴 **불일치(누락) → 수정 완료** | p.2 "We apply the commonly used term 'compound' truck to refer to those that may experience both inbound and outbound operations"; p.3 "We extend the work … by considering compounds trucks" → **병행 트럭 후속 연구**인데 원고가 이를 빠뜨림. 단 부분 하역 없음: p.3 $O\subset I$, "A truck will not leave the dock before it is completely unloaded or loaded", 식 (10) $b_i=a_i+\sum_j PD_{ij}$(전량 하역 후 적재). 도착 시각 없음: 식 (21) $a_i\ge0$, p.4 Lemma 3.1 증명 "the arrival time of the truck … for each dock m is zero". 납기 없음: 목적식 (1) $\min c_{max}$만. 해법 GA·VNS(p.5 §4). 원고를 "혼합 서비스 도어와 작업 선점을 허용하면서 하역을 마친 트럭이 다시 적재되는 병행 트럭을 다루고 메타휴리스틱으로 총 작업완료시간을 최소화하지만, 트럭은 싣고 온 화물을 모두 하역한 뒤 적재되고 도착 시각이나 납기는 두지 않는다"로 수정 |
| **Pan, Fan, Qi, Chen & Zhang (2021)** Math. Probl. Eng. 2021, Article ID 5592122 (`023`) | (수정 전) "반복 적재를 허용한 Pan 등이 **가장 가깝지만** 부분 하역 후 출고 전환은 다루지 않는다" | 🔴 **"가장 가깝다" 불일치 → 수정 완료** (전환 부재는 ✅) | p.4 §3.1 "a receiving dock … designated to serve a set R of inbound trucks and a shipping dock … a set S of outbound trucks", "the inbound truck i needs to unload all of its fresh produce before leaving", 가정 (1) "All inbound and outbound trucks are available at time zero" → 병행 트럭·도착 시각 없음. 가장 가까운 것은 Nowak & Puladi (2025)이므로 최상급 삭제, "병행 트럭을 다루지 않으며 모든 트럭이 시각 0에 가용하다고 가정한다"로 수정 |
| **Ropke & Pisinger (2006)** Transp. Sci. 40(4), 455–472 (`024`) | ALNS 원전 | ✅ 정확 | p.455 헤더 "Vol. 40, No. 4, November 2006, pp. 455–472", DOI 10.1287/trsc.1050.0135. 초록 "This general framework is denoted adaptive large neighborhood search" |
| **Kirkpatrick, Gelatt & Vecchi (1983)** Science 220(4598), 671–680 (`019`) | SA 원전 | ✅ 정확 | JSTOR 표지 "Science, May 13, 1983, New Series, Vol. 220, No. 4598, pp. 671-680"; p.671 제목 "Optimization by Simulated Annealing" |
| **Lourenço, Martin & Stützle (2019)** Handbook of Metaheuristics, 129–168 | ILS 틀 원전 | ⏸ **원문 미확보** | 저자 PDF 없음(구하지 못함). Crossref로 서지만 확인: DOI 10.1007/978-3-319-91086-4_5, 편집자 Gendreau & Potvin, Springer, Cham, 129–168 |

**신규성 재스캔 (2026-09-13)**: Semantic Scholar에서 Shahmardan & Sajadieh (2020)를 인용한 50편
(2019–2026)의 제목을 전수 확인했다. 병행 트럭·부분 하역을 도착 시각·납기·시간창과 결합한 논문은 없었다.
원문 대조 결과, 가장 가까운 후속 연구는 제목에 병행 트럭이 드러나지 않는 **Nowak & Puladi (2025)**다(병행 트럭 +
혼합 도어 + 선점, 단 전량 하역·도착 시각 없음·makespan 단일 목적). 제목 스캔만으로는 이를 놓쳤으므로, 향후
신규성 스캔은 인용 문헌의 모델 절까지 확인해야 한다. §2의 "인용 문헌 가운데 확인되지 않았다"는 문장의 근거이며,
인용 목록이 불완전할 수 있다는 한계는 `literature_scan_tw.md`와 같다.

**형식 확인 필요**: Lourenço et al. (2019)의 **단행본 챕터 표기**(`In 편집자(Eds.), 서명, 출판사, 도시, 쪽`)는
JKIIE 투고요령(hwp) 원문으로 확인하지 못했다.

---

## 참고: AI가 이미 검증 완료한 항목 (재확인 불필요)

- 참고문헌 17편 **전부 본문에서 인용됨** (미인용 0)
- 참고문헌에 없는 인용 0
- 알파벳순 정렬, JKIIE 형식(저자명+연도 괄호, 영문) 준수
- 본문 인용 형식: 저자명(연도)
- 상호참조(표·그림·식) 미정의 0

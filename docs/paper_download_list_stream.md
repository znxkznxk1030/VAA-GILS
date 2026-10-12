# 원문 확보 목록: 산업 보정 시나리오와 연속 도착 RL 연구

서지 정보는 웹 검색 요약에서 옮긴 것이다. "(확인 필요)"는 검색으로 확정하지 못한 항목이므로 내려받을 때 실제 서지로 확인할 것.

**PDF 저장 위치:** `refs/stream/` (저작권 때문에 git에 올리지 않음, `.gitignore`에 등록).
**파일 이름:** 아래 번호를 앞에 붙여 `S01_ladier2016.pdf`처럼 저장하면 검증 요청 시 번호로 지정할 수 있다.

## A. 산업 보정 시나리오용 (최우선)

| 번호 | 서지 | 확인할 내용 |
|---|---|---|
| S01 | Ladier, A.-L., & Alpan, G. (2016). Cross-docking operations: Current research versus industry practice. *Omega*, 62, 145–162. (HAL hal-01222831) | 관찰·인터뷰한 플랫폼의 도어 수, 일일 트럭 수, 도착 패턴(예약 여부, 시간대 집중), 트럭 유형(입고·출고·혼재), **하역 후 같은 트럭이 재적재하는 사례가 있는지**(병행 트럭 현실성), 납기·출고 마감 방식 |
| S02 | Akkerman, F., Lalla-Ruiz, E., Mes, M., & Spitters, T. (2022). Cross-docking: Current research versus industry practice and Industry 4.0 adoption. Emerald 총서 장(DOI 10.1108/S1877-636120220000028007) | S01 이후(2015–2020) 연구와 실무 차이 갱신, 산업 수치가 있으면 함께 |
| S03 | Cross-docking operation scheduling: Truck arrivals, shop-floor activities and truck departures. *IFAC-PapersOnLine* (2016) (HAL hal-01435896). 저자 (확인 필요) | Renault ILN 플랫폼의 도어 수, 트럭 수, 도착·출발 시간표, 처리시간 |
| S04 | Scheduling of truck arrivals, truck departures and shop-floor operation in a cross-dock platform, based on trucks loading plans. *International Journal of Production Economics* (2017 또는 2018) (확인 필요). 저자 (확인 필요) | S03의 확장. 산업 데이터 기반 인스턴스의 규모와 파라미터 |
| S05 | Gallo, A., et al. (2022). 확률적 유전 알고리즘으로 불확실성 아래 크로스도크 일정을 푸는 연구. *EURO Journal on Transportation and Logistics*. 제목·저자 (확인 필요) | 실제 271대 사례의 도착 분포, 도착 지연 크기, 도어 수, 처리시간 |
| S06 | Bartholdi, J. J., & Gue, K. R. (2000). Reducing labor costs in an LTL crossdocking terminal. *Operations Research*, 48(6), 823–832. | Viking Freight 터미널의 도어 수, 트레일러 수, 물동량 패턴 |
| S07 | Yu, W., Sharma, M., & Murty, K. G. LTL 터미널의 도어 배정 연구 (umich 공개 PDF `door_alloc_ltl_tt.pdf`). 학술지·연도 (확인 필요) | 일별 물동량 변동의 실측 크기, 도어 수, 야간 처리량 |
| S08 | Virginia Tech, "Improving the Efficiency of Hub Operations in a Less-than-Truckload Distribution Network" (학위논문, vtechworks 10919/10131). 저자·연도 (확인 필요) | 지역 LTL 운송사 데이터의 도어 수, 트레일러 수, 시간대별 도착 |
| S09 | Cross-dock trailer scheduling with workforce constraints: A dynamic discretization discovery approach. *Transportation Science*, 59(1), 165–186 (2025). 저자 (확인 필요) | LTL 실제 데이터 사용 여부, 트레일러 도착·처리 파라미터 |
| S10 | Torbali, B., & Alpan, G. (2023). A multi-agent-based real-time truck scheduling model for cross-docking problems with single inbound and outbound doors. *Supply Chain Analytics*, 3, 100028. 및 Torbali 박사논문 "Real-time Truck Scheduling in Cross-Docking: A Hybrid Multi-Agent Simulation Framework" (연도·기관 확인 필요) | 시간당 팔레트 수 등 파라미터의 근거(산업 출처인지), 다중 도어(2–20) 실험 설계, 비교 규칙 |

| S21 | Ertek, G. (2012). Crossdocking insights from a third party logistics firm in Turkey. (Shahmardan & Sajadieh 2020이 3PL 실무 근거로 인용, 출처 형식 확인 필요) | 실제 3PL 크로스도크 운영 수치, 같은 트럭의 하역·재적재 사례 여부 |
| S22 | Morais, V. W. C., Mateus, G. R., & Noronha, T. F. (2014). Iterated local search heuristics for the vehicle routing problem with cross-docking. *Expert Systems with Applications* (권호 확인 필요) | 수거·배송 겸용 차량 가정의 실무 근거(병행 트럭 정당화) |
| S23 | Tarantilis, C. D. (2013). Adaptive multi-restart tabu search algorithm for the vehicle routing problem with cross-docking. *Optimization Letters* (확인 필요) | 같은 목적 |

## B. 가장 가까운 경쟁·비교 연구 (원문 대조)

| 번호 | 서지 | 확인할 내용 |
|---|---|---|
| S11 | A rolling horizon based bi-objective optimization approach for dynamic truck dispatching with cross-dock door assignment (2026). ResearchGate 399944905. 학술지·저자 (확인 필요, **서지 자체 미확인**) | 실제 출판 여부, 도착 과정(연속 도착인지), 트럭 유형(병행 트럭 여부), 목적식, 기준선 |
| S12 | Larbi, R., Alpan, G., Baptiste, P., & Penz, B. (2011). Scheduling cross docking operations under full, partial and no information on inbound arrivals. *Computers & Operations Research*, 38(6), 889–900. | 정보 수준별 정책, 온라인 우선순위 규칙의 정의, 실험 파라미터 |
| S13 | Konur, D., & Golias, M. M. (2013). Analysis of different approaches to cross-dock truck scheduling with truck arrival time uncertainty. *Computers & Industrial Engineering*, 65(4), 663–672. | 도착 시간창 모형, 도착 불확실성 크기 |
| S14 | Konur, D., & Golias, M. M. (2013). Cost-stable truck scheduling at a cross-dock facility with unknown truck arrivals: A meta-heuristic approach. *Transportation Research Part E*, 49(1), 71–91. | FCFS 정책과의 비교 방식 |
| S15 | Container port truck dispatching optimization using Real2Sim based deep reinforcement learning. *European Journal of Operational Research*, 315(1), 161–175 (2024). 저자 (확인 필요) | 상태·행동 설계, 실제 데이터로 시뮬레이터를 보정한 방법(본 연구의 산업 보정 방법론 참고), 기준선 |
| S16 | Liu, G., Iloglu, S., Caldara, M., Durham, J. W., & Zavlanos, M. M. (2025). Distributionally robust multi-agent reinforcement learning for dynamic chute mapping. arXiv:2503.09755 (공개) | 에이전트 정의, 보상, 유입률 변동 모형(비정상 도착 모형 참고) |

## C. 방법론 (우선순위 낮음, 대부분 공개본 있음)

| 번호 | 서지 | 확인할 내용 |
|---|---|---|
| S17 | Bhattacharya, S., et al. (2020). Multiagent rollout and policy iteration for POMDP with application to multi-robot repair problems. arXiv:2011.04222 (공개, 저자 목록 확인 필요) | 본 연구의 Rollout → 증류와의 차이 |
| S18 | Goodson, J. C., Ohlmann, J. W., & Thomas, B. W. (2013). Rollout policies for dynamic solutions to the multivehicle routing problem with stochastic demand and duration limits. *Operations Research*, 61(1), 138–154. | rollout 대 롤링 호라이즌 비교 방식 |
| S19 | Offline–online approximate dynamic programming for dynamic vehicle routing with stochastic requests. *Transportation Science* (DOI 10.1287/trsc.2017.0767). 저자 (확인 필요) | 가치함수 근사 + rollout 결합(제안 1의 직접 선례) |
| S20 | Zhang, C., et al. (2020). Learning to dispatch for job shop scheduling via deep reinforcement learning. *NeurIPS 33* (arXiv:2010.12367, 공개) | 그래프 정책망과 규모 일반화 실험 설계 |

## 권장 확보 순서

1. **S01**(병행 트럭의 현장 근거, 산업 수치) → 결과에 따라 방향 재검토
2. S03–S05, S06–S09 중 접근되는 것(산업 수치)
3. **S11**(서지 미확인 경쟁 연구) → S12–S15
4. C 묶음은 RL 방법 착수 시점에

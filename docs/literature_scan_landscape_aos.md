# 문헌 스캔: Landscape 구조 & 학습형 연산자 선택(AOS) — 우리 결과와의 정합 (2026-07-30)

우리 실험에서 관측·측정한 두 사실
1. **품질의 출처 = 결정론적 구조**(descent + 유도연산자 + 재시작); 학습 선택·
   학습 초기해·SA 확률수락은 무기여 (B1/B2/K1, §6.2),
2. **landscape = 넓고 평평한 big-valley**(FDC S/M/L = +0.43/+0.51/+0.42, 랜덤
   1회 descent gap = 1.85/0.79/0.31%, 최적점 간 거리 0.72/0.82/0.86; fig5)

와 **일관되게 맞물리는** 최근 연구 흐름만 추린다. (지침: 새 문제축·RL 고도화
금지 전제. 순수 분석·프레이밍 위주.)

---

## 1. 정합하는 문헌 흐름 (consistent threads)

### 1.1 Landscape 특성화: FDC → Local Optima Networks(LON)
- Boese의 big-valley FDC 산점도(우리 fig5가 이 계열)를 넘어, 현재 조합최적화
  landscape의 표준 도구는 **LON**(local optima=노드, perturbation 전이=엣지).
- 핵심 정합점: **"단일 big-valley → 다중 funnel"**. TSP조차 단일 골짜기가
  아니라 여러 funnel로 분해됨이 밝혀짐. → 우리의 *FDC 양수 + 높은 공간분산 +
  작은 gap*은 **'많고 얕은 funnel(평평한 다중 골짜기)'**로 해석하는 것이 문헌과
  정합. LON이 이를 판별.
- 근거: Ochoa & Veerapen, *Mapping the global structure of TSP fitness
  landscapes* (J. Heuristics); Verel/Daolio/Ochoa/Tomassini, QAP LON 샘플링
  (PPSN); *Visualizing Multimodality in Combinatorial Search Landscapes* (2024,
  arXiv:2510.06517).

### 1.2 Perturbation 세기 × 전역 구조
- ILS의 **kick 세기**가 funnel 간 이동 능력을 좌우한다는 결과. 평평·다중 funnel
  이면 약한 kick으로 충분, 깊은 소수 funnel이면 강한 kick 필요.
- 정합점: 우리 B2에서 **restart(+0.069%)는 기여하나 SA 확률수락은 무기여** →
  "얕은 다중 funnel에서 약한 재시작만으로 충분"이라는 그림과 일치.
- 근거: Thomson/Ochoa/Verel, *Perturbation Strength and the Global Structure of
  QAP Fitness Landscapes* (PPSN 2018).

### 1.3 학습형 연산자 선택(AOS/RL): "언제 학습이 돕는가"
- 2024–25 서베이 물결. AOS를 **credit-assignment + selection-policy**로 분해하는
  틀이 표준. "학습이 이겼다"는 보고가 스케줄링(iterated greedy+Q-learning 등)
  에서 계속 나옴.
- 정합점: 우리 **negative-RL(uniform ≈ tabular ≈ DQN, 방향 예산의존)**은 이
  흐름에 대한 *통제된 반례*. §7의 "저렴평가·정적·포화예산·강한 LS 4조건에서
  학습 무효"는 이 서베이들의 "AOS 이득은 문제·예산 의존" 주장과 정합.
- 근거: Pei et al., *Adaptive Operator Selection for Meta-Heuristics: A Survey*
  (IEEE Trans. AI, 2025); Yang et al., *Advancements in Q-learning
  meta-heuristic optimization algorithms: A survey* (WIREs DMKD, 2024);
  *Q-learning into iterated greedy for permutation flowshop* (EJOR, 2023).

### 1.4 크로스도킹 도메인 현행성
- 최근 방법: flow-based 정식화 + RL strategic oscillation(door assignment,
  EJOR 2023); neural branch-and-price + metaheuristic(C&OR 2024); 최근접
  경쟁자 Q-ALNS(Li et al., arXiv:2412.09090, 우리 [6]).
- 정합점: 도메인도 "고전 메타휴리스틱(ILS/GRASP/IG) + 학습" 결합이 주류 →
  우리 프레이밍(강한 결정론 엔진 + 학습은 ablation)이 시의적절.

---

## 2. 우리 실험/논문에 넣을 것 (일관성 있는 것만, 우선순위)

| # | 추가 | 정합 근거 | 노력 | 임팩트 |
|---|---|---|---|---|
| **A** | **LON 분석**: descent+거리 기계에 "perturbation→재-descent 전이"만 더해 local-optima 네트워크 구축, funnel 수·크기 정량화 (fig6) | 1.1 | 중 | 최고 |
| **B** | **Perturbation-강도 스윕** (`restart_kick`=1~8) → 평평 landscape에서 강한 kick 불요 실증 | 1.2 | 소 | 높음 |
| **C** | **AOS 서베이 포지셔닝**: §2·§7에서 Pei'25·Yang'24 인용, credit/selection 분해 틀로 negative-RL을 반례로 명시 | 1.3 | 소(글) | 높음 |
| **D** | **관련연구 현행화**: §2에 Li'23 oscillation, neural B&P'24 추가 | 1.4 | 소(글) | 중 |

**권장 순서: C·D(저비용 글) 즉시 → B(저비용 실험) → A(핵심 분석).**
A(LON)가 §7을 "추측 → field-standard 증거"로 승격하는 최대 레버.

## 3. 넣지 말 것 (정합성 낮음 / 지침 위반)
- **ELA 기반 landscape-aware 알고리즘 선택**: 연속최적화 도구. 조합 대응물은
  LON → A로 대체, ELA는 future work 언급만.
- **학습형 AOS를 이기게 만드는 튜닝**(RL 고도화): 지침 위반.
- 단일-big-valley로 과단정: 우리 데이터(높은 분산)는 **다중 얕은 funnel**에 더
  가까움 → LON 전에는 "operationally big-valley(fitness 기준)"로 신중 표기.

## 4. 참고문헌 (확인된 링크)
- Ochoa & Veerapen — Mapping the global structure of TSP fitness landscapes,
  J. Heuristics. https://d-nb.info/1135460795/34
- Visualizing Multimodality in Combinatorial Search Landscapes, 2024.
  https://arxiv.org/pdf/2510.06517
- Thomson/Ochoa/Verel — Perturbation Strength and the Global Structure of QAP,
  PPSN 2018. https://link.springer.com/chapter/10.1007/978-3-319-99259-4_20
- Pei et al. — Adaptive Operator Selection for Meta-Heuristics: A Survey,
  IEEE Trans. AI 2025. https://ieeexplore.ieee.org/document/10904096/
- Yang et al. — Q-learning meta-heuristic optimization survey, WIREs 2024.
  https://wires.onlinelibrary.wiley.com/doi/full/10.1002/widm.1548
- Q-learning + iterated greedy for flowshop, EJOR 2023.
  https://www.sciencedirect.com/science/article/abs/pii/S0377221722002788
- Li et al. — flow-based + RL strategic oscillation, EJOR 2023.
  https://www.sciencedirect.com/science/article/abs/pii/S0377221723005520
- Neural branch-and-price + metaheuristic for cross-docks, C&OR 2024.
  https://www.sciencedirect.com/science/article/abs/pii/S0305054824000765
- Li et al. — Q-ALNS (mixed service mode docks), arXiv:2412.09090 (우리 [6]).
  https://arxiv.org/pdf/2412.09090

> 관련: [[research_deepening_plan]](research_deepening_plan.md) T3-1(§7 실증) ·
> [[d1_results]] · landscape 산출물 outputs/landscape*, fig5_landscape_fdc.svg.

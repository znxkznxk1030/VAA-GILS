<!--
C2 절 초안 (research/rl, 2026-11-07). SCI(E) 원고용 영어 초안.

작성 원칙과 확인할 점
- docs/scie_plan_stream.md 7절에 따라 VAA-GILS, 유도 연산자, JKIIE 결과는 쓰지 않았다. 사이클 풀이기는 원 논문의 VAA·SA-RL5와 CP-SAT만.
  "Extended-SA-RL5" 명칭도 쓰지 않고 "SA-RL5 with the tardiness term"으로 썼다.
- 숫자 출처: outputs/stream_gap_decomposition.txt, outputs/stream_hindsight_bias.txt, outputs/stream_eval.jsonl
  (야드 대기·사이클 대기는 이 초안을 위해 stream_eval.jsonl에서 다시 집계), outputs/stream_cycle_quality.txt,
  outputs/stream_behavior.txt, docs/stream_rl_research.md 5.6·5.7·5.9·5.10절.
- 절·그림·표·식 번호는 [Sec. X], [Fig. X] 같은 자리표시. 앞 절(모형, 방법, 실험 설계)에서 정의할 용어:
  FCFS-VAA, Tuned-Rule, RL-API, Rollout, Rollout-Oracle, Cyclic-*, HS-event, HS-free, J/work, SLA, tuning/test pool.
- 5.7절(사후 교사 증류)과 5.9절(2세대 교사)은 tuning 셋, 학습 시드 하나의 결과라 본문에서 "tuning-set evidence"로 낮춰 썼다.
- 운송 빈도 경직(L2)의 수치(freq_gap)는 tuning 셋의 Cyclic-VAA 값이다. Cyclic-CPSAT 값으로 다시 재면 바꿀 것.
- 문헌 인용: Sinclair et al. (2022) hindsight learning, Bertsekas (2020) rollout. 서지 확인 후 참고문헌에 추가.
-->

# 6. Where the gap comes from

The previous section ranked the policies. This section asks a structural question: of the cost that a simple dispatching rule leaves on the table, how much is due to the way static optimization is embedded in the stream, how much to the dispatching policy, how much to missing information about future arrivals, and how much to the limits of one-step look-ahead. We answer it with a gap decomposition (Section 6.1–6.4) and then explain why a teacher that sees the future does not help a learned policy (Section 6.5).

## 6.1 Decomposition method

A decomposition is only meaningful if its parts add up. We therefore express every policy as a *rung* on a ladder with one common reference and compute all rungs from paired per-instance ratios. For instance *i* and policy *π*,

    g_i(π) = J_i(π) / J_i(ref) − 1,

and the rung of *π* is the mean of g_i(π) over instances. The *step* between two consecutive rungs is the mean of the paired difference g_i(π_a) − g_i(π_b), so the steps sum exactly to the total gap between the top and the bottom rung. We report 95% confidence intervals from a paired bootstrap over instances (10,000 resamples) and Wilcoxon signed-rank tests on the paired differences.

Two ladders are used, because no single benchmark covers both questions.

- **Continuous streams** (test pool, sizes S and M, 60 streams; [Sec. X]). The reference is FCFS-VAA. The rungs are the cycle-optimal static plan (Cyclic-CPSAT), FCFS-VAA, the tuned priority rule, the distilled network (RL-API), the Rollout teacher, and Rollout with access to the realized future arrivals (Rollout-Oracle). No hindsight optimum is available for an endless stream, so this ladder ends at Rollout-Oracle.
- **Finite instances** (S facility, *n* = 6 trucks: 30 instances; *n* = 10 trucks: 12 instances; [Sec. X]). The reference is HS-event, the best perfect-information schedule within the policies' action space found by CP-SAT. This ladder extends below Rollout-Oracle to the hindsight optimum and therefore separates information from optimization.

The two ladders use different references and are never merged on one axis.

## 6.2 The static framework is the largest loss

Table 6.1 and Fig. 6.1(a) give the continuous ladder. Solving every cycle to optimality and executing the plans adaptively (Cyclic-CPSAT) costs 29.6% more than the state-based FCFS-VAA rule (95% CI 23.8–36.1; worse in 60 of 60 streams). This is the largest single step in the decomposition, larger than everything that separates FCFS-VAA from Rollout-Oracle combined (18.3 pp).

**Table 6.1.** Continuous streams, test pool S+M (60 streams). Rungs: mean per-stream J/work relative to FCFS-VAA. Steps add up to the total.

| Rung | Gap to FCFS-VAA | 95% CI |
|---|---:|---|
| Cyclic-CPSAT | +29.6% | +23.9, +36.3 |
| FCFS-VAA | 0 | |
| Tuned-Rule | −6.8% | −8.5, −5.2 |
| RL-API | −11.5% | −13.1, −9.9 |
| Rollout | −14.9% | −16.8, −13.2 |
| Rollout-Oracle | −18.3% | −20.1, −16.6 |

| Step | Size (pp) | 95% CI | Streams improved | Wilcoxon *p* |
|---|---:|---|---:|---:|
| Static framework (Cyclic-CPSAT → FCFS-VAA) | 29.6 | 23.8, 36.1 | 60/60 | 1.6 × 10⁻¹¹ |
| Rule tuning (→ Tuned-Rule) | 6.8 | 5.2, 8.5 | 52/60 | 2.1 × 10⁻⁹ |
| Learned policy (→ RL-API) | 4.7 | 3.8, 5.5 | 56/60 | 7.2 × 10⁻¹⁰ |
| Distillation loss (RL-API → Rollout) | 3.5 | 2.2, 4.9 | 55/60 | 2.3 × 10⁻¹⁰ |
| Information (Rollout → Rollout-Oracle) | 3.4 | 3.1, 3.7 | 60/60 | 1.6 × 10⁻¹¹ |

The loss does not come from the cycle solver. On 144 cycles extracted from tuning streams and solved to proven optimality, the static objective of VAA is 19.2% above the optimum, SA-RL5 with the tardiness term 0.63%, and CP-SAT 0 ([Sec. X]). In the stream, however, Cyclic-SA-RL5 and Cyclic-CPSAT are within one percentage point of each other (S: +27.7% and +27.6%; M: +33.1% and +31.6% relative to FCFS-VAA), and only the step from VAA to an improvement search matters (Cyclic-VAA: +38.5% and +74.5%). Beyond a reasonable cycle solution, better static optimization buys nothing in operation.

The loss comes from the framework. Three mechanisms are visible in the data.

1. **Cycle formation.** A cycle can be planned only once |D| trucks have arrived. Trucks wait on average 0.42 (S) and 0.43 (M) mean truck works for their cycle to form, identical for every cyclic method because it does not depend on the solver. Total yard waiting under Cyclic-CPSAT is 0.79 and 0.94 mean truck works, 6.4 and 4.7 times that of FCFS-VAA (0.12 and 0.20).
2. **Rigid transport frequency.** The static representation assigns exactly one carrier per destination and cycle, so each destination receives a share 1/|D| of the carriers regardless of its freight share. Under skewed demand the L1 distance between carrier shares and freight shares is 0.52 for the cyclic plan, against 0.28 for FCFS-VAA and 0.05 for RL-API (tuning streams).
3. **Plan–execution mismatch.** The static model assumes that all doors are free and all compound trucks of a cycle dock together. In the stream, doors are occupied by the previous cycle; the adaptive execution used here already relaxes the plan (nearest free door, carriers wait for their freight), and the loss remains.

The framework loss grows with congestion: +12.2%, +24.9% and +51.7% at nominal loads 0.5, 0.6 and 0.7 (S+M). It is also slightly larger for the larger facility (S: +27.6%, M: +31.6%).

## 6.3 Within state-based policies: tuning, non-linear judgement and look-ahead

Below FCFS-VAA the ladder descends in three comparable steps (Table 6.1). Tuning a nine-feature priority rule on the training pool gains 6.8 pp. The distilled network gains a further 4.7 pp. This step is not explained by information: a linear score over exactly the network's 24 candidate features, tuned by the same procedure, is no better than the nine-feature rule ([Sec. X]). Both tuned scores converge to never holding, whereas RL-API holds in about 13% of its decisions; the gain is non-linear judgement about *when* to wait. Rollout gains a further 3.5 pp over its own distilled network. This *distillation loss* is the price of a 0.2 ms decision instead of a 28–91 ms one, and it is of the same size as the value of knowing the future arrivals (3.4 pp).

## 6.4 Information versus optimization

The continuous ladder cannot say how far Rollout-Oracle is from optimal. The finite ladder can (Table 6.2, Fig. 6.1(b, c)).

**Table 6.2.** Finite S instances. Rungs: mean per-instance cost relative to HS-event; brackets: 95% CI.

| Rung | *n* = 6 (30 instances) | *n* = 10 (12 instances) |
|---|---:|---:|
| FCFS-VAA | +14.8% [11.1, 18.8] | +24.3% [16.8, 32.7] |
| Tuned-Rule | +14.2% | +22.5% |
| RL-API | +17.0% | +16.5% |
| Rollout | +8.0% [6.1, 10.1] | +10.3% [7.9, 12.6] |
| Rollout-Oracle | +8.2% [5.0, 12.0] | +6.1% [4.8, 7.5] |
| HS-event | 0 | 0 |

| Step | *n* = 6 | *n* = 10 |
|---|---|---|
| Look-ahead (FCFS-VAA → Rollout) | 6.8 pp [3.4, 10.4], *p* = 0.0014 | 14.0 pp [5.8, 22.5], *p* = 0.0093 |
| Information (Rollout → Rollout-Oracle) | −0.2 pp [−3.0, 2.3], *p* = 0.74 | 4.2 pp [1.9, 6.8], *p* = 0.0034 |
| Optimization (Rollout-Oracle → HS-event) | 8.2 pp [5.0, 12.0], *p* = 2.6 × 10⁻⁶ | 6.1 pp [4.8, 7.5], *p* = 0.0005 |

Is HS-event a valid stand-in for the optimum? It restricts docking to arrival and departure epochs, the same action space as the policies. On the 15 instances with *n* = 6 where both HS-event and the free-timing relaxation (HS-free) were proven optimal, HS-event is on average 0.61% above the free-timing optimum (maximum 6.1%). The event restriction therefore costs little, and the remaining gap is not an artefact of the action space. For *n* = 10 no instance was proven optimal within the time limit; HS-event is the best schedule found, and the true optimization gap may be larger than reported.

Three findings follow.

- **Look-ahead closes about half of the rule's gap to the hindsight optimum** (46% at *n* = 6, 58% at *n* = 10).
- **Information explains a minority of what remains.** Of Rollout's gap to HS-event (8.0% and 10.3%), knowing the realized arrivals explains essentially none at *n* = 6 and 41% at *n* = 10. The larger share grows with instance size, but twelve instances do not establish a trend.
- **The rest is an optimization gap that one-step improvement does not close.** Even with the future known, Rollout-Oracle remains 6–8 pp above HS-event in 41 of 42 instances.

The optimization gap resisted every attempt to close it within the policy-improvement family. Quadrupling the look-ahead computation (32 samples, two SLA horizon) changes the continuous-stream cost by +0.9% (*p* = 0.12, test pool). Replacing the base policy of the rollout by the distilled network—a second policy-iteration step—changes the tuning-set cost from 1.627 to 1.616 J/work (*p* = 0.85). Enlarging the action space with a carrier claim-timing decision under time-varying destination demand gains 1.3–2.1% and leaves the value of information unchanged ([Sec. X]). One-step improvement over a rule appears to be saturated for this problem; closing the remaining gap would require multi-step search over joint decisions rather than more samples or a better base policy.

RL-API ranks below FCFS-VAA at *n* = 6 because it was trained only on endless streams and has no notion of a shift end. We use the finite instances to decompose Rollout's gap, not to rank the learned policy.

## 6.5 Why a teacher that sees the future does not help

The finite ladder shows that the realized future is worth little to Rollout. One might still expect it to be a better *teacher*: hindsight learning distills, at each state, the action that is best for the realized exogenous future, and has been effective in resource-allocation problems where the hindsight bias is small (Sinclair et al., 2022). In our setting, distilling such labels gave a tuning-set cost of 1.759 J/work, against 1.680 for distilling the eight-sample Rollout teacher ([Sec. X]; one training seed per configuration).

We measured the quality of the labels directly. At 1,440 states visited by the Rollout teacher on the 12 tuning streams, each shortlisted action (6.4 on average) was simulated over one SLA under 40 futures with common random numbers and the same base policy as the teacher. A future drawn this way has, given the state, the same distribution as the realized future, so a label computed from one future has the distribution of a hindsight label. The expected-cost-best action *a** is estimated on 24 held-out futures; labels are formed from groups of *m* of the remaining 16 futures. Regret is normalized so that 0 is *a** and 1 is a uniformly random shortlisted action. Confidence intervals bootstrap over streams.

**Table 6.3.** Label quality versus the number of futures per label (*m* = 1: hindsight label; *m* = 8: Rollout teacher).

| *m* | Agreement with *a** | Normalized regret |
|---:|---:|---:|
| 1 | 54.7% [50.3, 58.8] | 0.327 [0.286, 0.372] |
| 2 | 61.3% | 0.233 |
| 4 | 67.8% | 0.164 |
| 8 | 75.0% [71.2, 78.1] | 0.104 [0.082, 0.131] |
| 16 | 79.5% | 0.075 |

A hindsight label agrees with the expected-cost-best action in only 55% of states, and its regret is about three times that of the Rollout label (Table 6.3, Fig. 6.2). Across 16 futures, the hindsight-best action takes 3.5 different values on average. The hindsight bias of the value, E_k min_a C − min_a E_k C, amounts to −0.48 [−0.56, −0.40] times the regret of a random action: knowing the future would allow a much lower cost, but through an action that changes from one future to the next. Labels are worst exactly where waiting is optimal (9.1% of states), where hindsight labels agree with *a** in 34% of cases against 60% for Rollout labels. The disagreement is not driven by a single quantity such as the time to the next arrival—the share of HOLD labels varies only from 8.0% to 9.4% across terciles of that time—but by the whole realization over the horizon.

The assumption that makes hindsight learning work, a small hindsight bias, therefore fails here. For a policy that observes only the current state, a hindsight label is a label with large random error, and averaging over sampled futures is the better teacher. Label quality keeps improving with *m* but slowly beyond eight futures, consistent with the absence of a gain from larger rollouts. The estimate *a** itself rests on 24 futures, so agreement rates are bounded below 100% and should be compared across *m* rather than read absolutely.

## 6.6 Summary

1. Embedding static optimization in a continuous stream costs about 30% against a simple state-based rule, and solving each cycle optimally does not reduce this loss. The loss is structural: cycle formation, a fixed carrier frequency and plan–execution mismatch.
2. Among state-based policies, rule tuning, non-linear learned judgement and look-ahead contribute steps of similar size (6.8, 4.7 and 3.5 pp). Distilling the look-ahead into a sub-millisecond policy costs about as much as not knowing the future.
3. Rollout remains 8–10% above the hindsight optimum on small finite instances. Information explains at most about two fifths of that gap; the rest is an optimization gap that more samples, a better base policy, a hindsight teacher or an additional timing decision did not close.
4. Hindsight teachers fail because their labels are noisy for a state-based learner (55% agreement, three times the regret), not because the future is uninformative.

**Fig. 6.1.** Gap decomposition. (a) Continuous streams: mean per-stream J/work relative to FCFS-VAA; consecutive rungs add up to the total. (b, c) Finite S instances: gap to the best perfect-information schedule in the policy action space (HS-event). Whiskers: paired bootstrap 95% CI. *(paper/figures/stream_gap_decomposition.pdf)*

**Fig. 6.2.** Quality of teacher labels versus the number of sampled futures per label. (a) Agreement with the expected-cost-best action; (b) regret normalized to a random shortlisted action. *m* = 1 corresponds to a hindsight label, *m* = 8 to the Rollout teacher. Bands: 95% CI, bootstrap over streams. *(paper/figures/stream_hindsight_bias.pdf)*

# Algorithm 1 의사코드 초안 (3장 "반복 탐색" 문단)

- 대응 심사 의견: R1-11 (후보해 수락 여부, 하강 탐색 적용 조건, 최선해 갱신 순서를 의사코드로 구체화), R2-9 (구성요소가 어떤 순서와 조건으로 수행되는지, flow chart 또는 pseudocode), R1 총평 (재현성)
- 반영 위치: 3장 "반복 탐색(iterated search)" 문단 바로 뒤. 흐름도(R1-10)는 이 의사코드의 줄 번호에 맞춰 그린다.
- 근거 코드: `crossdock_solver/baselines/vaa_qrl.py`의 `run_vaa_qrl`(주 반복), `_descent`, `_descent_moves`. 최종 엔진의 설정은 균등 선택, 탐욕적 수락, 하강 탐색과 섭동 재시작 사용이다.
- 표기 언어: 원고의 그림·표 캡션이 영문이므로 의사코드도 영문으로 썼다.

## 주석 표기 방법

`vaa_regret.md`와 같다. `> [주석 n | 의견 번호 | 구분]` 줄이 수정 표시이고, 원고에 옮길 때는 주석 줄을 뺀다. 주석 번호는 이 파일 안에서 새로 매긴다(A1, A2, …).

## 의사코드

**Algorithm 1.** VAA-GILS

```
Input : instance; operator set Ω = Ω_K ∪ Ω_G, where Ω_K is the set of
        7 generic operators (k1–k8) and Ω_G the set of 4 bottleneck-guided
        operators (g1–g4); iteration limit N = 1,000;
        restart threshold P = 30; kick strength K = 3
Output: best solution s*

 1: s ← VAA(instance)                       ▷ initial solution construction
 2: s ← Descent(s)
 3: s* ← s;  c ← 0                          ▷ c: iterations since s* was last updated
 4: for n = 1 to N do
 5:     select an operator ω ∈ Ω uniformly at random
 6:     if ω ∈ Ω_G then s′ ← GuidedMove(s, ω) else s′ ← ω(s)   ▷ candidate from the current solution
 7:     if J(s′) < J(s*) then               ▷ new best solution
 8:         s′ ← Descent(s′)
 9:         s* ← s′;  c ← 0
10:     else
11:         c ← c + 1
12:     end if
13:     if J(s′) < J(s) then                ▷ greedy acceptance
14:         s ← s′
15:     end if
16:     if c ≥ P then                       ▷ kick restart
17:         s ← s*
18:         repeat K times
19:             select κ ∈ Ω_K uniformly at random;  s ← κ(s)   ▷ κ: one generic move (k1–k8)
20:         end repeat
21:         c ← 0
22:     end if
23: end for
24: s* ← Descent(s*)
25: return s*
```

```
Procedure Descent(s)
 1: loop
 2:     N(s) ← all solutions obtained from s by
 3:            (i)   moving one outbound truck to any door and any position,
 4:            (ii)  swapping the doors of two compound trucks, or moving one
 5:                  compound truck to an unoccupied door,
 6:            (iii) swapping the destinations of two trucks
 7:     s⁺ ← argmin { J(x) : x ∈ N(s) }
 8:     if J(s⁺) < J(s) then s ← s⁺ else return s
 9: end loop
```

```
Procedure GuidedMove(s, g)
    Input: current solution s, guided operator g in {g1, g2, g3, g4}
    Output: an improved solution, or s if no improvement exists
    candidates: solutions obtained by the specified feasible moves
    J: objective function to minimize

 1: if no truck is tardy in s then
 2:     if g = g3 then g <- g1
 3:     if g = g4 then g <- g2
 4: end if

 5: switch g:
 6:     case g1:
 7:         target <- last outbound truck on the latest-finishing door
 8:         candidates <- relocate target to each feasible door and position

 9:     case g2:
10:         target <- truck with the latest completion time
11:         candidates <- swap target's destination with each other truck

12:     case g3:
13:         target <- truck with the greatest tardiness
14:         if target is an outbound truck then
15:             candidates <- relocate target to each feasible door and position
16:         else
17:             candidates <- swap doors with each other compound truck,
18:                           or move target to each unoccupied door
19:         end if

20:     case g4:
21:         target <- truck with the greatest tardiness
22:         candidates <- swap target's destination with each other truck
23: end switch

24: best <- s
25: for each candidate in candidates do
26:     if J(candidate) < J(best) then
27:         best <- candidate
28:     end if
29: end for
30: return best
```

병목의 정의(본문 "연산자 집합" 문단에 넣는다):

- 병목 도어(critical door) $m^*$: 마지막 작업의 완료 시각이 가장 늦은 도어. 도어 $m$에 배정된 트럭들의 완료 시각 중 최댓값을 $FT_m$이라 하면 $m^* = \arg\max_{m \in M} FT_m$이고 $FT_{m^*} = C_{\max}$이다.
- 병목 트럭(critical truck) $q^*$: 완료 시각이 가장 늦은 트럭, $q^* = \arg\max_{q \in I \cup F} C_q$.
- 최대 지연 트럭(most tardy truck) $q^T$: 납기지연이 가장 큰 트럭, $q^T = \arg\max_{q} T_q$ (단, $T_{q^T} > 0$). 납기지연이 있는 트럭이 없으면 정의되지 않는다.

> [주석 A7 | R1-12, R2-9, 자체 | 추가] 유도 연산자를 GuidedMove 절차로 따로 적고 병목의 정의를 식으로 넣는다. 이유: 병목 유도 연산자는 본 연구가 원 모델에 더한 구성요소인데, 주 절차에서는 5행의 $\Omega$ 안에 들어 있어 드러나지 않는다. R1-12가 병목 도어와 병목 트럭의 정의를 명시하라고 요구했고, R2-9가 구성요소를 구체적으로 설명하라고 요구했다. 기본 이웃(k)이 트럭과 도어를 무작위로 고르는 것과 달리, 유도 연산자는 병목이 되는 트럭 하나를 정한 뒤 그 트럭의 이동을 모두 평가해 가장 좋은 것을 택한다는 차이를 5~30행으로 보였다. 정의와 절차는 `fast_evaluator.py`와 `vaa_qrl.py`의 `_critical_outbound_relocate`, `_critical_destination_swap`, `_tardy_truck_relocate`, `_tardy_destination_swap`에서 확인했다.

> [주석 A8 | 자체 | 수정] 입력에서 연산자 집합을 $\Omega = \Omega_K \cup \Omega_G$로 나누었다. 아래 첨자는 연산자 이름과 맞춘 것으로, $\Omega_K$는 기본 이웃 k1~k8, $\Omega_G$는 병목 유도 연산자 g1~g4의 집합이다. 6행은 뽑힌 연산자가 유도 연산자이면 GuidedMove를 호출하고, 기본 이웃이면 무작위 이동 하나를 적용하도록 나누어 적었다. 이유: 처음 초안은 6행이 $s' \leftarrow \omega(s)$뿐이어서 GuidedMove 절차가 주 절차 어디에서 호출되는지 보이지 않았다. 줄 수는 그대로여서 흐름도의 줄 번호는 바뀌지 않는다. 흐름도에도 같은 위치(5~6행 상자 옆)에 연산자 집합 설명을 넣었다.

> [주석 A1 | R1-11, R2-9 | 추가] Algorithm 1 전체를 새로 넣는다. 이유: R1-11이 요구한 세 가지가 각각 줄로 드러난다. 하강 탐색 적용 조건은 7~8행(후보가 최선해보다 좋을 때만), 최선해 갱신 순서는 8~9행(하강 탐색을 먼저 하고 그 결과로 갱신), 수락 여부는 13~14행(현재 해보다 엄격히 좋을 때만)이다. R2-9가 물은 구성요소의 순서와 조건도 같은 코드로 답한다.

> [주석 A2 | R1-11 | 추가] 판정 순서를 "최선해 판정(7행) → 수락 판정(13행) → 재시작 판정(16행)"으로 적었다. 이유: 코드의 실제 실행 순서이다. 13행에 들어가는 $s'$는 8행에서 하강 탐색을 거친 뒤의 해이다. 제출본 본문은 이 순서를 명시하지 않는다.

> [주석 A3 | R1-11, 자체 | 수정] 재시작 조건을 "$s^*$가 갱신되지 않은 반복 횟수 $c$가 30 이상"으로 적었다(3, 9, 11, 16행). 이유: 제출본은 "30회 연속 개선이 없으면"이라고 써서 현재 해 $s$의 개선으로도 읽힌다. 코드가 세는 것은 최선해가 갱신되지 않은 횟수이며, 현재 해가 개선되어도 최선해가 그대로면 횟수가 올라간다. 본문 문장도 함께 고쳐야 한다(아래 "본문에서 함께 고칠 문장").

> [주석 A4 | R2-9 | 추가] Descent를 별도 절차로 적었다. 이유: R2-9가 각 구성요소를 구체적으로 설명하라고 요구했다. 세 이동 유형은 제출본 "하강 탐색" 문단의 서술과 같고, 한 번에 세 유형의 모든 이웃을 평가해 가장 좋은 하나를 택한다는 점(최선개선)과 종료 조건(개선하는 이웃이 없음)을 식으로 보였다.

> [주석 A5 | R1 총평(재현성) | 추가] 입력에 $N$, $P$, $K$의 값을 적었다. 이유: 본문 여러 문단에 흩어진 설정값을 한곳에 모아 재현할 수 있게 한다. 세 값 모두 제출본에 이미 있는 값이다.

## 본문에 덧붙일 설명 문장

> VAA-GILS의 전체 절차는 Algorithm 1과 같다. 한 반복에서 후보 $s'$는 먼저 최선해 $s^*$와 비교되며(7행), $s^*$보다 좋을 때만 하강 탐색을 거쳐 $s^*$를 갱신한다(8~9행). 이어서 $s'$가 현재 해 $s$보다 엄격히 좋으면 받아들인다(13~14행). $s^*$가 $P$회 연속 갱신되지 않으면 $s^*$에서 다시 시작하여 기본 이웃에서 무작위로 고른 이동을 $K$회 적용한다(16~22행). $s^*$는 초기해 또는 하강 탐색을 거친 해이므로 항상 지역 최적해이다.

> [주석 A6 | R1-11, R2-9 | 추가] 의사코드를 가리키는 설명 문장을 새로 넣는다. 이유: 의사코드만 두면 본문과 연결되지 않는다. 줄 번호로 세 가지 요구(수락, 하강 탐색 조건, 갱신 순서)를 다시 짚었다.

## 본문에서 함께 고칠 문장

| 위치 | 제출본 | 수정안 | 의견 | 이유 |
|---|---|---|---|---|
| 3장 섭동 재시작 | 30회 연속 개선이 없으면 섭동 재시작을 수행한다. | 최선해 $s^*$가 30회 연속 갱신되지 않으면 섭동 재시작을 수행한다. | R1-11, 자체 | 주석 A3. 코드가 세는 대상과 표현을 맞춘다. |
| 3장 반복 탐색 | 후보가 전역 최선해를 개선하면 하강 탐색을 적용해 현재 최선해를 갱신한다. | 후보가 최선해 $s^*$보다 좋으면 하강 탐색을 적용하고 그 결과로 $s^*$를 갱신한다. | R1-11 | "전역 최선해"와 "현재 최선해"가 같은 대상을 가리키는데 용어가 둘이다. $s^*$ 하나로 통일하고 갱신 순서를 밝힌다. |
| 3장 연산자 집합 | (g3)/(g4) 납기지연이 가장 큰 트럭 기준의 동일 이동(납기지연이 있는 트럭이 없으면 g1/g2로 대체) | (g3) 납기지연이 가장 큰 트럭을 최선 위치로 재배치(출고트럭이면 도어와 작업 순서, 병행 트럭이면 도어 교환 또는 빈 도어 이동), (g4) 그 트럭의 목적지를 전 트럭과 대조해 최선 교환(납기지연이 있는 트럭이 없으면 각각 g1, g2로 대체) | R1-12, 자체 | g3는 병행 트럭도 다루므로 g1과 "동일 이동"이 아니다. |
| 3장 연산자 집합 | 현재 병목을 먼저 식별한 뒤 | 문장 앞에 병목 도어 $m^*$, 병목 트럭 $q^*$, 최대 지연 트럭 $q^T$의 정의를 넣는다. | R1-12 | 주석 A7. |
| 3장 반복 탐색 | 수락 규칙은 후보가 현재 해를 엄격히 개선할 때만 받아들이는 탐욕적 규칙이다. | (유지) 문장 끝에 "(Algorithm 1의 13~14행)"을 덧붙인다. | R1-11 | 수락 여부를 의사코드의 줄과 연결한다. |

## 확인한 사실과 판단이 필요한 점

- **24행의 최종 하강 탐색은 해를 바꾸지 않는다.** $s^*$는 2행 또는 8행에서 이미 하강 탐색을 거친 지역 최적해이므로, 24행에서 개선되는 이웃이 없다. 코드에는 있는 단계이고 제출본도 "최종해에 적용한다"고 썼으므로 의사코드에 남겼다. 빼면 의사코드가 짧아지지만 본문의 해당 구절도 함께 지워야 한다. 권고: 남기되 설명 문장의 마지막 문장("$s^*$는 … 항상 지역 최적해이다")으로 사실을 밝힌다.
- **새 최선해는 항상 수락된다.** 7행이 참이면 $J(s') < J(s^*) \le J(s)$이므로 13행도 참이다. 그래서 9행에 `s ← s′`를 합쳐 쓸 수도 있지만, 코드의 구조와 R1-11이 물은 "수락 여부"를 그대로 보이려고 두 판정을 나누어 두었다.
- **비교는 엄격한 부등호이다.** 코드는 허용오차 $10^{-9}$를 두고 비교한다. 의사코드에는 적지 않았다.
- **연산자 선택은 최종 엔진 기준(균등 선택)이다.** 5.3절의 학습 정책 비교는 5행의 선택 방법만 바꾼 것이므로, 5행에 "selection policy (uniform by default)"라고 적는 방안도 있다. 제안 방법의 일부가 아닌 학습 정책을 의사코드에 끌어들이지 않으려고 균등 선택으로 적었다.
- **섭동 재시작은 별도 절차가 아니라 16~22행 전체이다.** 19행의 $\kappa$는 함수가 아니라 기본 이웃 7종(k1~k8) 가운데 무작위로 뽑은 연산자 하나이며, 5행의 $\omega$와 같은 종류의 대상이다. 각 연산자의 내용은 "연산자 집합" 문단이 설명하므로 의사코드로 다시 쓰지 않았다. 혼동을 줄이려고 19행에 주석을 달았다. Descent처럼 `Kick(s*, K)` 절차로 빼는 방안도 있으나, 네 줄뿐이고 재시작 조건(16행)과 붙어 있어야 읽기 쉬워 본문에 두었다.
- **유도 연산자는 개선이 없으면 해를 그대로 돌려준다.** GuidedMove 24~30행에서 개선하는 이동이 없으면 $s' = s$가 되어, 주 절차의 7행과 13행이 모두 거짓이 되고 $c$만 늘어난다.
- **g3는 병행 트럭과 출고트럭에서 이동이 다르다.** 제출본은 g3/g4를 "납기지연이 가장 큰 트럭 기준의 동일 이동"이라고 썼다. 코드에서 g3는 최대 지연 트럭이 병행 트럭이면 도어 교환과 빈 도어 이동을, 출고트럭이면 도어·위치 재배치를 평가한다. g1은 출고트럭만 다루므로 "동일 이동"은 정확하지 않다. 본문 문장을 GuidedMove 14~19행에 맞춰 고쳐야 한다.
- **g1에서 병목 도어에 출고트럭이 없는 경우.** 코드는 이때 출고트럭 하나를 무작위로 고른다. 드문 경우라 의사코드에는 넣지 않았다. 본문에 한 구절로 밝힐지 정해야 한다.
- **시간 제한 분기는 넣지 않았다.** 코드에는 시간 예산이 주어지면 중단하는 분기가 있으나, 제안 방법의 실험은 반복 횟수로만 종료한다.
